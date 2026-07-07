import logging
import math
import uuid
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting, WheatBerry, Equipment, BackgroundTask
from apps.core import bakers_math
from apps.core import gemma_client

# Initialize thread pool for offloading Gemma LLM queries
executor = ThreadPoolExecutor(max_workers=2)

logger = logging.getLogger("grainlab.views")

def get_engines_ff_json() -> str:
    from grainlab.engines.router import ENGINES
    from apps.core.gemma_client import CATEGORY_TO_ENGINE
    import json
    
    engines_ff_data = {}
    for cat_slug, eng_name in CATEGORY_TO_ENGINE.items():
        engine = ENGINES[eng_name]
        # We need clean python dictionary to serialize
        engines_ff_data[cat_slug] = {
            "permissible_form_factors": getattr(engine, "permissible_form_factors", {}),
            "production_profile": getattr(engine, "production_profile", {}),
            "secondary_ingredients": getattr(engine, "secondary_ingredients", {})
        }
    return json.dumps(engines_ff_data)

def calculator(request):
    """
    Renders the primary calculator workspace.
    """
    categories = DoughCategory.objects.all().order_by('name')
    form_factors = FormFactor.objects.all().order_by('name')
    presets = BreadPreset.objects.all().order_by('name')
    mixers = Equipment.objects.filter(equipment_type='mixer').order_by('name')
    
    # Load settings
    ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"
    
    # Default selection values
    category_slug = request.GET.get("dough_category")
    ff_slug = request.GET.get("form_factor")
    preset_slug = request.GET.get("preset")
    
    selected_preset = None
    if preset_slug:
        selected_preset = BreadPreset.objects.filter(slug=preset_slug).first()
        
    default_cat = None
    if category_slug:
        default_cat = DoughCategory.objects.filter(slug=category_slug).first()
    elif selected_preset:
        default_cat = selected_preset.dough_category
    if not default_cat:
        default_cat = DoughCategory.objects.filter(slug='lean-crusty').first() or categories.first()
        
    default_ff = None
    if ff_slug:
        default_ff = FormFactor.objects.filter(slug=ff_slug).first()
    elif selected_preset:
        default_ff = selected_preset.form_factor
        
    from grainlab.engines.router import get_engine_for_preset
    preset_slug_str = selected_preset.slug if selected_preset else None
    cat_slug_str = default_cat.slug if default_cat else None
    engine = get_engine_for_preset(preset_slug_str, cat_slug_str)
    permissible_slugs = list(getattr(engine, "permissible_form_factors", {}).keys())
    
    if default_ff and default_ff.slug not in permissible_slugs and permissible_slugs:
        first_perm_ff = FormFactor.objects.filter(slug=permissible_slugs[0]).first()
        if first_perm_ff:
            default_ff = first_perm_ff
            
    if not default_ff:
        if permissible_slugs:
            default_ff = FormFactor.objects.filter(slug=permissible_slugs[0]).first()
        if not default_ff:
            default_ff = FormFactor.objects.filter(slug='loaf-pan').first() or form_factors.first()
        
    # Calculate slider defaults based on category base ratios
    if selected_preset:
        base_hydration = selected_preset.hydration_override if selected_preset.hydration_override is not None else default_cat.base_hydration
        base_fat = selected_preset.fat_override if selected_preset.fat_override is not None else default_cat.base_fat
        default_sugar = int((selected_preset.sugar_override if selected_preset.sugar_override is not None else default_cat.base_sugar) * 100)
        default_starter = int((selected_preset.starter_override if selected_preset.starter_override is not None else default_cat.base_starter) * 100)
        default_flour_type = selected_preset.flour_type_default
        default_flour_maturity = selected_preset.flour_maturity_default
        default_texture_score = selected_preset.classifier_texture
        default_crumb_score = selected_preset.classifier_crumb
    else:
        base_hydration = default_cat.base_hydration if default_cat else 0.68
        base_fat = default_cat.base_fat if default_cat else 0.0
        default_sugar = int((default_cat.base_sugar if default_cat else 0.0) * 100)
        default_starter = int((default_cat.base_starter if default_cat else 0.0) * 100)
        default_flour_type = "all_purpose"
        default_flour_maturity = "matured"
        default_crumb_score = int(max(0.0, min(100.0, ((base_hydration - 0.45) / 0.40) * 100)))
        default_texture_score = int(max(0.0, min(100.0, (base_fat / 0.15) * 100)))
    
    active_berries = list(WheatBerry.objects.filter(is_active=True))
    
    context = {
        "categories": categories,
        "form_factors": form_factors,
        "presets": presets,
        "mixers": mixers,
        "active_berries": active_berries,
        "selected_preset": selected_preset,
        "selected_category": default_cat,
        "selected_form_factor": default_ff,
        "ai_enabled": ai_enabled,
        "default_hydration": int(base_hydration * 100),
        "default_fat": int(base_fat * 100),
        "default_sugar": default_sugar,
        "default_starter": default_starter,
        "default_flour_type": default_flour_type,
        "default_flour_maturity": default_flour_maturity,
        "default_texture_score": default_texture_score,
        "default_crumb_score": default_crumb_score,
        "engines_ff_json": get_engines_ff_json(),
    }
    return render(request, "calculator.html", context)


def search_presets(request):
    """
    Handles debounced preset search queries, returning HTMX results.
    """
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return HttpResponse("")
        
    presets = BreadPreset.objects.filter(name__icontains=q)[:5]
    return render(request, "partials/search_results.html", {"presets": presets})


def load_preset(request, preset_id):
    """
    Loads a selected preset, replacing the parameters panel and trigger recalculation.
    """
    preset = get_object_or_404(BreadPreset, id=preset_id)
    categories = DoughCategory.objects.all().order_by('name')
    form_factors = FormFactor.objects.all().order_by('name')
    mixers = Equipment.objects.filter(equipment_type='mixer').order_by('name')
    
    # Use preset values or category base values
    cat = preset.dough_category
    ff = preset.form_factor
    
    from grainlab.engines.router import get_engine_for_preset
    engine = get_engine_for_preset(preset.slug, cat.slug)
    permissible_slugs = list(getattr(engine, "permissible_form_factors", {}).keys())
    if ff.slug not in permissible_slugs and permissible_slugs:
        first_perm_ff = FormFactor.objects.filter(slug=permissible_slugs[0]).first()
        if first_perm_ff:
            ff = first_perm_ff
    
    hydration = int((preset.hydration_override if preset.hydration_override is not None else cat.base_hydration) * 100)
    fat = int((preset.fat_override if preset.fat_override is not None else cat.base_fat) * 100)
    sugar = int((preset.sugar_override if preset.sugar_override is not None else cat.base_sugar) * 100)
    starter = int((preset.starter_override if preset.starter_override is not None else cat.base_starter) * 100)
    
    active_berries = list(WheatBerry.objects.filter(is_active=True))
    presets = BreadPreset.objects.all().order_by('name')
    
    context = {
        "categories": categories,
        "form_factors": form_factors,
        "presets": presets,
        "mixers": mixers,
        "active_berries": active_berries,
        "selected_preset": preset,
        "selected_category": cat,
        "selected_form_factor": ff,
        "default_hydration": hydration,
        "default_fat": fat,
        "default_sugar": sugar,
        "default_starter": starter,
        "default_flour_type": preset.flour_type_default,
        "default_flour_maturity": preset.flour_maturity_default,
        "default_texture_score": preset.classifier_texture,
        "default_crumb_score": preset.classifier_crumb,
        "engines_ff_json": get_engines_ff_json(),
    }
    return render(request, "partials/calculator_form.html", context)


@require_POST
def calculate_recipe_ajax(request):
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
            secondary_binder=secondary_binder
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


def settings_page(request):
    """
    Renders system preferences and AI configurations page.
    """
    context = {
        "ai_enabled": SystemSetting.get_val("ai_enabled", "False") == "True",
        "ai_api_url": SystemSetting.get_val("ai_api_url", "http://host.docker.internal:11434/v1"),
        "ai_model_name": SystemSetting.get_val("ai_model_name", "gemma:12b"),
        "ai_thinking_enabled": SystemSetting.get_val("ai_thinking_enabled", "True") == "True",
        "ai_thinking_effort": SystemSetting.get_val("ai_thinking_effort", "medium"),
    }
    return render(request, "settings.html", context)


@require_POST
def save_settings(request):
    """
    Persists preferences to settings database.
    """
    ai_enabled = request.POST.get("ai_enabled") in ("on", "true", "True")
    ai_api_url = request.POST.get("ai_api_url", "").strip()
    ai_model_name = request.POST.get("ai_model_name", "").strip()
    ai_thinking_enabled = request.POST.get("ai_thinking_enabled") in ("on", "true", "True")
    ai_thinking_effort = request.POST.get("ai_thinking_effort", "medium")
    
    SystemSetting.set_val("ai_enabled", ai_enabled)
    SystemSetting.set_val("ai_api_url", ai_api_url)
    SystemSetting.set_val("ai_model_name", ai_model_name)
    SystemSetting.set_val("ai_thinking_enabled", ai_thinking_enabled)
    SystemSetting.set_val("ai_thinking_effort", ai_thinking_effort)
    
    return HttpResponse(
        "<div class='feedback-box' style='border-left-color: var(--success);'>"
        "<div class='feedback-header' style='color: var(--success);'>Settings Saved Successfully</div>"
        "<p>Baking configurations updated.</p></div>"
    )


@require_POST
def sourdough_calibrate(request):
    """
    Runs bulk fermentation countdown diagnostics based on inputs.
    """
    starter_feed_hours = request.POST.get("starter_feed_hours", "4_8")
    rise_speed = request.POST.get("rise_speed", "normal")
    mill_type = request.POST.get("mill_type", "stoneground")
    is_sifted = request.POST.get("is_sifted") in ("on", "true", "True")
    
    calibration = gemma_client.calibrate_fermentation(starter_feed_hours, rise_speed, mill_type, is_sifted)
    
    context = {
        "calibration": calibration,
    }
    return render(request, "partials/sourdough_diagnostic_output.html", context)


def inventory_page(request):
    """
    Renders inventory page listing wheat berries and equipment.
    """
    wheat_berries = WheatBerry.objects.all().order_by('name')
    equipment = Equipment.objects.all().order_by('name')
    context = {
        "wheat_berries": wheat_berries,
        "equipment": equipment,
    }
    return render(request, "inventory.html", context)


def add_wheat_berry(request):
    """
    Creates a new wheat berry record in the inventory.
    """
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        protein = float(request.POST.get("protein_content", 12.0) or 12.0)
        hardness = request.POST.get("hardness", "hard")
        absorption = float(request.POST.get("moisture_absorption_coef", 1.0) or 1.0)
        notes = request.POST.get("notes", "").strip()
        is_active = request.POST.get("is_active") in ("on", "true", "True")

        if name:
            WheatBerry.objects.create(
                name=name,
                protein_content=protein,
                hardness=hardness,
                moisture_absorption_coef=absorption,
                notes=notes,
                is_active=is_active
            )

    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('inventory_page')
    return response


def toggle_wheat_berry_active(request: HttpRequest, id: uuid.UUID) -> HttpResponse:
    """
    Toggles the active state of a wheat berry.
    """
    wb = get_object_or_404(WheatBerry, id=id)
    wb.is_active = not wb.is_active
    wb.save()
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('inventory_page')
    return response


def delete_wheat_berry(request: HttpRequest, id: uuid.UUID) -> HttpResponse:
    """
    Deletes a wheat berry from inventory.
    """
    wb = get_object_or_404(WheatBerry, id=id)
    wb.delete()
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('inventory_page')
    return response


def ai_analyze_wheat_berry(request: HttpRequest, id: uuid.UUID) -> HttpResponse:
    """
    Runs AI analysis for a specific wheat berry.
    """
    task = BackgroundTask.objects.create()
    import sys
    if 'test' in sys.argv:
        run_async_task(task.id, ai_analyze_wheat_berry_task, id)
    else:
        executor.submit(run_async_task, task.id, ai_analyze_wheat_berry_task, id)
    
    # Return loading indicator to trigger polling
    return HttpResponse(
        f'<div hx-get="{reverse("task_status", args=[task.id])}" hx-trigger="every 1s" hx-swap="outerHTML" style="display: flex; align-items: center; gap: 0.25rem;">'
        f'  <span class="spinner" style="width: 12px; height: 12px;"></span>'
        f'  <span style="font-size: 0.8rem; color: var(--text-muted);">AI Running...</span>'
        f'</div>'
    )


def add_equipment(request: HttpRequest) -> HttpResponse:
    """
    Creates a new equipment record in the inventory.
    """
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        eq_type = request.POST.get("equipment_type", "other")
        friction = float(request.POST.get("friction_heat_factor", 0.0) or 0.0)
        notes = request.POST.get("notes", "").strip()

        if name:
            Equipment.objects.create(
                name=name,
                equipment_type=eq_type,
                friction_heat_factor=friction,
                notes=notes
            )

    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('inventory_page')
    return response


def delete_equipment(request: HttpRequest, id: uuid.UUID) -> HttpResponse:
    """
    Deletes equipment from inventory.
    """
    eq = get_object_or_404(Equipment, id=id)
    eq.delete()
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('inventory_page')
    return response


def ai_analyze_equipment(request: HttpRequest, id: uuid.UUID) -> HttpResponse:
    """
    Runs AI analysis for a specific equipment item.
    """
    task = BackgroundTask.objects.create()
    import sys
    if 'test' in sys.argv:
        run_async_task(task.id, ai_analyze_equipment_task, id)
    else:
        executor.submit(run_async_task, task.id, ai_analyze_equipment_task, id)
    
    return HttpResponse(
        f'<div hx-get="{reverse("task_status", args=[task.id])}" hx-trigger="every 1s" hx-swap="outerHTML" style="display: flex; align-items: center; gap: 0.25rem;">'
        f'  <span class="spinner" style="width: 12px; height: 12px;"></span>'
        f'  <span style="font-size: 0.8rem; color: var(--text-muted);">AI Running...</span>'
        f'</div>'
    )


def bulk_ai_analyze(request: HttpRequest) -> HttpResponse:
    """
    Analyzes all unanalyzed inventory items.
    """
    task = BackgroundTask.objects.create()
    import sys
    if 'test' in sys.argv:
        run_async_task(task.id, bulk_ai_analyze_task)
    else:
        executor.submit(run_async_task, task.id, bulk_ai_analyze_task)
    
    return HttpResponse(
        f'<div hx-get="{reverse("task_status", args=[task.id])}?bulk=true" hx-trigger="every 1s" hx-swap="outerHTML" '
        f'style="display: flex; align-items: center; gap: 0.5rem; background: var(--bg-card); padding: 0.75rem 1.5rem; border-radius: var(--radius-sm); border: 1px solid var(--border);">'
        f'  <span>🤖 Bulk Analyzing...</span>'
        f'  <div style="flex: 1; height: 6px; background: var(--bg-input); border-radius: 3px; overflow: hidden; min-width: 100px;">'
        f'    <div style="width: 15%; height: 100%; background: var(--accent); transition: width 0.3s;"></div>'
        f'  </div>'
        f'  <span style="font-size: 0.85rem; font-weight: bold;">15%</span>'
        f'</div>'
    )


def redo_ai_analysis(request: HttpRequest, item_type: str, id: uuid.UUID) -> HttpResponse:
    """
    Re-analyzes an item (overriding manual tweaks).
    """
    task = BackgroundTask.objects.create()
    import sys
    if 'test' in sys.argv:
        run_async_task(task.id, redo_ai_analysis_task, item_type, id)
    else:
        executor.submit(run_async_task, task.id, redo_ai_analysis_task, item_type, id)
    
    return HttpResponse(
        f'<div hx-get="{reverse("task_status", args=[task.id])}" hx-trigger="every 1s" hx-swap="outerHTML" style="display: flex; align-items: center; gap: 0.25rem;">'
        f'  <span class="spinner" style="width: 12px; height: 12px;"></span>'
        f'  <span style="font-size: 0.8rem; color: var(--text-muted);">AI Running...</span>'
        f'</div>'
    )


# -----------------------------------------------------------------------------
# Background Task Executers
# -----------------------------------------------------------------------------

def run_async_task(task_id: uuid.UUID, task_func, *args, **kwargs) -> None:
    try:
        task = BackgroundTask.objects.get(id=task_id)
        task.status = 'RUNNING'
        task.progress = 15
        task.save()
        
        result_data = task_func(task, *args, **kwargs)
        
        task.status = 'SUCCESS'
        task.progress = 100
        task.result = result_data
        task.completed_at = timezone.now()
        task.save()
    except Exception as e:
        logger.error(f"[BackgroundTask] - Error - Task {task_id} failed: {e}")
        try:
            task = BackgroundTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.progress = 100
            task.error = str(e)
            task.completed_at = timezone.now()
            task.save()
        except Exception:
            pass


def ai_analyze_wheat_berry_task(task: BackgroundTask, wb_id: uuid.UUID) -> dict:
    wb = WheatBerry.objects.get(id=wb_id)
    task.progress = 30
    task.save()
    
    analysis = gemma_client.analyze_wheat_berry_ai(wb.name)
    task.progress = 80
    task.save()
    
    if analysis:
        wb.protein_content = analysis.get("protein_content", wb.protein_content)
        wb.moisture_absorption_coef = analysis.get("moisture_absorption_coef", wb.moisture_absorption_coef)
        wb.hardness = analysis.get("hardness", wb.hardness)
        wb.notes = analysis.get("notes", wb.notes)
        wb.ai_analyzed = True
        wb.save()
        return {"status": "success", "item_name": wb.name}
    else:
        raise Exception("Gemma AI response was empty or failed.")


def ai_analyze_equipment_task(task: BackgroundTask, eq_id: uuid.UUID) -> dict:
    eq = Equipment.objects.get(id=eq_id)
    task.progress = 30
    task.save()
    
    analysis = gemma_client.analyze_equipment_ai(eq.name, eq.equipment_type)
    task.progress = 80
    task.save()
    
    if analysis:
        eq.friction_heat_factor = analysis.get("friction_heat_factor", eq.friction_heat_factor)
        eq.notes = analysis.get("notes", eq.notes)
        eq.details = analysis.get("details", eq.details)
        eq.ai_analyzed = True
        eq.save()
        return {"status": "success", "item_name": eq.name}
    else:
        raise Exception("Gemma AI response was empty or failed.")


def bulk_ai_analyze_task(task: BackgroundTask) -> dict:
    unanalyzed_berries = list(WheatBerry.objects.filter(ai_analyzed=False))
    unanalyzed_eq = list(Equipment.objects.filter(ai_analyzed=False))
    
    total_items = len(unanalyzed_berries) + len(unanalyzed_eq)
    if total_items == 0:
        return {"status": "success", "processed_count": 0}
        
    processed = 0
    for wb in unanalyzed_berries:
        progress_pct = int(10 + (processed / total_items) * 80)
        task.progress = progress_pct
        task.save()
        
        analysis = gemma_client.analyze_wheat_berry_ai(wb.name)
        if analysis:
            wb.protein_content = analysis.get("protein_content", wb.protein_content)
            wb.moisture_absorption_coef = analysis.get("moisture_absorption_coef", wb.moisture_absorption_coef)
            wb.hardness = analysis.get("hardness", wb.hardness)
            wb.notes = analysis.get("notes", wb.notes)
            wb.ai_analyzed = True
            wb.save()
        processed += 1
        
    for eq in unanalyzed_eq:
        progress_pct = int(10 + (processed / total_items) * 80)
        task.progress = progress_pct
        task.save()
        
        analysis = gemma_client.analyze_equipment_ai(eq.name, eq.equipment_type)
        if analysis:
            eq.friction_heat_factor = analysis.get("friction_heat_factor", eq.friction_heat_factor)
            eq.notes = analysis.get("notes", eq.notes)
            eq.details = analysis.get("details", eq.details)
            eq.ai_analyzed = True
            eq.save()
        processed += 1
        
    return {"status": "success", "processed_count": processed}


def redo_ai_analysis_task(task: BackgroundTask, item_type: str, item_id: uuid.UUID) -> dict:
    if item_type == "wheat_berry":
        return ai_analyze_wheat_berry_task(task, item_id)
    elif item_type == "equipment":
        return ai_analyze_equipment_task(task, item_id)
    else:
        raise Exception(f"Unknown item type: {item_type}")


def task_status(request: HttpRequest, task_id: uuid.UUID) -> HttpResponse:
    task = get_object_or_404(BackgroundTask, id=task_id)
    is_bulk = request.GET.get("bulk") == "true"
    
    if task.status in ('PENDING', 'RUNNING'):
        if is_bulk:
            return HttpResponse(
                f'<div hx-get="{reverse("task_status", args=[task.id])}?bulk=true" '
                f'hx-trigger="every 1s" hx-swap="outerHTML" '
                f'style="display: flex; align-items: center; gap: 0.5rem; background: var(--bg-card); padding: 0.75rem 1.5rem; border-radius: var(--radius-sm); border: 1px solid var(--border);">'
                f'  <span>🤖 Bulk Analyzing...</span>'
                f'  <div style="flex: 1; height: 6px; background: var(--bg-input); border-radius: 3px; overflow: hidden; min-width: 100px;">'
                f'    <div style="width: {task.progress}%; height: 100%; background: var(--accent); transition: width 0.3s;"></div>'
                f'  </div>'
                f'  <span style="font-size: 0.85rem; font-weight: bold;">{task.progress}%</span>'
                f'</div>'
            )
        else:
            return HttpResponse(
                f'<div hx-get="{reverse("task_status", args=[task.id])}" '
                f'hx-trigger="every 1s" hx-swap="outerHTML" style="display: flex; align-items: center; gap: 0.25rem;">'
                f'  <span class="spinner" style="width: 12px; height: 12px;"></span>'
                f'  <span style="font-size: 0.8rem; color: var(--text-muted);">AI Running ({task.progress}%)...</span>'
                f'</div>'
            )
            
    elif task.status == 'SUCCESS':
        response = HttpResponse(status=200)
        response['HX-Redirect'] = reverse('inventory_page')
        return response
        
    else:  # FAILED
        return HttpResponse(
            f'<div class="warning-box" style="margin: 0; padding: 0.5rem 1rem; border-radius: var(--radius-sm); font-size: 0.85rem; display: flex; flex-direction: column; gap: 0.25rem;">'
            f'  <h4 style="margin:0; font-size:0.9rem; color: var(--text-primary);">🤖 AI Analysis Failed</h4>'
            f'  <p style="margin:0; color: var(--text-secondary);">{task.error or "Unknown Ollama/Gemma error."}</p>'
            f'</div>'
        )


def ai_grain_advisory(request):
    """
    Returns dynamic recommendation and warning details for the requested preset or category.
    """
    from django.http import JsonResponse
    from apps.core import gemma_client
    from apps.core.models import SystemSetting
    
    preset_slug = request.GET.get("preset_slug", "").strip()
    category_slug = request.GET.get("category_slug", "").strip()
    selected_grains = request.GET.get("selected_grains", "").strip()
    
    if not preset_slug and not category_slug:
        return JsonResponse({
            "grain_evaluations": [],
            "elevate_recipe": []
        })
        
    ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"
    advisory = None
    if ai_enabled:
        try:
            advisory = gemma_client.get_grain_advisory_ai(preset_slug, category_slug, selected_grains=selected_grains)
        except Exception as e:
            logger.error(f"[AI] - Advisory - Failed fetching advisory from Gemma: {e}")
            advisory = {"grain_evaluations": [], "elevate_recipe": []}
    else:
        advisory = gemma_client.get_local_grain_advisory(preset_slug, category_slug)
        
    return JsonResponse(advisory or {"grain_evaluations": [], "elevate_recipe": []})

def get_inactive_grain_recommendations(preset_slug: str, category_slug: str = None) -> list[dict]:
    """
    Evaluates all inactive grains and returns those that are 'recommended' for the current preset/engine.
    """
    from apps.core.models import WheatBerry, BreadPreset
    from grainlab.engines import router
    from apps.core.gemma_client import evaluate_single_grain

    preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
    if not category_slug and preset and preset.dough_category:
        category_slug = preset.dough_category.slug
    
    try:
        engine = router.get_engine_for_preset(preset_slug, category_slug)
    except Exception:
        return []

    inactive_berries = list(WheatBerry.all_objects.filter(is_active=False, deleted_at__isnull=True))
    recommended_inactive = []

    for wb in inactive_berries:
        res = evaluate_single_grain(wb, engine)
        if res["tier"] == "recommended":
            recommended_inactive.append({
                "name": wb.name,
                "protein": wb.protein_content,
                "benefit": getattr(wb, "notes", "") or "enhances flavor and structure"
            })
            
    return recommended_inactive


def ai_sidebar_insight(request):
    """
    Returns dynamic labor ROI and critique analysis for the hovered element.
    """
    from django.http import JsonResponse
    from apps.core import gemma_client
    
    element = request.GET.get("element", "").strip()
    category_slug = request.GET.get("category_slug", "").strip()
    preset_slug = request.GET.get("preset_slug", "").strip()
    
    if not element:
        return JsonResponse({
            "labor_roi": "Low Priority / Minor Textural Return",
            "last_10_percent_analysis": "Hover over any ingredient or control setting on the left to see objective science and AI magic diagnostics."
        })
        
    # Determine the category group to guarantee recipe-aware fallback diagnostics
    if category_slug in ['lean-crusty', 'enriched-soft', 'alkaline-bath', 'flatbreads-griddles', 'fried-doughs']:
        group = "bread"
    elif category_slug in ['quick-breads-scones', 'cakes-batters', 'pastry-lamination', 'cookies-shortbread', 'choux-paste']:
        group = "sweet_tender"
    elif category_slug in ['fresh-pasta-noodles']:
        group = "pasta"
    else:
        group = "bread"
        
    # Recipe-aware python local fallback dictionary definition
    fallbacks = {}
    
    if group == "bread":
        fallbacks = {
            "refined": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Commercial refined flour handles consistently without requiring hydration shifts. However, it lacks the deep, nutty cellular flavor matrix of fresh-milled grain."
            },
            "milled": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Fresh-milled whole grains possess active wheat germ oils and enzymes that elevate flavor profiles and crust blister complexes. Adjust hydration dynamically to accommodate increased bran absorption."
            },
            "grain_hard_red_spring": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Spring wheat brings massive gluten elasticity and gas holding power to hearth baking, ensuring a high-rise open crumb. Highly worth milling fresh for rustic breads."
            },
            "grain_hard_red_winter": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "An all-purpose workhorse hard wheat. Good balance of elasticity and extensibility, but lacks the high-torque ceiling of spring varieties."
            },
            "grain_soft_white": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Soft white wheat lacks the gluten strength needed to support high-rising loaves. Using it will result in a flat, dense bake with poor gas retention."
            },
            "grain_hard_white": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Provides strong structure without the bitter tannin flavors of red wheats. Useful if you want mild flavor with high lift."
            },
            "grain_spelt": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Ancient grain that injects deep nutty flavor and high extensibility. Restrict mechanical energy to avoid collapsing its fragile gluten bonds."
            },
            "grain_kamut": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Ancient Khorasan wheat adds a rich golden color and sweet flavor. Absorbs liquid slowly, demanding patience during mixing."
            },
            "grain_rye": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Savory rye grass grain that introduces high pentosans and complex earthy sweetness. Expect sticky handling and a tight, moist crumb."
            },
            "stand_mixer": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Develops gluten rapidly but introduces planetary friction heat. A machine can easily handle this step, but watch internal temperatures."
            },
            "bread_machine": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Enclosed, high-friction kneader. Convenient for zero-effort development but risks over-warming yeast and restricting airy rise."
            },
            "food_processor": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Intense blade shearing forces rapid hydration and gluten alignment. Great for quick buns, but easy to over-mix."
            },
            "hand_beaters": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not recommended. Lacks the torque required for heavy yeast doughs, risking motor burnout."
            },
            "whisk": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Useful only for pre-mixing liquid starters or hydrating flour during autolyse. Lacks the structure to knead."
            },
            "spatula_bowl": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Ideal for initial ingredient incorporation and dynamic stretch-and-folds during bulk fermentation."
            },
            "knead": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Kneading develops the structural gluten matrix needed to trap gas and support oven spring. Highly worth the effort for crusty loaves."
            },
            "cream": {
                "labor_roi": "Low Priority / Sub-Optimal Selection",
                "last_10_percent_analysis": "Rarely used, except for certain sweet brioches. In bread, we want gluten development first, not fat encapsulation."
            },
            "fold": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Gentle folding layers the dough and develops structure without degassing. Crucial for retaining large, irregular open crumb cells."
            },
            "cut_in": {
                "labor_roi": "Low Priority / Sub-Optimal Selection",
                "last_10_percent_analysis": "Occasionally used in laminated brioche. In normal bread, fat is kneaded in as soft butter rather than cut in."
            },
            "sheet": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Used in laminated croissants and danishes to layer butter. For general breads, sheeting is avoided to preserve crumb aeration."
            },
            "extrude": {
                "labor_roi": "Low Priority / Sub-Optimal Selection",
                "last_10_percent_analysis": "Not used. Breads are shaped manually or portioned to preserve the delicate, fermented cell structure."
            },
            "ambient": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Countertop proofing provides a steady, natural rise at room temperature. Safe and consistent, requiring minimal intervention."
            },
            "mat": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "A heated mat speeds up yeast activity by warming the bowl bottom. Saves time but can result in uneven fermentation temperatures."
            },
            "box": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Warm, humid enclosed chamber prevents the dough surface from drying out. Ensures a uniform rise and excellent crust browning."
            },
            "refrigerator": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Cold retardation solidifies butter fats and allows active enzymes to release sugars. Essential for creating complex flavors and deep blisters."
            },
            "bench_rest": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Relaxing the gluten matrix prevents dough from snapping back during final shaping, guaranteeing uniform size and structure."
            },
            "cast-iron-dutch-oven": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Retains intense heat and traps steam released from the dough. Ensures optimal starch gelatinization and maximum oven spring."
            },
            "open-baking-stone-steel": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Transfers heat instantly to the bottom of the dough. Crucial for a crisp bottom crust and rapid gas expansion in hearth loaves."
            },
            "standard-9x5-pan": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Forces the dough to rise vertically by restricting lateral expansion. Great for soft sandwich breads, but has low structural ROI."
            },
            "perforated-baking-sheet": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Enables even heat circulation and steam escape around portioned dough, forming the signature shiny crust of bagels and pretzels."
            },
            "butter": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Adds rich dairy fat to soften the crumb. Reduces gluten tensile strength, yielding a tender, melt-in-the-mouth brioche."
            },
            "unsalted_butter": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Allows precise control over salt while providing dairy fats to tenderize the loaf crumb."
            },
            "salted_butter": {
                "labor_roi": "Seamless Math Adjustment",
                "last_10_percent_analysis": "Salted butter detected. The engine has automatically reduced the standalone fine sea salt weight by 1.5% of the total butter mass to maintain perfect flavor balance and prevent over-seasoning your cookie crumb."
            },
            "olive_oil": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Liquid fats coat gluten strands completely, producing an exceptionally extensible dough and a moist, long-lasting tender crumb."
            },
            "canola_oil": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Provides liquid fat to soften the crumb without introducing strong flavors. Useful for everyday sandwich loaves."
            },
            "vegetable_oil": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Softens the crumb structure and extends shelf life by preventing retrogradation (staling)."
            },
            "whole_milk": {
                "labor_roi": "Sub-Optimal Crumb Shift",
                "last_10_percent_analysis": "Swapping water for milk introduces lactose and dairy fats to a lean hearth dough. This will cause the crust to brown significantly faster in the oven and will soften the traditional crisp, open-cell artisan chew into a sandwich-style crumb."
            },
            "almond_milk": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Nut proteins and water substitute standard liquid. Lacks the tenderizing fats of dairy milk, yielding a slightly tougher bake."
            },
            "coconut_oil": {
                "labor_roi": "Low Priority / Flavor Shift",
                "last_10_percent_analysis": "Coconut oil provides a clean, plant-based solid lipid profile. It solidifies at cooler room temperatures, imparting a faint tropical aroma."
            },
            "avocado_oil": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Avocado oil is a neutral liquid lipid that remains fluid at room temperature. It coats gluten strands completely to produce an incredibly soft, moist, and long-lasting crumb."
            },
            "pure_water": {
                "labor_roi": "Standard Baseline",
                "last_10_percent_analysis": "Pure water provides clean, zero-interference hydration. It is the absolute optimal choice for lean hearth loaves to keep the crumb airy and the crust crispy."
            },
            "heavy_cream": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Heavy cream adds immense dairy fat richness (37% fat) and milk sugars. It tenderizes the crumb dramatically, yielding an ultra-soft slice at the cost of some oven rise."
            },
            "buttermilk": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Buttermilk introduces active lactic acidity. This chemically tenderizes the gluten matrix and triggers chemical leavening reactions, yielding an exceptionally tender crumb."
            },
            "none": {
                "labor_roi": "Standard Baseline",
                "last_10_percent_analysis": "No binder selected. The recipe relies purely on the gluten network and hydration matrix to establish structural integrity."
            },
            "whole_eggs": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Whole eggs contribute fat, moisture, and lecithin emulsifiers. They bind the structure together and promote rich browning and a soft, custard-like crumb."
            },
            "egg_whites": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Egg whites contribute pure albumin protein and hydration. They dry and solidify during baking, creating a taller, lighter, and crisper crust structure."
            },
            "aquafaba_vegan": {
                "labor_roi": "Critical Structural Risk",
                "last_10_percent_analysis": "Choux paste relies completely on the intense protein coagulation and water-binding capacity of whole egg lipids to hold its hollow balloon shape. Substituting a vegan binder here introduces a massive inflation failure risk; the shells will likely collapse into flat discs."
            }
        }
    elif group == "sweet_tender":
        fallbacks = {
            "refined": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Provides highly consistent, low-protein performance. Ideal for ensuring a tender, delicate structure in confections and pastries without gluten toughness."
            },
            "milled": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Adds a rustic, earthy flavor dimension. However, the presence of sharp bran flakes can cut gluten networks and alter fat absorption, requiring careful mixing adjustment."
            },
            "grain_hard_red_spring": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Spring wheat contains excessively strong, elastic gluten. This is not recommended, as it will fight spread and make pastries tough and rubbery."
            },
            "grain_hard_red_winter": {
                "labor_roi": "Low Priority / Sub-Optimal Selection",
                "last_10_percent_analysis": "Moderate protein content can lead to gluten toughness if over-mixed. Best reserved for bread systems rather than tender confections."
            },
            "grain_soft_white": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Soft white wheat delivers an exceptionally tender crumb for cookies and pastries by avoiding gluten toughness. Critical for achieving melting spread."
            },
            "grain_hard_white": {
                "labor_roi": "Low Priority / Sub-Optimal Selection",
                "last_10_percent_analysis": "Offers a mild flavor but possesses moderate gluten strength. Can toughen cookies and cakes if the mixing is not carefully controlled."
            },
            "grain_spelt": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Ancient grain with highly extensible, soft gluten. Excellent for tender tarts and cookies, adding a nutty sweetness without rubbery toughness."
            },
            "grain_kamut": {
                "labor_roi": "Low Priority / Sub-Optimal Selection",
                "last_10_percent_analysis": "Extremely hard grain that resists moisture absorption. Its high protein content can make pastries too dense and chewy."
            },
            "grain_rye": {
                "labor_roi": "High Priority / Flavor Enhancement Opportunity",
                "last_10_percent_analysis": "Brings dark, spiced flavor notes to shortbreads and cookies. Lacks gluten-forming proteins, ensuring a highly short and tender bite."
            },
            "stand_mixer": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Ideal for creaming butter and sugar, or whipping egg whites to aerate batters. Watch speeds to prevent over-mixing once flour is added."
            },
            "bread_machine": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not recommended. Enclosed heating and harsh paddle action will over-knead delicate batters, yielding a rubbery, tough texture."
            },
            "food_processor": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Excellent for cutting cold fat into flour for pie crusts or biscuits. Blade action creates distinct fat pockets before gluten forms."
            },
            "hand_beaters": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Light whipping beaters are perfect for aerating eggs and creamed fat. A machine is highly recommended here to build micro-bubbles."
            },
            "whisk": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Manual whisking is perfect for aerating pancake or cake batters. Requires minimal physical effort while keeping gluten development low."
            },
            "spatula_bowl": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Zero-friction manual mixing is critical for delicate batters. Using a hand spatula prevents gluten development, preserving short tenderness."
            },
            "knead": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not recommended for tender confections. Kneading develops gluten, which destroys the melting tenderness of cookies and cakes."
            },
            "cream": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Creaming traps microscopic air bubbles inside the fat phase, creating the tender crumb of cookies and cakes. Essential for proper rise."
            },
            "fold": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Used to incorporate whipped egg whites or delicate dry ingredients into batters without collapsing the trapped air pocket bubbles."
            },
            "cut_in": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Distributing cold fat pieces throughout dry flour creates flat butter pockets. Crucial for baking flaky, laminated scone and pastry layers."
            },
            "sheet": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Aligns fats and dough sheets in puff pastry and croissants, driving steam-lift lamination. Keep cold to prevent fat melting."
            },
            "extrude": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Used for spritz cookies or piped pastries (choux). Assures uniform portioning while avoiding structural handling."
            },
            "ambient": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Ideal for resting cookie dough briefly or bringing cake ingredients to room temp to optimize emulsion stability."
            },
            "mat": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not recommended. Heat will melt solid fats (butter/shortening) prematurely, ruining the structure of cookies and pastries."
            },
            "box": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Used for yeast-raised donuts or danishes. Humid warmth allows yeast expansion without forming a dry surface skin."
            },
            "refrigerator": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Resting cookie or pastry dough solidifies butter fats and hydrates starch. Crucial for controlling cookie spread and preventing pastry shrinkage."
            },
            "bench_rest": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Allows gluten developed during mixing to relax, ensuring cookies spread evenly and pastries roll out without shrinking."
            },
            "cast-iron-dutch-oven": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not recommended. Enclosed high-heat environment will scorch sugar-rich confections and ruin delicate pastries."
            },
            "open-baking-stone-steel": {
                "labor_roi": "Low Priority / Sub-Optimal Selection",
                "last_10_percent_analysis": "Useful for cookies or flat pastries if lined with parchment, but direct steel contact can burn bottom sugars rapidly."
            },
            "standard-9x5-pan": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Excellent for quick breads and pound cakes. Provides structured vertical support for heavy batters."
            },
            "perforated-baking-sheet": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Excellent for delicate macarons or eclairs, letting heat distribute evenly to dry out shells without warping."
            },
            "butter": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Solid butter contains 18% water, which turns to steam and creates tiny layers during baking. Crucial for a flaky, melting texture."
            },
            "unsalted_butter": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Unsalted solid butter allows precise control over salt while providing emulsified dairy fats for a tender crumb."
            },
            "salted_butter": {
                "labor_roi": "Seamless Math Adjustment",
                "last_10_percent_analysis": "Salted butter detected. The engine has automatically reduced the standalone fine sea salt weight by 1.5% of the total butter mass to maintain perfect flavor balance and prevent over-seasoning your cookie crumb."
            },
            "olive_oil": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Brings a fruity, savory note to specialized olive oil cakes and shortbreads. Keeps the crumb extremely moist."
            },
            "canola_oil": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Provides pure liquid fat to tenderize dough without contributing any flavor. Great for neutral cakes or flatbreads."
            },
            "vegetable_oil": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Neutral liquid fat that remains fluid at room temp, keeping the baked crumb soft and preventing dryness."
            },
            "whole_milk": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Adds fat, sugar, and moisture to balance cake batters. Lactose promotes beautiful caramelization and crust color."
            },
            "almond_milk": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Acts as a dairy-free liquid substitute. Lacks milk fats, yielding a slightly drier and more open crumb."
            },
            "coconut_oil": {
                "labor_roi": "Low Priority / Flavor Shift",
                "last_10_percent_analysis": "Coconut oil provides a clean, plant-based solid lipid profile. It solidifies at cooler room temperatures, imparting a faint tropical aroma."
            },
            "avocado_oil": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Avocado oil is a neutral liquid lipid that remains fluid at room temperature. It coats gluten strands completely to produce an incredibly soft, moist, and long-lasting crumb."
            },
            "pure_water": {
                "labor_roi": "Standard Baseline",
                "last_10_percent_analysis": "Pure water provides clean, zero-interference hydration. It is the absolute optimal choice for lean hearth loaves to keep the crumb airy and the crust crispy."
            },
            "heavy_cream": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Heavy cream adds immense dairy fat richness (37% fat) and milk sugars. It tenderizes the crumb dramatically, yielding an ultra-soft slice at the cost of some oven rise."
            },
            "buttermilk": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Buttermilk introduces active lactic acidity. This chemically tenderizes the gluten matrix and triggers chemical leavening reactions, yielding an exceptionally tender crumb."
            },
            "none": {
                "labor_roi": "Standard Baseline",
                "last_10_percent_analysis": "No binder selected. The recipe relies purely on the gluten network and hydration matrix to establish structural integrity."
            },
            "whole_eggs": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Whole eggs contribute fat, moisture, and lecithin emulsifiers. They bind the structure together and promote rich browning and a soft, custard-like crumb."
            },
            "egg_whites": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Egg whites contribute pure albumin protein and hydration. They dry and solidify during baking, creating a taller, lighter, and crisper crust structure."
            },
            "aquafaba_vegan": {
                "labor_roi": "Critical Structural Risk",
                "last_10_percent_analysis": "Choux paste relies completely on the intense protein coagulation and water-binding capacity of whole egg lipids to hold its hollow balloon shape. Substituting a vegan binder here introduces a massive inflation failure risk; the shells will likely collapse into flat discs."
            }
        }
    elif group == "pasta":
        fallbacks = {
            "refined": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Allows smooth, uniform extrusion and dough sheet alignment. Provides a clean, bright appearance for fresh pasta."
            },
            "milled": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Produces a rustic whole-grain noodle with high mineral tooth (al dente). Requires extra resting time to allow complete bran hydration before sheeting."
            },
            "grain_hard_red_spring": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Hard spring wheat provides good tensile strength for noodles, but can be too elastic for rolling thin pasta sheets without snapping back."
            },
            "grain_hard_red_winter": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Good all-purpose option. Provides reasonable structural integrity for fresh noodles without making the dough too difficult to roll."
            },
            "grain_soft_white": {
                "labor_roi": "Low Priority / Sub-Optimal Selection",
                "last_10_percent_analysis": "Soft wheat lacks the structural resilience needed for al dente pasta, causing the noodles to become mushy when boiled."
            },
            "grain_hard_white": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Good structural candidate. Yields clean, pale noodles with high breaking strength and excellent chew."
            },
            "grain_spelt": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Produces a delicate, nutty specialty pasta. Requires minimal handling and rolling to prevent tearing the weak gluten structure."
            },
            "grain_kamut": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Golden ancient grain closely related to durum. Imparts a bright yellow hue, high tensile strength, and a sweet, buttery bite to pasta."
            },
            "grain_rye": {
                "labor_roi": "Low Priority / Sub-Optimal Selection",
                "last_10_percent_analysis": "High pentosan content makes pasta dough extremely sticky and brittle. Best blended in small fractions (under 15%) for rustic noodles."
            },
            "stand_mixer": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Efficiently forces moisture into dense semolina/egg dough. Excellent for initial compaction before hand kneading."
            },
            "bread_machine": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Can be used to mix pasta dough, but the motor will struggle with the extremely low hydration required for noodles."
            },
            "food_processor": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Combines flour and liquid in seconds. The fast spinning blade mimics high pressure compaction, perfect for pasta dough preparation."
            },
            "hand_beaters": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not recommended. Lacks the torque to mix dense, dry pasta dough."
            },
            "whisk": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Useful for beating eggs into a well of flour before incorporating, but cannot handle mixing the final dough."
            },
            "spatula_bowl": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Useful for initial dough clean-up and gathering scrap flour before tipping onto the bench for hand kneading."
            },
            "knead": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Essential step. Heavy hand-kneading aligns gluten proteins under tension, giving the noodle its resilient al dente snap."
            },
            "cream": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not used. Fat in pasta is typically egg yolks or oil mixed directly into the flour, not creamed."
            },
            "fold": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Folding during rolling layers the dough, aligning the proteins uniformly for a smooth, tear-free sheet."
            },
            "cut_in": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not used. Pasta relies on uniform hydration rather than solid fat pockets."
            },
            "sheet": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Repeated passing through rollers aligns gluten strands and egg proteins, yielding a smooth, thin noodle that holds its shape when boiled."
            },
            "extrude": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Forcing dense dough through shaped dies under pressure. Commercial brass dies yield a rougher sauce-binding noodle surface."
            },
            "ambient": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Allows gluten strands to relax at room temp, making the dough highly extensible and easy to roll out."
            },
            "mat": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Warm environments are unnecessary; pasta contains no yeast and heat can dry out the dough, making it brittle."
            },
            "box": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not recommended. Excess humidity makes pasta sticky and difficult to sheet."
            },
            "refrigerator": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Useful for resting pasta dough overnight if needed, but wrap tightly to prevent drying out and graying from oxidation."
            },
            "bench_rest": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Crucial 30-minute rest allows the flour to hydrate fully and the gluten to relax, making sheeting effortless without snapping."
            },
            "cast-iron-dutch-oven": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not used. Pasta is boiled in a pot, not baked in a dutch oven."
            },
            "open-baking-stone-steel": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not used."
            },
            "standard-9x5-pan": {
                "labor_roi": "Low Priority / Dangerous Structural Choice",
                "last_10_percent_analysis": "Not used."
            },
            "perforated-baking-sheet": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Used occasionally for drying cut noodles to prevent condensation buildup."
            },
            "butter": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Occasionally added to filled pasta doughs for richness, but typically not a standard sheeting ingredient."
            },
            "unsalted_butter": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Not a standard pasta component; fat is typically provided by egg yolks."
            },
            "salted_butter": {
                "labor_roi": "Seamless Math Adjustment",
                "last_10_percent_analysis": "Salted butter detected. The engine has automatically reduced the standalone fine sea salt weight by 1.5% of the total butter mass to maintain perfect flavor balance and prevent over-seasoning your cookie crumb."
            },
            "olive_oil": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "A classic addition. Enhances dough extensibility, making hand-sheeting easier and adding a subtle sheen to noodles."
            },
            "canola_oil": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Rarely used; olive oil is preferred for its flavor affinity."
            },
            "vegetable_oil": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Rarely used."
            },
            "whole_milk": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Rarely used; eggs provide the required liquid phase."
            },
            "almond_milk": {
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Not used."
            },
            "coconut_oil": {
                "labor_roi": "Low Priority / Flavor Shift",
                "last_10_percent_analysis": "Coconut oil provides a clean, plant-based solid lipid profile. It solidifies at cooler room temperatures, imparting a faint tropical aroma."
            },
            "avocado_oil": {
                "labor_roi": "Low Priority / Effortless Texture Shift",
                "last_10_percent_analysis": "Avocado oil is a neutral liquid lipid that remains fluid at room temperature. It coats gluten strands completely to produce an incredibly soft, moist, and long-lasting crumb."
            },
            "pure_water": {
                "labor_roi": "Standard Baseline",
                "last_10_percent_analysis": "Pure water provides clean, zero-interference hydration. It is the optimal choice for lean hearth loaves to keep the crumb airy and the crust crispy."
            },
            "heavy_cream": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Heavy cream adds immense dairy fat richness (37% fat) and milk sugars. It tenderizes the crumb dramatically, yielding an ultra-soft slice at the cost of some oven rise."
            },
            "buttermilk": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Buttermilk introduces active lactic acidity. This chemically tenderizes the gluten matrix and triggers chemical leavening reactions, yielding an exceptionally tender crumb."
            },
            "none": {
                "labor_roi": "Standard Baseline",
                "last_10_percent_analysis": "No binder selected. The recipe relies purely on the gluten network and hydration matrix to establish structural integrity."
            },
            "whole_eggs": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Whole eggs contribute fat, moisture, and lecithin emulsifiers. They bind the structure together and promote rich browning and a soft, custard-like crumb."
            },
            "egg_whites": {
                "labor_roi": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": "Egg whites contribute pure albumin protein and hydration. They dry and solidify during baking, creating a taller, lighter, and crisper crust structure."
            },
            "aquafaba_vegan": {
                "labor_roi": "Critical Structural Risk",
                "last_10_percent_analysis": "Choux paste relies completely on the intense protein coagulation and water-binding capacity of whole egg lipids to hold its hollow balloon shape. Substituting a vegan binder here introduces a massive inflation failure risk; the shells will likely collapse into flat discs."
            }
        }
    
    # Try querying Gemma if AI is active and enabled
    ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"
    insight = None
    if ai_enabled:
        try:
            insight = gemma_client.get_sidebar_insight_ai(element, category_slug, preset_slug)
        except Exception as e:
            logger.error(f"[AI] - Sidebar - Failed querying Gemma: {e}")
            
    if not insight:
        # Fall back to our clean recipe-aware local dictionary mapping
        # 1. First, check if it's a grain (only if AI is NOT enabled, to prevent applying algorithmic rules)
        if not ai_enabled and element.startswith("grain_"):
            from apps.core.models import WheatBerry, BreadPreset
            from grainlab.engines import router
            from apps.core.gemma_client import evaluate_single_grain

            preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
            category_slug = category_slug or (preset.dough_category.slug if preset and preset.dough_category else None)
            
            try:
                engine = router.get_engine_for_preset(preset_slug, category_slug)
            except Exception:
                engine = None
                
            if engine:
                # Find the hovered grain in DB (active or inactive)
                grain_obj = None
                for wb in WheatBerry.all_objects.filter(deleted_at__isnull=True):
                    import re
                    wb_slug = "grain_" + re.sub(r'[^a-z0-9]', '_', wb.name.lower())
                    if wb_slug == element or element in wb_slug or wb_slug in element:
                        grain_obj = wb
                        break
                        
                if grain_obj:
                    res = evaluate_single_grain(grain_obj, engine)
                    # Determine labor_roi based on tier
                    if res["tier"] == "recommended":
                        roi = "High Priority / Flavor Enhancement Opportunity"
                    elif res["tier"] == "sub-optimal":
                        roi = "Low Priority / Minor Textural Return"
                    else:
                        roi = "Low Priority / Dangerous Structural Choice"
                        
                    insight = {
                        "recommendation_tier": res["tier"],
                        "labor_roi": roi,
                        "last_10_percent_analysis": res["reasoning"]
                    }
                    
        # 2. If not a grain, or not resolved, look up in the static fallbacks
        if not insight:
            insight = fallbacks.get(element)
            if not insight and element.startswith("grain_"):
                # fallback for matching similar keys
                for k, val in fallbacks.items():
                    if k.startswith("grain_") and (k in element or element in k):
                        insight = val
                        break
            if insight:
                # Copy fallback to customize
                insight = dict(insight)
                # Map dynamic recommendation_tier based on labor_roi
                roi_lower = insight.get("labor_roi", "").lower()
                if "dangerous" in roi_lower or "sub-optimal" in roi_lower or "critical" in roi_lower:
                    insight["recommendation_tier"] = "not-recommended" if "dangerous" in roi_lower or "critical" in roi_lower else "sub-optimal"
                else:
                    insight["recommendation_tier"] = "recommended"
            else:
                insight = {
                    "recommendation_tier": "recommended",
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "An objective workspace configuration parameter. No significant performance anomalies or hidden labor opportunities detected."
                }
                
        # 3. Dynamic out-of-stock grain suggestion (only when AI is NOT enabled)
        if not ai_enabled:
            inactive_recs = get_inactive_grain_recommendations(preset_slug, category_slug)
            if inactive_recs:
                # Avoid duplicate recommendations if the hovered element itself is that out-of-stock grain
                rec = inactive_recs[0]
                hovered_clean = element.replace("grain_", "").replace("_", " ").lower()
                if rec["name"].lower() not in hovered_clean:
                    suggestion = f" Since {rec['name']} is currently out of stock, consider acquiring some; its {rec['protein']}% protein profile will enhance flavor and allow for superior texture."
                    analysis = insight.get("last_10_percent_analysis", "")
                    if suggestion not in analysis:
                        insight["last_10_percent_analysis"] = analysis.rstrip() + suggestion
        
    if insight and "elevate_recipe" not in insight:
        insight["elevate_recipe"] = ""
        
    return JsonResponse(insight)



