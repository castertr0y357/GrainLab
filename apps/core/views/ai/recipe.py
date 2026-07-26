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


class AiRecipeDetailsView(View):
    def get(self, request):
        """
        Returns AI-generated detailed science profile and elevate recipe tips for a selected recipe.
        Accepts: GET ?recipe_slug=<slug>&engine_id=<slug>&active_archetype_id=<slug>&selected_grains=<comma-separated>&category_slug=<slug>
        Returns: JSON { sidebar_science_profile: "...", elevate_recipe: [...] }
        """
        from django.http import JsonResponse
        from apps.core import gemma

        recipe_slug = request.GET.get("recipe_slug", "").strip()
        recipe_name = request.GET.get("recipe_name", "").strip()
        engine_id = request.GET.get("engine_id", "").strip()
        active_archetype_id = request.GET.get("active_archetype_id", "").strip()
        selected_grains = request.GET.get("selected_grains", "").strip()
        category_slug = request.GET.get("category_slug", "").strip()
        mill_type = request.GET.get("mill_type", "").strip()
        is_sifted = request.GET.get("is_sifted", "false").strip().lower() == "true"

        if not recipe_slug:
            return JsonResponse({"error": "recipe_slug is required."}, status=400)

        # Convert grain IDs to actual human-readable names for the LLM
        selected_grains_names = ""
        if selected_grains:
            grain_ids = [g.strip() for g in selected_grains.split(",") if g.strip()]
            parsed_uuids = []
            raw_names = []
            for gid in grain_ids:
                try:
                    parsed_uuids.append(uuid.UUID(gid))
                except ValueError:
                    raw_names.append(gid)
        
            db_grains = WheatBerry.objects.filter(id__in=parsed_uuids)
            db_names = [b.name for b in db_grains]
            all_names = db_names + raw_names
            selected_grains_names = ", ".join(all_names)

        # Sanitize archetype ID if it contains suffixes
        if active_archetype_id:
            for suffix in ["_level", "_l1", "_l2", "_l3", "_v1", "_v2", "_v3", "_alt"]:
                if suffix in active_archetype_id:
                    active_archetype_id = active_archetype_id.split(suffix)[0]

        result = gemma.generate_recipe_details(
            engine_id=engine_id,
            active_archetype_id=active_archetype_id,
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            selected_grains=selected_grains_names,
            category_slug=category_slug,
            mill_type=mill_type,
            is_sifted=is_sifted
        )

        if result is None:
            from apps.core.models import SystemSetting
            if SystemSetting.get_val('ai_enabled', 'False') == 'True':
                return JsonResponse({'error': 'Failed generating recipe details'}, status=503)
            result = gemma.get_local_recipe_details(
                recipe_slug=recipe_slug,
                recipe_name=recipe_name,
                engine_id=engine_id,
                active_archetype_id=active_archetype_id,
                selected_grains=selected_grains_names,
                mill_type=mill_type,
                is_sifted=is_sifted
            )
            return JsonResponse(result, status=200)

        return JsonResponse(result, status=200)



class AiGenerateSubstitutesView(View):
    def post(self, request):
        """
        Returns AI-generated substitutes for a specific category.
        Accepts: POST JSON payload with engine_id, active_archetype_id, recipe_slug, recipe_name, selected_grains, target_category, original_recommendation
        Returns: JSON { substitutes: [...] }
        """
        from django.http import JsonResponse
        from apps.core import gemma
        import json

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        recipe_slug = data.get("recipe_slug", "").strip()
        recipe_name = data.get("recipe_name", "").strip()
        engine_id = data.get("engine_id", "").strip()
        active_archetype_id = data.get("active_archetype_id", "").strip()
        selected_grains = data.get("selected_grains", "").strip()
        target_category = data.get("target_category", "").strip()
        original_recommendation = data.get("original_recommendation", {})

        exclude_names = data.get("exclude_names", [])

        if not recipe_slug or not target_category:
            return JsonResponse({"error": "recipe_slug and target_category are required."}, status=400)

        result = gemma.generate_substitutes(
            engine_id=engine_id,
            active_archetype_id=active_archetype_id,
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            selected_grains=selected_grains,
            target_category=target_category,
            original_recommendation=original_recommendation,
            exclude_names=exclude_names
        )

        if result is None:
            return JsonResponse({'error': 'Failed generating substitutes'}, status=503)

        return JsonResponse(result, status=200)

class AiProcessAlternativesView(View):
    def post(self, request):
        from django.http import JsonResponse
        from apps.core import gemma
        import json

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        recipe_slug = data.get("recipe_slug", "").strip()
        recipe_name = data.get("recipe_name", "").strip()
        engine_id = data.get("engine_id", "").strip()
        active_archetype_id = data.get("active_archetype_id", "").strip()
        target_category = data.get("target_category", "").strip()
        original_recommendation = data.get("original_recommendation", {})
        exclude_names = data.get("exclude_names", [])

        if not recipe_slug or not target_category:
            return JsonResponse({"error": "recipe_slug and target_category are required."}, status=400)

        result = gemma.generate_process_alternatives(
            engine_id=engine_id,
            active_archetype_id=active_archetype_id,
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            target_category=target_category,
            original_recommendation=original_recommendation,
            exclude_names=exclude_names
        )

        if result is None:
            return JsonResponse({'error': 'Failed generating process alternatives'}, status=503)

        return JsonResponse(result, status=200)

class AiProcessDetailsView(View):
    def get(self, request):
        from django.http import JsonResponse
        from apps.core import gemma

        recipe_slug = request.GET.get("recipe_slug", "").strip()
        recipe_name = request.GET.get("recipe_name", "").strip()
        engine_id = request.GET.get("engine_id", "").strip()
        active_archetype_id = request.GET.get("active_archetype_id", "").strip()

        if not recipe_slug:
            return JsonResponse({"error": "recipe_slug is required."}, status=400)

        result = gemma.generate_process_details(
            engine_id=engine_id,
            active_archetype_id=active_archetype_id,
            recipe_slug=recipe_slug,
            recipe_name=recipe_name
        )

        if result is None:
            return JsonResponse({'error': 'Failed generating process details'}, status=503)

        return JsonResponse(result, status=200)

