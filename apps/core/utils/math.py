import logging
import math

logger = logging.getLogger(__name__)


# --- From shared_math.py ---
def f_to_c(f: float) -> float:
    return round((f - 32.0) * 5.0 / 9.0, 1)


def c_to_f(c: float) -> float:
    return round((c * 9.0 / 5.0) + 32.0, 1)


def scale_baking_profile(
    base_temp: float, base_time: float, base_weight: float, target_mass: float, is_portioned: bool
) -> tuple[float, float]:
    """
    Algorithmically scale baking profile (temperature and time) based on mass and form factor.
    """
    mass_ratio = target_mass / base_weight if base_weight > 0 else 1.0
    scaled_time = round(base_time * (mass_ratio**0.4))

    scaled_temp = base_temp
    if not is_portioned:
        if mass_ratio > 1.2:
            scaled_temp = base_temp - 10
        elif mass_ratio < 0.8:
            scaled_temp = base_temp + 10

    return scaled_temp, scaled_time


def calculate_yield_mass(is_portioned: bool, unit_weight: float, portion_count: int, target_weight: float) -> float:
    """
    Dynamic yield multiplier logic. Calculates total target mass of the recipe.
    """
    if is_portioned:
        return unit_weight * portion_count
    return target_weight


# --- From bakers_math.py ---
GRAIN_THIRST_MODIFIERS = {
    "all_purpose": 0.0,
    "whole_wheat": 0.03,
    "spelt": 0.05,
    "kamut": 0.06,
    "einkorn": 0.04,
}

MATURITY_HYDRATION_MODIFIERS = {
    "just_milled": 0.0,
    "dead_zone": -0.02,
    "matured": 0.0,
}

FRICTION_FACTORS = {
    "hand_knead": 2.0,
    "stand_mixer": 10.0,
    "bread_machine": 15.0,
}


def _get_val(obj, key, default=None):
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def calculate_wheat_berry_shares(
    active_berries: list, texture_score: int, crumb_score: int, preset_slug: str = None, preset_name: str = None
) -> tuple[dict[str, float], float, str | None]:
    """
    Delegates to HearthEngine (BaseEngine) for shares calculations.
    """
    from apps.core.engines import router

    engine = router.get_engine_for_preset(preset_slug)
    return engine.calculate_wheat_berry_shares(active_berries, texture_score, crumb_score, preset_slug, preset_name)


def calculate_recipe(
    base_hydration: float,
    base_fat: float,
    base_sugar: float,
    target_mass: float,
    grain_type: str = "all_purpose",
    flour_maturity: str = "matured",
    leaven_type: str = "yeast",
    leaven_pct: float = 0.015,
    salt_pct: float = 0.02,
    room_temp_f: float = 72.0,
    flour_temp_f: float = 70.0,
    mixing_method: str = "stand_mixer",
    substitution: dict[str, str] = None,
    active_berries: list = None,
    texture_score: int = 50,
    crumb_score: int = 50,
    friction_override: float = None,
    preset_slug: str = None,
    preset_name: str = None,
    category_slug: str = None,
    **kwargs,
) -> dict:
    """
    Resolves the active sub-engine and computes the recipe.
    """
    # If preset_slug and category_slug are missing (e.g. during standalone tests),
    # run a quick classification check to resolve the closest preset and category.
    if not preset_slug and not category_slug:
        try:
            from apps.core.models import BreadPreset

            all_presets = BreadPreset.objects.all()
            classified_preset = None
            min_distance = float("inf")
            for p in all_presets:
                dist = math.sqrt((p.classifier_texture - texture_score) ** 2 + (p.classifier_crumb - crumb_score) ** 2)
                if dist < min_distance:
                    min_distance = dist
                    classified_preset = p
            if classified_preset:
                preset_slug = classified_preset.slug
                if classified_preset.dough_category:
                    category_slug = classified_preset.dough_category.slug
        except Exception as e:
            logger.warning(f"Failed to auto-resolve BreadPreset during standalone calculation: {e}", exc_info=True)

    from apps.core.engines import router

    engine = router.get_engine_for_preset(preset_slug, category_slug)
    return engine.calculate_recipe(
        base_hydration=base_hydration,
        base_fat=base_fat,
        base_sugar=base_sugar,
        target_mass=target_mass,
        grain_type=grain_type,
        flour_maturity=flour_maturity,
        leaven_type=leaven_type,
        leaven_pct=leaven_pct,
        salt_pct=salt_pct,
        room_temp_f=room_temp_f,
        flour_temp_f=flour_temp_f,
        mixing_method=mixing_method,
        substitution=substitution,
        active_berries=active_berries,
        texture_score=texture_score,
        crumb_score=crumb_score,
        friction_override=friction_override,
        preset_slug=preset_slug,
        preset_name=preset_name,
        **kwargs,
    )


def get_local_sensory_benchmark(
    grain_type: str, flour_maturity: str, effective_hydration: float, category_slug: str = None, preset_slug: str = None
) -> str:
    from apps.core.engines import router

    engine = router.get_engine_for_preset(preset_slug, category_slug)
    return engine.get_sensory_benchmark(grain_type, flour_maturity, effective_hydration, category_slug, preset_slug)


def get_local_contextual_pitfalls(
    category_slug: str, effective_hydration: float, grain_type: str, preset_slug: str = None
) -> list[dict[str, str]]:
    from apps.core.engines import router

    engine = router.get_engine_for_preset(preset_slug, category_slug)
    return engine.get_contextual_pitfalls(effective_hydration, grain_type, preset_slug)
