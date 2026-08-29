import logging
import math
import uuid
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views import View

from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting, WheatBerry, Equipment, BackgroundTask
from apps.core.utils import math as bakers_math
from apps.core import gemma
from apps.core.background_tasks import executor, run_async_task, ai_analyze_wheat_berry_task, ai_analyze_equipment_task, bulk_ai_analyze_task, redo_ai_analysis_task
from apps.core.services.calculator.session import get_engines_ff_json, get_engines_archetypes_json

logger = logging.getLogger("grainlab.views")


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
        
        # Update session with preset data
        request.session['calculator_state'] = {
            'selected_master': preset.dough_category.slug,
            'preset_slug': preset.slug,
            'form_factor': preset.form_factor.slug,
            'texture_score': preset.classifier_texture,
            'crumb_score': preset.classifier_crumb,
            'grain_type': preset.flour_type_default,
            'flour_maturity': preset.flour_maturity_default,
        }
        
        return redirect('calculator_phase2', category=preset.dough_category.slug)


