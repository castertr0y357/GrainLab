from apps.core.models import SystemSetting

def system_settings(request):
    """
    Exposes key SystemSettings to all templates.
    """
    return {
        'theme_preference': SystemSetting.get_val("theme_preference", "system"),
        'keep_screen_awake': SystemSetting.get_val("keep_screen_awake", "True") == "True",
        'timeline_audio_alerts': SystemSetting.get_val("timeline_audio_alerts", "True") == "True",
        'weight_unit': SystemSetting.get_val("weight_unit", "grams"),
        'temperature_unit': SystemSetting.get_val("temperature_unit", "celsius"),
    }
