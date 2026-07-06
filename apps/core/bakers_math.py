import math
from grainlab.engines import router
from grainlab.engines.base_engine import BaseEngine

# Keep constants for backward compatibility
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


def calculate_wheat_berry_shares(active_berries: list, texture_score: int, crumb_score: int, preset_slug: str = None, preset_name: str = None) -> tuple[dict[str, float], float, str | None]:
    """
    Delegates to HearthEngine (BaseEngine) for shares calculations.
    """
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
    **kwargs
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
            min_distance = float('inf')
            for p in all_presets:
                dist = math.sqrt(
                    (p.classifier_texture - texture_score) ** 2 +
                    (p.classifier_crumb - crumb_score) ** 2
                )
                if dist < min_distance:
                    min_distance = dist
                    classified_preset = p
            if classified_preset:
                preset_slug = classified_preset.slug
                if classified_preset.dough_category:
                    category_slug = classified_preset.dough_category.slug
        except Exception:
            pass

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
        **kwargs
    )


def get_local_sensory_benchmark(grain_type: str, flour_maturity: str, effective_hydration: float, category_slug: str = None, preset_slug: str = None) -> str:
    # Identify group
    if category_slug in ['lean-crusty', 'enriched-soft', 'alkaline-bath', 'flatbreads-griddles', 'fried-doughs']:
        group = "bread"
    elif category_slug in ['quick-breads-scones', 'cakes-batters', 'pastry-lamination', 'cookies-shortbread', 'choux-paste']:
        group = "sweet_tender"
    elif category_slug in ['fresh-pasta-noodles']:
        group = "pasta"
    else:
        group = "bread"
        
    grain_name = grain_type.replace("_", " ").title()
    
    if group == "bread":
        desc = f"For fresh-milled {grain_name} dough: "
        if effective_hydration >= 0.75:
            desc += "The dough will be wet and sticky. Look for a glossy surface and a clean, dome-like rise. "
        elif effective_hydration >= 0.65:
            desc += "Expect a supple, holding structure. The dough should feel alive, resilient, and elastic when touched. "
        else:
            desc += "Dough is firm and tight. It will not double dramatically; monitor for a rounded dome and a smooth outer skin. "
            
        if flour_maturity == "just_milled":
            desc += "As this flour was milled today, gluten activity is highly active but lacks extensibility. Expect rapid enzyme fermentation; handle gently to avoid tearing."
        elif flour_maturity == "dead_zone":
            desc += "Caution: Flour is in the 1-2 week enzyme dead zone. Gluten structure is relaxed and vulnerable. The dough will feel sticky and might lack holding power; do not over-proof."
        else:
            desc += "Flour is fully matured. Gluten bonds are stable and predictable. The rise will be steady with solid gas retention."
            
    elif group == "sweet_tender":
        desc = f"For fresh-milled {grain_name} confections: "
        if category_slug == 'cookies-shortbread':
            desc += "Expect a thick, soft paste or firm chilled dough. The fat should be fully creamed with flour particles evenly coated to control spread. "
        elif category_slug == 'cakes-batters':
            desc += "Expect a highly aerated, smooth fluid batter. It should hold micro-air bubbles from egg/fat whipping with zero large pockets. "
        else:
            desc += "The batter/dough should be delicate and soft. Mixing should be kept to an absolute minimum to ensure a tender crumb. "
            
        if flour_maturity == "just_milled":
            desc += "As this flour was milled today, its enzymes will promote fast browning. Keep mixing short to avoid any accidental gluten development."
        elif flour_maturity == "dead_zone":
            desc += "Caution: Flour is in the 1-2 week dead zone. The structural proteins are slightly unstable. Bake promptly after mixing to ensure the rise sets correctly."
        else:
            desc += "Flour is fully matured. It will provide a highly stable, predictable structure and excellent tender mouthfeel."
            
    elif group == "pasta":
        desc = f"For fresh-milled {grain_name} pasta: "
        desc += "Expect a very dense, dry, and crumbly initial mixture. It should consolidate into a firm, non-sticky mass after firm pressure. "
        
        if flour_maturity == "just_milled":
            desc += "Today's fresh-milled flour hydrates rapidly but the gluten needs extra resting time. Let the wrapped dough sit for 45 minutes before sheeting."
        elif flour_maturity == "dead_zone":
            desc += "Caution: Flour is in the 1-2 week dead zone. The dough might feel slightly brittle during sheeting; roll out slowly to prevent edge cracking."
        else:
            desc += "Flour is fully matured. Gluten structure is stable and resilient, providing an excellent al dente bite when boiled."
            
    return desc


def get_local_contextual_pitfalls(category_slug: str, effective_hydration: float, grain_type: str, preset_slug: str = None) -> list[dict[str, str]]:
    pitfalls = []
    
    # Resolve the engine to see if there are custom pitfalls or warnings
    engine = router.get_engine_for_preset(preset_slug, category_slug)
    
    if preset_slug == "pretzel" or engine.slug == "bath":
        pitfalls.append({
            "title": "Mandatory Alkaline Bath",
            "message": "To achieve the signature deep mahogany color and unique flavor, you must boil the shaped pretzels in a 3% baking soda bath (or carefully dip in a 3% lye solution) for 30 seconds before baking."
        })
    
    if effective_hydration >= 0.78:
        pitfalls.append({
            "title": "High Hydration Handling",
            "message": "With a hydration of over 78%, this dough is wet. Do not add raw flour to the workspace; instead, perform 'stretch-and-folds' with wet hands to build gluten structure."
        })

    if grain_type in ["spelt", "kamut", "einkorn"]:
        pitfalls.append({
            "title": "Ancient Grain Fragility",
            "message": f"{grain_type.title()} has weaker gluten networks. Avoid intensive machine mixing. Prefer short hand mixing followed by gentle folds to keep the structure from collapsing."
        })
        
    if category_slug == "enriched-soft" or engine.slug == "pan":
        pitfalls.append({
            "title": "Fermentation Retardation",
            "message": "Fats and sugars slow down yeast fermentation. Allow for a longer bulk proof or create a warm, moist proofing box to encourage active rising."
        })

    # Default general fallback advice if empty
    if not pitfalls:
        pitfalls.append({
            "title": "Standard Proofing Check",
            "message": "Keep dough covered at a stable temp of 75-78°F. The poke test is your best guide: if a gentle indent springs back slowly, it is ready to bake."
        })
        
    return pitfalls
