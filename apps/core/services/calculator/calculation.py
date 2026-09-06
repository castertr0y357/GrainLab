import json
import logging

from django.db.models import F, FloatField
from django.db.models.functions import Power, Sqrt

from apps.core import gemma
from apps.core.engines import router
from apps.core.models import BreadPreset, DoughCategory, Equipment, FormFactor, SystemSetting, WheatBerry
from apps.core.utils import math as bakers_math

logger = logging.getLogger("grainlab.services")


def calculate_final_recipe(state: dict, run_ai: bool = False) -> dict:
    """
    Main calculation route adapted for multi-phase state.
    Processes Baker's Math and fail-safes, runs the Classifier Engine,
    queries Gemma client (or fallbacks), and outputs recipe context.
    """
    # 1. Parse parameters from state
    cat_slug = state.get("selected_master") or state.get("dough_category")
    if not cat_slug:
        raise ValueError("Missing selected_master (or dough_category) in state.")

    try:
        cat = DoughCategory.objects.get(slug=cat_slug)
    except DoughCategory.DoesNotExist:
        cat = DoughCategory.objects.first()
    preset_slug = state.get("preset_slug")

    engine = router.get_engine_for_preset(preset_slug, cat.slug)

    # Extract active archetype early to use its defaults
    archetype_id = state.get("active_archetype_id") or state.get("archetype_id") or preset_slug or ""
    active_arch = engine.archetypes.get(archetype_id, {})

    ff_slug = state.get("form_factor")
    if not ff_slug:
        # Check archetype default first, then fallback to first engine form factor
        ff_slug = active_arch.get("default_form_factor")
        if not ff_slug:
            ff_slug = (
                list(getattr(engine, "permissible_form_factors", {}).keys())[0]
                if getattr(engine, "permissible_form_factors", {})
                else None
            )

    # Validate ff_slug is permissible for active engine
    permissible_slugs = list(getattr(engine, "permissible_form_factors", {}).keys())
    if ff_slug not in permissible_slugs and permissible_slugs:
        for slug in permissible_slugs:
            if FormFactor.objects.filter(slug=slug).exists():
                ff_slug = slug
                break

    try:
        ff = FormFactor.objects.get(slug=ff_slug)
    except FormFactor.DoesNotExist:
        ff_config_dict = getattr(engine, "permissible_form_factors", {}).get(ff_slug, {})
        if not ff_config_dict:
            from django.http import Http404

            raise Http404(f"Form factor {ff_slug} not found.")
        ff = FormFactor(
            slug=ff_slug,
            name=ff_config_dict.get("label", ff_slug),
            is_portioned=ff_config_dict.get("is_portioned", False),
            unit_weight=ff_config_dict.get("unit_weight", 50),
            default_count=ff_config_dict.get("base_count", 12),
            is_enriched_profile=ff_config_dict.get("is_enriched_profile", False),
            bake_temp_f=ff_config_dict.get("bake_temp_f", 350),
            bake_time_min=ff_config_dict.get("bake_time_min", 15),
            steam_required=ff_config_dict.get("steam_required", False),
        )

    ff_config = getattr(engine, "permissible_form_factors", {}).get(ff.slug, {})
    is_portioned = ff_config.get("is_portioned", ff.is_portioned)
    base_unit_weight = ff_config.get("unit_weight", ff.unit_weight)
    base_default_count = ff_config.get("base_count", ff.default_count)
    base_weight = base_unit_weight * base_default_count

    try:
        texture_score = int(state.get("texture", state.get("texture_score", 50)))
    except (ValueError, TypeError):
        texture_score = 50

    try:
        crumb_score = int(state.get("crumb", state.get("crumb_score", 50)))
    except (ValueError, TypeError):
        crumb_score = 50

    # Base percentages from UI/AI State (if present), fallback to legacy static mapping
    try:
        base_hydration_pct = float(state.get("hydration_pct", -1)) / 100.0
    except (ValueError, TypeError):
        base_hydration_pct = -1.0

    try:
        base_fat_pct = float(state.get("fat_pct", -1)) / 100.0
    except (ValueError, TypeError):
        base_fat_pct = -1.0

    try:
        base_sugar_pct = float(state.get("sugar_pct", -1)) / 100.0
    except (ValueError, TypeError):
        base_sugar_pct = -1.0

    if base_hydration_pct >= 0:
        hydration_pct = base_hydration_pct
    else:
        hydration_pct = 0.45 + (crumb_score / 100.0) * 0.40

    if base_fat_pct >= 0:
        fat_pct = base_fat_pct
    else:
        fat_pct = (texture_score / 100.0) * 0.15

    if base_sugar_pct >= 0:
        sugar_pct = base_sugar_pct
    else:
        sugar_pct = (texture_score / 100.0) * 0.12

    try:
        starter_pct = float(state.get("starter", state.get("starter_pct", 0))) / 100.0
    except (ValueError, TypeError):
        starter_pct = 0.0

    grain_type = state.get("grain_type", "all_purpose")
    flour_maturity = state.get("flour_maturity", "matured")
    leaven_type = state.get("leaven_type", "yeast")

    try:
        room_temp = float(state.get("room_temp", 72))
    except (ValueError, TypeError):
        room_temp = 72.0

    try:
        flour_temp = float(state.get("flour_temp", 70))
    except (ValueError, TypeError):
        flour_temp = 70.0

    mixing_method = state.get("mixing_method", "stand_mixer")

    # Portioned handling
    try:
        unit_weight = float(state.get("unit_weight", base_unit_weight))
    except (ValueError, TypeError):
        unit_weight = float(base_unit_weight)

    try:
        portion_count = int(state.get("portion_count", base_default_count))
    except (ValueError, TypeError):
        portion_count = int(base_default_count)

    if is_portioned:
        target_mass = unit_weight * portion_count
    else:
        try:
            target_mass = float(state.get("target_weight", base_weight))
        except (ValueError, TypeError):
            target_mass = float(base_weight)

    try:
        salt_val = state.get("salt_pct")
        if salt_val is not None:
            salt_pct = float(salt_val) / 100.0
        else:
            salt_pct = active_arch.get("default_salt_pct", getattr(engine, "default_salt_pct", 0.02))
    except (ValueError, TypeError):
        salt_pct = active_arch.get("default_salt_pct", getattr(engine, "default_salt_pct", 0.02))

    try:
        leaven_val = state.get("leaven_pct")
        if leaven_val is not None:
            leaven_pct = float(leaven_val) / 100.0
        else:
            leaven_pct = starter_pct if leaven_type == "sourdough" else getattr(engine, "default_leaven_pct", 0.015)
    except (ValueError, TypeError):
        leaven_pct = starter_pct if leaven_type == "sourdough" else getattr(engine, "default_leaven_pct", 0.015)

    # 2. Process Substitution
    sub_orig = state.get("sub_original")
    sub_new = state.get("sub_substitute")
    substitution = None
    if sub_orig and sub_new:
        substitution = {"original": sub_orig, "substitute": sub_new}

    # 3. Calculate Baker's Math and apply fail-safes
    custom_mixer_id = state.get("custom_mixer")
    friction_override = state.get("friction_factor")
    if friction_override is None:
        if custom_mixer_id and str(custom_mixer_id) != "static":
            try:
                mixer = Equipment.objects.get(id=custom_mixer_id)
                friction_override = mixer.friction_heat_factor
            except (ValueError, Equipment.DoesNotExist):
                pass
    else:
        try:
            friction_override = float(friction_override)
        except (ValueError, TypeError):
            friction_override = None

    active_berries_state = state.get("active_berries", state.get("selected_grains", []))
    if isinstance(active_berries_state, str) and active_berries_state.strip():
        try:
            active_berries_state = json.loads(active_berries_state)
        except Exception:
            active_berries_state = []

    selected_grain_ids = []
    for b in active_berries_state:
        if isinstance(b, dict) and "id" in b:
            selected_grain_ids.append(str(b["id"]))
        else:
            selected_grain_ids.append(str(b))

    if selected_grain_ids:
        active_berries = list(WheatBerry.objects.filter(id__in=selected_grain_ids))
    else:
        active_berries = []

    preset_name = None
    if preset_slug:
        try:
            preset_obj = BreadPreset.objects.get(slug=preset_slug)
            preset_name = preset_obj.name
        except BreadPreset.DoesNotExist:
            pass

    try:
        ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"
        if ai_enabled and substitution and run_ai:
            recipe_state = {
                "effective_hydration_pct": hydration_pct * 100,
                "effective_fat_pct": fat_pct * 100,
                "effective_sugar_pct": sugar_pct * 100,
            }
            offset = gemma.get_substitution_offset(sub_orig, sub_new, recipe_state)
            if offset:
                hydration_pct = max(0.40, hydration_pct + offset.get("water_offset_pct", 0.0))
                fat_pct = max(0.0, fat_pct + offset.get("fat_offset_pct", 0.0))
                sugar_pct = max(0.0, sugar_pct + offset.get("sugar_offset_pct", 0.0))

        secondary_ingredients = state.get("secondary_ingredients") or {}
        if isinstance(secondary_ingredients, str) and secondary_ingredients.strip():
            try:
                secondary_ingredients = json.loads(secondary_ingredients) or {}
            except Exception:
                secondary_ingredients = {}
        elif not isinstance(secondary_ingredients, dict):
            secondary_ingredients = {}

        secondary_lipids = secondary_ingredients.get("lipids") or []
        secondary_liquids = secondary_ingredients.get("liquids") or []
        secondary_binders = secondary_ingredients.get("binders") or []
        secondary_sweeteners = secondary_ingredients.get("sweeteners") or []
        secondary_leaveners = secondary_ingredients.get("leaveners") or []
        secondary_additives = secondary_ingredients.get("additives") or []

        # Guard: AI sometimes mis-classifies eggs as a liquid medium since they provide moisture.
        # Re-route any egg value from liquid -> binder so it renders in the correct "Binder" row.
        _EGG_LIQUID_TERMS = ("egg", "aquafaba")
        actual_liquids = []
        for liq in secondary_liquids:
            if isinstance(liq, dict) and any(t in str(liq.get("name", "")).lower() for t in _EGG_LIQUID_TERMS):
                secondary_binders.append(liq)
            else:
                actual_liquids.append(liq)
        secondary_liquids = actual_liquids

        flavor_inclusions = state.get("flavor_inclusions") or []
        if isinstance(flavor_inclusions, str) and flavor_inclusions.strip():
            try:
                flavor_inclusions = json.loads(flavor_inclusions) or []
            except Exception:
                flavor_inclusions = []
        elif not isinstance(flavor_inclusions, list):
            flavor_inclusions = []

        flour_blend = state.get("flour_blend") or {}
        if isinstance(flour_blend, str) and flour_blend.strip():
            try:
                flour_blend = json.loads(flour_blend) or {}
            except Exception:
                flour_blend = {}
        elif not isinstance(flour_blend, dict):
            flour_blend = {}

        inferred_flavor_profile = state.get("inferred_flavor_profile", "neutral")

        recipe = bakers_math.calculate_recipe(
            base_hydration=hydration_pct,
            base_fat=fat_pct,
            base_sugar=sugar_pct,
            target_mass=target_mass,
            grain_type=grain_type,
            flour_maturity=flour_maturity,
            leaven_type=leaven_type,
            leaven_pct=leaven_pct,
            salt_pct=salt_pct,
            room_temp_f=room_temp,
            flour_temp_f=flour_temp,
            mixing_method=mixing_method,
            substitution=substitution if not ai_enabled else None,
            active_berries=active_berries,
            texture_score=texture_score,
            crumb_score=crumb_score,
            friction_override=friction_override,
            preset_slug=preset_slug,
            preset_name=preset_name,
            category_slug=cat.slug,
            secondary_lipids=secondary_lipids,
            secondary_liquids=secondary_liquids,
            secondary_binders=secondary_binders,
            secondary_sweeteners=secondary_sweeteners,
            secondary_leaveners=secondary_leaveners,
            secondary_additives=secondary_additives,
            flavor_inclusions=flavor_inclusions,
            flour_blend=flour_blend,
            inferred_flavor_profile=inferred_flavor_profile,
        )

        if ai_enabled and substitution and "offset" in locals() and offset:
            recipe["substitution_notes"] = [offset.get("explanation", "Balanced via AI substitution module.")]

    except Exception as e:
        logger.error(f"[Calculator] - Math Error - Failed executing Baker's Math: {str(e)}")
        raise e

    # 4. Classifier Engine: Euclidean distance match
    classified_preset = (
        BreadPreset.objects.annotate(
            distance=Sqrt(
                Power(F("classifier_texture") - texture_score, 2) + Power(F("classifier_crumb") - crumb_score, 2),
                output_field=FloatField(),
            )
        )
        .order_by("distance")
        .first()
    )

    # 5. Fetch AI Diagnostics (Sensory benchmark & pitfalls)
    eff_hyd = recipe["effective_hydration_pct"] / 100.0
    preset_slug_resolved = preset_slug or (classified_preset.slug if classified_preset else None)

    if run_ai:
        sensory_desc = gemma.get_sensory_benchmark(grain_type, flour_maturity, eff_hyd, cat.slug, preset_slug_resolved)
        pitfalls = gemma.get_contextual_pitfalls(cat.slug, eff_hyd, grain_type, preset_slug_resolved)
    else:
        sensory_desc = None
        pitfalls = []

    # 6. Core Thermal Doneness Temperature
    doneness_temp_f = 190 if ff_config.get("is_enriched_profile", ff.is_enriched_profile) else 205
    doneness_temp_c = round((doneness_temp_f - 32) * 5 / 9, 1)

    # 7. Resolve form factor baseline parameters from engine configuration
    base_temp = ff_config.get("bake_temp_f", ff.bake_temp_f)
    base_time = ff_config.get("bake_time_min", ff.bake_time_min)
    base_steam = ff_config.get("steam_required", ff.steam_required)

    if is_portioned:
        mass_ratio = 1.0
    else:
        mass_ratio = target_mass / base_weight if base_weight > 0 else 1.0

    scaled_time = round(base_time * (mass_ratio**0.4))
    scaled_temp = base_temp
    if not is_portioned:
        if mass_ratio > 1.2:
            scaled_temp = base_temp - 10
        elif mass_ratio < 0.8:
            scaled_temp = base_temp + 10

    # 7b. Query geometry advisory and apply offsets
    if run_ai:
        geom_advisory = gemma.get_geometry_advisory(preset_slug_resolved, preset_name, cat.slug, ff.slug) or {}
        geom_eval = geom_advisory.get("geometry_evaluation") or {}
        profile_adjustments = geom_eval.get("profile_adjustments") or {}
    else:
        geom_eval = {}
        profile_adjustments = {}

    temp_offset = int(profile_adjustments.get("oven_temp_offset_f", 0))
    time_offset = int(profile_adjustments.get("bake_time_offset_m", 0))
    steam_override = profile_adjustments.get("steam_override", "no-change")

    scaled_time = max(1, scaled_time + time_offset)
    scaled_temp = max(0, scaled_temp + temp_offset)

    if steam_override == "force-on":
        adjusted_steam = True
    elif steam_override == "force-off":
        adjusted_steam = False
    else:
        adjusted_steam = base_steam

    # 8. Calculate dynamic countdown timelines for Countertop Mode
    estimated_bulk_hours = 1.5
    estimated_proof_hours = 1.0

    if leaven_type == "sourdough":
        starter_feed_hours = state.get("starter_feed_hours", "4_8")
        rise_speed = state.get("flow_rise_speed", "normal")
        mill_type = state.get("mill_type", "stoneground")
        is_sifted = state.get("is_sifted") in ("on", "true", "True", True)

        if run_ai:
            calibration = gemma.calibrate_fermentation(starter_feed_hours, rise_speed, mill_type, is_sifted) or {}
            estimated_bulk_hours = calibration.get("estimated_bulk_fermentation_hours", 4.0) or 4.0
            estimated_proof_hours = 2.0
        else:
            estimated_bulk_hours = 4.0
            estimated_proof_hours = 2.0

    if room_temp < 70:
        estimated_bulk_hours += 1.0
    elif room_temp > 76:
        estimated_bulk_hours = max(0.5 if leaven_type == "yeast" else 3.0, estimated_bulk_hours - 1.0)

    proofing_env = state.get("proofing_environment", "ambient")
    if proofing_env == "mat":
        estimated_proof_hours *= 0.9
    elif proofing_env == "box":
        estimated_proof_hours *= 0.75

    estimated_bulk_minutes = int(estimated_bulk_hours * 60)
    estimated_proof_minutes = int(estimated_proof_hours * 60)

    # Resolve active sub-engine and load dynamic timeline steps
    active_engine = router.get_engine_for_preset(preset_slug_resolved, cat.slug)
    steps_list = active_engine.get_live_timeline_steps(
        recipe_data=recipe,
        estimated_bulk_minutes=estimated_bulk_minutes,
        estimated_proof_minutes=estimated_proof_minutes,
        bake_time_min=scaled_time,
        mixing_method=mixing_method,
        preset_slug=preset_slug_resolved,
    )
    countertop_steps_json = json.dumps(steps_list)

    return {
        "recipe": recipe,
        "ff": ff,
        "cat": cat,
        "sensory_description": sensory_desc,
        "pitfalls": pitfalls,
        "doneness_temp_f": doneness_temp_f,
        "doneness_temp_c": doneness_temp_c,
        "leaven_type": leaven_type,
        "classified_preset": classified_preset,
        "texture_score": texture_score,
        "crumb_score": crumb_score,
        "current_phase": int(state.get("current_phase", 4)),
        "bake_temp_f": scaled_temp,
        "bake_time_min": scaled_time,
        "estimated_bulk_minutes": estimated_bulk_minutes,
        "estimated_proof_minutes": estimated_proof_minutes,
        "countertop_steps_json": countertop_steps_json,
        "steam_required": adjusted_steam,
        "geometry_evaluation": geom_eval,
    }
