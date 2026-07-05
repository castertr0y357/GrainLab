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
    
    hydration = int((preset.hydration_override if preset.hydration_override is not None else cat.base_hydration) * 100)
    fat = int((preset.fat_override if preset.fat_override is not None else cat.base_fat) * 100)
    sugar = int((preset.sugar_override if preset.sugar_override is not None else cat.base_sugar) * 100)
    starter = int((preset.starter_override if preset.starter_override is not None else cat.base_starter) * 100)
    
    active_berries = list(WheatBerry.objects.filter(is_active=True))
    
    context = {
        "categories": categories,
        "form_factors": form_factors,
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
    current_phase = int(request.POST.get("current_phase", 1))
    
    cat = get_object_or_404(DoughCategory, slug=cat_slug)
    ff = get_object_or_404(FormFactor, slug=ff_slug)
    
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
    is_portioned = ff.is_portioned
    unit_weight = float(request.POST.get("unit_weight", ff.unit_weight))
    portion_count = int(request.POST.get("portion_count", ff.default_count))
    
    if is_portioned:
        target_mass = unit_weight * portion_count
    else:
        target_mass = float(request.POST.get("target_weight", ff.target_weight))
        
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

    preset_slug = request.POST.get("preset_slug")
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
            category_slug=cat.slug
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
    
    sensory_desc = gemma_client.get_sensory_benchmark(grain_type, flour_maturity, eff_hyd)
    pitfalls = gemma_client.get_contextual_pitfalls(cat.slug, eff_hyd, grain_type, preset_slug_resolved)
    
    # 6. Core Thermal Doneness Temperature
    doneness_temp_f = 190 if ff.is_enriched_profile else 205
    doneness_temp_c = round((doneness_temp_f - 32) * 5 / 9, 1)

    # 7. Algorithmically scale baking profile based on mass and form factor
    base_temp = ff.bake_temp_f
    base_time = ff.bake_time_min
    base_weight = ff.target_weight if not ff.is_portioned else (ff.unit_weight * ff.default_count)
    
    mass_ratio = target_mass / base_weight if base_weight > 0 else 1.0
    scaled_time = round(base_time * (mass_ratio ** 0.4))
    
    scaled_temp = base_temp
    if not ff.is_portioned:
        if mass_ratio > 1.2:
            scaled_temp = base_temp - 10
        elif mass_ratio < 0.8:
            scaled_temp = base_temp + 10

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
    Returns dynamic recommendation and warning details for the requested preset.
    """
    from django.http import JsonResponse
    from apps.core import gemma_client
    
    preset_slug = request.GET.get("preset_slug", "").strip()
    if not preset_slug:
        return JsonResponse({
            "recommended_name": "",
            "recommended_reason": "",
            "high_risk_name": "",
            "high_risk_reason": ""
        })
        
    advisory = None
    try:
        advisory = gemma_client.get_grain_advisory_ai(preset_slug)
    except Exception as e:
        logger.error(f"[AI] - Advisory - Failed fetching advisory from Gemma: {e}")
        
    if not advisory:
        advisory = gemma_client.get_local_grain_advisory(preset_slug)
        
    return JsonResponse(advisory)



