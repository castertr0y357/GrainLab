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
from apps.core.views.calculator.base import get_engines_ff_json, get_engines_archetypes_json

logger = logging.getLogger("grainlab.views")
executor = ThreadPoolExecutor(max_workers=2)


class SearchPresetsView(View):
    def get(self, request):
        """
        Handles debounced preset search queries, returning HTMX results.
        """
        q = request.GET.get("q", "").strip()
        if len(q) < 2:
            return HttpResponse("")
        
        presets = BreadPreset.objects.filter(name__icontains=q)[:5]
        return render(request, "partials/search_results.html", {"presets": presets})


class LoadPresetView(View):
    def get(self, request, preset_id):
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
            "engines_archetypes_json": get_engines_archetypes_json(),
        }
        return render(request, "partials/calculator_form.html", context)


