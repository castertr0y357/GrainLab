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


class AiGrainAdvisoryView(View):
    def get(self, request):
        """
        Returns dynamic recommendation and warning details for the requested preset or category.
        """
        from django.http import JsonResponse
        from apps.core import gemma
        from apps.core.models import SystemSetting
        import json
    
        preset_slug = request.GET.get("preset_slug", "").strip()
        preset_name = request.GET.get("preset_name", "").strip()
        category_slug = request.GET.get("category_slug", "").strip()
        selected_grains = request.GET.get("selected_grains", "").strip()
        only_evaluations = request.GET.get("only_evaluations", "false").lower() == "true"
        only_elevate = request.GET.get("only_elevate", "false").lower() == "true"
    
        active_archetype_id = request.GET.get("active_archetype_id", "").strip() or None
    
        lipid = request.GET.get("lipid", "").strip() or request.GET.get("secondary_lipid", "").strip() or None
        liquid = request.GET.get("liquid", "").strip() or request.GET.get("secondary_liquid", "").strip() or None
        binder = request.GET.get("binder", "").strip() or request.GET.get("secondary_binder", "").strip() or None

        # Sanitize preset_slug from any recipe or level suffix
        if preset_slug:
            for suffix in ["_level", "_l1", "_l2", "_l3", "_v1", "_v2", "_v3", "_alt"]:
                if suffix in preset_slug:
                    preset_slug = preset_slug.split(suffix)[0]
    
        if not preset_slug and not category_slug:
            return JsonResponse({
                "grain_evaluations": [],
                "elevate_recipe": []
            })
        
        stream = request.GET.get("stream", "false").lower() == "true"
        
        ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"
        
        if stream and ai_enabled and only_evaluations:
            from django.http import StreamingHttpResponse
            
            def event_stream():
                try:
                    generator = gemma.stream_grain_evaluations(
                        preset_slug, category_slug, 
                        preset_name=preset_name,
                        active_archetype_id=active_archetype_id
                    )
                    for item in generator:
                        yield f"data: {json.dumps(item)}\n\n"
                except Exception as e:
                    logger.error(f"[AI] - Advisory Stream Error: {e}")
                    yield f"data: {json.dumps({'error': 'Failed streaming advisory'})}\n\n"
                
                yield "data: [DONE]\n\n"
                
            return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

        advisory = None
        if ai_enabled:
            try:
                advisory = gemma.get_grain_advisory_ai(
                    preset_slug, category_slug, 
                    selected_grains=selected_grains,
                    only_evaluations=only_evaluations,
                    only_elevate=only_elevate,
                    preset_name=preset_name,
                    active_archetype_id=active_archetype_id,
                    lipid=lipid,
                    liquid=liquid,
                    binder=binder
                )
            except Exception as e:
                logger.error(f"[AI] - Advisory - Failed fetching advisory from Gemma: {e}")
                return JsonResponse({"error": "Failed fetching advisory"}, status=503)
        else:
            advisory = gemma.get_local_grain_advisory(preset_slug, category_slug, preset_name=preset_name, active_archetype_id=active_archetype_id)
            if only_elevate:
                # Generate local/mock elevate tips when AI is disabled
                mock_data = gemma.get_mock_gemma_response(
                    system_prompt="",
                    user_prompt=json.dumps({
                        "preset_slug": preset_slug,
                        "category_slug": category_slug,
                        "active_archetype_id": active_archetype_id,
                        "selected_grains": [s.strip() for s in selected_grains.split(",") if s.strip()]
                    }),
                    expected_keys=["elevate_recipe"]
                )
                advisory = {"elevate_recipe": mock_data.get("elevate_recipe", [])}
        
        if advisory is None:
            advisory = {}
        
        if only_evaluations:
            return JsonResponse({
                "grain_evaluations": advisory.get("grain_evaluations", []),
                "mill_evaluations": advisory.get("mill_evaluations", []),
                "sifter_evaluations": advisory.get("sifter_evaluations", {})
            })
        elif only_elevate:
            return JsonResponse({"elevate_recipe": advisory.get("elevate_recipe", [])})
        else:
            return JsonResponse({
                "grain_evaluations": advisory.get("grain_evaluations", []),
                "elevate_recipe": advisory.get("elevate_recipe", []),
                "mill_evaluations": advisory.get("mill_evaluations", []),
                "sifter_evaluations": advisory.get("sifter_evaluations", {})
            })


def get_inactive_grain_recommendations(preset_slug: str, category_slug: str = None, active_archetype_id: str = None) -> list[dict]:
    """
    Evaluates all inactive grains and returns those that are 'recommended' for the current preset/engine/archetype.
    """
    from apps.core.models import WheatBerry, BreadPreset
    from grainlab.engines import router
    from apps.core.gemma import evaluate_grains_batch

    preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
    if not category_slug and preset and preset.dough_category:
        category_slug = preset.dough_category.slug
    
    try:
        engine = router.get_engine_for_preset(preset_slug, category_slug)
    except Exception:
        return []

    inactive_berries = list(WheatBerry.all_objects.filter(is_active=False, deleted_at__isnull=True))
    if not inactive_berries:
        return []

    evals = evaluate_grains_batch(inactive_berries, engine, preset_slug=preset_slug, active_archetype_id=active_archetype_id)
    recommended_inactive = []

    for wb in inactive_berries:
        res = evals.get(str(wb.id))
        if res and res.get("tier") == "recommended":
            recommended_inactive.append({
                "name": wb.name,
                "protein": wb.protein_content,
                "benefit": getattr(wb, "notes", "") or "enhances flavor and structure"
            })
            
    return recommended_inactive


