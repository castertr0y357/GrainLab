import json
import logging
from apps.core.gemma.core_client import call_gemma_api, assemble_system_prompt
from apps.core.gemma.phase3_client import get_local_recipe_details
from apps.core.gemma.core_client import load_grain_registry, get_archetype_mechanics, FACTUAL_DICTIONARY, get_grain_registry_profile
from apps.core.gemma.phase3_client import evaluate_single_grain
from apps.core.gemma.core_client import call_gemma_api


logger = logging.getLogger("grainlab.gemma")


def get_grain_advisory_ai(
    preset_slug: str,
    category_slug: str = None,
    selected_grains: str = None,
    only_evaluations: bool = False,
    preset_name: str = None,
    active_archetype_id: str = None,
    lipid: str = None,
    liquid: str = None,
    binder: str = None
) -> dict | None:
    """
    Evaluates raw kitchen inventory against target archetype mechanics using the dynamic pipeline.
    """
    from apps.core.models import WheatBerry, BreadPreset
    from apps.core.engines import router
    import json
    
    preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
    if not category_slug and preset and preset.dough_category:
        category_slug = preset.dough_category.slug
    engine = router.get_engine_for_preset(preset_slug, category_slug)
    
    active_berries = list(WheatBerry.objects.filter(is_active=True))
    if not active_berries:
        return {"grain_evaluations": []}

    if True:
        selected_ids = [s.strip() for s in selected_grains.split(",") if s.strip()] if selected_grains else []
        selected_berries = [wb for wb in active_berries if str(wb.id) in selected_ids]
        selected_names = [wb.name for wb in selected_berries]

        archetype_display, mechanics = get_archetype_mechanics(engine, active_archetype_id, preset_slug)
        sifting_req = preset.get_sifting_requirement_display() if preset else "Optional (Variable)"

        # Resolve recommended grains and specialty ingredients natively part of the preset_slug
        recommended_slugs = []
        specialty_ingredients = []
        
        # Read specialty inclusions directly from the localized request payload at the moment of execution
        has_selections = (lipid is not None) or (liquid is not None) or (binder is not None)
        if has_selections:
            if lipid and lipid != "none":
                specialty_ingredients.append(lipid.replace("_", " "))
            if liquid and liquid != "none" and liquid != "pure_water" and liquid != "water":
                specialty_ingredients.append(liquid.replace("_", " "))
            if binder and binder != "none":
                specialty_ingredients.append(binder.replace("_", " "))
        elif preset_slug:
            native_details = get_local_recipe_details(
                recipe_slug=preset_slug,
                recipe_name=preset_name or preset_slug,
                engine_id=engine.slug if engine else "default",
                active_archetype_id=active_archetype_id or "default",
                selected_grains=selected_grains
            )
            recommended_slugs = native_details.get("recommended_grain_ids", [])
            sec_ingredients = native_details.get("secondary_ingredients") or {}
            
            # Handle lipids
            lipids = sec_ingredients.get("lipids")
            if not lipids:
                native_lipid = "none"
            elif isinstance(lipids, list):
                if len(lipids) > 0:
                    first_lipid = lipids[0]
                    if isinstance(first_lipid, dict):
                        native_lipid = first_lipid.get("name", "none")
                    else:
                        native_lipid = str(first_lipid)
                else:
                    native_lipid = "none"
            else:
                native_lipid = lipids.get("required", "none")

            # Handle liquids
            liquids = sec_ingredients.get("liquids")
            if not liquids:
                native_liquid = "pure_water"
            elif isinstance(liquids, list):
                if len(liquids) > 0:
                    first_liquid = liquids[0]
                    if isinstance(first_liquid, dict):
                        native_liquid = first_liquid.get("name", "pure_water")
                    else:
                        native_liquid = str(first_liquid)
                else:
                    native_liquid = "pure_water"
            else:
                native_liquid = liquids.get("required", "pure_water")
                
            # Handle binders
            binders = sec_ingredients.get("binders")
            if not binders:
                native_binder = "none"
            elif isinstance(binders, list):
                if len(binders) > 0:
                    first_binder = binders[0]
                    if isinstance(first_binder, dict):
                        native_binder = first_binder.get("name", "none")
                    else:
                        native_binder = str(first_binder)
                else:
                    native_binder = "none"
            else:
                native_binder = binders.get("required", "none")
            
            if native_lipid != "none":
                specialty_ingredients.append(native_lipid.replace("_", " "))
            if native_liquid != "none" and native_liquid != "pure_water" and native_liquid != "water":
                specialty_ingredients.append(native_liquid.replace("_", " "))
            if native_binder != "none":
                specialty_ingredients.append(native_binder.replace("_", " "))
                
        # Resolve recommended grain names from slugs
        native_grain_names = []
        for slug in recommended_slugs:
            for wb in active_berries:
                import re
                wb_slug = re.sub(r'[^a-z0-9]', '_', wb.name.lower()).strip('_')
                wb_slug = re.sub(r'_+', '_', wb_slug)
                if wb_slug == slug or slug in wb_slug or wb_slug in slug:
                    native_grain_names.append(wb.name)
                    break
        
        # If the user has not selected an item, pass empty array bounds [] to force the model to reason about macro mechanics
        if selected_names:
            active_grains_list = selected_names
        else:
            active_grains_list = []

        expected_keys = ["grain_evaluations"]

        if only_evaluations:
            from apps.core.models import Equipment
            mills = Equipment.objects.filter(equipment_type='mill').order_by('name')
            mills_text = "\n".join([f"- {m.id} ({m.name})" for m in mills])
            inventory_text = "\n".join([f"- {b.id} ({b.name}) [Protein: {b.protein_content}%, Hardness: {b.hardness}]" for b in active_berries])
            
            data_context = (
                f"[TARGET PRODUCTION ARCHETYPE MECHANICS]\n"
                f"* Core Archetype: {archetype_display} (Engine: {getattr(engine, 'name', 'Default')})\n"
                f"* Required Gluten Elasticity: {mechanics.get('required_gluten_elasticity')}\n"
                f"* Desired Horizontal Flow: {mechanics.get('desired_horizontal_flow')}\n"
                f"* Moisture/Lipid Ratio: {mechanics.get('moisture_lipid_ratio')}\n"
                f"* Preferred Target Protein Window: {mechanics.get('optimal_protein_window')}\n"
                f"* Sifting/Bran Separation Constraint: {sifting_req}\n"
                f"\n[RAW MATERIAL INVENTORY]\n{inventory_text}\n"
                f"\n[AVAILABLE MILL MACHINERY]\n{mills_text}\n"
            )
            task_instructions = (
                f"You MUST evaluate ALL {len(active_berries)} raw material grains provided in the inventory against the mechanics. DO NOT skip or group any grains together. "
                "For each grain, assign a RECOMMENDED, SUB-OPTIMAL, or NOT RECOMMENDED compatibility tier, and write a 2-sentence chemistry justification.\n"
                f"The physical structure of this archetype defines bran separation/sifting as: '{sifting_req}'. You MUST factor this constraint into your evaluation of the 'sifted' vs 'unsifted' options. Also evaluate BOTH bran separation options (sifted high-extraction vs whole grain unsifted). Assign a tier (RECOMMENDED, SUB-OPTIMAL, or NOT-RECOMMENDED) and write a 1-sentence reason for each.\n"
                "Also evaluate EACH mill type from the 'mills' list provided. Assign a tier (RECOMMENDED, SUB-OPTIMAL, or NOT-RECOMMENDED) and write a 1-sentence reason for each. Output exactly ONE evaluation per mill and ONE per sifter option."
            )
            response_schema = (
                "{\n"
                "  \"grain_evaluations\": [\n"
                "    {\n"
                "      \"grain_id\": \"string (UUID of the grain)\",\n"
                "      \"tier\": \"recommended | sub-optimal | not-recommended\",\n"
                "      \"reasoning\": \"A concise 2-sentence analytical justification.\"\n"
                "    }\n"
                "  ],\n"
                "  \"mill_evaluations\": [\n"
                "    {\n"
                "      \"mill_id\": \"string (ID of the mill)\",\n"
                "      \"tier\": \"recommended | not-recommended\",\n"
                "      \"reasoning\": \"1 sentence explaining why this mill is recommended or not for the archetype.\"\n"
                "    }\n"
                "  ],\n"
                "  \"sifter_evaluations\": {\n"
                "    \"sifted\": {\n"
                "      \"tier\": \"recommended | not-recommended\",\n"
                "      \"reasoning\": \"1 sentence explaining why bran separation helps or hurts.\"\n"
                "    },\n"
                "    \"unsifted\": {\n"
                "      \"tier\": \"recommended | not-recommended\",\n"
                "      \"reasoning\": \"1 sentence explaining why whole grain helps or hurts.\"\n"
                "    }\n"
                "  }\n"
                "}"
            )
            system_prompt = assemble_system_prompt(engine, data_context, task_instructions, response_schema, active_archetype_id=active_archetype_id)
            expected_keys = ["grain_evaluations"]
        else:
            data_context = (
                f"[TARGET PRODUCTION ARCHETYPE MECHANICS]\n"
                f"* Core Archetype: {archetype_display} (Engine: {getattr(engine, 'name', 'Default')})\n"
                f"* Required Gluten Elasticity: {mechanics.get('required_gluten_elasticity')}\n"
                f"* Desired Horizontal Flow: {mechanics.get('desired_horizontal_flow')}\n"
                f"* Moisture/Lipid Ratio: {mechanics.get('moisture_lipid_ratio')}\n"
                f"* Preferred Target Protein Window: {mechanics.get('optimal_protein_window')}\n"
                f"* Sifting/Bran Separation Constraint: {sifting_req}\n"
            )
            task_instructions = (
                "Evaluate each raw material grain against the mechanics and assign RECOMMENDED, SUB-OPTIMAL, or NOT RECOMMENDED compatibility tier, and write a 2-sentence chemistry justification.\n"
                f"The physical structure of this archetype defines bran separation/sifting as: '{sifting_req}'. You MUST factor this constraint into your evaluation of the 'sifted' vs 'unsifted' options. Also evaluate BOTH bran separation options (sifted high-extraction vs whole grain unsifted). Assign a tier (RECOMMENDED, SUB-OPTIMAL, or NOT-RECOMMENDED) and write a 1-sentence reason for each. The reasoning for not-recommended or sub-optimal options MUST be specific to the physical/chemical properties of that option (e.g., 'Whole grain bran interrupts the gluten network, causing a denser crumb') rather than simply stating it is worse than the recommended option.\n"
                "Also evaluate EACH mill type from the 'mills' list provided. Assign a tier (RECOMMENDED, SUB-OPTIMAL, or NOT-RECOMMENDED) and write a 1-sentence reason for each. Provide exactly ONE evaluation per mill, and provide specific mechanical or thermal reasoning for not-recommended or sub-optimal items (e.g., 'Impact mills generate too much heat for this delicate dough') rather than just stating it's not the best choice."
            )
            response_schema = (
                "{\n"
                "  \"grain_evaluations\": [\n"
                "    {\n"
                "      \"grain_id\": \"string (UUID of the grain)\",\n"
                "      \"tier\": \"recommended | sub-optimal | not-recommended\",\n"
                "      \"reasoning\": \"A concise 2-sentence analytical justification.\"\n"
                "    }\n"
                "  ],\n"
                "  \"mill_evaluations\": [\n"
                "    {\n"
                "      \"mill_id\": \"string (ID of the mill)\",\n"
                "      \"tier\": \"recommended | not-recommended\",\n"
                "      \"reasoning\": \"1 sentence explaining why this mill is recommended or not for the archetype.\"\n"
                "    }\n"
                "  ],\n"
                "  \"sifter_evaluations\": {\n"
                "    \"sifted\": {\n"
                "      \"tier\": \"recommended | not-recommended\",\n"
                "      \"reasoning\": \"1 sentence explaining why bran separation helps or hurts.\"\n"
                "    },\n"
                "    \"unsifted\": {\n"
                "      \"tier\": \"recommended | not-recommended\",\n"
                "      \"reasoning\": \"1 sentence explaining why whole grain helps or hurts.\"\n"
                "    }\n"
                "  }\n"
                "}"
            )
            system_prompt = assemble_system_prompt(engine, data_context, task_instructions, response_schema, active_archetype_id=active_archetype_id)

        from apps.core.models import Equipment
        mills_qs = Equipment.objects.filter(equipment_type='mill', deleted_at__isnull=True)
        payload = {
            "engine_id": engine.slug if engine else "default",
            "active_archetype_id": active_archetype_id,
            "selected_grains": selected_names,
            "grains": active_grains_list,
            "specialty_ingredients": specialty_ingredients,
            "mills": [{"id": str(m.id), "name": m.name} for m in mills_qs],
            "inventory": [
                {
                    "id": str(wb.id),
                    "name": wb.name,
                    "crude_protein_percentage": get_grain_registry_profile(wb.name).get("crude_protein_percentage"),
                    "gluten_binding_capacity": get_grain_registry_profile(wb.name).get("gluten_binding_capacity"),
                    "pentosan_concentration": get_grain_registry_profile(wb.name).get("pentosan_concentration"),
                    "bran_tannin_profile": get_grain_registry_profile(wb.name).get("bran_tannin_profile")
                }
                for wb in active_berries
            ]
        }
        
        user_prompt = json.dumps(payload)
        import re
        res = call_gemma_api(system_prompt, user_prompt, expected_keys=expected_keys)
        if res and isinstance(res, dict):
            evaluations = res.get("grain_evaluations", [])
            if isinstance(evaluations, list):
                for evaluation in evaluations:
                    if not isinstance(evaluation, dict):
                        continue
                    matched_wb = None
                    # 1. Exact match on grain_id
                    for wb in active_berries:
                        if str(wb.id) == str(evaluation.get("grain_id", "")).strip():
                            matched_wb = wb
                            break
                    # 2. Case-insensitive name match or slug match on grain_id
                    if not matched_wb:
                        for wb in active_berries:
                            wb_slug = re.sub(r'[^a-z0-9]', '', wb.name.lower())
                            id_slug = re.sub(r'[^a-z0-9]', '', str(evaluation.get("grain_id", "")).lower())
                            if wb_slug == id_slug or wb_slug in id_slug or id_slug in wb_slug:
                                matched_wb = wb
                                break
                    # 3. Matching via grain name inside reasoning
                    if not matched_wb:
                        reasoning_lower = evaluation.get("reasoning", "").lower()
                        for wb in active_berries:
                            if wb.name.lower() in reasoning_lower:
                                matched_wb = wb
                                break
                    if matched_wb:
                        evaluation["grain_id"] = str(matched_wb.id)
            return res

    # Local fallback
    evaluations = []
    if not only_elevate:
        for wb in active_berries:
            res = evaluate_single_grain(wb, engine, preset_name=preset_name, preset_slug=preset_slug, active_archetype_id=active_archetype_id)
            evaluations.append({
                "grain_id": str(wb.id),
                "tier": res["tier"],
                "reasoning": res["reasoning"]
            })

    return {
        "grain_evaluations": evaluations
    }

def get_local_grain_advisory(preset_slug: str, category_slug: str = None, preset_name: str = None, active_archetype_id: str = None) -> dict:
    """
    Local fallback logic performing programmatic evaluation of kitchen inventory 
    using the active sub-engine mechanics.
    """
    from apps.core.models import WheatBerry, BreadPreset
    from apps.core.engines import router
 
    preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
    if not category_slug and preset and preset.dough_category:
        category_slug = preset.dough_category.slug
    engine = router.get_engine_for_preset(preset_slug, category_slug)
 
    active_berries = list(WheatBerry.objects.filter(is_active=True))
    evaluations = []
 
    for wb in active_berries:
        res = evaluate_single_grain(wb, engine, preset_name=preset_name, preset_slug=preset_slug, active_archetype_id=active_archetype_id)
        evaluations.append({
            "grain_id": str(wb.id),
            "tier": res["tier"],
            "reasoning": res["reasoning"]
        })
 
    return {
        "grain_evaluations": evaluations
    }

def get_sidebar_insight_ai(element: str, category_slug: str, preset_slug: str) -> dict | None:
    """
    Queries Gemma to generate a custom labor ROI tag, recommendation tier, and 'Last 10%' critique/reasoning.
    """
    import json
    import re
    from apps.core.models import BreadPreset, WheatBerry
    from apps.core.engines import router
    
    preset = BreadPreset.objects.filter(slug=preset_slug).first()
    preset_name = preset.name if preset else (preset_slug.replace("-", " ").title() if preset_slug else "Custom / Manual Blend")
    
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
            b_name_slug = re.sub(r'[^a-z0-9]', '_', b.name.lower())
            if key_part in b_name_slug or b_name_slug in key_part:
                wb = b
                break

    # Retrieve factual description
    factual_desc = FACTUAL_DICTIONARY.get(element.lower(), '')
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
        "1. Banned Terminology: You are strictly prohibited from using these words or variants in your generated JSON response: "
        "anomalies, parameter, workspace, matrix, objective, configuration, optimization, performance, detected, asset, baseline.\n"
        "2. Strict Context Anchoring: The 'last_10_percent_analysis' field must explicitly synthesize the hovered element name directly with the active recipe target name (e.g. 'Soft White Wheat' + 'Chewy Chocolate Chip Cookies'). It cannot output generic definitions.\n"
        "3. TRULY INSIGHTFUL ANALYSIS & OUT-OF-STOCK ALTERNATIVES:\n"
        f"   - If the hovered element is sub-optimal or can be elevated, look at the following wheat grains that are currently NOT on hand (out of stock/inactive in the user's inventory): {inactive_grain_names}.\n"
        "   - Suggest acquiring or activating a specific grain from this out-of-stock list if it would significantly enhance the flavor or yield a superior texture for the target preset. Give a clear explanation of its impact.\n"
        "4. INGREDIENTS MUST USE HUMAN-READABLE NAMES: You MUST write the actual human-readable names of all grains, flours, and ingredients (e.g. 'Hard Red Spring Wheat', 'Rye', 'Soft White Wheat', 'unsalted butter'). You are STRICTLY PROHIBITED from using database IDs, UUIDs, keys, or hashes (such as '302adef7-9477-4728-8bb7-dae99b05eab9') under any circumstances in your text outputs.\n"
        "5. DOUBLE TEMPERATURE SCALE REQUIRED: Any temperature value you mention must always be provided in both Celsius and Fahrenheit scales (for example: '350°F (177°C)' or '30°C (86°F)'). Never provide a temperature in only a single scale.\n"

        "6. BE HIGHLY CRITICAL AND DISCERNING: Do NOT lazily categorize everything as 'High Priority' or 'Recommended'. Most options in a kitchen are 'Sub-Optimal', 'Low Priority', or 'Standard Baseline'. ONLY rate something as 'High Priority / Worth the Extra Step' or 'Recommended' if it provides a MASSIVE, noticeable improvement to the final texture or flavor for that specific recipe. You are a harsh, pragmatic critic. If it's a minor difference, rate it 'Low Priority'.\n"

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
        "  \"recommendation_tier\": \"recommended\",\n"
        "  \"labor_roi_rating\": \"High Priority / Worth the Extra Step\",\n"
        "  \"last_10_percent_analysis\": \"Using Soft White Wheat here ensures your cookies melt into a perfectly tender, uniform pool instead of puffing up into cakey domes. To unlock the real magic, give this fresh-milled dough a 12-hour rest in the fridge before baking so the bran has time to fully absorb the butter fat.\",\n"
        "  \"elevate_recipe\": \"For an even richer flavor profile, substitute 20% of the soft white wheat with fresh-milled Rye (regardless of inventory) to introduce pentosans that keep the cookie center exceptionally gooey.\"\n"
        "}\n"
        "\n"
        "Example B (Hovering 'Manual Spatula' on 'Chewy Chocolate Chip Cookies'):\n"
        "{\n"
        "  \"recommendation_tier\": \"sub-optimal\",\n"
        "  \"labor_roi_rating\": \"Low Priority / Minor Textural Return\",\n"
        "  \"last_10_percent_analysis\": \"There is zero reason to wear out your forearm hand-mixing a massive batch of cookie dough. Throw it in the stand mixer with the paddle attachment on low speed; you will get the exact same tender crumb without the manual exhaustion.\",\n"
        "  \"elevate_recipe\": \"Using a paddle attachment on a stand mixer develops uniform sugar hydration without building unwanted gluten toughness.\"\n"
        "}\n"
        "\n"
        "Example C (Hovering 'Manual Spatula' on 'Buttermilk Biscuits'):\n"
        "{\n"
        "  \"recommendation_tier\": \"recommended\",\n"
        "  \"labor_roi_rating\": \"High Priority / Absolute Requirement\",\n"
        "  \"last_10_percent_analysis\": \"Put the electric mixers away. Hand-folding your wet ingredients with a spatula is the exact threshold where biscuit magic lives; a machine will activate the gluten webs in seconds, turning a flaky, layered biscuit into a tough hockey puck.\",\n"
        "  \"elevate_recipe\": \"Incorporate cold lard instead of butter to create distinct fat barriers for maximum flaky lamination rise.\"\n"
        "}"
    )
    
    # Format the element name to human readable form for the prompt
    element_clean = element.replace("grain_", "").replace("_", " ").title()
    
    user_prompt = json.dumps({
        "hovered_element": element_clean,
        "recipe_target_name": preset_name,
        "category_slug": category_slug,
        "preset_slug": preset_slug,
        "inactive_grains_not_on_hand": inactive_grain_names
    })
    
    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["recommendation_tier", "labor_roi_rating", "last_10_percent_analysis", "elevate_recipe"])
        if result and "labor_roi_rating" in result and "last_10_percent_analysis" in result:
            return {
                "recommendation_tier": result.get("recommendation_tier", "recommended"),
                "labor_roi": result["labor_roi_rating"],
                "last_10_percent_analysis": result["last_10_percent_analysis"],
                "elevate_recipe": result.get("elevate_recipe", "")
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
        "and 'notes' (string, summary description of properties)."
    )
    user_prompt = json.dumps({"name": name})
    
    if True:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["protein_content", "hardness", "moisture_absorption_coef"])
        if result:
            try:
                result["protein_content"] = float(result.get("protein_content", 12.0))
                result["moisture_absorption_coef"] = float(result.get("moisture_absorption_coef", 1.0))
                result["hardness"] = str(result.get("hardness", "hard")).lower()
                if result["hardness"] not in ('hard', 'soft', 'durum', 'ancient'):
                    result["hardness"] = 'hard'
                result["notes"] = str(result.get("notes", "Analyzed via local Gemma model."))
                return result
            except Exception as e:
                logger.error(f"[AI] - Parsing - Failed converting wheat berry analysis data: {e}")
    
    # Fallback/mock responses if AI disabled or api fails
    name_lower = name.lower()
    if "spelt" in name_lower:
        return {"protein_content": 11.5, "hardness": "ancient", "moisture_absorption_coef": 1.05, "notes": "Ancient grain with highly water-soluble gluten. Adds nutty flavor."}
    elif "einkorn" in name_lower:
        return {"protein_content": 12.5, "hardness": "ancient", "moisture_absorption_coef": 1.04, "notes": "Most ancient cultivated wheat. Soft gluten, rich yellow carotenoids."}
    elif "soft" in name_lower or "white" in name_lower:
        return {"protein_content": 9.5, "hardness": "soft", "moisture_absorption_coef": 0.97, "notes": "Low protein, weak gluten. Ideal for tender pastries, cookies, and soft rolls."}
    elif "durum" in name_lower or "semolina" in name_lower:
        return {"protein_content": 13.5, "hardness": "durum", "moisture_absorption_coef": 1.08, "notes": "Extremely hard durum wheat. Provides yellow tint and high stretch resilience."}
    elif "spring" in name_lower:
        return {"protein_content": 14.5, "hardness": "hard", "moisture_absorption_coef": 1.02, "notes": "High protein spring wheat. Extremely strong gluten, excellent for sourdough."}
    else:
        return {"protein_content": 13.0, "hardness": "hard", "moisture_absorption_coef": 1.0, "notes": "Standard hard wheat berry. Good gluten strength for general crusty breads."}

def analyze_equipment_ai(name: str, equipment_type: str) -> dict | None:
    """
    Asks Gemma to estimate friction heat factor and notes/details for an equipment item.
    """
    system_prompt = (
        "You are a food science assistant. Analyze the equipment name and type provided and estimate its specifications. "
        "Return a JSON object with keys: "
        "'friction_heat_factor' (float, friction temperature rise in Fahrenheit. For mixers/kneaders, standard stand mixers add 10.0, Ankarsrum/spiral mixers add 6.0, manual hand kneading is 2.0, bread machines add 15.0. For other non-mixer equipment type, return 0.0), "
        "'notes' (string, summary description of capabilities and recommendations), "
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
                "details": {"capacity_grams": 1000, "recommended_speed": "Speed 2"}
            }
        elif "ankarsrum" in name_lower or "spiral" in name_lower:
            return {
                "friction_heat_factor": 6.0,
                "notes": "Rotating bowl spiral mixer. Low friction design, preserves dough temperature well.",
                "details": {"capacity_grams": 2500, "recommended_speed": "Medium low"}
            }
        elif "machine" in name_lower:
            return {
                "friction_heat_factor": 15.0,
                "notes": "Enclosed bread machine motor. High friction and heat generation.",
                "details": {"capacity_grams": 800, "recommended_speed": "Automatic"}
            }
        else:
            return {
                "friction_heat_factor": 8.0,
                "notes": "Standard dough mixer. Moderate friction heating.",
                "details": {"capacity_grams": 1200}
            }
    elif equipment_type == "mill":
        return {
            "friction_heat_factor": 0.0,
            "notes": "Grain mill for processing wheat berries. Check stone temp during long runs to avoid overheating flour.",
            "details": {"capacity_grams": 500}
        }
    else:
        return {
            "friction_heat_factor": 0.0,
            "notes": "Baking accessory helper.",
            "details": {}
        }

def stream_grain_evaluations(
    preset_slug: str,
    category_slug: str = None,
    preset_name: str = None,
    active_archetype_id: str = None,
    target: str = "all"
):
    """
    Streaming generator for grain evaluations.
    Yields evaluation objects (grains, mills, and sifters) individually using a flat schema.
    """
    from apps.core.models import WheatBerry, BreadPreset, Equipment
    from apps.core.engines import router
    from apps.core.gemma.core_client import stream_gemma_api, assemble_system_prompt
    import json

    preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
    if not category_slug and preset and preset.dough_category:
        category_slug = preset.dough_category.slug
    engine = router.get_engine_for_preset(preset_slug, category_slug)

    active_berries = list(WheatBerry.objects.filter(is_active=True))
    if not active_berries:
        return

    archetype_display, mechanics = get_archetype_mechanics(engine, active_archetype_id, preset_slug)
    sifting_req = preset.get_sifting_requirement_display() if preset else "Optional (Variable)"
    mills = Equipment.objects.filter(equipment_type='mill').order_by('name')
    mills_text = "\n".join([f"- {m.id} ({m.name})" for m in mills])
    inventory_text = "\n".join([f"- {b.id} ({b.name}) [Protein: {b.protein_content}%, Hardness: {b.hardness}]" for b in active_berries])

    data_context = (
        f"[TARGET PRODUCTION ARCHETYPE MECHANICS]\n"
        f"* Core Archetype: {archetype_display} (Engine: {getattr(engine, 'name', 'Default')})\n"
        f"* Required Gluten Elasticity: {mechanics.get('required_gluten_elasticity')}\n"
        f"* Desired Horizontal Flow: {mechanics.get('desired_horizontal_flow')}\n"
        f"* Moisture/Lipid Ratio: {mechanics.get('moisture_lipid_ratio')}\n"
        f"* Target Protein Window: {mechanics.get('optimal_protein_window')}\n"
        f"* Sifting/Bran Separation Constraint: {sifting_req}\n"
        f"\n[RAW MATERIAL INVENTORY]\n{inventory_text}\n"
        f"\n[AVAILABLE MILL MACHINERY]\n{mills_text}\n"
    )

    task_instructions = ""
    response_schema = ""

    if target == "grains":
        task_instructions = (
            f"You MUST evaluate ALL {len(active_berries)} raw material grains provided in the inventory against the mechanics. DO NOT skip or group any grains together. "
            "For each grain, assign a RECOMMENDED, SUB-OPTIMAL, or NOT RECOMMENDED tier, and write a 2-sentence chemistry justification."
        )
        response_schema = (
            "{\n"
            "  \"evaluations\": [\n"
            "    {\n"
            "      \"type\": \"grain\",\n"
            "      \"id\": \"string (Exact ID of the grain from inventory)\",\n"
            "      \"tier\": \"recommended | sub-optimal | not-recommended\",\n"
            "      \"reasoning\": \"A concise 2-sentence analytical justification.\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
    elif target == "mills":
        task_instructions = (
            "Evaluate EACH mill type from the 'mills' list provided against the mechanics. Assign a tier (RECOMMENDED or NOT-RECOMMENDED) and write a 1-sentence reason for each. CRITICAL: Provide exactly ONE evaluation per mill."
        )
        response_schema = (
            "{\n"
            "  \"evaluations\": [\n"
            "    {\n"
            "      \"type\": \"mill\",\n"
            "      \"id\": \"string (ID of the mill)\",\n"
            "      \"tier\": \"recommended | not-recommended\",\n"
            "      \"reasoning\": \"1 sentence explaining why this mill is recommended or not for the archetype.\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
    elif target == "sifters":
        task_instructions = (
            f"The physical structure of this archetype defines bran separation/sifting as: '{sifting_req}'. You MUST factor this hard constraint into your evaluation of the 'sifted' vs 'unsifted' options. Evaluate BOTH bran separation options (sifted high-extraction vs whole grain unsifted). Assign a tier (RECOMMENDED or NOT-RECOMMENDED) and write a 1-sentence reason for each. CRITICAL: Provide exactly ONE evaluation per sifter option."
        )
        response_schema = (
            "{\n"
            "  \"evaluations\": [\n"
            "    {\n"
            "      \"type\": \"sifter\",\n"
            "      \"id\": \"sifted\",\n"
            "      \"tier\": \"recommended | not-recommended\",\n"
            "      \"reasoning\": \"1 sentence explaining why bran separation helps or hurts.\"\n"
            "    },\n"
            "    {\n"
            "      \"type\": \"sifter\",\n"
            "      \"id\": \"unsifted\",\n"
            "      \"tier\": \"recommended | not-recommended\",\n"
            "      \"reasoning\": \"1 sentence explaining why whole grain helps or hurts.\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
    else:
        # Fallback to the original monolithic logic
        task_instructions = (
            f"You MUST evaluate ALL {len(active_berries)} raw material grains provided in the inventory against the mechanics. DO NOT skip or group any grains together. "
            "For each grain, assign a RECOMMENDED, SUB-OPTIMAL, or NOT RECOMMENDED tier, and write a 2-sentence chemistry justification.\n"
            f"The physical structure of this archetype defines bran separation/sifting as: '{sifting_req}'. You MUST factor this hard constraint into your evaluation of the 'sifted' vs 'unsifted' options. Also evaluate BOTH bran separation options (sifted high-extraction vs whole grain unsifted). Assign a tier (RECOMMENDED or NOT-RECOMMENDED) and write a 1-sentence reason for each.\n"
            "Also evaluate EACH mill type from the 'mills' list provided. Assign a tier (RECOMMENDED or NOT-RECOMMENDED) and write a 1-sentence reason for each. CRITICAL: Provide exactly ONE evaluation per mill and ONE evaluation per sifter option."
        )

        response_schema = (
            "{\n"
            "  \"evaluations\": [\n"
            "    {\n"
            "      \"type\": \"grain\",\n"
            "      \"id\": \"string (Exact ID of the grain from inventory)\",\n"
            "      \"tier\": \"recommended | sub-optimal | not-recommended\",\n"
            "      \"reasoning\": \"A concise 2-sentence analytical justification.\"\n"
            "    },\n"
            "    {\n"
            "      \"type\": \"mill\",\n"
            "      \"id\": \"string (ID of the mill)\",\n"
            "      \"tier\": \"recommended | not-recommended\",\n"
            "      \"reasoning\": \"1 sentence explaining why this mill is recommended or not for the archetype.\"\n"
            "    },\n"
            "    {\n"
            "      \"type\": \"sifter\",\n"
            "      \"id\": \"sifted\",\n"
            "      \"tier\": \"recommended | not-recommended\",\n"
            "      \"reasoning\": \"1 sentence explaining why bran separation helps or hurts.\"\n"
            "    },\n"
            "    {\n"
            "      \"type\": \"sifter\",\n"
            "      \"id\": \"unsifted\",\n"
            "      \"tier\": \"recommended | not-recommended\",\n"
            "      \"reasoning\": \"1 sentence explaining why whole grain helps or hurts.\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )

    system_prompt = assemble_system_prompt(engine, data_context, task_instructions, response_schema, active_archetype_id=active_archetype_id)
    user_prompt = "{}"
    
    import logging
    logger = logging.getLogger("grainlab.gemma")
    logger.info(f"[Gemma Client] - Phase 2 AI SYSTEM PROMPT FED TO STREAM_GRAIN_EVALUATIONS: {system_prompt}")

    for item in stream_gemma_api(system_prompt, user_prompt):
        yield item
