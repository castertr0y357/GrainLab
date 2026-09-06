import json
import logging

from apps.core import gemma
from apps.core.engines import router
from apps.core.gemma import evaluate_grains_batch
from apps.core.models import BreadPreset, SystemSetting, WheatBerry

logger = logging.getLogger("grainlab.services.ai")


def process_grain_advisory(cleaned_data):
    preset_slug = cleaned_data.get("preset_slug", "")
    category_slug = cleaned_data.get("category_slug", "")

    if not preset_slug and not category_slug:
        return False, {"grain_evaluations": [], "elevate_recipe": []}

    ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"

    if ai_enabled:

        def event_stream():
            try:
                generator = gemma.stream_grain_evaluations(
                    preset_slug,
                    category_slug,
                    preset_name=cleaned_data.get("preset_name"),
                    active_archetype_id=cleaned_data.get("active_archetype_id"),
                    active_variation_id=cleaned_data.get("active_variation_id"),
                    target=cleaned_data.get("target"),
                )
                for item in generator:
                    yield f"data: {json.dumps(item)}\n\n"
            except Exception as e:
                logger.error(f"[AI] - Advisory Stream Error: {e}")
                yield f"data: {json.dumps({'error': 'Failed streaming advisory'})}\n\n"
            yield "data: [DONE]\n\n"

        return True, event_stream

    return False, {"grain_evaluations": [], "elevate_recipe": [], "mill_evaluations": [], "sifter_evaluations": {}}


def get_inactive_grain_recommendations(
    preset_slug: str, category_slug: str = None, active_archetype_id: str = None
) -> list[dict]:
    """
    Evaluates all inactive grains and returns those that are 'recommended' for the current preset/engine/archetype.
    """
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

    evals = evaluate_grains_batch(
        inactive_berries, engine, preset_slug=preset_slug, active_archetype_id=active_archetype_id
    )
    recommended_inactive = []

    for wb in inactive_berries:
        res = evals.get(str(wb.id))
        if res and res.get("tier") == "recommended":
            recommended_inactive.append(
                {
                    "name": wb.name,
                    "protein": wb.protein_content,
                    "benefit": getattr(wb, "notes", "") or "enhances flavor and structure",
                }
            )

    return recommended_inactive
