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
from apps.core.views.ai.advisory import get_inactive_grain_recommendations

logger = logging.getLogger("grainlab.views")
executor = ThreadPoolExecutor(max_workers=2)


class AiSidebarInsightView(View):
    def get(self, request):
        """
        Returns dynamic labor ROI and critique analysis for the hovered element.
        """
        from django.http import JsonResponse
        from apps.core import gemma
    
        element = request.GET.get("element", "").strip()
        category_slug = request.GET.get("category_slug", "").strip()
        preset_slug = request.GET.get("preset_slug", "").strip()
        active_archetype_id = request.GET.get("active_archetype_id", "").strip() or None
    
        if not element:
            return JsonResponse({
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Hover over any ingredient or control setting on the left to see objective science and AI magic diagnostics."
            })
        
        from grainlab.engines import router
        try:
            engine = router.get_engine_for_preset(preset_slug, category_slug)
        except Exception:
            engine = None

        # Try querying Gemma if AI is active and enabled
        ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"
        insight = None
        if ai_enabled:
            try:
                insight = gemma.get_sidebar_insight_ai(element, category_slug, preset_slug)
            except Exception as e:
                logger.error(f"[AI] - Sidebar - Failed querying Gemma: {e}")
            
        if not insight:
            # 1. First, check if it's a grain (only if AI is NOT enabled, to prevent applying algorithmic rules)
            if not ai_enabled and element.startswith("grain_"):
                from apps.core.models import WheatBerry, BreadPreset
                from apps.core.gemma import evaluate_single_grain

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
                        res = evaluate_single_grain(grain_obj, engine, preset_slug=preset_slug)
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
                if engine:
                    insight = engine.get_diagnostic_insight(element)
                
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
                inactive_recs = get_inactive_grain_recommendations(preset_slug, category_slug, active_archetype_id=active_archetype_id)
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


class AiBatchInsightsView(View):
    def get(self, request):
        from django.http import JsonResponse
        from apps.core import gemma
        import json
        from django.http import HttpRequest
    
        elements_raw = request.GET.get("elements", "[]")
        try:
            elements = json.loads(elements_raw)
        except:
            elements = []
        
        category_slug = request.GET.get("category_slug", "").strip()
        preset_slug = request.GET.get("preset_slug", "").strip()
        active_archetype_id = request.GET.get("active_archetype_id", "").strip() or None
    
        results = {}
    
        for el in elements:
            # Construct mock request to re-use ai_sidebar_insight logic directly
            req = HttpRequest()
            req.GET = {
                "element": el,
                "category_slug": category_slug,
                "preset_slug": preset_slug,
                "active_archetype_id": active_archetype_id or ""
            }
            res = AiSidebarInsightView().get(req)
            try:
                results[el] = json.loads(res.content)
            except Exception as e:
                results[el] = {}
            
        return JsonResponse({"batch_insights": results})


