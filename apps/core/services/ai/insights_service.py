import logging

from apps.core import gemma
from apps.core.engines import router
from apps.core.models import SystemSetting
from apps.core.services.ai.advisory_service import get_inactive_grain_recommendations

logger = logging.getLogger("grainlab.services.ai")


def get_sidebar_insight(cleaned_data):
    element = cleaned_data.get("element", "")
    category_slug = cleaned_data.get("category_slug", "")
    preset_slug = cleaned_data.get("preset_slug", "")
    active_archetype_id = cleaned_data.get("active_archetype_id", "") or None

    if not element:
        return {
            "labor_roi": "Low Priority / Minor Textural Return",
            "last_10_percent_analysis": "Hover over any ingredient or control setting on the left to see objective science and AI magic diagnostics.",
        }

    try:
        engine = router.get_engine_for_preset(preset_slug, category_slug)
    except Exception:
        engine = None

    ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"
    insight = None
    if ai_enabled:
        try:
            insight = gemma.get_sidebar_insight_ai(element, category_slug, preset_slug)
        except Exception as e:
            logger.error(f"[AI] - Sidebar - Failed querying Gemma: {e}")

    if not insight:
        if not ai_enabled and element.startswith("grain_"):
            from apps.core.gemma import evaluate_single_grain
            from apps.core.models import WheatBerry

            if engine:
                grain_obj = None
                for wb in WheatBerry.all_objects.filter(deleted_at__isnull=True):
                    import re

                    wb_slug = "grain_" + re.sub(r"[^a-z0-9]", "_", wb.name.lower())
                    if wb_slug == element or element in wb_slug or wb_slug in element:
                        grain_obj = wb
                        break

                if grain_obj:
                    res = evaluate_single_grain(grain_obj, engine, preset_slug=preset_slug)
                    if res["tier"] == "recommended":
                        roi = "High Priority / Flavor Enhancement Opportunity"
                    elif res["tier"] == "sub-optimal":
                        roi = "Low Priority / Minor Textural Return"
                    else:
                        roi = "Low Priority / Dangerous Structural Choice"

                    insight = {
                        "recommendation_tier": res["tier"],
                        "labor_roi": roi,
                        "last_10_percent_analysis": res["reasoning"],
                    }

        if not insight:
            if engine:
                insight = engine.get_diagnostic_insight(element)

            if insight:
                insight = dict(insight)
                roi_lower = insight.get("labor_roi", "").lower()
                if "dangerous" in roi_lower or "sub-optimal" in roi_lower or "critical" in roi_lower:
                    insight["recommendation_tier"] = (
                        "not-recommended" if "dangerous" in roi_lower or "critical" in roi_lower else "sub-optimal"
                    )
                else:
                    insight["recommendation_tier"] = "recommended"
            else:
                insight = {
                    "recommendation_tier": "recommended",
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "An objective workspace configuration parameter. No significant performance anomalies or hidden labor opportunities detected.",
                }

        if not ai_enabled:
            inactive_recs = get_inactive_grain_recommendations(
                preset_slug, category_slug, active_archetype_id=active_archetype_id
            )
            if inactive_recs:
                rec = inactive_recs[0]
                hovered_clean = element.replace("grain_", "").replace("_", " ").lower()
                if rec["name"].lower() not in hovered_clean:
                    suggestion = f" Since {rec['name']} is currently out of stock, consider acquiring some; its {rec['protein']}% protein profile will enhance flavor and allow for superior texture."
                    analysis = insight.get("last_10_percent_analysis", "")
                    if suggestion not in analysis:
                        insight["last_10_percent_analysis"] = analysis.rstrip() + suggestion

    if insight and "elevate_recipe" not in insight:
        insight["elevate_recipe"] = ""

    return insight


def get_batch_insights(cleaned_data):
    elements = cleaned_data.get("elements", [])
    category_slug = cleaned_data.get("category_slug", "")
    preset_slug = cleaned_data.get("preset_slug", "")
    active_archetype_id = cleaned_data.get("active_archetype_id", "") or None

    results = {}
    for el in elements:
        res = get_sidebar_insight(
            {
                "element": el,
                "category_slug": category_slug,
                "preset_slug": preset_slug,
                "active_archetype_id": active_archetype_id,
            }
        )
        results[el] = res

    return results
