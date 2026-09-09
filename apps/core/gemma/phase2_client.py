import json
import logging

from apps.core.gemma.core_client import (
    FACTUAL_DICTIONARY,
    call_gemma_api,
    get_archetype_mechanics,
    get_grain_registry_profile,
)

logger = logging.getLogger("grainlab.gemma")


def get_sidebar_insight_ai(element: str, category_slug: str, preset_slug: str) -> dict | None:
    """
    Queries Gemma to generate a custom labor ROI tag, recommendation tier, and 'Last 10%' critique/reasoning.
    """
    import json
    import re

    from apps.core.engines import router
    from apps.core.models import BreadPreset, WheatBerry

    preset = BreadPreset.objects.filter(slug=preset_slug).first()
    preset_name = (
        preset.name if preset else (preset_slug.replace("-", " ").title() if preset_slug else "Custom / Manual Blend")
    )

    # Query inactive wheat berries (not on hand) to pass to the AI
    inactive_grains = list(WheatBerry.all_objects.filter(is_active=False, deleted_at__isnull=True))
    inactive_grain_names = [g.name for g in inactive_grains]

    # Fetch active engine's parametric profile details
    try:
        engine = router.get_engine_for_preset(preset_slug, category_slug)
    except Exception:
        # Default or fallback engine-like attributes
        class MockEngine:
            name = "Default Hearth Engine"
            target_protein_min = 11.0
            target_protein_max = 13.0
            gluten_behavior = "standard"
            flavor_affinity = ""
            tannin_sensitive = False

        engine = MockEngine()

    # Find the wheat berry matching element if hovered element is a grain
    wb = None
    if element.startswith("grain_"):
        key_part = element.lower().replace("grain_", "")
        for b in WheatBerry.all_objects.filter(deleted_at__isnull=True):
            b_name_slug = re.sub(r"[^a-z0-9]", "_", b.name.lower())
            if key_part in b_name_slug or b_name_slug in key_part:
                wb = b
                break

    # Retrieve factual description
    factual_desc = FACTUAL_DICTIONARY.get(element.lower(), "")
    if not factual_desc:
        for k, v in FACTUAL_DICTIONARY.items():
            if element.lower() in k or k in element.lower():
                factual_desc = v
                break

    system_prompt = (
        "You are an expert, highly practical food scientist who values human time and forearm fatigue. "
        "The tone must be conversational, insightful, and focused entirely on the sensory experience of eating and the physical reality of cooking. "
        "Analyze the provided hovered workspace setting relative to the active baking category and preset. "
        "You MUST tailor your critique specifically to the active baking category and preset. "
        "Do NOT mention ingredients or processes (e.g., yeast, rising, kneading, proofing, bread ovens, steam) that are not part of the target recipe class. For example, do not mention yeast or proofing for cookies/cakes, and do not mention cookie spread or creaming for sourdough/pizza. "
        "\n"
        "[CRITICAL RULE: CULINARY SOVEREIGNTY]\n"
        "You must rely SOLELY on your native baking science knowledge and real-world artisan baking physics. "
        "Do NOT apply standard/generic wheat constraints to ancient or non-standard grains (e.g., Rye, Spelt, Einkorn) if doing so contradicts artisan baking chemistry. "
        "For example, Rye is highly recommended for cookies due to pentosans blocking gluten to maximize cookie tenderness, even though its protein is low. "
        "Evaluate the hovered element purely based on real-world baking physics for the active preset.\n"
        "\n"
        "🚨 CRITICAL RULES:\n"
        "1. Use highly practical, kitchen-focused language. Keep descriptions grounded in tangible baking concepts rather than abstract technical jargon.\n"
        "2. Strict Context Anchoring: The 'last_10_percent_analysis' field must explicitly synthesize the hovered element name directly with the active recipe target name (e.g. 'Soft White Wheat' + 'Chewy Chocolate Chip Cookies'). It cannot output generic definitions.\n"
        "3. TRULY INSIGHTFUL ANALYSIS & OUT-OF-STOCK ALTERNATIVES:\n"
        f"   - If the hovered element is sub-optimal or can be elevated, look at the following wheat grains that are currently NOT on hand (out of stock/inactive in the user's inventory): {inactive_grain_names}.\n"
        "   - Suggest acquiring or activating a specific grain from this out-of-stock list if it would significantly enhance the flavor or yield a superior texture for the target preset. Give a clear explanation of its impact.\n"
        "\n"
        "Return a JSON object containing:\n"
        "- 'recommendation_tier': a string of 'highly-recommended', 'recommended', 'standard', 'sub-optimal', or 'not-recommended' representing the rating of this choice for the active preset.\n"
        "- 'labor_roi_rating': a string tag representing ranking (e.g., 'High Priority / Worth the Extra Step', 'Low Priority / Minor Textural Return', 'High Priority / Absolute Requirement')\n"
        "- 'last_10_percent_analysis': a tight 2-sentence conversational critique.\n"
        "- 'elevate_recipe': a 1-2 sentence recommendation on a potential way to elevate this recipe, suggesting a specific grain to mix in (regardless of inventory), a particular secondary ingredient (like a fat/liquid swap), or a specific method (like autolyse, cold proofing) to achieve greater results.\n"
        "\n"
        "EXAMPLES:\n"
        "Example A (Hovering 'Soft White Wheat' on 'Chewy Chocolate Chip Cookies'):\n"
        "{\n"
        '  "recommendation_tier": "recommended",\n'
        '  "labor_roi_rating": "High Priority / Worth the Extra Step",\n'
        '  "last_10_percent_analysis": "Using Soft White Wheat here ensures your cookies melt into a perfectly tender, uniform pool instead of puffing up into cakey domes. To unlock the real magic, give this fresh-milled dough a 12-hour rest in the fridge before baking so the bran has time to fully absorb the butter fat.",\n'
        '  "elevate_recipe": "For an even richer flavor profile, substitute 20% of the soft white wheat with fresh-milled Rye (regardless of inventory) to introduce pentosans that keep the cookie center exceptionally gooey."\n'
        "}\n"
        "\n"
        "Example B (Hovering 'Manual Spatula' on 'Chewy Chocolate Chip Cookies'):\n"
        "{\n"
        '  "recommendation_tier": "sub-optimal",\n'
        '  "labor_roi_rating": "Low Priority / Minor Textural Return",\n'
        '  "last_10_percent_analysis": "There is zero reason to wear out your forearm hand-mixing a massive batch of cookie dough. Throw it in the stand mixer with the paddle attachment on low speed; you will get the exact same tender crumb without the manual exhaustion.",\n'
        '  "elevate_recipe": "Using a paddle attachment on a stand mixer develops uniform sugar hydration without building unwanted gluten toughness."\n'
        "}\n"
        "\n"
        "Example C (Hovering 'Manual Spatula' on 'Buttermilk Biscuits'):\n"
        "{\n"
        '  "recommendation_tier": "recommended",\n'
        '  "labor_roi_rating": "High Priority / Absolute Requirement",\n'
        '  "last_10_percent_analysis": "Put the electric mixers away. Hand-folding your wet ingredients with a spatula is the exact threshold where biscuit magic lives; a machine will activate the gluten webs in seconds, turning a flaky, layered biscuit into a tough hockey puck.",\n'
        '  "elevate_recipe": "Incorporate cold lard instead of butter to create distinct fat barriers for maximum flaky lamination rise."\n'
        "}"
    )

    # Format the element name to human readable form for the prompt
    element_clean = element.replace("grain_", "").replace("_", " ").title()

    user_prompt = json.dumps(
        {
            "hovered_element": element_clean,
            "recipe_target_name": preset_name,
            "category_slug": category_slug,
            "preset_slug": preset_slug,
            "inactive_grains_not_on_hand": inactive_grain_names,
        }
    )

    try:
        result = call_gemma_api(
            system_prompt,
            user_prompt,
            expected_keys=["recommendation_tier", "labor_roi_rating", "last_10_percent_analysis", "elevate_recipe"],
        )
        if result and "labor_roi_rating" in result and "last_10_percent_analysis" in result:

            def append_celsius(match):
                f_val = int(match.group(1))
                c_val = round((f_val - 32) * 5.0 / 9.0)
                # Return standard °F (°C) format
                return f"{f_val}°F ({c_val}°C)"

            analysis = result["last_10_percent_analysis"]
            # Look for 350F or 350°F
            analysis = re.sub(r"(\d+)\s*(?:°F|F)\b", append_celsius, analysis)

            elevate = result.get("elevate_recipe", "")
            elevate = re.sub(r"(\d+)\s*(?:°F|F)\b", append_celsius, elevate)

            return {
                "recommendation_tier": result.get("recommendation_tier", "recommended"),
                "labor_roi": result["labor_roi_rating"],
                "last_10_percent_analysis": analysis,
                "elevate_recipe": elevate,
            }
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling sidebar insight API: {str(e)}")
    return None


logger = logging.getLogger("grainlab.gemma")


def analyze_wheat_berry_ai(name: str) -> dict | None:
    """
    Asks Gemma to estimate protein content, hardness, moisture absorption, and notes for a wheat berry.
    """
    system_prompt = (
        "You are a food science assistant. Analyze the wheat berry name provided and estimate its properties. "
        "Return a JSON object with keys: "
        "'protein_content' (float, default 12.0), "
        "'hardness' (string: 'hard', 'soft', 'durum', or 'ancient'), "
        "'moisture_absorption_coef' (float, default 1.0; standard AP is 1.0, whole wheat is 1.03, spelt is 1.05, durum is 1.08, einkorn is 1.04), "
        "and 'notes' (string, summary description of properties, STRICTLY limited to 2-3 concise sentences)."
    )
    user_prompt = json.dumps({"name": name})

    if True:
        result = call_gemma_api(
            system_prompt, user_prompt, expected_keys=["protein_content", "hardness", "moisture_absorption_coef"]
        )
        if result:
            try:
                result["protein_content"] = float(result.get("protein_content", 12.0))
                result["moisture_absorption_coef"] = float(result.get("moisture_absorption_coef", 1.0))
                result["hardness"] = str(result.get("hardness", "hard")).lower()
                if result["hardness"] not in ("hard", "soft", "durum", "ancient"):
                    result["hardness"] = "hard"
                result["notes"] = str(result.get("notes", "Analyzed via local Gemma model."))
                return result
            except Exception as e:
                logger.error(f"[AI] - Parsing - Failed converting wheat berry analysis data: {e}")

    # Fallback/mock responses if AI disabled or api fails
    name_lower = name.lower()
    if "spelt" in name_lower:
        return {
            "protein_content": 11.5,
            "hardness": "ancient",
            "moisture_absorption_coef": 1.05,
            "notes": "Ancient grain with highly water-soluble gluten. Adds nutty flavor.",
        }
    elif "einkorn" in name_lower:
        return {
            "protein_content": 12.5,
            "hardness": "ancient",
            "moisture_absorption_coef": 1.04,
            "notes": "Most ancient cultivated wheat. Soft gluten, rich yellow carotenoids.",
        }
    elif "soft" in name_lower or "white" in name_lower:
        return {
            "protein_content": 9.5,
            "hardness": "soft",
            "moisture_absorption_coef": 0.97,
            "notes": "Low protein, weak gluten. Ideal for tender pastries, cookies, and soft rolls.",
        }
    elif "durum" in name_lower or "semolina" in name_lower:
        return {
            "protein_content": 13.5,
            "hardness": "durum",
            "moisture_absorption_coef": 1.08,
            "notes": "Extremely hard durum wheat. Provides yellow tint and high stretch resilience.",
        }
    elif "spring" in name_lower:
        return {
            "protein_content": 14.5,
            "hardness": "hard",
            "moisture_absorption_coef": 1.02,
            "notes": "High protein spring wheat. Extremely strong gluten, excellent for sourdough.",
        }
    else:
        return {
            "protein_content": 13.0,
            "hardness": "hard",
            "moisture_absorption_coef": 1.0,
            "notes": "Standard hard wheat berry. Good gluten strength for general crusty breads.",
        }


def analyze_equipment_ai(name: str, equipment_type: str) -> dict | None:
    """
    Asks Gemma to estimate friction heat factor and notes/details for an equipment item.
    """
    system_prompt = (
        "You are a food science assistant. Analyze the equipment name and type provided and estimate its specifications. "
        "Return a JSON object with keys: "
        "'friction_heat_factor' (float, friction temperature rise in Fahrenheit. For mixers/kneaders, standard stand mixers add 10.0, Ankarsrum/spiral mixers add 6.0, manual hand kneading is 2.0, bread machines add 15.0. For other non-mixer equipment type, return 0.0), "
        "'notes' (string, summary description of capabilities and recommendations, STRICTLY limited to 2-3 concise sentences), "
        "and 'details' (JSON object containing other details like 'capacity_grams' (integer, estimated capacity) or 'recommended_speed' (string))."
    )
    user_prompt = json.dumps({"name": name, "type": equipment_type})

    if True:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["friction_heat_factor", "notes", "details"])
        if result:
            try:
                result["friction_heat_factor"] = float(result.get("friction_heat_factor", 0.0))
                result["notes"] = str(result.get("notes", "Analyzed via local Gemma model."))
                if not isinstance(result.get("details"), dict):
                    result["details"] = {}
                return result
            except Exception as e:
                logger.error(f"[AI] - Parsing - Failed converting equipment analysis data: {e}")

    # Fallback/mock responses if AI disabled or api fails
    name_lower = name.lower()
    if equipment_type == "mixer":
        if "kitchenaid" in name_lower or "classic" in name_lower:
            return {
                "friction_heat_factor": 10.0,
                "notes": "Planetary stand mixer. High speed mixing can introduce significant heat to dough.",
                "details": {"capacity_grams": 1000, "recommended_speed": "Speed 2"},
            }
        elif "ankarsrum" in name_lower or "spiral" in name_lower:
            return {
                "friction_heat_factor": 6.0,
                "notes": "Rotating bowl spiral mixer. Low friction design, preserves dough temperature well.",
                "details": {"capacity_grams": 2500, "recommended_speed": "Medium low"},
            }
        elif "machine" in name_lower:
            return {
                "friction_heat_factor": 15.0,
                "notes": "Enclosed bread machine motor. High friction and heat generation.",
                "details": {"capacity_grams": 800, "recommended_speed": "Automatic"},
            }
        else:
            return {
                "friction_heat_factor": 8.0,
                "notes": "Standard dough mixer. Moderate friction heating.",
                "details": {"capacity_grams": 1200},
            }
    elif equipment_type == "mill":
        return {
            "friction_heat_factor": 0.0,
            "notes": "Grain mill for processing wheat berries. Check stone temp during long runs to avoid overheating flour.",
            "details": {"capacity_grams": 500},
        }
    else:
        return {"friction_heat_factor": 0.0, "notes": "Baking accessory helper.", "details": {}}


def stream_grain_evaluations(
    preset_slug: str,
    category_slug: str = None,
    preset_name: str = None,
    active_archetype_id: str = None,
    active_variation_id: str = None,
    target: str = "all",
):
    """
    Streaming generator for grain evaluations.
    Yields evaluation objects (grains, mills, and sifters) individually using a flat schema.
    """

    from apps.core.engines import router
    from apps.core.gemma.core_client import assemble_system_prompt, stream_gemma_api
    from apps.core.models import BreadPreset, Equipment, WheatBerry

    preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
    if not category_slug and preset and preset.dough_category:
        category_slug = preset.dough_category.slug
    engine = router.get_engine_for_preset(preset_slug, category_slug)

    active_berries = list(WheatBerry.objects.filter(is_active=True))
    if not active_berries:
        return

    archetype_display, mechanics = get_archetype_mechanics(
        engine, active_archetype_id, preset_slug, active_variation_id
    )
    sifting_req = preset.get_sifting_requirement_display() if preset else "Optional (Variable)"
    mills = Equipment.objects.filter(equipment_type="mill").order_by("name")
    mills_text = "\n".join([f"- {m.id} ({m.name})" for m in mills])
    inventory_list = []
    for b in active_berries:
        prof = get_grain_registry_profile(b.name)
        inventory_list.append(
            f"- ID: {b.id} ({b.name})\n"
            f"  Protein: {prof.get('crude_protein_percentage', '12.0%')}, Hardness: {b.hardness}\n"
            f"  Gluten Capacity: {prof.get('gluten_binding_capacity', 'high')}, Moisture Retention (Pentosans): {prof.get('pentosan_concentration', 'low_standard')}\n"
            f"  Flavor/Tannin Profile: {prof.get('bran_tannin_profile', 'none_neutral')}\n"
        )
    inventory_text = "".join(inventory_list)

    variation_line = f"* Requested Target Variation: {active_variation_id}\n" if active_variation_id else ""
    data_context = (
        f"[TARGET PRODUCTION ARCHETYPE MECHANICS]\n"
        f"* Core Archetype: {archetype_display} (Engine: {getattr(engine, 'name', 'Default')})\n"
        f"{variation_line}"
        f"* Required Gluten Elasticity: {mechanics.get('required_gluten_elasticity')}\n"
        f"* Desired Horizontal Flow: {mechanics.get('desired_horizontal_flow')}\n"
        f"* Moisture/Lipid Ratio: {mechanics.get('moisture_lipid_ratio')}\n"
        f"* Target Protein Window: {mechanics.get('optimal_protein_window')}\n"
        f"* Target Flavor Profile: {mechanics.get('target_flavor_profile', 'neutral_sweet')}\n"
        f"* Sifting/Bran Separation Constraint: {sifting_req}\n"
        f"\n[RAW MATERIAL INVENTORY]\n{inventory_text}\n"
        f"\n[AVAILABLE MILL MACHINERY]\n{mills_text}\n"
    )

    import logging

    logger = logging.getLogger("grainlab.services.ai")
    logger.info(f"AI Grain Evaluation Request Data Context:\n{data_context}")

    task_instructions = ""
    response_schema = ""

    if target == "grains":
        task_instructions = (
            f"GrainLab celebrates the unique, vibrant properties of freshly milled whole grains! When evaluating the inventory, look for grains that shine as powerful structural components. "
            "Classify a grain as RECOMMENDED if its native chemistry directly supports the target mechanics and its flavor profile complements the target flavor profile, OR if it contributes essential characteristics to a custom whole-grain flour blend without overpowering the desired flavor. "
            "For each grain, assign a RECOMMENDED, SUB-OPTIMAL, or NOT RECOMMENDED tier, and write a 2-sentence chemistry justification highlighting its potential and flavor fit. "
            f"You MUST evaluate ALL {len(active_berries)} provided raw material grains against the target mechanics. DO NOT skip or group any grains together."
        )
        response_schema = (
            "{\n"
            '  "evaluations": [\n'
            "    {\n"
            '      "type": "grain",\n'
            '      "id": "string (Exact ID of the grain from inventory)",\n'
            '      "tier": "recommended | sub-optimal | not-recommended",\n'
            '      "reasoning": "A concise 2-sentence analytical justification."\n'
            "    }\n"
            "  ]\n"
            "}"
        )
    elif target == "mills":
        task_instructions = "Evaluate EACH mill type from the 'mills' list provided against the mechanics. Assign a tier (RECOMMENDED or NOT-RECOMMENDED) and write a 1-sentence reason for each. CRITICAL: Provide exactly ONE evaluation per mill."
        response_schema = (
            "{\n"
            '  "evaluations": [\n'
            "    {\n"
            '      "type": "mill",\n'
            '      "id": "string (ID of the mill)",\n'
            '      "tier": "recommended | not-recommended",\n'
            '      "reasoning": "1 sentence explaining why this mill is recommended or not for the archetype."\n'
            "    }\n"
            "  ]\n"
            "}"
        )
    elif target == "sifters":
        task_instructions = f"The physical structure of this archetype defines bran separation/sifting as: '{sifting_req}'. You MUST factor this hard constraint into your evaluation of the 'sifted' vs 'unsifted' options. Evaluate BOTH bran separation options (sifted high-extraction vs whole grain unsifted). Assign a tier (RECOMMENDED or NOT-RECOMMENDED) and write a 1-sentence reason for each. CRITICAL: Provide exactly ONE evaluation per sifter option."
        response_schema = (
            "{\n"
            '  "evaluations": [\n'
            "    {\n"
            '      "type": "sifter",\n'
            '      "id": "sifted",\n'
            '      "tier": "recommended | not-recommended",\n'
            '      "reasoning": "1 sentence explaining why bran separation helps or hurts."\n'
            "    },\n"
            "    {\n"
            '      "type": "sifter",\n'
            '      "id": "unsifted",\n'
            '      "tier": "recommended | not-recommended",\n'
            '      "reasoning": "1 sentence explaining why whole grain helps or hurts."\n'
            "    }\n"
            "  ]\n"
            "}"
        )
    else:
        # Fallback to the original monolithic logic
        task_instructions = (
            f"GrainLab celebrates the unique, vibrant properties of freshly milled whole grains! When evaluating the inventory, look for grains that shine as powerful structural components. "
            "Classify a grain as RECOMMENDED if its native chemistry directly supports the target mechanics and its flavor profile complements the target flavor profile, OR if it contributes essential characteristics to a custom whole-grain flour blend without overpowering the desired flavor. "
            "For each grain, assign a RECOMMENDED, SUB-OPTIMAL, or NOT RECOMMENDED tier, and write a 2-sentence chemistry justification highlighting its potential and flavor fit. "
            f"You MUST evaluate ALL {len(active_berries)} raw material grains provided in the inventory against the mechanics. DO NOT skip or group any grains together.\n"
            f"The physical structure of this archetype defines bran separation/sifting as: '{sifting_req}'. You MUST factor this hard constraint into your evaluation of the 'sifted' vs 'unsifted' options. Also evaluate BOTH bran separation options (sifted high-extraction vs whole grain unsifted). Assign a tier (RECOMMENDED or NOT-RECOMMENDED) and write a 1-sentence reason for each.\n"
            "Also evaluate EACH mill type from the 'mills' list provided. Assign a tier (RECOMMENDED or NOT-RECOMMENDED) and write a 1-sentence reason for each. CRITICAL: Provide exactly ONE evaluation per mill and ONE evaluation per sifter option."
        )

        response_schema = (
            "{\n"
            '  "evaluations": [\n'
            "    {\n"
            '      "type": "grain",\n'
            '      "id": "string (Exact ID of the grain from inventory)",\n'
            '      "tier": "recommended | sub-optimal | not-recommended",\n'
            '      "reasoning": "A concise 2-sentence analytical justification."\n'
            "    },\n"
            "    {\n"
            '      "type": "mill",\n'
            '      "id": "string (ID of the mill)",\n'
            '      "tier": "recommended | not-recommended",\n'
            '      "reasoning": "1 sentence explaining why this mill is recommended or not for the archetype."\n'
            "    },\n"
            "    {\n"
            '      "type": "sifter",\n'
            '      "id": "sifted",\n'
            '      "tier": "recommended | not-recommended",\n'
            '      "reasoning": "1 sentence explaining why bran separation helps or hurts."\n'
            "    },\n"
            "    {\n"
            '      "type": "sifter",\n'
            '      "id": "unsifted",\n'
            '      "tier": "recommended | not-recommended",\n'
            '      "reasoning": "1 sentence explaining why whole grain helps or hurts."\n'
            "    }\n"
            "  ]\n"
            "}"
        )

    system_prompt = assemble_system_prompt(
        engine,
        data_context,
        task_instructions,
        response_schema,
        active_archetype_id=active_archetype_id,
        include_global_rules=False,
        active_variation_id=active_variation_id,
    )
    user_prompt = "{}"

    import logging

    logger = logging.getLogger("grainlab.gemma")
    logger.info(f"[Gemma Client] - Phase 2 AI SYSTEM PROMPT FED TO STREAM_GRAIN_EVALUATIONS: {system_prompt}")

    for item in stream_gemma_api(system_prompt, user_prompt):
        yield item
