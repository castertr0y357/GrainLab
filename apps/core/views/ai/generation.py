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
from apps.core import gemma
from apps.core.views.tasks import run_async_task, ai_analyze_wheat_berry_task, ai_analyze_equipment_task, bulk_ai_analyze_task, redo_ai_analysis_task

logger = logging.getLogger("grainlab.views")
executor = ThreadPoolExecutor(max_workers=2)


class GenerateVariantsView(View):
    def get(self, request):
        """
        Polymorphic Tier 2 variant generator.
        Accepts: GET ?engine_id=<slug>&active_archetype_id=<slug>&inventory_ids=<comma-separated-uuids>&creativity_level=<int>
        Returns: JSON { generated_variants: [...] }
        """
        engine_id = request.GET.get("engine_id", "").strip()
        active_archetype_id = request.GET.get("active_archetype_id", "").strip()
        inventory_ids_raw = request.GET.get("inventory_ids", "").strip()
        creativity_level_raw = request.GET.get("creativity_level", "").strip()
        exclude_names_raw = request.GET.get("exclude_names", "").strip()
        exclude_names = [n.strip() for n in exclude_names_raw.split(",") if n.strip()]
        limit_raw = request.GET.get("limit", "5").strip()
        try:
            limit = int(limit_raw)
        except:
            limit = 5

        # Sanitize archetype_id from any recipe or level suffix
        if active_archetype_id:
            for suffix in ["_level", "_l1", "_l2", "_l3", "_v1", "_v2", "_v3", "_alt"]:
                if suffix in active_archetype_id:
                    active_archetype_id = active_archetype_id.split(suffix)[0]

        if not engine_id or not active_archetype_id:
            return JsonResponse({"error": "engine_id and active_archetype_id are required."}, status=400)

        # Resolve inventory grains
        inventory = []
        if inventory_ids_raw:
            id_list = [iid.strip() for iid in inventory_ids_raw.split(",") if iid.strip()]
            grains = WheatBerry.objects.filter(id__in=id_list, is_active=True)
            for g in grains:
                inventory.append({
                    "id": str(g.id),
                    "name": g.name,
                    "hardness": g.hardness,
                    "protein": float(g.protein_content),
                    "absorption": float(g.moisture_absorption_coef),
                })
        else:
            # Fall back to all active grains
            grains = WheatBerry.objects.filter(is_active=True)
            for g in grains:
                inventory.append({
                    "id": str(g.id),
                    "name": g.name,
                    "hardness": g.hardness,
                    "protein": float(g.protein_content),
                    "absorption": float(g.moisture_absorption_coef),
                })

        if creativity_level_raw:
            try:
                creativity_level = int(creativity_level_raw)
                result = gemma.generate_creativity_variants(engine_id, creativity_level, active_archetype_id, inventory, exclude_names=exclude_names, count=limit)
            except Exception as e:
                logger.error(f"[Views] Failed generating creativity variants: {e}")
                return JsonResponse({"error": "Failed generating variants"}, status=503)
        else:
            result = gemma.generate_recipe_variants(engine_id, active_archetype_id, inventory, exclude_names=exclude_names, count=limit)

        if result is None:
            return JsonResponse({"error": "Failed generating variants"}, status=503)

        return JsonResponse(result, status=200)


class GenerateCreativityRecipesView(View):
    def get(self, request):
        """
        Generate exactly 15 recipe profiles corresponding to Creativity Levels 1, 2, and 3 (5 per row).
        Accepts: GET ?engine_id=<slug>&active_archetype_id=<slug>&inventory_ids=<comma-separated-uuids>
        Returns: JSON { recipes: [...] }
        """
        engine_id = request.GET.get("engine_id", "").strip()
        active_archetype_id = request.GET.get("active_archetype_id", "").strip()
        inventory_ids_raw = request.GET.get("inventory_ids", "").strip()

        # Sanitize archetype_id from any recipe or level suffix
        if active_archetype_id:
            for suffix in ["_level", "_l1", "_l2", "_l3", "_v1", "_v2", "_v3", "_alt"]:
                if suffix in active_archetype_id:
                    active_archetype_id = active_archetype_id.split(suffix)[0]

        if not engine_id:
            return JsonResponse({"error": "engine_id is required."}, status=400)
        if not active_archetype_id:
            return JsonResponse({"error": "active_archetype_id is required."}, status=400)

        # Resolve inventory grains
        inventory = []
        if inventory_ids_raw:
            id_list = [iid.strip() for iid in inventory_ids_raw.split(",") if iid.strip()]
            grains = WheatBerry.objects.filter(id__in=id_list, is_active=True)
            for g in grains:
                inventory.append({
                    "id": str(g.id),
                    "name": g.name,
                    "hardness": g.hardness,
                    "protein": float(g.protein_content),
                    "absorption": float(g.moisture_absorption_coef),
                })
        else:
            # Fall back to all active grains
            grains = WheatBerry.objects.filter(is_active=True)
            for g in grains:
                inventory.append({
                    "id": str(g.id),
                    "name": g.name,
                    "hardness": g.hardness,
                    "protein": float(g.protein_content),
                    "absorption": float(g.moisture_absorption_coef),
                })

        result = gemma.generate_creativity_recipes(engine_id, active_archetype_id, inventory)
        if not result or not result.get("recipes"):
            fallback = gemma.get_fallback_creativity_recipes(engine_id, active_archetype_id, pref_slugs=[])
            return JsonResponse(fallback, status=200)

        return JsonResponse(result, status=200)


class AiOptimizeSharesView(View):
    def get(self, request):
        from django.http import JsonResponse
        from apps.core import gemma
        from apps.core.models import WheatBerry
        import json
    
        preset_slug = request.GET.get("preset_slug", "").strip()
        preset_name = request.GET.get("preset_name", "").strip()
        selected_grains = request.GET.get("selected_grains", "").strip()
    
        selected_ids = [s.strip() for s in selected_grains.split(",") if s.strip()] if selected_grains else []
        active_berries = []
        if selected_ids:
            active_berries = list(WheatBerry.objects.filter(id__in=selected_ids))
    
        if not active_berries or not preset_slug:
            return JsonResponse({"shares": {}})
        
        result = gemma.optimize_grain_blend(preset_slug, preset_name, active_berries)
        if result:
            shares, warning = result
            return JsonResponse({"shares": shares, "warning": warning})
        return JsonResponse({"shares": {}})


