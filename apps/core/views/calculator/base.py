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


class CalculatorView(View):
    def get(self, request):
        """
        Renders the primary calculator workspace.
        """
        categories = DoughCategory.objects.all().order_by('name')
        form_factors = FormFactor.objects.all().order_by('name')
        presets = BreadPreset.objects.all().order_by('name')
        mixers = Equipment.objects.filter(equipment_type='mixer').order_by('name')
        mills = Equipment.objects.filter(equipment_type='mill').order_by('name')
    
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
            "mills": mills,
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
            "engines_archetypes_json": get_engines_archetypes_json(),
        }
        return render(request, "calculator.html", context)


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


def get_engines_archetypes_json() -> str:
    """
    Serializes each engine's archetypes dict keyed by category slug for Alpine.js consumption.
    """
    from grainlab.engines.router import ENGINES
    from apps.core.gemma_client import CATEGORY_TO_ENGINE
    import json

    archetypes_data = {}
    for cat_slug, eng_name in CATEGORY_TO_ENGINE.items():
        engine = ENGINES[eng_name]
        archetypes_data[cat_slug] = getattr(engine, "archetypes", {})
    return json.dumps(archetypes_data)


