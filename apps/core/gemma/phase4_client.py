import json
import logging

from apps.core.gemma.core_client import CATEGORY_TO_ENGINE, call_gemma_api

logger = logging.getLogger("grainlab.gemma")


def get_substitution_offset(original_ing: str, substitute_ing: str, current_recipe: dict) -> dict:
    """
    Retrieves mathematical hydration/fat offsets from Gemma, falling back to local logic.
    """
    if True:
        system_prompt = (
            "Analyze an ingredient swap (substitution) in baking. You must determine the exact composition of the SUBSTITUTE ingredient. "
            "Return a JSON object with: "
            "'substitute_water_pct' (float, between 0.0 and 1.0, e.g., 0.87 for milk), "
            "'substitute_fat_pct' (float, between 0.0 and 1.0, e.g., 0.04 for milk), "
            "'substitute_sugar_pct' (float, between 0.0 and 1.0, e.g., 0.05 for milk), "
            "and 'explanation' (string detailing the chemical makeup)."
        )
        user_prompt = json.dumps(
            {
                "original": original_ing,
                "substitute": substitute_ing,
            }
        )

        result = call_gemma_api(
            system_prompt, user_prompt, expected_keys=["substitute_water_pct", "substitute_fat_pct"]
        )
        if result:
            try:
                water_pct = float(result.get("substitute_water_pct", 1.0))
                fat_pct = float(result.get("substitute_fat_pct", 0.0))
                sugar_pct = float(result.get("substitute_sugar_pct", 0.0))
                explanation = result.get("explanation", "Calculated mathematically based on AI ingredient composition.")

                # Math logic for perfect dough hydration balance:
                if original_ing == "water" and water_pct > 0:
                    multiplier = 1.0 / water_pct
                    return {
                        "water_offset_pct": round(multiplier - 1.0, 3),
                        "fat_offset_pct": -round(multiplier * fat_pct, 3),
                        "sugar_offset_pct": -round(multiplier * sugar_pct, 3),
                        "explanation": explanation,
                    }
                elif original_ing == "fat" and fat_pct > 0:
                    multiplier = 1.0 / fat_pct
                    return {
                        "water_offset_pct": -round(multiplier * water_pct, 3),
                        "fat_offset_pct": round(multiplier - 1.0, 3),
                        "sugar_offset_pct": -round(multiplier * sugar_pct, 3),
                        "explanation": explanation,
                    }
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.warning(f"[Gemma Client] - Warning - AI returned malformed composition numbers: {e}")

    # Fallback default math-based offset objects matching our local engine
    # In view layer, we process substitutions natively; gemma client returns standard defaults matching bakers_math
    if original_ing == "water" and substitute_ing == "whole_milk":
        return {
            "water_offset_pct": 0.15,  # Needs 15% more volume to reach same water level
            "fat_offset_pct": -0.046,  # Reduces fat by 4.6% of flour weight
            "sugar_offset_pct": -0.057,
            "explanation": "Whole Milk is 87% water, 4% fat, and 5% sugar. Hydration increased to compensate for milk solids, and fat/sugar weights reduced.",
        }
    elif original_ing == "water" and substitute_ing == "almond_milk":
        return {
            "water_offset_pct": 0.03,
            "fat_offset_pct": -0.01,
            "sugar_offset_pct": 0.0,
            "explanation": "Almond Milk is 97% water, 1% fat. Liquid volume increased by 3% to compensate for solids.",
        }
    elif original_ing == "fat" and substitute_ing == "butter":
        return {
            "water_offset_pct": -0.225,  # Subtract water content
            "fat_offset_pct": 0.25,  # Requires 25% more butter weight
            "sugar_offset_pct": 0.0,
            "explanation": "Butter contains 80% fat and 18% water. Butter weight scaled up by 25% and formula hydration decreased to balance water input.",
        }

    return {
        "water_offset_pct": 0.0,
        "fat_offset_pct": 0.0,
        "sugar_offset_pct": 0.0,
        "explanation": "No adjustments required.",
    }


def calibrate_fermentation(starter_feed_hours: str, rise_speed: str, mill_type: str, is_sifted: bool) -> dict:
    """
    Computes diagnostic parameters based on sourdough activity and sifting factors.
    """
    if True:
        system_prompt = (
            "Calibrate bulk fermentation countdown targets and ash estimate based on "
            "starter feeding schedule and milling profile. Return a JSON object with: "
            "'ash_content_estimate' (float), 'estimated_bulk_fermentation_hours' (float), "
            "and 'notes' (string)."
        )
        user_prompt = json.dumps(
            {
                "starter_feed_hours": starter_feed_hours,
                "rise_speed": rise_speed,
                "mill_type": mill_type,
                "is_sifted": is_sifted,
            }
        )

        result = call_gemma_api(
            system_prompt, user_prompt, expected_keys=["estimated_bulk_fermentation_hours", "ash_content_estimate"]
        )
        if result:
            return result

    # Fallback calculations based on bread-science equations
    # Ash estimate: stoneground = 1.5%, steel roller = 0.5%. Sifting reduces ash by 0.3%.
    ash = 1.5 if mill_type == "stoneground" else 0.5
    if is_sifted:
        ash = max(0.4, ash - 0.3)

    # Fermentation target: active feed (4-8 hours) = 4 hours bulk, slow feed (12+ hours) = 7 hours bulk
    hours = 4.0
    if starter_feed_hours == "12_18":
        hours = 6.0
    elif starter_feed_hours == "18_plus":
        hours = 8.0

    if rise_speed == "slow":
        hours += 1.5
    elif rise_speed == "fast":
        hours = max(3.0, hours - 1.0)

    notes = (
        f"Milling profile: {mill_type} (sifted={is_sifted}). Estimated ash content of {ash}%. "
        f"Starter fed {starter_feed_hours.replace('_', '-')} hours ago shows {rise_speed} activity. "
        f"Target bulk fermentation set to {hours} hours."
    )

    return {
        "ash_content_estimate": ash,
        "estimated_bulk_fermentation_hours": hours,
        "notes": notes,
    }


def get_geometry_advisory(preset_slug: str, preset_name: str, category_slug: str, form_factor_slug: str) -> dict:
    """
    Evaluates form factor suitability for the given recipe preset and category using Gemma.
    """
    engine_slug = CATEGORY_TO_ENGINE.get(category_slug, "base")

    fallback_data = {
        "status": "recommended",
        "advisory_label": f"Standard baking geometry for {preset_name or category_slug}.",
        "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "no-change"},
    }

    system_prompt = (
        "You are an expert baking science assistant. Evaluate the suitability of the selected baking geometry (equipment form factor) "
        "for the active recipe type and return a structured JSON response. Consider thermal mass, heat conduction, expansion, and steam dynamics.\n"
        "Your response MUST be pure JSON matching this schema exactly:\n"
        "{\n"
        '  "geometry_evaluation": {\n'
        '    "status": "recommended" or "sub-optimal",\n'
        '    "advisory_label": "A clear 1-2 sentence structural justification explaining heat penetration, expansion, or steam mechanics.",\n'
        '    "profile_adjustments": {\n'
        '      "oven_temp_offset_f": integer offset,\n'
        '      "bake_time_offset_m": integer offset,\n'
        '      "steam_override": "no-change" or "force-on" or "force-off"\n'
        "    }\n"
        "  }\n"
        "}"
    )

    user_prompt = (
        f"Active Recipe Preset: {preset_name or preset_slug or 'Custom'}\n"
        f"Active Recipe Category: {category_slug} (Sub-Engine: {engine_slug})\n"
        f"Selected Form Factor (Geometry): {form_factor_slug}\n"
        f"Generate the suitability status, a scientific advisory label, and the recommended oven temperature offset (°F), "
        f"bake time offset (minutes), and steam override choice. Do not rely on any preset baselines; calculate the ideal offsets directly. "
        f"Output ONLY valid JSON."
    )

    try:
        response = call_gemma_api(system_prompt, user_prompt, expected_keys=["geometry_evaluation"])
        if response and "geometry_evaluation" in response:
            ge = response["geometry_evaluation"]
            status = ge.get("status", fallback_data["status"])
            if status not in ["recommended", "sub-optimal"]:
                status = fallback_data["status"]

            advisory_label = ge.get("advisory_label", fallback_data["advisory_label"])

            adjustments = ge.get("profile_adjustments", {})
            oven_temp_offset = int(adjustments.get("oven_temp_offset_f", 0))
            bake_time_offset = int(adjustments.get("bake_time_offset_m", 0))
            steam_override = adjustments.get("steam_override", "no-change")
            if steam_override not in ["no-change", "force-on", "force-off"]:
                steam_override = "no-change"

            return {
                "geometry_evaluation": {
                    "status": status,
                    "advisory_label": advisory_label,
                    "profile_adjustments": {
                        "oven_temp_offset_f": oven_temp_offset,
                        "bake_time_offset_m": bake_time_offset,
                        "steam_override": steam_override,
                    },
                }
            }
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling geometry advisory API: {str(e)}")

    return {"geometry_evaluation": fallback_data}


def generate_process_details(
    engine_id: str, active_archetype_id: str, recipe_slug: str, recipe_name: str, flavor_inclusions: list = None
) -> dict | None:
    logger.info(f"[Gemma Client] - Info - Calling generate_process_details for: {recipe_slug}")

    try:
        system_prompt = (
            "You are an expert baking science assistant. Your task is to recommend optimal process parameters "
            "for a specific bread or pastry recipe based on its characteristics.\n"
            "Provide the top recommended option for the relevant categories among: mixing_method, dough_handling, proofing_environment, baking_vessel, and shaping_style.\n"
            "CRITICAL: You MUST omit any category that is completely irrelevant or contradictory for the specific recipe type. For example, cookies generally do not need a 'proofing_environment' or 'baking_vessel'. If a category is unnecessary, simply do not include it in the JSON.\n"
            "For the 'mixing_method' category, you MUST explicitly specify if it should be done by hand or with a stand mixer. If using a mixer, explicitly state the attachment (e.g., standard paddle, dough hook, whisk).\n"
            "For each recommendation, provide a brief (1-2 sentence) explanation of WHY it is optimal for this recipe.\n"
            "Also, if `supported_tweaks` is provided in the prompt, you MUST provide `slider_recommendations` for each tweak. For each tweak, provide a `recommended_value` (integer between 0 and 100, where 0 represents the extreme left pole and 100 represents the extreme right pole), and a detailed `explanation` formatted as HTML. The HTML explanation MUST contain three paragraphs: the first explaining what the left pole (0) achieves, the second explaining what the right pole (100) achieves, and the third explaining the reasoning for your specific recommended value.\n"
            "Your response MUST be pure JSON matching this schema exactly (omitting irrelevant keys in process_recommendations):\n"
            "{\n"
            '  "process_recommendations": {\n'
            '    "mixing_method": { "name": "string", "explanation": "string" },\n'
            '    "dough_handling": { "name": "string", "explanation": "string" },\n'
            '    "proofing_environment": { "name": "string", "explanation": "string" },\n'
            '    "baking_vessel": { "name": "string", "explanation": "string" },\n'
            '    "shaping_style": { "name": "string", "explanation": "string" }\n'
            "  },\n"
            '  "slider_recommendations": {\n'
            '    "tweak_id": { "explanation": "string (HTML formatted)", "recommended_value": 0 }\n'
            "  }\n"
            "}\n"
            "Do not include markdown blocks, just raw JSON."
        )

        from apps.core.engines.router import ENGINES

        engine = ENGINES.get(engine_id)
        supported_tweaks = getattr(engine, "supported_tweaks", []) if engine else []
        tweak_labels = getattr(engine, "tweak_labels", {}) if engine else {}

        user_prompt = json.dumps(
            {
                "engine_id": engine_id,
                "active_archetype_id": active_archetype_id,
                "recipe_slug": recipe_slug,
                "recipe_name": recipe_name,
                "supported_tweaks": supported_tweaks,
                "tweak_labels": tweak_labels,
                "flavor_inclusions": flavor_inclusions or [],
            }
        )

        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["process_recommendations"])
        if result and isinstance(result, dict) and "process_recommendations" in result:
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_process_details: {str(e)}")

    return None


def stream_process_details(
    engine_id: str,
    active_archetype_id: str,
    recipe_slug: str,
    recipe_name: str,
    flavor_inclusions: list = None,
    target: str = "all",
):
    """
    Streaming version of generate_process_details.
    Yields JSON string chunks as Server-Sent Events from the LLM.
    """
    import logging

    logger = logging.getLogger("grainlab.gemma")
    logger.info(f"[Gemma Client] - Info - Calling stream_process_details for: {recipe_slug}")
    import json

    from apps.core.gemma.core_client import SystemSetting

    ai_thinking_enabled = SystemSetting.get_val("ai_thinking_enabled", "True") == "True"
    ai_thinking_effort = SystemSetting.get_val("ai_thinking_effort", "medium")

    system_prompt = (
        "You are an expert baking science assistant. Your task is to recommend optimal process parameters "
        "for a specific bread or pastry recipe based on its characteristics.\n"
    )

    if target == "processes":
        system_prompt += (
            "Provide the top recommended option for all 5 categories: mixing_method, dough_handling, proofing_environment, baking_vessel, and shaping_style.\n"
            "Adapt the interpretation of each category to the specific recipe type. For example, for cookies or quick breads, 'proofing_environment' might refer to resting or chilling the dough, 'baking_vessel' refers to the baking sheet or pan, and 'shaping_style' refers to scooping, rolling, or depositing.\n"
            "For the 'mixing_method' category, you MUST explicitly specify if it should be done by hand or with a stand mixer. If using a mixer, explicitly state the attachment (e.g., standard paddle, dough hook, whisk).\n"
            "For each recommendation, provide a brief (1-2 sentence) explanation of WHY it is optimal for this recipe.\n"
            "Your response MUST be a pure JSON array matching this schema exactly:\n"
            "[\n"
            '  { "type": "process", "category": "mixing_method", "name": "string", "explanation": "string" },\n'
            '  { "type": "process", "category": "dough_handling", "name": "string", "explanation": "string" },\n'
            '  { "type": "process", "category": "proofing_environment", "name": "string", "explanation": "string" },\n'
            '  { "type": "process", "category": "baking_vessel", "name": "string", "explanation": "string" },\n'
            '  { "type": "process", "category": "shaping_style", "name": "string", "explanation": "string" }\n'
            "]\n"
            "Do not include markdown blocks, just the raw JSON array."
        )
    elif target == "tweaks":
        system_prompt += (
            "If `supported_tweaks` is provided in the prompt, you MUST provide `slider_recommendations` for each tweak. For each tweak, provide a `recommended_value` (integer between 0 and 100, where 0 represents the extreme left pole and 100 represents the extreme right pole), and a detailed `explanation` formatted as HTML. The HTML explanation MUST contain three paragraphs: the first explaining what the left pole (0) achieves, the second explaining what the right pole (100) achieves, and the third explaining the reasoning for your specific recommended value.\n"
            "Your response MUST be a pure JSON array matching this schema exactly:\n"
            "[\n"
            '  { "type": "slider", "tweak_id": "string", "explanation": "string (HTML formatted)", "recommended_value": 0 }\n'
            "]\n"
            "Do not include markdown blocks, just the raw JSON array."
        )
    else:
        raise ValueError(f"Invalid target '{target}'. Must be 'processes' or 'tweaks'.")

    if ai_thinking_enabled:
        system_prompt += f"\n[CRITICAL] Use thorough reasoning and step-by-step thinking (thinking effort: {ai_thinking_effort}) before responding."
    else:
        system_prompt += "\n[CRITICAL] Do NOT use thinking/reasoning steps. Respond immediately with the direct answer."

    # Look up preset to find relevant tweaks
    from apps.core.models import BreadPreset

    preset = BreadPreset.objects.filter(slug=recipe_slug).first()
    supported_tweaks = []
    if preset:
        for tweak in preset.supported_tweaks.all():
            supported_tweaks.append(
                {
                    "id": tweak.id,
                    "name": tweak.name,
                    "description": tweak.description,
                    "left_pole": tweak.left_pole_description,
                    "right_pole": tweak.right_pole_description,
                }
            )

    user_prompt_data = {
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "recipe_slug": recipe_slug,
        "recipe_name": recipe_name,
        "flavor_inclusions": flavor_inclusions,
        "supported_tweaks": supported_tweaks,
    }
    user_prompt = json.dumps(user_prompt_data)

    logger.info(f"[Gemma Client] - Phase 4 AI PROMPT FED TO STREAM_PROCESS_DETAILS (target={target}): {user_prompt}")

    from apps.core.gemma.core_client import stream_gemma_api

    for chunk in stream_gemma_api(system_prompt, user_prompt, yield_raw=True):
        yield chunk


def stream_process_alternatives(
    engine_id: str,
    active_archetype_id: str,
    recipe_slug: str,
    recipe_name: str,
    target_category: str,
    original_recommendation: dict,
    exclude_names: list = None,
):
    """
    Streaming version of generate_process_alternatives.
    """
    logger.info(
        f"[Gemma Client] - Info - Calling stream_process_alternatives for: {recipe_slug}, category: {target_category}"
    )
    from apps.core.gemma.core_client import SystemSetting

    ai_thinking_enabled = SystemSetting.get_val("ai_thinking_enabled", "True") == "True"
    ai_thinking_effort = SystemSetting.get_val("ai_thinking_effort", "medium")

    system_prompt = (
        "You are an expert baking science assistant. Your task is to provide alternative recommendations "
        "for a specific process parameter category.\n"
        "Provide exactly 3 alternative options for the specified category that are distinct from the original recommendation.\n"
        "For each alternative, explain its unique impact on the final product.\n"
        "Your response MUST be a pure JSON array matching this schema exactly:\n"
        "[\n"
        '  { "type": "alternative", "name": "string", "difference_explanation": "string" }\n'
        "]\n"
        "Do not include markdown blocks, just the raw JSON array."
    )

    if ai_thinking_enabled:
        system_prompt += f"\n[CRITICAL] Use thorough reasoning and step-by-step thinking (thinking effort: {ai_thinking_effort}) before responding."
    else:
        system_prompt += "\n[CRITICAL] Do NOT use thinking/reasoning steps. Respond immediately with the direct answer."

    user_prompt = json.dumps(
        {
            "engine_id": engine_id,
            "active_archetype_id": active_archetype_id,
            "recipe_slug": recipe_slug,
            "recipe_name": recipe_name,
            "target_category": target_category,
            "original_recommendation": original_recommendation,
            "excluded_names": exclude_names,
        }
    )

    from apps.core.gemma.core_client import stream_gemma_api

    for chunk in stream_gemma_api(system_prompt, user_prompt, yield_raw=True):
        yield chunk


def generate_process_alternatives(
    engine_id: str,
    active_archetype_id: str,
    recipe_slug: str,
    recipe_name: str,
    target_category: str,
    original_recommendation: dict,
    exclude_names: list = None,
) -> dict | None:
    logger.info(
        f"[Gemma Client] - Info - Calling generate_process_alternatives for: {recipe_slug}, category: {target_category}"
    )

    try:
        exclude_text = ""
        if exclude_names:
            names_str = ", ".join(exclude_names)
            exclude_text = f"\nCRITICAL: Do NOT recommend any of the following options: {names_str}. Provide entirely new alternatives."

        system_prompt = (
            f"You are a baking science expert. You are providing process alternatives for a specific category ({target_category}).\n"
            f"Given the recipe context, the target process category, and the originally recommended process, "
            f"generate 2-3 suitable alternative options.{exclude_text}\n"
            f"If the target category is 'mixing_method', you MUST explicitly specify if the alternative should be done by hand or with a stand mixer. If using a mixer, explicitly state the required attachment (e.g., standard paddle, dough hook, whisk).\n"
            f"For each option, you MUST explain the structural and flavor differences compared to the original recommendation (e.g., how it impacts crumb, crust, or schedule).\n"
            f"Each response must match this JSON schema exactly:\n"
            f"{{\n"
            f'  "alternatives": [\n'
            f"    {{\n"
            f'      "name": "string",\n'
            f'      "difference_explanation": "string"\n'
            f"    }}\n"
            f"  ]\n"
            f"}}\n\n"
            f"Do not include markdown blocks, just raw JSON."
        )

        user_prompt = json.dumps(
            {
                "engine_id": engine_id,
                "active_archetype_id": active_archetype_id,
                "recipe_slug": recipe_slug,
                "recipe_name": recipe_name,
                "target_category": target_category,
                "original_recommendation": original_recommendation,
            }
        )

        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["alternatives"])
        if result and isinstance(result, dict) and "alternatives" in result:
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_process_alternatives: {str(e)}")
    return None


def stream_recipe_tweaks(
    engine_id: str, active_archetype_id: str, recipe_name: str, current_ingredients: list, applied_tweaks_history: list
):
    system_prompt = (
        "You are an expert baking scientist. Given the current ingredient list, propose creative and unique recipe tweaks (enhancements, flavor profiles, or structural shifts). "
        "CRITICAL EXCLUSION RULE: You will be provided with an 'applied_tweaks_history' list containing tweaks that were already applied or discarded. You MUST NEVER suggest any concept, ingredient addition, or tweak that is semantically similar to any item in this history list. "
        "CRITICAL: You are generating enhancements for a recipe that CONTAINS EXACTLY the provided ingredients. Treat the provided ingredient list as absolute truth. DO NOT use phrases like 'assuming butter is used' if butter is listed. Be definitive and confident.\n"
        "If you cannot think of any new creative tweaks because the applied_tweaks_history covers everything, return a single item with tweak_title set exactly to 'Out of Options'.\n"
        "Return a pure JSON array of objects, exactly matching this schema:\n"
        "[\n"
        "  {\n"
        '    "type": "tweak",\n'
        "    \"tweak_title\": \"Name of the tweak (e.g., 'Make it Chewier', 'Add Garlic & Herb')\",\n"
        '    "reasoning": "A short 1-2 sentence explanation of why this works, referencing specific ingredients present in the base recipe.",\n'
        '    "expected_outcome": "How this affects the final product.",\n'
        '    "proposed_modifications": [\n'
        '      "Increase whole eggs slightly to bind the dough",\n'
        '      "Change mixing method to high_torque for better gluten development",\n'
        '      "Reduce fat to compensate"\n'
        "    ]\n"
        "  }\n"
        "]\n"
    )
    user_prompt = json.dumps(
        {
            "engine_id": engine_id,
            "active_archetype_id": active_archetype_id,
            "recipe_name": recipe_name,
            "current_ingredients": current_ingredients,
            "applied_tweaks_history": applied_tweaks_history,
        }
    )

    from apps.core.gemma.core_client import stream_gemma_api

    for chunk in stream_gemma_api(system_prompt, user_prompt, yield_raw=True):
        if chunk:
            yield chunk


def generate_recipe_tweaks(
    engine_id: str, active_archetype_id: str, recipe_name: str, current_ingredients: list, applied_tweaks_history: list
) -> dict:
    return None


def generate_tweak_application_state(
    engine_id, active_archetype_id, recipe_slug, recipe_name, proposed_modifications, current_state
) -> dict:
    system_prompt = (
        "You are an expert baking scientist. Categorize a list of newly applied ingredients into the correct backend categories and baker's percentages. "
        "CRITICAL: If modifying an existing base ingredient (like flour, fat, sugar, or binders/eggs), output the updated `target_xxx_pct` INSTEAD of adding it to secondary_ingredients. For example, if adjusting eggs, adjust target_binder_pct. Do not duplicate base ingredients in secondary_ingredients."
        "Return a pure JSON object matching this schema:\n"
        "{\n"
        '  "secondary_ingredients": {\n'
        '    "additives": [{"name": "Ingredient Name", "notes": "..."}],\n'
        '    "liquids": [],\n'
        '    "fats": [],\n'
        '    "sugars": [],\n'
        '    "binders": []\n'
        "  },\n"
        '  "percentages": {\n'
        '    "Ingredient Name": 5.0\n'
        "  },\n"
        '  "target_fat_pct": 15.0,\n'
        '  "target_sugar_pct": 10.0,\n'
        '  "target_hydration_pct": 75.0,\n'
        '  "target_leaven_pct": 20.0,\n'
        '  "target_salt_pct": 2.0,\n'
        '  "target_binder_pct": 35.0,\n'
        '  "target_mixing_method": "stand_mixer",\n'
        '  "target_flour_blend": {"soft_white_wheat": 75, "spelt": 20, "rye": 5}\n'
        "}\n"
        "If modifying the flour blend (rebalancing grain ratios), provide the new `target_flour_blend` mapping. Provide relative proportional weights for the blend; the backend will automatically normalize these values to 100%. "
        "If a base parameter like hydration or fat doesn't change, omit it from the root object. Omit empty categories."
    )
    user_prompt = json.dumps(
        {
            "engine_id": engine_id,
            "recipe_slug": recipe_slug,
            "proposed_modifications": proposed_modifications,
            "current_state": current_state,
        }
    )
    from apps.core.gemma.core_client import call_gemma_api

    result = call_gemma_api(system_prompt, user_prompt, expected_keys=["secondary_ingredients", "percentages"])
    if result:
        blend = result.get("target_flour_blend")
        if isinstance(blend, dict) and len(blend) > 0:
            total_weight = sum(blend.values())
            if total_weight > 0:
                normalized_blend = {k: round((v / total_weight) * 100, 1) for k, v in blend.items()}
                result["target_flour_blend"] = normalized_blend
        return result
    return {}
