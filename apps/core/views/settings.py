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
import requests

from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting, WheatBerry, Equipment, BackgroundTask
from apps.core.utils import math as bakers_math
from apps.core import gemma
from apps.core.background_tasks import executor, run_async_task, ai_analyze_wheat_berry_task, ai_analyze_equipment_task, bulk_ai_analyze_task, redo_ai_analysis_task

logger = logging.getLogger("grainlab.views")

class SettingsPageView(View):
    def get(self, request):
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


class SaveSettingsView(View):
    def post(self, request):
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


class SourdoughCalibrateView(View):
    def post(self, request):
        """
        Runs bulk fermentation countdown diagnostics based on inputs.
        """
        starter_feed_hours = request.POST.get("starter_feed_hours", "4_8")
        rise_speed = request.POST.get("rise_speed", "normal")
        mill_type = request.POST.get("mill_type", "stoneground")
        is_sifted = request.POST.get("is_sifted") in ("on", "true", "True")
    
        calibration = gemma.calibrate_fermentation(starter_feed_hours, rise_speed, mill_type, is_sifted)
    
        context = {
            "calibration": calibration,
        }
        return render(request, "partials/sourdough_diagnostic_output.html", context)


class DiscoverModelsView(View):
    def get(self, request):
        """
        Discovers available models from the provided AI API URL.
        """
        api_url = request.GET.get("ai_api_url", "").strip()
        if not api_url:
            api_url = SystemSetting.get_val("ai_api_url", "http://host.docker.internal:11434/v1")
            
        current_model = SystemSetting.get_val("ai_model_name", "gemma:12b")
            
        # Try to form the models URL
        models_url = api_url.split("/chat/completions")[0]
        if models_url.endswith("/v1"):
            models_url = models_url + "/models"
        else:
            models_url = models_url.rstrip("/") + "/v1/models"
            
        models = []
        error_msg = None
        try:
            # Short timeout to avoid hanging the UI
            response = requests.get(models_url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    models = [m.get("id") for m in data["data"] if "id" in m]
                elif "models" in data:
                    # Some Ollama raw endpoints return {"models": [{"name": ...}]}
                    models = [m.get("name") for m in data["models"] if "name" in m]
            else:
                error_msg = f"API returned status {response.status_code}"
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            
        context = {
            "models": models,
            "error_msg": error_msg,
            "current_model": current_model,
        }
        return render(request, "partials/model_discovery_output.html", context)

