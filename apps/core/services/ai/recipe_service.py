import json
import logging

from apps.core import gemma
from apps.core.gemma.phase4_client import generate_recipe_tweaks, generate_tweak_application_state, stream_recipe_tweaks
from apps.core.models import SystemSetting
from apps.core.services.calculator.session import get_calculator_state, update_calculator_state

logger = logging.getLogger("grainlab.services.ai")


def process_recipe_details(cleaned_data):
    is_stream = cleaned_data.get("stream", False)

    if is_stream:

        def event_stream():
            try:
                generator = gemma.stream_recipe_details(
                    engine_id=cleaned_data.get("engine_id"),
                    active_archetype_id=cleaned_data.get("active_archetype_id"),
                    recipe_slug=cleaned_data.get("recipe_slug"),
                    recipe_name=cleaned_data.get("recipe_name"),
                    selected_grains=cleaned_data.get("selected_grains"),
                    category_slug=cleaned_data.get("category_slug"),
                    mill_type=cleaned_data.get("mill_type"),
                    is_sifted=cleaned_data.get("is_sifted"),
                    target=cleaned_data.get("target", "all"),
                    active_variation_id=cleaned_data.get("active_variation_id"),
                )
                for item in generator:
                    yield f"data: {json.dumps(item)}\n\n"
            except Exception as e:
                import traceback

                logger.error(f"[AI] - Recipe Details Stream Error: {e}\n{traceback.format_exc()}")
                yield f"data: {json.dumps({'error': 'Failed streaming recipe details'})}\n\n"
            yield "data: [DONE]\n\n"

        return event_stream

    result = gemma.generate_recipe_details(
        engine_id=cleaned_data.get("engine_id"),
        active_archetype_id=cleaned_data.get("active_archetype_id"),
        recipe_slug=cleaned_data.get("recipe_slug"),
        recipe_name=cleaned_data.get("recipe_name"),
        selected_grains=cleaned_data.get("selected_grains"),
        category_slug=cleaned_data.get("category_slug"),
        mill_type=cleaned_data.get("mill_type"),
        is_sifted=cleaned_data.get("is_sifted"),
        active_variation_id=cleaned_data.get("active_variation_id"),
    )

    if result is None:
        if SystemSetting.get_val("ai_enabled", "False") == "True":
            return None
        result = gemma.get_local_recipe_details(
            recipe_slug=cleaned_data.get("recipe_slug"),
            recipe_name=cleaned_data.get("recipe_name"),
            engine_id=cleaned_data.get("engine_id"),
            active_archetype_id=cleaned_data.get("active_archetype_id"),
            selected_grains=cleaned_data.get("selected_grains"),
            mill_type=cleaned_data.get("mill_type"),
            is_sifted=cleaned_data.get("is_sifted"),
        )
    return result


def process_recipe_percentages(cleaned_data):
    return gemma.generate_recipe_percentages(
        engine_id=cleaned_data.get("engine_id"),
        active_archetype_id=cleaned_data.get("active_archetype_id"),
        recipe_slug=cleaned_data.get("recipe_slug"),
        recipe_name=cleaned_data.get("recipe_name"),
        secondary_ingredients=cleaned_data.get("secondary_ingredients", []),
    )


def process_generate_substitutes(cleaned_data):
    is_stream = cleaned_data.get("stream", False)
    if is_stream:

        def event_stream():
            try:
                generator = gemma.stream_generate_substitutes(
                    engine_id=cleaned_data.get("engine_id"),
                    active_archetype_id=cleaned_data.get("active_archetype_id"),
                    recipe_slug=cleaned_data.get("recipe_slug"),
                    recipe_name=cleaned_data.get("recipe_name"),
                    selected_grains=cleaned_data.get("selected_grains"),
                    target_category=cleaned_data.get("target_category"),
                    original_recommendation=cleaned_data.get("original_recommendation"),
                    exclude_names=cleaned_data.get("exclude_names"),
                )
                for item in generator:
                    yield f"data: {json.dumps(item)}\n\n"
            except Exception as e:
                logger.error(f"[AI] - Substitute Stream Error: {e}")
                yield f"data: {json.dumps({'error': 'Failed streaming substitutes'})}\n\n"
            yield "data: [DONE]\n\n"

        return event_stream

    return gemma.generate_substitutes(
        engine_id=cleaned_data.get("engine_id"),
        active_archetype_id=cleaned_data.get("active_archetype_id"),
        recipe_slug=cleaned_data.get("recipe_slug"),
        recipe_name=cleaned_data.get("recipe_name"),
        selected_grains=cleaned_data.get("selected_grains"),
        target_category=cleaned_data.get("target_category"),
        original_recommendation=cleaned_data.get("original_recommendation"),
        exclude_names=cleaned_data.get("exclude_names"),
    )


def process_alternatives(cleaned_data):
    is_stream = cleaned_data.get("stream", False)
    if is_stream:

        def event_stream():
            try:
                generator = gemma.stream_process_alternatives(
                    engine_id=cleaned_data.get("engine_id"),
                    active_archetype_id=cleaned_data.get("active_archetype_id"),
                    recipe_slug=cleaned_data.get("recipe_slug"),
                    recipe_name=cleaned_data.get("recipe_name"),
                    target_category=cleaned_data.get("target_category"),
                    original_recommendation=cleaned_data.get("original_recommendation"),
                    exclude_names=cleaned_data.get("exclude_names"),
                )
                for chunk in generator:
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                logger.error(f"[AI] - Process Alternatives Stream Error: {e}")
                yield f"data: {json.dumps({'error': 'Failed streaming process alternatives'})}\n\n"
            yield "data: [DONE]\n\n"

        return event_stream

    return gemma.generate_process_alternatives(
        engine_id=cleaned_data.get("engine_id"),
        active_archetype_id=cleaned_data.get("active_archetype_id"),
        recipe_slug=cleaned_data.get("recipe_slug"),
        recipe_name=cleaned_data.get("recipe_name"),
        target_category=cleaned_data.get("target_category"),
        original_recommendation=cleaned_data.get("original_recommendation"),
        exclude_names=cleaned_data.get("exclude_names"),
    )


def process_details(cleaned_data, request):
    state = get_calculator_state(request)
    flavor_inclusions = state.get("flavor_inclusions", [])
    additives = state.get("secondary_ingredients", {}).get("additives", [])
    combined_inclusions = list(flavor_inclusions) + list(additives)

    is_stream = cleaned_data.get("stream", False)
    if is_stream:

        def event_stream():
            try:
                generator = gemma.stream_process_details(
                    engine_id=cleaned_data.get("engine_id"),
                    active_archetype_id=cleaned_data.get("active_archetype_id"),
                    recipe_slug=cleaned_data.get("recipe_slug"),
                    recipe_name=cleaned_data.get("recipe_name"),
                    flavor_inclusions=combined_inclusions,
                    target=cleaned_data.get("target", "all"),
                )
                for item in generator:
                    yield f"data: {json.dumps(item)}\n\n"
            except Exception as e:
                logger.error(f"[AI] - Process Details Stream Error: {e}")
                yield f"data: {json.dumps({'error': 'Failed streaming process details'})}\n\n"
            yield "data: [DONE]\n\n"

        return event_stream

    return gemma.generate_process_details(
        engine_id=cleaned_data.get("engine_id"),
        active_archetype_id=cleaned_data.get("active_archetype_id"),
        recipe_slug=cleaned_data.get("recipe_slug"),
        recipe_name=cleaned_data.get("recipe_name"),
        flavor_inclusions=combined_inclusions,
    )


def process_recipe_tweaks(cleaned_data):
    is_stream = cleaned_data.get("stream", False)
    if is_stream:
        generator = stream_recipe_tweaks(
            engine_id=cleaned_data.get("engine_id"),
            active_archetype_id=cleaned_data.get("active_archetype_id"),
            recipe_name=cleaned_data.get("recipe_name"),
            current_ingredients=cleaned_data.get("current_ingredients"),
            applied_tweaks_history=cleaned_data.get("applied_tweaks_history"),
        )

        def event_stream():
            if generator:
                for chunk in generator:
                    if chunk:
                        yield f"data: {json.dumps({'text': chunk})}\n\n"
            yield "data: [DONE]\n\n"

        return event_stream

    return generate_recipe_tweaks(
        engine_id=cleaned_data.get("engine_id"),
        active_archetype_id=cleaned_data.get("active_archetype_id"),
        recipe_name=cleaned_data.get("recipe_name"),
        current_ingredients=cleaned_data.get("current_ingredients"),
        applied_tweaks_history=cleaned_data.get("applied_tweaks_history"),
    )


def apply_tweak(cleaned_data, request):
    state = get_calculator_state(request)
    tweak_title = cleaned_data.get("tweak_title", "")

    result = generate_tweak_application_state(
        engine_id=cleaned_data.get("engine_id"),
        active_archetype_id=cleaned_data.get("active_archetype_id"),
        recipe_slug=cleaned_data.get("recipe_slug"),
        recipe_name=cleaned_data.get("recipe_name"),
        proposed_modifications=cleaned_data.get("proposed_modifications"),
        current_state=state,
    )

    if not result:
        return None

    existing_sec = state.get("secondary_ingredients", {})
    new_sec = result.get("secondary_ingredients", {})

    for cat_key, items in new_sec.items():
        if cat_key not in existing_sec:
            existing_sec[cat_key] = []
        existing_names = {item.get("name", "") for item in existing_sec[cat_key]}
        for item in items:
            if item.get("name", "") not in existing_names:
                existing_sec[cat_key].append(item)

    state["secondary_ingredients"] = existing_sec

    existing_pct = state.get("applied_tweak_percentages", {})
    new_pct = result.get("percentages", {})
    existing_pct.update(new_pct)
    state["applied_tweak_percentages"] = existing_pct

    percentages_map = state["applied_tweak_percentages"]
    for cat_key, items in state["secondary_ingredients"].items():
        for item in items:
            name = item.get("name", "")
            if name in percentages_map:
                item["bakers_percentage"] = percentages_map[name]

    additives = state["secondary_ingredients"].get("additives", [])
    existing_flavor = state.get("flavor_inclusions", [])
    existing_flavor_names = {item.get("name", "") for item in existing_flavor}
    for additive in additives:
        if additive.get("name", "") not in existing_flavor_names:
            existing_flavor.append(additive)
    state["flavor_inclusions"] = existing_flavor

    if "target_fat_pct" in result:
        state["fat_pct"] = result["target_fat_pct"]
    if "target_sugar_pct" in result:
        state["sugar_pct"] = result["target_sugar_pct"]
    if "target_hydration_pct" in result:
        state["hydration_pct"] = result["target_hydration_pct"]
    if "target_leaven_pct" in result:
        state["leaven_pct"] = result["target_leaven_pct"]
    if "target_salt_pct" in result:
        state["salt_pct"] = result["target_salt_pct"]
    if "target_binder_pct" in result:
        state["binder_pct"] = result["target_binder_pct"]
    if "target_mixing_method" in result:
        state["mixing_method"] = result["target_mixing_method"]
    if "target_flour_blend" in result and isinstance(result["target_flour_blend"], dict):
        state["flour_blend"] = result["target_flour_blend"]

    if tweak_title:
        history = state.get("applied_tweaks_history", [])
        applied_title = f"Applied: {tweak_title}"
        if applied_title not in history:
            history.append(applied_title)
        state["applied_tweaks_history"] = history

    update_calculator_state(request, state)
    return True
