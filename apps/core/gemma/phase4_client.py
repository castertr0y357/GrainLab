import json
import logging
from apps.core.gemma.core_client import call_gemma_api, _is_ai_enabled, _get_val
from apps.core.gemma.core_client import CATEGORY_TO_ENGINE


logger = logging.getLogger("grainlab.gemma")


def get_substitution_offset(original_ing: str, substitute_ing: str, current_recipe: dict) -> dict:
    """
    Retrieves mathematical hydration/fat offsets from Gemma, falling back to local logic.
    """
    if _is_ai_enabled():
        system_prompt = (
            "Analyze an ingredient swap (substitution) in baking. You must determine the exact composition of the SUBSTITUTE ingredient. "
            "Return a JSON object with: "
            "'substitute_water_pct' (float, between 0.0 and 1.0, e.g., 0.87 for milk), "
            "'substitute_fat_pct' (float, between 0.0 and 1.0, e.g., 0.04 for milk), "
            "'substitute_sugar_pct' (float, between 0.0 and 1.0, e.g., 0.05 for milk), "
            "and 'explanation' (string detailing the chemical makeup)."
        )
        user_prompt = json.dumps({
            "original": original_ing,
            "substitute": substitute_ing,
        })
        
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["substitute_water_pct", "substitute_fat_pct"])
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
                        "explanation": explanation
                    }
                elif original_ing == "fat" and fat_pct > 0:
                    multiplier = 1.0 / fat_pct
                    return {
                        "water_offset_pct": -round(multiplier * water_pct, 3),
                        "fat_offset_pct": round(multiplier - 1.0, 3),
                        "sugar_offset_pct": -round(multiplier * sugar_pct, 3),
                        "explanation": explanation
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
            "explanation": "Whole Milk is 87% water, 4% fat, and 5% sugar. Hydration increased to compensate for milk solids, and fat/sugar weights reduced."
        }
    elif original_ing == "water" and substitute_ing == "almond_milk":
        return {
            "water_offset_pct": 0.03,
            "fat_offset_pct": -0.01,
            "sugar_offset_pct": 0.0,
            "explanation": "Almond Milk is 97% water, 1% fat. Liquid volume increased by 3% to compensate for solids."
        }
    elif original_ing == "fat" and substitute_ing == "butter":
        return {
            "water_offset_pct": -0.225, # Subtract water content
            "fat_offset_pct": 0.25,     # Requires 25% more butter weight
            "sugar_offset_pct": 0.0,
            "explanation": "Butter contains 80% fat and 18% water. Butter weight scaled up by 25% and formula hydration decreased to balance water input."
        }
        
    return {
        "water_offset_pct": 0.0,
        "fat_offset_pct": 0.0,
        "sugar_offset_pct": 0.0,
        "explanation": "No adjustments required."
    }

def calibrate_fermentation(starter_feed_hours: str, rise_speed: str, mill_type: str, is_sifted: bool) -> dict:
    """
    Computes diagnostic parameters based on sourdough activity and sifting factors.
    """
    if _is_ai_enabled():
        system_prompt = (
            "Calibrate bulk fermentation countdown targets and ash estimate based on "
            "starter feeding schedule and milling profile. Return a JSON object with: "
            "'ash_content_estimate' (float), 'estimated_bulk_fermentation_hours' (float), "
            "and 'notes' (string)."
        )
        user_prompt = json.dumps({
            "starter_feed_hours": starter_feed_hours,
            "rise_speed": rise_speed,
            "mill_type": mill_type,
            "is_sifted": is_sifted,
        })
        
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["estimated_bulk_fermentation_hours", "ash_content_estimate"])
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
        "profile_adjustments": {
            "oven_temp_offset_f": 0,
            "bake_time_offset_m": 0,
            "steam_override": "no-change"
        }
    }
    
    if not _is_ai_enabled():
        return {
            "geometry_evaluation": fallback_data
        }

    system_prompt = (
        "You are an expert baking science assistant. Evaluate the suitability of the selected baking geometry (equipment form factor) "
        "for the active recipe type and return a structured JSON response. Consider thermal mass, heat conduction, expansion, and steam dynamics.\n"
        "Your response MUST be pure JSON matching this schema exactly:\n"
        "{\n"
        "  \"geometry_evaluation\": {\n"
        "    \"status\": \"recommended\" or \"sub-optimal\",\n"
        "    \"advisory_label\": \"A clear 1-2 sentence structural justification explaining heat penetration, expansion, or steam mechanics.\",\n"
        "    \"profile_adjustments\": {\n"
        "      \"oven_temp_offset_f\": integer offset,\n"
        "      \"bake_time_offset_m\": integer offset,\n"
        "      \"steam_override\": \"no-change\" or \"force-on\" or \"force-off\"\n"
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
                        "steam_override": steam_override
                    }
                }
            }
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling geometry advisory API: {str(e)}")
        
    return {
        "geometry_evaluation": fallback_data
    }

def generate_process_details(engine_id: str, active_archetype_id: str, recipe_slug: str, recipe_name: str, flavor_inclusions: list = None) -> dict | None:
    logger.info(f"[Gemma Client] - Info - Calling generate_process_details for: {recipe_slug}")
    
    try:
        if not _is_ai_enabled():
            import time
            time.sleep(1)
            return {
                "process_recommendations": {
                    "mixing_method": {"name": "Hand Knead", "explanation": "Gentle hand mixing preserves delicate gluten networks."},
                    "dough_handling": {"name": "Stretch and Fold", "explanation": "Builds structure slowly without oxidizing the dough."},
                    "proofing_environment": {"name": "Cold Retard (38°F)", "explanation": "Slows yeast activity to develop complex organic acids and flavor."},
                    "baking_vessel": {"name": "Dutch Oven", "explanation": "Traps steam to maximize oven spring and crust gelatinization."},
                    "shaping_style": {"name": "Boule", "explanation": "Classic round shape promotes even baking and crumb openness."}
                }
            }
            
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
            "  \"process_recommendations\": {\n"
            "    \"mixing_method\": { \"name\": \"string\", \"explanation\": \"string\" },\n"
            "    \"dough_handling\": { \"name\": \"string\", \"explanation\": \"string\" },\n"
            "    \"proofing_environment\": { \"name\": \"string\", \"explanation\": \"string\" },\n"
            "    \"baking_vessel\": { \"name\": \"string\", \"explanation\": \"string\" },\n"
            "    \"shaping_style\": { \"name\": \"string\", \"explanation\": \"string\" }\n"
            "  },\n"
            "  \"slider_recommendations\": {\n"
            "    \"tweak_id\": { \"explanation\": \"string (HTML formatted)\", \"recommended_value\": 0 }\n"
            "  }\n"
            "}\n"
            "Do not include markdown blocks, just raw JSON."
        )

        from grainlab.engines.router import ENGINES
        engine = ENGINES.get(engine_id)
        supported_tweaks = getattr(engine, "supported_tweaks", []) if engine else []
        tweak_labels = getattr(engine, "tweak_labels", {}) if engine else {}

        user_prompt = json.dumps({
            "engine_id": engine_id,
            "active_archetype_id": active_archetype_id,
            "recipe_slug": recipe_slug,
            "recipe_name": recipe_name,
            "supported_tweaks": supported_tweaks,
            "tweak_labels": tweak_labels,
            "flavor_inclusions": flavor_inclusions or []
        })

        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["process_recommendations"])
        if result and isinstance(result, dict) and "process_recommendations" in result:
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_process_details: {str(e)}")

    return None

def stream_process_details(engine_id: str, active_archetype_id: str, recipe_slug: str, recipe_name: str, flavor_inclusions: list = None):
    """
    Streaming version of generate_process_details.
    Yields JSON string chunks as Server-Sent Events from the LLM.
    """
    logger.info(f"[Gemma Client] - Info - Calling stream_process_details for: {recipe_slug}")
    from apps.core.gemma.core_client import SystemSetting
    
    ai_thinking_enabled = SystemSetting.get_val("ai_thinking_enabled", "True") == "True"
    ai_thinking_effort = SystemSetting.get_val("ai_thinking_effort", "medium")

    system_prompt = (
        "You are an expert baking science assistant. Your task is to recommend optimal process parameters "
        "for a specific bread or pastry recipe based on its characteristics.\n"
        "Provide the top recommended option for the relevant categories among: mixing_method, dough_handling, proofing_environment, baking_vessel, and shaping_style.\n"
        "CRITICAL: You MUST omit any category that is completely irrelevant or contradictory for the specific recipe type. For example, cookies generally do not need a 'proofing_environment' or 'baking_vessel'. If a category is unnecessary, simply do not include it in the JSON.\n"
        "For the 'mixing_method' category, you MUST explicitly specify if it should be done by hand or with a stand mixer. If using a mixer, explicitly state the attachment (e.g., standard paddle, dough hook, whisk).\n"
        "For each recommendation, provide a brief (1-2 sentence) explanation of WHY it is optimal for this recipe.\n"
        "Also, if `supported_tweaks` is provided in the prompt, you MUST provide `slider_recommendations` for each tweak. For each tweak, provide a `recommended_value` (integer between 0 and 100, where 0 represents the extreme left pole and 100 represents the extreme right pole), and a detailed `explanation` formatted as HTML. The HTML explanation MUST contain three paragraphs: the first explaining what the left pole (0) achieves, the second explaining what the right pole (100) achieves, and the third explaining the reasoning for your specific recommended value.\n"
        "Your response MUST be a pure JSON array matching this schema exactly:\n"
        "[\n"
        "  { \"type\": \"process\", \"category\": \"mixing_method\", \"name\": \"string\", \"explanation\": \"string\" },\n"
        "  { \"type\": \"process\", \"category\": \"dough_handling\", \"name\": \"string\", \"explanation\": \"string\" },\n"
        "  { \"type\": \"process\", \"category\": \"proofing_environment\", \"name\": \"string\", \"explanation\": \"string\" },\n"
        "  { \"type\": \"process\", \"category\": \"baking_vessel\", \"name\": \"string\", \"explanation\": \"string\" },\n"
        "  { \"type\": \"process\", \"category\": \"shaping_style\", \"name\": \"string\", \"explanation\": \"string\" },\n"
        "  { \"type\": \"slider\", \"tweak_id\": \"string\", \"explanation\": \"string (HTML formatted)\", \"recommended_value\": 0 }\n"
        "]\n"
        "Do not include markdown blocks, just the raw JSON array."
    )

    if ai_thinking_enabled:
        system_prompt += f"\n[CRITICAL] Use thorough reasoning and step-by-step thinking (thinking effort: {ai_thinking_effort}) before responding."
    else:
        system_prompt += "\n[CRITICAL] Do NOT use thinking/reasoning steps. Respond immediately with the direct answer."

    from grainlab.engines.router import ENGINES
    engine = ENGINES.get(engine_id)
    supported_tweaks = getattr(engine, "supported_tweaks", []) if engine else []
    tweak_labels = getattr(engine, "tweak_labels", {}) if engine else {}

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "recipe_slug": recipe_slug,
        "recipe_name": recipe_name,
        "supported_tweaks": supported_tweaks,
        "tweak_labels": tweak_labels,
        "flavor_inclusions": flavor_inclusions or []
    })
    
    logger.info(f"[Gemma Client] - Phase 4 AI PROMPT FED TO STREAM_PROCESS_DETAILS: {user_prompt}")

    if not _is_ai_enabled():
        import time
        time.sleep(1)
        mock_data = [
            { "type": "process", "category": "mixing_method", "name": "Hand Knead", "explanation": "Gentle hand mixing preserves delicate gluten networks." },
            { "type": "process", "category": "dough_handling", "name": "Stretch and Fold", "explanation": "Builds structure slowly without oxidizing the dough." },
            { "type": "process", "category": "proofing_environment", "name": "Cold Retard (38°F)", "explanation": "Slows yeast activity to develop complex organic acids and flavor." },
            { "type": "process", "category": "baking_vessel", "name": "Dutch Oven", "explanation": "Traps steam to maximize oven spring and crust gelatinization." },
            { "type": "process", "category": "shaping_style", "name": "Boule", "explanation": "Classic round shape promotes even baking and crumb openness." }
        ]
        for m in mock_data:
            yield json.dumps(m)
        return

    from apps.core.gemma.core_client import stream_gemma_api
    for chunk in stream_gemma_api(system_prompt, user_prompt, yield_raw=True):
        yield chunk

def stream_process_alternatives(engine_id: str, active_archetype_id: str, recipe_slug: str, recipe_name: str, target_category: str, original_recommendation: dict, exclude_names: list = None):
    """
    Streaming version of generate_process_alternatives.
    """
    logger.info(f"[Gemma Client] - Info - Calling stream_process_alternatives for: {recipe_slug}, category: {target_category}")
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
        "  { \"type\": \"alternative\", \"name\": \"string\", \"difference_explanation\": \"string\" }\n"
        "]\n"
        "Do not include markdown blocks, just the raw JSON array."
    )

    if ai_thinking_enabled:
        system_prompt += f"\n[CRITICAL] Use thorough reasoning and step-by-step thinking (thinking effort: {ai_thinking_effort}) before responding."
    else:
        system_prompt += "\n[CRITICAL] Do NOT use thinking/reasoning steps. Respond immediately with the direct answer."

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "recipe_slug": recipe_slug,
        "recipe_name": recipe_name,
        "target_category": target_category,
        "original_recommendation": original_recommendation,
        "excluded_names": exclude_names
    })

    if not _is_ai_enabled():
        import time
        time.sleep(1)
        mock_data = [
            { "type": "alternative", "name": "Mix by Hand", "difference_explanation": "A gentle approach that connects you with the dough and prevents over-oxidation." },
            { "type": "alternative", "name": "Food Processor", "difference_explanation": "Incredibly fast gluten development, but requires ice water to prevent overheating." },
            { "type": "alternative", "name": "No-Knead Method", "difference_explanation": "Relies entirely on time and enzymatic action to develop gluten naturally." }
        ]
        for m in mock_data:
            yield json.dumps(m)
        return

    from apps.core.gemma.core_client import stream_gemma_api
    for chunk in stream_gemma_api(system_prompt, user_prompt, yield_raw=True):
        yield chunk

def generate_process_alternatives(engine_id: str, active_archetype_id: str, recipe_slug: str, recipe_name: str, target_category: str, original_recommendation: dict, exclude_names: list = None) -> dict | None:
    logger.info(f"[Gemma Client] - Info - Calling generate_process_alternatives for: {recipe_slug}, category: {target_category}")
    
    try:
        if not _is_ai_enabled():
            import time
            time.sleep(1)
            return {
                "alternatives": [
                    {
                        "name": "Alternative 1",
                        "difference_explanation": "This option produces a tighter crumb structure but is much easier to execute."
                    },
                    {
                        "name": "Alternative 2",
                        "difference_explanation": "This results in better volume but requires careful temperature control."
                    }
                ]
            }
            
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
            f"  \"alternatives\": [\n"
            f"    {{\n"
            f"      \"name\": \"string\",\n"
            f"      \"difference_explanation\": \"string\"\n"
            f"    }}\n"
            f"  ]\n"
            f"}}\n\n"
            f"Do not include markdown blocks, just raw JSON."
        )

        user_prompt = json.dumps({
            "engine_id": engine_id,
            "active_archetype_id": active_archetype_id,
            "recipe_slug": recipe_slug,
            "recipe_name": recipe_name,
            "target_category": target_category,
            "original_recommendation": original_recommendation
        })

        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["alternatives"])
        if result and isinstance(result, dict) and "alternatives" in result:
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_process_alternatives: {str(e)}")

    return None
