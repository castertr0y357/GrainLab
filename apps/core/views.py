import logging
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting
from apps.core import bakers_math
from apps.core import gemma_client

logger = logging.getLogger("grainlab.views")

def calculator(request):
    """
    Renders the primary calculator workspace.
    """
    categories = DoughCategory.objects.all().order_by('name')
    form_factors = FormFactor.objects.all().order_by('name')
    presets = BreadPreset.objects.all().order_by('name')
    
    # Load settings
    ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"
    
    # Default selection values
    default_cat = DoughCategory.objects.filter(slug='lean-crusty').first() or categories.first()
    default_ff = FormFactor.objects.filter(slug='loaf-pan').first() or form_factors.first()
    
    context = {
        "categories": categories,
        "form_factors": form_factors,
        "presets": presets,
        "selected_category": default_cat,
        "selected_form_factor": default_ff,
        "ai_enabled": ai_enabled,
        "default_hydration": int((default_cat.base_hydration if default_cat else 0.68) * 100),
        "default_fat": int((default_cat.base_fat if default_cat else 0.0) * 100),
        "default_sugar": int((default_cat.base_sugar if default_cat else 0.0) * 100),
        "default_starter": int((default_cat.base_starter if default_cat else 0.0) * 100),
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
    
    # Use preset values or category base values
    cat = preset.dough_category
    ff = preset.form_factor
    
    hydration = int((preset.hydration_override if preset.hydration_override is not None else cat.base_hydration) * 100)
    fat = int((preset.fat_override if preset.fat_override is not None else cat.base_fat) * 100)
    sugar = int((preset.sugar_override if preset.sugar_override is not None else cat.base_sugar) * 100)
    starter = int((preset.starter_override if preset.starter_override is not None else cat.base_starter) * 100)
    
    context = {
        "categories": categories,
        "form_factors": form_factors,
        "selected_preset": preset,
        "selected_category": cat,
        "selected_form_factor": ff,
        "default_hydration": hydration,
        "default_fat": fat,
        "default_sugar": sugar,
        "default_starter": starter,
        "default_flour_type": preset.flour_type_default,
        "default_flour_maturity": preset.flour_maturity_default,
    }
    return render(request, "partials/calculator_form.html", context)


@require_POST
def calculate_recipe_ajax(request):
    """
    Main calculation route. Intercepts inputs, processes Baker's Math and fail-safes,
    queries Gemma client (or fallbacks), and outputs formatted recipe card.
    """
    # 1. Parse parameters
    cat_slug = request.POST.get("dough_category")
    ff_slug = request.POST.get("form_factor")
    
    cat = get_object_or_404(DoughCategory, slug=cat_slug)
    ff = get_object_or_404(FormFactor, slug=ff_slug)
    
    hydration_pct = float(request.POST.get("hydration_pct", 68)) / 100.0
    fat_pct = float(request.POST.get("fat_pct", 0)) / 100.0
    sugar_pct = float(request.POST.get("sugar_pct", 0)) / 100.0
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
            substitution=substitution if not ai_enabled else None  # Natively balanced in bakers_math if AI is off
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

    # 4. Fetch AI Diagnostics (Sensory benchmark & pitfalls)
    eff_hyd = recipe["effective_hydration_pct"] / 100.0
    preset_slug = request.POST.get("preset_slug")
    
    sensory_desc = gemma_client.get_sensory_benchmark(grain_type, flour_maturity, eff_hyd)
    pitfalls = gemma_client.get_contextual_pitfalls(cat.slug, eff_hyd, grain_type, preset_slug)
    
    # 5. Core Thermal Doneness Temperature
    doneness_temp_f = 190 if ff.is_enriched_profile else 205
    doneness_temp_c = round((doneness_temp_f - 32) * 5 / 9, 1)

    context = {
        "recipe": recipe,
        "ff": ff,
        "cat": cat,
        "sensory_description": sensory_desc,
        "pitfalls": pitfalls,
        "doneness_temp_f": doneness_temp_f,
        "doneness_temp_c": doneness_temp_c,
        "leaven_type": leaven_type,
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
    ai_enabled = request.POST.get("ai_enabled") == "on"
    ai_api_url = request.POST.get("ai_api_url", "").strip()
    ai_model_name = request.POST.get("ai_model_name", "").strip()
    ai_thinking_enabled = request.POST.get("ai_thinking_enabled") == "on"
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
    is_sifted = request.POST.get("is_sifted") == "on"
    
    calibration = gemma_client.calibrate_fermentation(starter_feed_hours, rise_speed, mill_type, is_sifted)
    
    context = {
        "calibration": calibration,
    }
    return render(request, "partials/sourdough_diagnostic_output.html", context)
