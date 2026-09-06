import logging

import requests
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from apps.core import gemma
from apps.core.models import (
    Equipment,
    SystemSetting,
)

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
            # New Settings
            "weight_unit": SystemSetting.get_val("weight_unit", "grams"),
            "temperature_unit": SystemSetting.get_val("temperature_unit", "celsius"),
            "date_time_format": SystemSetting.get_val("date_time_format", "24h"),
            "default_ambient_temperature": SystemSetting.get_val("default_ambient_temperature", "72"),
            "default_ambient_humidity": SystemSetting.get_val("default_ambient_humidity", "50"),
            "default_mixer": SystemSetting.get_val("default_mixer", ""),
            "default_proofing_environment": SystemSetting.get_val("default_proofing_environment", ""),
            "theme_preference": SystemSetting.get_val("theme_preference", "system"),
            "keep_screen_awake": SystemSetting.get_val("keep_screen_awake", "True") == "True",
            "timeline_audio_alerts": SystemSetting.get_val("timeline_audio_alerts", "True") == "True",
            "fractional_scaling_increment": SystemSetting.get_val("fractional_scaling_increment", "0.5"),
            "soft_delete_retention_days": SystemSetting.get_val("soft_delete_retention_days", "30"),
            "export_format_default": SystemSetting.get_val("export_format_default", "json"),
            # Inventory for dropdowns
            "mixers": Equipment.objects.filter(equipment_type="mixer", deleted_at__isnull=True),
            "proofing_environments": Equipment.objects.filter(equipment_type="proofing_box", deleted_at__isnull=True),
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

        # New Settings
        SystemSetting.set_val("weight_unit", request.POST.get("weight_unit", "grams"))
        SystemSetting.set_val("temperature_unit", request.POST.get("temperature_unit", "celsius"))
        SystemSetting.set_val("date_time_format", request.POST.get("date_time_format", "24h"))
        SystemSetting.set_val("default_ambient_temperature", request.POST.get("default_ambient_temperature", "72"))
        SystemSetting.set_val("default_ambient_humidity", request.POST.get("default_ambient_humidity", "50"))
        SystemSetting.set_val("default_mixer", request.POST.get("default_mixer", ""))
        SystemSetting.set_val("default_proofing_environment", request.POST.get("default_proofing_environment", ""))
        SystemSetting.set_val("theme_preference", request.POST.get("theme_preference", "system"))
        SystemSetting.set_val("keep_screen_awake", request.POST.get("keep_screen_awake") in ("on", "true", "True"))
        SystemSetting.set_val(
            "timeline_audio_alerts", request.POST.get("timeline_audio_alerts") in ("on", "true", "True")
        )
        SystemSetting.set_val("fractional_scaling_increment", request.POST.get("fractional_scaling_increment", "0.5"))
        SystemSetting.set_val("soft_delete_retention_days", request.POST.get("soft_delete_retention_days", "30"))
        SystemSetting.set_val("export_format_default", request.POST.get("export_format_default", "json"))

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
