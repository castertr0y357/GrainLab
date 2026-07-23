import logging
import math
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views import View

from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting, WheatBerry, Equipment, BackgroundTask
from apps.core import bakers_math
from apps.core import gemma_client
from apps.core.views.tasks import run_async_task, ai_analyze_wheat_berry_task, ai_analyze_equipment_task, bulk_ai_analyze_task, redo_ai_analysis_task

logger = logging.getLogger("grainlab.views")
executor = ThreadPoolExecutor(max_workers=2)


class CalculateRecipeAjaxView(View):
    def post(self, request):
        """
        Main calculation route. Intercepts inputs, processes Baker's Math and fail-safes,
        runs the Classifier Engine, queries Gemma client (or fallbacks), and outputs recipe card.
        """
        # 1. Parse parameters and scores
        cat_slug = request.POST.get("dough_category")
        ff_slug = request.POST.get("form_factor")
        current_phase_str = request.POST.get("current_phase", "1")
        try:
            current_phase = int(current_phase_str) if current_phase_str and current_phase_str.strip() else 1
        except ValueError:
            current_phase = 1
    
        cat = get_object_or_404(DoughCategory, slug=cat_slug)
    
        # Resolve active sub-engine based on preset and category
        preset_slug = request.POST.get("preset_slug")
        from grainlab.engines.router import get_engine_for_preset
        engine = get_engine_for_preset(preset_slug, cat.slug)
    
        # Validate ff_slug is permissible for active engine
        permissible_slugs = list(getattr(engine, "permissible_form_factors", {}).keys())
        if ff_slug not in permissible_slugs and permissible_slugs:
            for slug in permissible_slugs:
                if FormFactor.objects.filter(slug=slug).exists():
                    ff_slug = slug
                    break
        
        ff = get_object_or_404(FormFactor, slug=ff_slug)
    
        # Resolve form factor baseline details from engine config
        ff_config = getattr(engine, "permissible_form_factors", {}).get(ff.slug, {})
        is_portioned = ff_config.get("is_portioned", ff.is_portioned)
        base_unit_weight = ff_config.get("unit_weight", ff.unit_weight)
        base_default_count = ff_config.get("base_count", ff.default_count)
        base_weight = base_unit_weight * base_default_count
    
        texture_score = int(request.POST.get("texture_score", 50))
        crumb_score = int(request.POST.get("crumb_score", 50))
    
        # Map simplified scores (0-100) to baker's math percentages
        # Crumb (0-100) -> Hydration (45%-85%)
        hydration_pct = 0.45 + (crumb_score / 100.0) * 0.40
        # Texture (0-100) -> Fat (0%-15%)
        fat_pct = (texture_score / 100.0) * 0.15
        # Texture (0-100) -> Sugar (0%-12%)
        sugar_pct = (texture_score / 100.0) * 0.12
    
        starter_pct = float(request.POST.get("starter_pct", 0)) / 100.0
    
        grain_type = request.POST.get("grain_type", "all_purpose")
        flour_maturity = request.POST.get("flour_maturity", "matured")
        leaven_type = request.POST.get("leaven_type", "yeast")
    
        room_temp = float(request.POST.get("room_temp", 72))
        flour_temp = float(request.POST.get("flour_temp", 70))
        mixing_method = request.POST.get("mixing_method", "stand_mixer")
    
        # Portioned handling
        unit_weight = float(request.POST.get("unit_weight", base_unit_weight))
        portion_count = int(request.POST.get("portion_count", base_default_count))
    
        if is_portioned:
            target_mass = unit_weight * portion_count
        else:
            target_mass = float(request.POST.get("target_weight", base_weight))
        
        # Salt and leaven percents
        salt_pct = 0.02
        leaven_pct = starter_pct if leaven_type == "sourdough" else 0.015
    
        # 2. Process Substitution
        sub_orig = request.POST.get("sub_original")
        sub_new = request.POST.get("sub_substitute")
        substitution = None
        if sub_orig and sub_new:
            substitution = {"original": sub_orig, "substitute": sub_new}
        
        # 3. Calculate Baker's Math and apply fail-safes
        custom_mixer_id = request.POST.get("custom_mixer")
        friction_override = None
        if custom_mixer_id and custom_mixer_id != "static":
            try:
                mixer = Equipment.objects.get(id=custom_mixer_id)
                friction_override = mixer.friction_heat_factor
            except (ValueError, Equipment.DoesNotExist):
                pass
 
        selected_grain_ids = request.POST.getlist("selected_grains")
        if selected_grain_ids:
            active_berries = list(WheatBerry.objects.filter(id__in=selected_grain_ids))
        else:
            active_berries = list(WheatBerry.objects.filter(is_active=True))
 
        preset_name = None
        if preset_slug:
            try:
                preset_obj = BreadPreset.objects.get(slug=preset_slug)
                preset_name = preset_obj.name
            except BreadPreset.DoesNotExist:
                pass
 
        try:
            # If AI is active, we can fetch substitution offsets from AI first
            ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"
            if ai_enabled and substitution:
                recipe_state = {
                    "effective_hydration_pct": hydration_pct * 100,
                    "effective_fat_pct": fat_pct * 100,
                    "effective_sugar_pct": sugar_pct * 100,
                }
                offset = gemma_client.get_substitution_offset(sub_orig, sub_new, recipe_state)
                if offset:
                    # Custom AI-rebalanced calculation
                    # Adjust base ratios using AI-derived offsets
                    hydration_pct = max(0.40, hydration_pct + offset.get("water_offset_pct", 0.0))
                    fat_pct = max(0.0, fat_pct + offset.get("fat_offset_pct", 0.0))
                    sugar_pct = max(0.0, sugar_pct + offset.get("sugar_offset_pct", 0.0))
                
            secondary_lipid = request.POST.get("secondary_lipid") or None
            secondary_liquid = request.POST.get("secondary_liquid") or None
            secondary_binder = request.POST.get("secondary_binder") or None
        
            flavor_inclusions_json = request.POST.get("flavor_inclusions")
            flavor_inclusions = []
            if flavor_inclusions_json:
                try:
                    import json
                    flavor_inclusions = json.loads(flavor_inclusions_json)
                except Exception as ex:
                    logger.error(f"Failed to parse flavor_inclusions: {ex}")
                
            flour_blend_json = request.POST.get("flour_blend")
            flour_blend = {}
            if flour_blend_json:
                try:
                    import json
                    flour_blend = json.loads(flour_blend_json)
                except Exception as ex:
                    logger.error(f"Failed to parse flour_blend: {ex}")

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
                substitution=substitution if not ai_enabled else None,  # Natively balanced in bakers_math if AI is off
                active_berries=active_berries,
                texture_score=texture_score,
                crumb_score=crumb_score,
                friction_override=friction_override,
                preset_slug=preset_slug,
                preset_name=preset_name,
                category_slug=cat.slug,
                secondary_lipid=secondary_lipid,
                secondary_liquid=secondary_liquid,
                secondary_binder=secondary_binder,
                flavor_inclusions=flavor_inclusions,
                flour_blend=flour_blend
            )
        
            # Override AI explanations if AI offsets were loaded
            if ai_enabled and substitution and 'offset' in locals() and offset:
                recipe["substitution_notes"] = [offset.get("explanation", "Balanced via AI substitution module.")]
            
        except Exception as e:
            logger.error(f"[Calculator] - Math Error - Failed executing Baker's Math: {str(e)}")
            return HttpResponse(
                "<div class='warning-box'><h4>Mathematical Calculation Error</h4>"
                "<p>Please verify your inputs are positive values.</p></div>"
            )
 
        # 4. Classifier Engine: Euclidean distance match
        all_presets = BreadPreset.objects.select_related('dough_category', 'form_factor').all()
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
 
        # 5. Fetch AI Diagnostics (Sensory benchmark & pitfalls)
        eff_hyd = recipe["effective_hydration_pct"] / 100.0
        preset_slug_resolved = preset_slug or (classified_preset.slug if classified_preset else None)
    
        sensory_desc = gemma_client.get_sensory_benchmark(grain_type, flour_maturity, eff_hyd, cat.slug, preset_slug_resolved)
        pitfalls = gemma_client.get_contextual_pitfalls(cat.slug, eff_hyd, grain_type, preset_slug_resolved)
    
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
        
        scaled_time = round(base_time * (mass_ratio ** 0.4))
        scaled_temp = base_temp
        if not is_portioned:
            if mass_ratio > 1.2:
                scaled_temp = base_temp - 10
            elif mass_ratio < 0.8:
                scaled_temp = base_temp + 10
            
        # 7b. Query geometry advisory and apply offsets
        geom_advisory = gemma_client.get_geometry_advisory(preset_slug_resolved, preset_name, cat.slug, ff.slug)
        geom_eval = geom_advisory.get("geometry_evaluation", {})
        profile_adjustments = geom_eval.get("profile_adjustments", {})
    
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
            starter_feed_hours = request.POST.get("starter_feed_hours", "4_8")
            rise_speed = request.POST.get("flow_rise_speed", "normal")  # Map from Alpine name
            mill_type = request.POST.get("mill_type", "stoneground")
            is_sifted = request.POST.get("is_sifted") in ("on", "true", "True")
        
            calibration = gemma_client.calibrate_fermentation(starter_feed_hours, rise_speed, mill_type, is_sifted)
            estimated_bulk_hours = calibration.get("estimated_bulk_fermentation_hours", 4.0)
            estimated_proof_hours = 2.0
        
        if room_temp < 70:
            estimated_bulk_hours += 1.0
        elif room_temp > 76:
            estimated_bulk_hours = max(0.5 if leaven_type == 'yeast' else 3.0, estimated_bulk_hours - 1.0)
        
        proofing_env = request.POST.get("proofing_environment", "ambient")
        if proofing_env == "mat":
            estimated_proof_hours *= 0.9
        elif proofing_env == "box":
            estimated_proof_hours *= 0.75
 
        estimated_bulk_minutes = int(estimated_bulk_hours * 60)
        estimated_proof_minutes = int(estimated_proof_hours * 60)

        # Resolve active sub-engine and load dynamic timeline steps
        from grainlab.engines import router
        import json
        active_engine = router.get_engine_for_preset(preset_slug_resolved, cat.slug)
        steps_list = active_engine.get_live_timeline_steps(
            recipe_data=recipe,
            estimated_bulk_minutes=estimated_bulk_minutes,
            estimated_proof_minutes=estimated_proof_minutes,
            bake_time_min=scaled_time,
            mixing_method=mixing_method,
            preset_slug=preset_slug_resolved
        )
        countertop_steps_json = json.dumps(steps_list)

        context = {
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
            "current_phase": current_phase,
            "bake_temp_f": scaled_temp,
            "bake_time_min": scaled_time,
            "estimated_bulk_minutes": estimated_bulk_minutes,
            "estimated_proof_minutes": estimated_proof_minutes,
            "countertop_steps_json": countertop_steps_json,
            "steam_required": adjusted_steam,
            "geometry_evaluation": geom_eval,
        }
        return render(request, "partials/recipe_output.html", context)


