import json
import logging
from django.core.cache import cache
from apps.core.gemma.core_client import call_gemma_api, heal_json_string, assemble_system_prompt
from apps.core.gemma.core_client import load_grain_registry, get_archetype_mechanics, get_grain_registry_profile
from django.conf import settings
from apps.core.gemma.core_client import call_gemma_api, heal_json_string, assemble_system_prompt, stream_gemma_api
from apps.core.gemma.core_client import get_archetype_mechanics, CATEGORY_TO_ENGINE, ENGINE_FLAVORS
from apps.core.models import SystemSetting


logger = logging.getLogger("grainlab.gemma")


def calculate_local_compatibility_from_specs(wb, engine, preset_slug=None, active_archetype_id=None) -> dict:
    grain_profile = get_grain_registry_profile(wb.name)
    archetype_display, mechanics = get_archetype_mechanics(engine, active_archetype_id, preset_slug)
    
    try:
        if hasattr(wb, "protein_content") and wb.protein_content is not None:
            gp = float(wb.protein_content)
        else:
            gp = float(grain_profile.get("crude_protein_percentage", "12.0%").replace("%", ""))
    except Exception:
        gp = 12.0

    window_str = mechanics.get("optimal_protein_window", "11.0% - 13.0%")
    try:
        parts = window_str.replace("%", "").split("-")
        p_min = float(parts[0].strip())
        p_max = float(parts[1].strip())
    except Exception:
        p_min, p_max = 11.0, 13.0

    elasticity = mechanics.get("required_gluten_elasticity", "high_retention")
    binding = grain_profile.get("gluten_binding_capacity", "high")
    
    if p_min <= gp <= p_max:
        tier = "recommended"
    elif (p_min - 1.5) <= gp <= (p_max + 1.5):
        tier = "sub-optimal"
    else:
        tier = "not-recommended"

    if elasticity == "minimal_to_none" and binding in ["negligible", "moderate"]:
        tier = "recommended"
    elif elasticity == "extreme_tensile" and binding == "negligible":
        tier = "not-recommended"
    elif elasticity == "minimal_to_none" and binding == "extreme":
        tier = "not-recommended"

    justification = (
        f"At crude protein of {gp}%, the raw material aligns with the target window of {window_str}. "
        f"Gluten binding capacity of {binding} provides the necessary structural behaviour for {elasticity} elasticity requirements."
    )
    
    return {
        "tier": tier,
        "reasoning": justification
    }

def optimize_grain_blend(preset_slug: str, preset_name: str, active_berries: list) -> tuple[dict, str | None] | None:
    """
    Queries Gemma model to optimize the percentage blend of active wheat berries
    for a specific bread preset.
    Returns: (shares_dict, structural_warning) or None
    """
    system_prompt = (
        "You are a food science assistant specializing in flour milling. "
        "Analyze the requested bread preset and the active wheat berries available. "
        "Optimize the percentage blend (between 0.0 and 1.0, summing to 1.0) of each active wheat berry "
        "to achieve the best structural and flavor profile for the preset. "
        "If the preset is a high-rise bread (like Boule, Baguette, Ciabatta, French Loaf, Pizza, Bagel) "
        "and the user has selected a blend that lacks sufficient gluten strength (e.g. too much soft wheat/ancient grains), "
        "you MUST set 'structural_warning' to a warning string explaining the hazard, and adjust the blend to include "
        "at least 70% of a hard/structural wheat berry. "
        "Return a JSON object containing:\n"
        "1. 'shares': a dictionary mapping each active wheat berry name to its float share (e.g., {\"Hard Red Spring Wheat\": 0.7, \"Soft White Wheat\": 0.3})\n"
        "2. 'structural_warning': a string warning if the configuration is impossible/unsafe, or null/empty if safe."
    )
    
    # Serialize berries to simple representation for the model
    berries_data = []
    for b in active_berries:
        berries_data.append({
            "name": _get_val(b, 'name'),
            "protein_content": _get_val(b, 'protein_content', 12.0),
            "hardness": _get_val(b, 'hardness', 'hard'),
            "moisture_absorption_coef": _get_val(b, 'moisture_absorption_coef', 1.0)
        })
        
    user_prompt = json.dumps({
        "preset_slug": preset_slug,
        "preset_name": preset_name,
        "active_berries": berries_data
    })
    
    result = call_gemma_api(system_prompt, user_prompt, expected_keys=["shares"])
    if result and isinstance(result.get("shares"), dict):
        return result.get("shares"), result.get("structural_warning")
    return None

def evaluate_single_grain(wb, engine, preset_name: str = None, preset_slug: str = None, active_archetype_id: str = None) -> dict:
    """
    Polymorphically evaluates a single grain against target mechanics using the two-dataset prompt.
    """
    import json
    from django.conf import settings
    
    engine_id = engine.slug if engine else "default"
    archetype_id = active_archetype_id or "default"
    variant_id = preset_slug or "default"
    grain_id = str(wb.id)
    cache_key = f"engine_{engine_id}::arch_{archetype_id}::var_{variant_id}::grain_{grain_id}"
    
    cached_val = cache.get(cache_key)
    if cached_val:
        logger.info(f"[AI] - Cache Hit - Key: {cache_key}")
        return cached_val
        
    # 1. Fetch intrinsic chemical profile of the grain from grain_registry.json
    grain_profile = get_grain_registry_profile(wb.name)
    
    # 2. Fetch target archetype mechanics from active engine (force explicit dynamic prompt binding)
    archetype_display, mechanics = get_archetype_mechanics(engine, active_archetype_id, preset_slug)
    
    if True:
        data_context = (
            f"[INTRINSIC RAW MATERIAL PROFILE]\n"
            f"* Element Name: {wb.name}\n"
            f"* Crude Protein: {grain_profile.get('crude_protein_percentage', '12.0%')}\n"
            f"* Gluten Binding Capacity: {grain_profile.get('gluten_binding_capacity', 'high')}\n"
            f"* Pentosan Concentration: {grain_profile.get('pentosan_concentration', 'low_standard')}\n"
            f"* Bran Flavor Profile: {grain_profile.get('bran_tannin_profile', 'none_neutral')}\n\n"
            f"[TARGET PRODUCTION ARCHETYPE MECHANICS]\n"
            f"* Core Archetype: {archetype_display} (Engine: {getattr(engine, 'name', 'Default')})\n"
            f"* Required Gluten Elasticity: {mechanics.get('required_gluten_elasticity', 'high_retention')}\n"
            f"* Desired Horizontal Flow: {mechanics.get('desired_horizontal_flow', 'controlled_expansion')}\n"
            f"* Moisture/Lipid Ratio: {mechanics.get('moisture_lipid_ratio', 'balanced_emulsion')}\n"
            f"* Target Protein Window: {mechanics.get('optimal_protein_window', '11.0% - 13.0%')}\n"
        )
        task_instructions = (
            "1. Relational Matching: Analyze how the raw ingredient's chemical attributes will behave under the thermal, hydraulic, and mechanical demands of the target archetype.\n"
            "2. Determine Compatibility Tier: Select exactly one tier string: \"RECOMMENDED\", \"SUB-OPTIMAL\", or \"NOT RECOMMENDED\".\n"
            "   - If the grain's native properties directly support or enhance the mechanical goals (even if it breaks traditional wheat rules, like an ancient grain with zero gluten maximizing tenderness where minimal elasticity is requested), classify it as RECOMMENDED.\n"
            "   - If the grain's native properties directly conflict with the physical targets (like an extreme-tensile bread flour causing toughness where high horizontal flow is requested), classify it as NOT RECOMMENDED.\n"
            "3. Chemistry-Driven Critique: Write a concise, 2-sentence conversational analysis explaining the precise molecular interaction (e.g., starch gelatinization, protein cross-linking, pentosan water-hoarding, lipid crystallization) driving your tier selection."
        )
        response_schema = (
            "{\n"
            "  \"evaluation_result\": {\n"
            "    \"compatibility_tier\": \"RECOMMENDED | SUB-OPTIMAL | NOT RECOMMENDED\",\n"
            "    \"technical_justification\": \"A conversational, expert 2-sentence food science breakdown.\"\n"
            "  }\n"
            "}"
        )
        system_prompt = assemble_system_prompt(engine, data_context, task_instructions, response_schema)
        
        user_prompt = json.dumps({
            "grain_id": str(wb.id),
            "grain_name": wb.name,
            "engine_id": engine.slug if engine else "default",
            "active_archetype_id": active_archetype_id
        })
        
        try:
            res = call_gemma_api(system_prompt, user_prompt, expected_keys=["evaluation_result"])
            if res and "grain_evaluations" in res:
                evals = res["grain_evaluations"]
                for e in evals:
                    e_id = str(e.get("grain_id", ""))
                    if e_id == str(wb.id) or wb.name.lower() in e_id.lower() or e_id.lower() in wb.name.lower():
                        res_dict = {
                            "tier": e.get("tier", "SUB-OPTIMAL").lower().replace("_", "-"),
                            "reasoning": e.get("reasoning", "")
                        }
                        cache.set(cache_key, res_dict, timeout=None)
                        return res_dict
            if res and "evaluation_result" in res:
                eval_result = res["evaluation_result"]
                tier_raw = str(eval_result.get("compatibility_tier", "SUB-OPTIMAL")).upper().strip()
                if "NOT" in tier_raw:
                    tier = "not-recommended"
                elif "SUB" in tier_raw:
                    tier = "sub-optimal"
                else:
                    tier = "recommended"
                    
                res_dict = {
                    "tier": tier,
                    "reasoning": eval_result.get("technical_justification", "Analyzed physical targets and chemical profile successfully.")
                }
                cache.set(cache_key, res_dict, timeout=None)
                return res_dict
        except Exception as e:
            logger.error(f"[Gemma Client] - Error - Failed evaluation for grain {wb.name}: {e}")

    # Local fallback
    res_dict = calculate_local_compatibility_from_specs(wb, engine, preset_slug, active_archetype_id)
    cache.set(cache_key, res_dict, timeout=None)
    return res_dict

def evaluate_grains_batch(grains: list, engine, preset_name: str = None, preset_slug: str = None, active_archetype_id: str = None) -> dict:
    """
    Evaluates multiple grains in a single LLM API call, caching the results individually.
    """
    import json
    
    engine_id = engine.slug if engine else "default"
    archetype_id = active_archetype_id or "default"
    variant_id = preset_slug or "default"
    
    results = {}
    uncached_grains = []
    
    # 1. Try to load from cache first
    for wb in grains:
        grain_id = str(wb.id)
        cache_key = f"engine_{engine_id}::arch_{archetype_id}::var_{variant_id}::grain_{grain_id}"
        
        cached_val = cache.get(cache_key)
        if cached_val:
            results[grain_id] = cached_val
        else:
            uncached_grains.append(wb)
            
    if not uncached_grains:
        return results
        
    # 2. If there are uncached grains, query the LLM or run fallback
    if True:
        archetype_display, mechanics = get_archetype_mechanics(engine, active_archetype_id, preset_slug)
        
        data_context = (
            f"[TARGET PRODUCTION ARCHETYPE MECHANICS]\n"
            f"* Core Archetype: {archetype_display} (Engine: {getattr(engine, 'name', 'Default')})\n"
            f"* Required Gluten Elasticity: {mechanics.get('required_gluten_elasticity')}\n"
            f"* Desired Horizontal Flow: {mechanics.get('desired_horizontal_flow')}\n"
            f"* Moisture/Lipid Ratio: {mechanics.get('moisture_lipid_ratio')}\n"
            f"* Preferred Target Protein Window: {mechanics.get('optimal_protein_window')}\n"
        )
        task_instructions = (
            "Evaluate each raw material grain provided in the user context against the mechanics and assign RECOMMENDED, SUB-OPTIMAL, or NOT RECOMMENDED compatibility tier, and write a 2-sentence chemistry justification."
        )
        response_schema = (
            "{\n"
            "  \"grain_evaluations\": [\n"
            "    {\n"
            "      \"grain_id\": \"string (UUID of the grain)\",\n"
            "      \"tier\": \"recommended | sub-optimal | not-recommended\",\n"
            "      \"reasoning\": \"A concise 2-sentence analytical justification.\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        system_prompt = assemble_system_prompt(engine, data_context, task_instructions, response_schema)
        
        payload = {
            "engine_id": engine_id,
            "active_archetype_id": active_archetype_id,
            "grains": [
                {
                    "id": str(wb.id),
                    "name": wb.name,
                    "crude_protein_percentage": get_grain_registry_profile(wb.name).get("crude_protein_percentage"),
                    "gluten_binding_capacity": get_grain_registry_profile(wb.name).get("gluten_binding_capacity"),
                    "pentosan_concentration": get_grain_registry_profile(wb.name).get("pentosan_concentration"),
                    "bran_tannin_profile": get_grain_registry_profile(wb.name).get("bran_tannin_profile")
                }
                for wb in uncached_grains
            ]
        }
        
        try:
            res = call_gemma_api(system_prompt, json.dumps(payload), expected_keys=["grain_evaluations"])
            if res and isinstance(res, dict) and "grain_evaluations" in res:
                for ev in res["grain_evaluations"]:
                    ev_id = str(ev.get("grain_id", "")).strip()
                    # Find matching grain from uncached_grains to get the exact UUID
                    matched_wb = None
                    for wb in uncached_grains:
                        if str(wb.id) == ev_id or wb.name.lower() in ev_id.lower() or ev_id.lower() in wb.name.lower():
                            matched_wb = wb
                            break
                    if matched_wb:
                        grain_id = str(matched_wb.id)
                        res_dict = {
                            "tier": ev.get("tier", "SUB-OPTIMAL").lower().replace("_", "-"),
                            "reasoning": ev.get("reasoning", "Analyzed successfully.")
                        }
                        # Write to persistent cache
                        cache_key = f"engine_{engine_id}::arch_{archetype_id}::var_{variant_id}::grain_{grain_id}"
                        cache.set(cache_key, res_dict, timeout=None)
                        results[grain_id] = res_dict
        except Exception as e:
            logger.error(f"[Gemma Client] - Batch Error - Failed batch evaluation: {e}")
            
    # 3. For any grains that are still not evaluated, evaluate using programmatic fallback
    for wb in uncached_grains:
        grain_id = str(wb.id)
        if grain_id not in results:
            res_dict = calculate_local_compatibility_from_specs(wb, engine, preset_slug, active_archetype_id)
            cache_key = f"engine_{engine_id}::arch_{archetype_id}::var_{variant_id}::grain_{grain_id}"
            cache.set(cache_key, res_dict, timeout=None)
            results[grain_id] = res_dict
            
    return results


logger = logging.getLogger("grainlab.gemma")


def generate_dynamic_flavors(cat_slug: str, level: int, count: int = 8, exclude_names: list = None) -> list:
    if exclude_names is None:
        exclude_names = []
    exclude_set = {n.strip().lower() for n in exclude_names}
    
    bases = {
        "alkaline-bath": [
            "Poppy Seed Crusted", "Toasted Onion & Chive", "Sweet Molasses", "Black Pepper Asiago", 
            "Sundried Tomato Basil", "Smoked Paprika Glazed", "Sourdough Rye Twist", "Maple Brown Sugar",
            "Cheddar Herb Butter", "Spiced Pumpkin Seed", "Garlic Herb Infusion", "Sweet Honey Oat"
        ],
        "cakes-batters": [
            "Lemon Raspberry Drizzle", "Spiced Apple Streusel", "Rich Fudge Marble", "Banana Chocolate Chunk",
            "Toasted Almond Peach", "Orange Cranberry Spice", "Classic Red Velvet", "Vanilla Cream Swirl",
            "Coconut Pineapple Delight", "Gingerbread Molasses", "Maple Pecan Muffin", "Strawberry Buttermilk"
        ],
        "choux-paste": [
            "Pecan Maple Cream", "White Chocolate Raspberry", "Dark Chocolate Orange", "Salted Caramel Pecan",
            "Vanilla Custard Glaze", "Double Chocolate Mousse", "Coffee Espresso Swirl", "Lemon Meringue Puff",
            "Spiced Apple Cinnamon", "Toasted Almond Praline", "Blueberry Cream Custard", "Sweet Coconut Cream"
        ],
        "cookies-shortbread": [
            "Snickerdoodle Cinnamon", "Triple Chocolate Chunk", "White Chocolate Macadamia", "Chewy Oatmeal Raisin",
            "Lemon Zest Butter", "Spiced Ginger Molasses", "Classic Sugar Sparkle", "Toasted Pecan Shortbread",
            "Double Fudge Brownie Drop", "Maple Walnut Cookie", "Cranberry Orange Drop", "Almond Butter Sandies"
        ],
        "enriched-soft": [
            "Chocolate Fudge Babka", "Cinnamon Streusel Swirl", "Sweet Maple Braid", "Orange Blossom Honey Rolls",
            "Cardamom Almond Crown", "Buttermilk Parker House", "Spiced Pumpkin Brioche", "Vanilla Custard Roll",
            "Toasted Coconut Buns", "Raspberry Jam Twists", "Apple Cinnamon Morning Buns", "Golden Egg Dinner Rolls"
        ],
        "flatbreads-griddles": [
            "Everything Bagel Focaccia", "Garlic Butter Naan", "Spinach Feta Piadina", "Pesto Mozzarella Flatbread",
            "Caramelized Onion Roti", "Toasted Sesame Pita", "Chili Flake Olive Flatbread", "Rosemary Parmesan Focaccia",
            "Sweet Honey Butter Crumpet", "Roasted Garlic Herb Pita", "Smoked Paprika Flatbread", "Za'atar Olive Flatbread"
        ],
        "fresh-pasta-noodles": [
            "Saffron Egg Tagliatelle", "Spinach Ricotta Ravioli", "Beet Root Pink Lasagna", "Squid Ink Black Linguine",
            "Porcini Mushroom Fettuccine", "Roasted Garlic Pappardelle", "Black Pepper Semolina Pasta", "Basil Pesto Penne",
            "Tomato Paste Fettuccine", "Lemon Herb Tagliolini", "Spiced Red Pepper Pappardelle", "Whole Grain Durum Noodle"
        ],
        "fried-doughs": [
            "Apple Cider Fritter", "Maple Glazed Bacon Donut", "Meyer Lemon Curd Berliner", "Chocolate Frosted Glaze",
            "Cinnamon Sugar Beignet", "Cardamom Spiced Churro", "Raspberry Jam Jelly Donut", "Powdered Sugar Funnel Cake",
            "Vanilla Bean Glazed Cruller", "Spiced Pumpkin Donut", "Toasted Coconut Fry Bread", "Blueberry Glazed Donut"
        ],
        "lean-crusty": [
            "Fig & Walnut Sourdough", "Cranberry Pecan Batard", "Toasted Sesame Boule", "Olive Oregano Sourdough",
            "Roasted Garlic Hearth Batard", "Rosemary French Baguette", "Multigrain Honey Seeded Boule", "Dark Beer Stout Rye",
            "Classic Country Sourdough", "Sun-Dried Tomato Batard", "Spiced Pumpkin Seed Hearth", "Ancient Grain Emmer Boule"
        ],
        "pastry-lamination": [
            "Meyer Lemon Cream Danish", "Almond Frangipane Turnover", "Raspberry Jam Pinwheel", "Cinnamon Sugar Palmier",
            "Vanilla Custard Fruit Plait", "Maple Butter Laminated Knot", "Chocolate Hazelnut Croissant", "Orange Glazed Cruffin",
            "Cardamom Spiced Morning Roll", "Toasted Pecan Laminated Twist", "Apple Compote Turnover", "Savory Ham Cheese Croissant"
        ],
        "quick-breads-scones": [
            "Zucchini Walnut Quick Bread", "Blueberry Lemon Glazed Scone", "Maple Pecan Oatmeal Scone", "Cranberry Orange Loaf",
            "Chocolate Chip Banana Bread", "Sharp Cheddar Herb Scone", "Spiced Pumpkin Ginger Bread", "Honey Butter Cornbread",
            "Vanilla Bean Blackberry Scone", "Apple Streusel Quick Loaf", "Savory Bacon Green Onion Scone", "Toasted Almond Poppyseed"
        ]
    }
    
    category_bases = bases.get(cat_slug, bases["cookies-shortbread"])
    
    variants = []
    descriptions = [
        "A beautiful, aromatic variant optimized to accentuate whole grain notes.",
        "A texture-focused twist featuring hydration adjustments for a softer bite.",
        "A premium profile featuring rich inclusion blending and deep flavor depth.",
        "An artisanal variation using custom preferment ratios for complex aromatics.",
        "A delightful variation balancing sweet/savory flavor tones and fine crumb.",
        "A rustic formula prioritizing crumb tenderness and high oven spring.",
        "A mouthwatering twist designed for uniform heat distribution and crispy edges.",
        "A sophisticated variation adding subtle spices to contrast the grain profile.",
        "A modern take with adjusted baking parameters to produce a stunning crust.",
        "A highly reliable recipe modification designed for consistent, delicious results."
    ]
    
    gen_idx = 0
    tweak_count = 0
    while len(variants) < count and gen_idx < len(category_bases) * 2:
        name = category_bases[gen_idx % len(category_bases)]
        if name.lower() not in exclude_set:
            variants.append({
                "name": name,
                "desc": f"{descriptions[tweak_count % len(descriptions)]} Perfect for pairing with active milled grains.",
                "menu_desc": f"{name} crafted to highlight the unique nuances of freshly milled flour."
            })
            tweak_count += 1
        gen_idx += 1
        
    return variants

def get_fallback_creativity_recipes(engine_id: str, active_archetype_id: str, pref_slugs: list) -> dict:
    cat_slug = engine_id
    if cat_slug not in ENGINE_FLAVORS:
        for k, v in CATEGORY_TO_ENGINE.items():
            if v == engine_id:
                cat_slug = k
                break
                
    flavors_data = ENGINE_FLAVORS.get(cat_slug)
    if not flavors_data:
        flavors_data = ENGINE_FLAVORS["cookies-shortbread"]
        
    recipes = []
    for lvl in [1, 2]:
        for idx, item in enumerate(flavors_data[lvl]):
            recipes.append({
                "recipe_id": f"{active_archetype_id}_level{lvl}_{idx+1}",
                "recipe_name": item["name"],
                "creativity_level": lvl,
                "description": item["desc"],
                "menu_description": f"A delightful artisanal version of {item['name']}, baked fresh with heritage grains."
            })
    return {"recipes": recipes}

def get_fallback_variants(engine_id: str, active_archetype_id: str, creativity_level: int, pref_slugs: list, exclude_names: list = None) -> dict:
    cat_slug = engine_id
    if cat_slug not in ENGINE_FLAVORS:
        for k, v in CATEGORY_TO_ENGINE.items():
            if v == engine_id:
                cat_slug = k
                break
                
    dynamic_items = generate_dynamic_flavors(cat_slug, creativity_level, count=5, exclude_names=exclude_names)
    
    variants = []
    for idx, item in enumerate(dynamic_items):
        variants.append({
            "variant_id": f"{active_archetype_id}_v{creativity_level}_alt{idx+1}",
            "variant_name": item["name"],
            "description": item["desc"],
            "menu_description": item.get("menu_desc", f"A delicious, elevated take on {item['name']}.")
        })
    return {"generated_variants": variants}

def generate_recipe_variants(engine_id: str, active_archetype_id: str, inventory: list, exclude_names: list = None, count: int = 5) -> dict | None:
    """
    Given the active engine slug, selected archetype ID, and inventory grain list,
    asks the LLM to generate a list of recipe variants with descriptions
    and recommended_grain_ids for golden highlight ring binding.
    """
    import json

    system_prompt = (
        "You are a baking science variant generator. Given an engine type and structural archetype, "
        f"generate exactly {count} distinct recipe variants optimized for fresh-milled whole grains.\n"
        f"CRITICAL: The variants must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        "You are strictly prohibited from generating recipes crossing over into other archetypes or categories.\n"
        f"CRITICAL: The generated variants must NOT repeat or have the same flavor/recipe name as these primary/existing recipes: {exclude_names or []}.\n"
        "CRITICAL: The variants MUST be 100% unique. Do NOT generate duplicate recipes.\n"
        "CRITICAL: Do NOT append words like 'Classic', 'Modern', 'Variant', or 'Level' to the variant names. The names should be simple and natural.\n"
        "CRITICAL: The variants must be defined by their culinary/flavor targets (e.g. Chocolate Chip, Snickerdoodle, Roasted Garlic Herb, Fig & Walnut, Cinnamon Swirl, Blueberry Lemon, etc.), NOT by the specific grains used (e.g. do not call them 'Spelt Cookie' or 'Rye Batard'). The grains in the inventory should be used to accentuate and pair with these flavor targets, and specified in the recommended_grain_ids list.\n"
        "\n"
        "Each variant must match this JSON schema:\n"
        "{\n"
        "  \"generated_variants\": [\n"
        "    {\n"
        "      \"variant_id\": \"unique_slug\",\n"
        "      \"variant_name\": \"Human readable variant label (representing a culinary/flavor target)\",\n"
        "      \"description\": \"1-2 sentence description explaining the structural/flavor tweak and how it pairs with the whole grain notes.\",\n"
        "      \"menu_description\": \"A rich, descriptive flavor profile written in the style of a high-end restaurant menu item description.\",\n"
        "      \"recommended_grain_ids\": [\"grain_name_slug\"]\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "IMPORTANT: recommended_grain_ids must be lowercase name slugs matching grains from the provided inventory. "
        "Return ONLY raw JSON with no markdown fences."
    )

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "inventory": inventory,
        "exclude_names": exclude_names or [],
    })

    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["generated_variants"])
        if result and isinstance(result.get("generated_variants"), list):
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_recipe_variants: {str(e)}")

    return None

def generate_creativity_recipes(engine_id: str, active_archetype_id: str, inventory: list) -> dict | None:
    """
    Given the engine slug, selected archetype ID, and inventory grain list, asks the LLM to generate
    exactly 10 recipe profiles (5 per Creativity Level: 1 and 2).
    """
    import json

    system_prompt = (
        "You are a baking science expert. Given an engine type, target archetype, and inventory grain list, "
        "generate exactly 10 distinct recipe profiles matching these two Creativity Levels (exactly 5 recipes per level):\n"
        f"CRITICAL: All 10 generated recipe profiles must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        "You are strictly prohibited from generating recipes crossing over into other archetypes or categories.\n"
        "- Creativity Level 1: Baseline Standard Profiles. (Simple, classic, highly traditional, reliable profiles. NO unusual flavors).\n"
        "- Creativity Level 2: Advanced Modern Profiles. (Wildly creative, unconventional, artisanal, or avant-garde flavor combinations).\n"
        "\n"
        "CRITICAL: The recipe profiles MUST be 100% unique. Do NOT generate duplicate recipes.\n"
        "CRITICAL: Do NOT append words like 'Classic', 'Modern', 'Variant', or 'Level' to the variant names. The names should be simple and natural.\n"
        "CRITICAL: The recipe profiles must be defined by their culinary/flavor targets (e.g. Chocolate Chip, Snickerdoodle, Roasted Garlic Herb, Fig & Walnut, Cinnamon Swirl, Blueberry Lemon, etc.), NOT by the specific grains used (e.g. do not call them 'Spelt Cookie' or 'Rye Batard').\n"
        "\n"
        "Each recipe must match this JSON schema:\n"
        "{\n"
        "  \"recipes\": [\n"
        "    {\n"
        "      \"recipe_id\": \"unique_slug\",\n"
        "      \"recipe_name\": \"Human readable title (representing a culinary/flavor target)\",\n"
        "      \"creativity_level\": 1,  // must be 1 or 2\n"
        "      \"description\": \"1-2 sentence description explaining the flavor structure\",\n"
        "      \"menu_description\": \"A rich, descriptive flavor profile written in the style of a high-end restaurant menu item description.\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Return ONLY raw JSON with no markdown fences."
    )

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "inventory": inventory,
    })

    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["recipes"])
        if result and isinstance(result.get("recipes"), list):
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_creativity_recipes: {str(e)}")

    return None

def generate_creativity_variants(engine_id: str, creativity_level: int, active_archetype_id: str, inventory: list, exclude_names: list = None, count: int = 5) -> dict | None:
    """
    Given the engine, target creativity level, parent recipe, and inventory grain list,
    asks the LLM to generate 8 alternative recipe variations matching ONLY that creativity level.
    """
    import json

    system_prompt = (
        f"You are a baking science expert. Given an engine type, a parent recipe ID, and a target Creativity Level of {creativity_level}, "
        f"generate exactly {count} alternative structural profile variations matching ONLY that creativity level.\n"
        f"CRITICAL: The variations must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        f"You are strictly prohibited from generating recipes crossing over into other archetypes or categories.\n"
        f"CRITICAL: The generated variants must NOT repeat or have the same flavor/recipe name as these primary/existing recipes: {exclude_names or []}.\n"
        "CRITICAL: The generated variations MUST be 100% unique. Do NOT generate duplicate recipes.\n"
        "CRITICAL: Do NOT append words like 'Classic', 'Modern', 'Variant', or 'Level' to the variant names. The names should be simple and natural.\n"
        "CRITICAL: The variations must be defined by their culinary/flavor targets (e.g. Chocolate Chip, Snickerdoodle, Roasted Garlic Herb, Fig & Walnut, Cinnamon Swirl, Blueberry Lemon, etc.), NOT by the specific grains used (e.g. do not call them 'Spelt Cookie' or 'Rye Batard').\n"
        "\n"
        "Each variation must match this JSON schema:\n"
        "{\n"
        "  \"generated_variants\": [\n"
        "    {\n"
        "      \"variant_id\": \"unique_slug\",\n"
        "      \"variant_name\": \"Human readable variant label (representing a culinary/flavor target)\",\n"
        "      \"description\": \"1-2 sentence description explaining the structural/flavor tweak and how it pairs with the whole grain notes.\",\n"
        "      \"menu_description\": \"A rich, descriptive flavor profile written in the style of a high-end restaurant menu item description.\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Return ONLY raw JSON with no markdown fences."
    )

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "creativity_level": creativity_level,
        "active_archetype_id": active_archetype_id,
        "inventory": inventory,
        "exclude_names": exclude_names or [],
    })

    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["generated_variants"])
        if result and isinstance(result.get("generated_variants"), list):
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_creativity_variants: {str(e)}")

    return None

def stream_recipe_variants(engine_id: str, active_archetype_id: str, inventory: list, exclude_names: list = None, count: int = 5):
    """
    Streaming generator for recipe variants.
    """
    import json
    system_prompt = (
        "You are a baking science variant generator. Given an engine type and structural archetype, "
        f"generate exactly {count} distinct recipe variants optimized for fresh-milled whole grains.\n"
        f"CRITICAL: The variants must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        "You are strictly prohibited from generating recipes crossing over into other archetypes or categories.\n"
        f"CRITICAL: The generated variants must NOT repeat or have the same flavor/recipe name as these primary/existing recipes: {exclude_names or []}.\n"
        "CRITICAL: The variants MUST be 100% unique. Do NOT generate duplicate recipes.\n"
        "CRITICAL: Do NOT append words like 'Classic', 'Modern', 'Variant', or 'Level' to the variant names. The names should be simple and natural.\n"
        "CRITICAL: The variants must be defined by the culinary/flavor profile of the dough/batter/bread itself (e.g. Honey Oat, Roasted Garlic Herb, Cinnamon Swirl, Jalapeno Cheddar). Do NOT generate recipes for fillings, toppings, or sandwiches (e.g. never suggest 'Ham & Swiss' or 'Roast Beef'). The names must not just use the specific grain names (e.g. do not call them 'Spelt Cookie' or 'Rye Batard'). The grains in the inventory should be used to accentuate and pair with these flavor targets, and specified in the recommended_grain_ids list.\n"
        "\n"
        "Each variant must match this JSON schema:\n"
        "{\n"
        "  \"generated_variants\": [\n"
        "    {\n"
        "      \"variant_id\": \"unique_slug\",\n"
        "      \"variant_name\": \"Human readable variant label (representing a culinary/flavor target)\",\n"
        "      \"description\": \"1-2 sentence description explaining the structural/flavor tweak and how it pairs with the whole grain notes.\",\n"
        "      \"menu_description\": \"A rich, descriptive flavor profile written in the style of a high-end restaurant menu item description.\",\n"
        "      \"recommended_grain_ids\": [\"grain_name_slug\"]\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "IMPORTANT: recommended_grain_ids must be lowercase name slugs matching grains from the provided inventory. "
        "Return ONLY raw JSON with no markdown fences."
    )

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "inventory": inventory,
        "exclude_names": exclude_names or [],
    })

    for item in stream_gemma_api(system_prompt, user_prompt):
        yield item

def stream_creativity_recipes(engine_id: str, active_archetype_id: str, inventory: list, level: str = ""):
    """
    Streaming generator for creativity recipes.
    """
    import json
    
    if level == "1":
        level_instruction = "- Creativity Level 1: Baseline Standard Profiles. (Simple, classic, highly traditional, reliable profiles. NO unusual flavors).\n"
        count = 5
        temperature = 0.1
    elif level == "2":
        level_instruction = "- Creativity Level 2: Advanced Modern Profiles. (Wildly creative, unconventional, artisanal, or avant-garde flavor combinations).\n"
        count = 5
        temperature = 0.5
    else:
        level_instruction = (
            "- Creativity Level 1: Baseline Standard Profiles. (Simple, classic, highly traditional, reliable profiles. NO unusual flavors).\n"
            "- Creativity Level 2: Advanced Modern Profiles. (Wildly creative, unconventional, artisanal, or avant-garde flavor combinations).\n"
        )
        count = 10
        temperature = 0.1

    system_prompt = (
        f"You are a baking science expert. Given an engine type, target archetype, and inventory grain list, "
        f"generate exactly {count} distinct recipe profiles matching this Creativity Level (exactly {count} recipes):\n"
        f"CRITICAL: All generated recipe profiles must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        "You are strictly prohibited from generating recipes crossing over into other archetypes or categories.\n"
        f"{level_instruction}"
        "\n"
        "CRITICAL: The recipe profiles MUST be 100% unique. Do NOT generate duplicate recipes.\n"
        "CRITICAL: Do NOT append words like 'Classic', 'Modern', 'Variant', or 'Level' to the variant names. The names should be simple and natural.\n"
        "CRITICAL: The recipe profiles must be defined by the culinary/flavor profile of the dough/batter/bread itself (e.g. Honey Oat, Roasted Garlic Herb, Cinnamon Swirl, Jalapeno Cheddar). Do NOT generate recipes for fillings, toppings, or sandwiches (e.g. never suggest 'Ham & Swiss' or 'Roast Beef'). The names must not just use the specific grain names (e.g. do not call them 'Spelt Cookie' or 'Rye Batard').\n"
        "\n"
        "Each recipe must match this JSON schema:\n"
        "{\n"
        "  \"recipes\": [\n"
        "    {\n"
        "      \"recipe_id\": \"unique_slug\",\n"
        "      \"creativity_level\": " + ("1" if level == "1" else ("2" if level == "2" else "1")) + ",\n"
        "      \"recipe_name\": \"Human readable title (representing a culinary/flavor target)\",\n"
        "      \"description\": \"1-2 sentence description explaining the flavor structure\",\n"
        "      \"menu_description\": \"A rich, descriptive flavor profile written in the style of a high-end restaurant menu item description.\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Return ONLY raw JSON with no markdown fences."
    )

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "inventory": inventory,
    })

    for item in stream_gemma_api(system_prompt, user_prompt, yield_raw=True, temperature=temperature):
        yield item

def stream_creativity_variants(engine_id: str, creativity_level: int, active_archetype_id: str, inventory: list, exclude_names: list = None, count: int = 5):
    """
    Streaming generator for creativity variants.
    """
    import json
    system_prompt = (
        f"You are a baking science expert. Given an engine type, a parent recipe ID, and a target Creativity Level of {creativity_level}, "
        f"generate exactly {count} alternative structural profile variations matching ONLY that creativity level.\n"
        f"CRITICAL: The variations must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        f"You are strictly prohibited from generating recipes crossing over into other archetypes or categories.\n"
        f"CRITICAL: The generated variants must NOT repeat or have the same flavor/recipe name as these primary/existing recipes: {exclude_names or []}.\n"
        "CRITICAL: The generated variations MUST be 100% unique. Do NOT generate duplicate recipes.\n"
        "CRITICAL: Do NOT append words like 'Classic', 'Modern', 'Variant', or 'Level' to the variant names. The names should be simple and natural.\n"
        "CRITICAL: The variations must be defined by the culinary/flavor profile of the dough/batter/bread itself (e.g. Honey Oat, Roasted Garlic Herb, Cinnamon Swirl, Jalapeno Cheddar). Do NOT generate recipes for fillings, toppings, or sandwiches (e.g. never suggest 'Ham & Swiss' or 'Roast Beef'). The names must not just use the specific grain names (e.g. do not call them 'Spelt Cookie' or 'Rye Batard').\n"
        "\n"
        "Each variation must match this JSON schema:\n"
        "{\n"
        "  \"generated_variants\": [\n"
        "    {\n"
        "      \"variant_name\": \"Human readable variant label (representing a culinary/flavor target)\",\n"
        "      \"variant_id\": \"unique_slug\",\n"
        "      \"description\": \"1-2 sentence description explaining the structural/flavor tweak and how it pairs with the whole grain notes.\",\n"
        "      \"menu_description\": \"A rich, descriptive flavor profile written in the style of a high-end restaurant menu item description.\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Return ONLY raw JSON with no markdown fences."
    )

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "creativity_level": creativity_level,
        "active_archetype_id": active_archetype_id,
        "inventory": inventory,
        "exclude_names": exclude_names or [],
    })

    for item in stream_gemma_api(system_prompt, user_prompt, yield_raw=True):
        yield item


def sanitize_ai_recipe_json(engine_id: str, result: dict) -> dict:
    if not isinstance(result, dict):
        return result
    
    sec = result.get("secondary_ingredients", {})
    if not isinstance(sec, dict):
        return result

    # Deduplicate across categories to prevent the same ingredient acting as two roles
    seen_names = set()
    for cat_name in ["lipids", "liquids", "binders", "sweeteners", "leaveners", "additives"]:
        cat_items = sec.get(cat_name, [])
        if isinstance(cat_items, list):
            new_items = []
            for item in cat_items:
                if isinstance(item, dict):
                    name = str(item.get("name", "")).strip().lower()
                    if name and name not in seen_names:
                        seen_names.add(name)
                        new_items.append(item)
            sec[cat_name] = new_items

    # 1. Leavener Limits
    leaveners = sec.get("leaveners", [])
    if isinstance(leaveners, list):
        for l in leaveners:
            if isinstance(l, dict):
                name = str(l.get("name", "")).lower()
                pct = float(l.get("bakers_percentage", 0))
                if "powder" in name or "soda" in name or "chemical" in name:
                    if pct > 5.0:
                        l["bakers_percentage"] = 5.0
                elif "starter" in name or "levain" in name or "sourdough" in name:
                    if pct > 60.0:
                        l["bakers_percentage"] = 60.0
                else:
                    if pct > 1.5:
                        l["bakers_percentage"] = 1.5

    # 2. Total Liquid Limit
    # Note: Max 80.0% for quick breads/cookies/batters
    if engine_id in ["quick", "cookie", "batter"]:
        liquids = sec.get("liquids", [])
        if isinstance(liquids, list):
            total_liquid = sum(float(x.get("bakers_percentage", 0)) for x in liquids if isinstance(x, dict))
            if total_liquid > 80.0:
                scale = 80.0 / total_liquid
                for x in liquids:
                    if isinstance(x, dict):
                        x["bakers_percentage"] = round(float(x["bakers_percentage"]) * scale, 2)
                        
    # 3. Total Lipid Limit
    if engine_id in ["quick", "cookie", "batter"]:
        lipids = sec.get("lipids", [])
        if isinstance(lipids, list):
            total_lipid = sum(float(x.get("bakers_percentage", 0)) for x in lipids if isinstance(x, dict))
            if total_lipid > 80.0:
                scale = 80.0 / total_lipid
                for x in lipids:
                    if isinstance(x, dict):
                        x["bakers_percentage"] = round(float(x["bakers_percentage"]) * scale, 2)

    return result

def generate_recipe_details(engine_id: str, active_archetype_id: str, recipe_slug: str, recipe_name: str, selected_grains: str, category_slug: str, mill_type: str = "", is_sifted: bool = False) -> dict | None:
    """
    Asks the LLM to generate the detailed science profile and ways to elevate (last_10_percent_magic)
    for a specific selected recipe.
    """
    import json
    
    # Retrieve thinking mode settings
    ai_thinking_enabled = SystemSetting.get_val("ai_thinking_enabled", "True") == "True"
    ai_thinking_effort = SystemSetting.get_val("ai_thinking_effort", "medium")

    system_prompt = (
        "You are a baking science expert. Given an engine type, target archetype, a specific selected recipe slug, "
        "the human-readable recipe name, and a list of active selected grains, generate the menu description, technical science profile, recommended grain selections, and required secondary ingredients.\n"
        "CRITICAL RULE FOR SECONDARY INGREDIENTS:\n"
        "You MUST provide your absolute best recommendations for each required category (e.g., 'lipids', 'liquids', 'binders', 'leaveners').\n"
        "You MAY provide multiple ingredients for a single category if a blend yields a superior result (e.g., blending butter and oil for lipids, or using both brown and white sugar for sweeteners).\n"
        "For each recommended ingredient, you MUST provide the specific `name` (e.g. 'Unsalted Butter'), the target `temperature` (e.g. 'Room Temp'), and a concise `reasoning` explaining why it is the perfect fit.\n"
        "CRITICAL RULE FOR ADDITIVES:\n"
        "You MUST align the 'additives' specifically with the provided recipe_name. For example, if the recipe is 'Cinnamon Sugar Drop', you MUST include cinnamon and sugar as additives. Chocolate chips for a chocolate chip cookie MUST be additives.\n"
        "CRITICAL RULE FOR REQUIRED ACTIONS:\n"
        "You MUST ONLY select actions from the permissible actions list provided by the engine. Do not hallucinate or guess actions like 'knead' or 'fold' unless they are explicitly allowed.\n"
        "Each response must match this JSON schema exactly:\n"
        "{\n"
        "  \"default_yield_amount\": 24,\n"
        "  \"yield_unit\": \"cookies\",\n"
        "  \"is_portionable\": true,\n"
        "  \"sidebar_science_profile\": \"A concise 2-3 sentence technical overview of this recipe's expected structural mechanics, flavor development, and hydration physics.\",\n"
        "  \"recommended_grain_ids\": [\"grain_name_slug\"],\n"
        "  \"flour_blend\": {\"grain_name_slug\": 80, \"another_grain_slug\": 20},\n"
        "  \"fat_starting_temp\": \"room_temp\",\n"
        "  \"required_actions\": [\"ACTION_STRING\"],\n"
        "  \"required_hardware\": [\"stand_mixer\", \"dough_whisk\"],\n"
        "  \"secondary_ingredients\": {\n"
        "    \"lipids\": [{ \"category_name\": \"Fat / Lipid\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" }],\n"
        "    \"liquids\": [{ \"category_name\": \"Liquid Medium\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" }],\n"
        "    \"binders\": [{ \"category_name\": \"Binder\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" }],\n"
        "    \"sweeteners\": [{ \"category_name\": \"Sweetener\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" }],\n"
        "    \"leaveners\": [{ \"category_name\": \"Leavener\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" }],\n"
        "    \"additives\": [{ \"category_name\": \"Additive\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" }]\n"
        "  }\n"
        "}\n\n"
        "ABSOLUTE CATEGORY RULES — violating any of these is a critical error:\n"
        "  - The 'liquids' key MUST only contain true fluid media: water, milk, cream, buttermilk, juice, coffee, or similar pourable liquids.\n"
        "  - Eggs (whole eggs, egg whites, yolks) and aquafaba are NEVER liquids. They are protein-based binders. Always place them under 'binders'.\n"
        "  - Fats (butter, oil, lard, shortening) are NEVER liquids. Always place them under 'lipids'.\n"
        "  - If a recipe does not require a liquid medium (e.g., cookies or shortbread where all moisture comes from eggs and butter), set 'liquids' to null.\n"
        "Do not include markdown blocks, just raw JSON."
    )
    
    from apps.core.engines import router
    engine = router.get_engine_for_preset(recipe_slug, category_slug)
    permissible_actions = engine.production_profile.get("permissible_action_types", [])
    system_prompt += f"\n\n🚨 [PERMISSIBLE REQUIRED ACTIONS]\nYou MUST ONLY use actions from this list for 'required_actions': {permissible_actions}"

    culinary_directive = engine.get_ai_culinary_directive()
    if culinary_directive:
        system_prompt += f"\n\n🚨 [ENGINE CULINARY DIRECTIVE]\n{culinary_directive}"
        
    additive_directive = getattr(engine, "get_additive_scaling_directive", lambda: "")()
    if additive_directive:
        system_prompt += f"\n\n🚨 [ADDITIVE SCALING DIRECTIVE]\n{additive_directive}"

    if ai_thinking_enabled:
        system_prompt += f"\n[CRITICAL] Use thorough reasoning and step-by-step thinking (thinking effort: {ai_thinking_effort}) before responding."
    else:
        system_prompt += "\n[CRITICAL] Do NOT use thinking/reasoning steps. Respond immediately with the direct answer."

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "recipe_slug": recipe_slug,
        "recipe_name": recipe_name,
        "selected_grains": selected_grains,
        "category_slug": category_slug
    })

    logger.info(f"[Gemma Client] - Info - Calling generate_recipe_details for: {recipe_slug}")

    try:
        # If AI is globally disabled in settings, use the offline mock fallback
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["secondary_ingredients", "recommended_grain_ids"])
        if result and isinstance(result, dict) and "secondary_ingredients" in result:
            result = sanitize_ai_recipe_json(engine_id, result)
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_recipe_details: {str(e)}")

    # If AI is enabled but fails, we do NOT fallback to mock data, we return None to let the UI error overlay trigger
    if True:
        return None

def stream_recipe_details(engine_id: str, active_archetype_id: str, recipe_slug: str, recipe_name: str, selected_grains: str, category_slug: str, mill_type: str = "", is_sifted: bool = False, target: str = "all"):
    """
    Streaming version of generate_recipe_details.
    Yields JSON string chunks as Server-Sent Events from the LLM.
    """
    import json
    from apps.core.engines import router
    from apps.core.gemma.core_client import SystemSetting
    
    ai_thinking_enabled = SystemSetting.get_val("ai_thinking_enabled", "True") == "True"
    ai_thinking_effort = SystemSetting.get_val("ai_thinking_effort", "medium")

    system_prompt = (
        "You are a baking science expert. Given an engine type, target archetype, a specific selected recipe slug, "
        "the human-readable recipe name, and a list of active selected grains, generate the requested JSON payload.\n"
    )

    if target == "base":
        system_prompt += (
            "CRITICAL RULE FOR FLOUR BLEND:\n"
            "Evaluate the 'selected_grains' and assign a functional percentage to each (totaling 100). Do NOT just split them evenly (e.g., 50/50). Use your baking science expertise to determine the optimal ratio. For example, if blending a strong structural grain with a weaker flavor grain (like Rye or Einkorn), use the strong grain as the base (70-80%) and the flavor grain as an accent (20-30%).\n"
            "The keys in 'flour_blend' MUST be the exact names from 'selected_grains', but converted to lowercase and with ALL non-alphanumeric characters (including spaces, dashes, parentheses) replaced by underscores. For example, 'Spelt Wheat (Ancient)' MUST become 'spelt_wheat__ancient_'.\n"
            "CRITICAL RULE FOR REQUIRED ACTIONS:\n"
            "You MUST ONLY select actions from the permissible actions list provided by the engine. Do not hallucinate or guess actions like 'knead' or 'fold' unless they are explicitly allowed.\n"
            "Each response must match this JSON schema exactly:\n"
            "{\n"
            "  \"default_yield_amount\": 24,\n"
            "  \"yield_unit\": \"cookies\",\n"
            "  \"is_portionable\": true,\n"
            "  \"sidebar_science_profile\": \"A concise 2-3 sentence technical overview of this recipe's expected structural mechanics, flavor development, and hydration physics.\",\n"
            "  \"recommended_grain_ids\": [\"grain_name_slug\"],\n"
            "  \"flour_blend\": [{ \"type\": \"blend\", \"ratios\": {\"grain_name_slug\": 80, \"another_grain_slug\": 20}, \"reasoning\": \"string\" }],\n"
            "  \"fat_starting_temp\": \"room_temp\",\n"
            "  \"required_actions\": [\"ACTION_STRING\"],\n"
            "  \"required_hardware\": [\"stand_mixer\", \"dough_whisk\"]\n"
            "}\n\n"
            "Do not include markdown blocks, just raw JSON."
        )
    elif target == "ingredients":
        system_prompt += (
            "CRITICAL RULE FOR SECONDARY INGREDIENTS:\n"
            "You MUST provide your absolute best recommendations for each required category (e.g., 'lipids', 'liquids', 'binders', 'leaveners').\n"
            "You MAY provide multiple ingredients for a single category if a blend yields a superior result (e.g., blending butter and oil for lipids, or using both brown and white sugar for sweeteners).\n"
            "For each recommended ingredient, you MUST provide the specific `name` (e.g. 'Unsalted Butter'), the target `temperature` (e.g. 'Room Temp'), and a concise `reasoning` explaining why it is the perfect fit.\n"
            "CRITICAL RULE FOR ADDITIVES:\n"
            "You MUST align the 'additives' specifically with the provided recipe_name. For example, if the recipe is 'Cinnamon Sugar Drop', you MUST include cinnamon and sugar as additives. Chocolate chips for a chocolate chip cookie MUST be additives.\n"
            "CRITICAL RULE: You MAY generate multiple objects for the same category_key (e.g. two sweeteners). If a recipe has multiple distinct flavors (e.g. 'Lemon Blueberry'), you MUST generate multiple distinct 'additives' objects (one for Lemon, one for Blueberry).\n"
            "ABSOLUTE CATEGORY RULES — violating any of these is a critical error:\n"
            "  - The 'liquids' key MUST only contain true fluid media: water, milk, cream, buttermilk, juice, coffee, or similar pourable liquids.\n"
            "  - Eggs (whole eggs, egg whites, yolks) and aquafaba are NEVER liquids. They are protein-based binders. Always place them under 'binders'.\n"
            "  - Fats (butter, oil, lard, shortening) are NEVER liquids. Always place them under 'lipids'.\n"
            "  - If a recipe does not require a liquid medium (e.g., cookies or shortbread where all moisture comes from eggs and butter), set 'liquids' to null.\n"
            "Each response must match this JSON schema exactly:\n"
            "{\n"
            "  \"secondary_ingredients\": [\n"
            "    { \"type\": \"secondary\", \"category_key\": \"lipids\", \"category_name\": \"Fat / Lipid\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" },\n"
            "    { \"type\": \"secondary\", \"category_key\": \"liquids\", \"category_name\": \"Liquid Medium\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" },\n"
            "    { \"type\": \"secondary\", \"category_key\": \"binders\", \"category_name\": \"Binder\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" },\n"
            "    { \"type\": \"secondary\", \"category_key\": \"sweeteners\", \"category_name\": \"Sweetener\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" },\n"
            "    { \"type\": \"secondary\", \"category_key\": \"leaveners\", \"category_name\": \"Leavener\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" },\n"
            "    { \"type\": \"secondary\", \"category_key\": \"additives\", \"category_name\": \"Additive\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" }\n"
            "  ]\n"
            "}\n\n"
            "Do not include markdown blocks, just raw JSON."
        )
    else:
        system_prompt += (
            "CRITICAL RULE FOR SECONDARY INGREDIENTS:\n"
            "You MUST provide your absolute best recommendations for each required category (e.g., 'lipids', 'liquids', 'binders', 'leaveners').\n"
            "You MAY provide multiple ingredients for a single category if a blend yields a superior result (e.g., blending butter and oil for lipids, or using both brown and white sugar for sweeteners).\n"
            "For each recommended ingredient, you MUST provide the specific `name` (e.g. 'Unsalted Butter'), the target `temperature` (e.g. 'Room Temp'), and a concise `reasoning` explaining why it is the perfect fit.\n"
            "CRITICAL RULE FOR ADDITIVES:\n"
            "You MUST align the 'additives' specifically with the provided recipe_name. For example, if the recipe is 'Cinnamon Sugar Drop', you MUST include cinnamon and sugar as additives. Chocolate chips for a chocolate chip cookie MUST be additives.\n"
            "CRITICAL RULE FOR FLOUR BLEND:\n"
            "Evaluate the 'selected_grains' and assign a functional percentage to each (totaling 100). Do NOT just split them evenly (e.g., 50/50). Use your baking science expertise to determine the optimal ratio. For example, if blending a strong structural grain with a weaker flavor grain (like Rye or Einkorn), use the strong grain as the base (70-80%) and the flavor grain as an accent (20-30%).\n"
            "The keys in 'flour_blend' MUST be the exact names from 'selected_grains', but converted to lowercase and with ALL non-alphanumeric characters (including spaces, dashes, parentheses) replaced by underscores. For example, 'Spelt Wheat (Ancient)' MUST become 'spelt_wheat__ancient_'.\n"
            "CRITICAL RULE FOR REQUIRED ACTIONS:\n"
            "You MUST ONLY select actions from the permissible actions list provided by the engine. Do not hallucinate or guess actions like 'knead' or 'fold' unless they are explicitly allowed.\n"
            "Each response must match this JSON schema exactly:\n"
            "{\n"
            "  \"default_yield_amount\": 24,\n"
            "  \"yield_unit\": \"cookies\",\n"
            "  \"is_portionable\": true,\n"
            "  \"sidebar_science_profile\": \"A concise 2-3 sentence technical overview of this recipe's expected structural mechanics, flavor development, and hydration physics.\",\n"
            "  \"recommended_grain_ids\": [\"grain_name_slug\"],\n"
            "  \"flour_blend\": [{ \"type\": \"blend\", \"ratios\": {\"grain_name_slug\": 80, \"another_grain_slug\": 20}, \"reasoning\": \"string\" }],\n"
            "  \"fat_starting_temp\": \"room_temp\",\n"
            "  \"required_actions\": [\"ACTION_STRING\"],\n"
            "  \"required_hardware\": [\"stand_mixer\", \"dough_whisk\"],\n"
            "  \"secondary_ingredients\": [\n"
            "    { \"type\": \"secondary\", \"category_key\": \"lipids\", \"category_name\": \"Fat / Lipid\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" },\n"
            "    { \"type\": \"secondary\", \"category_key\": \"liquids\", \"category_name\": \"Liquid Medium\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" },\n"
            "    { \"type\": \"secondary\", \"category_key\": \"binders\", \"category_name\": \"Binder\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" },\n"
            "    { \"type\": \"secondary\", \"category_key\": \"sweeteners\", \"category_name\": \"Sweetener\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" },\n"
            "    { \"type\": \"secondary\", \"category_key\": \"leaveners\", \"category_name\": \"Leavener\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" },\n"
            "    { \"type\": \"secondary\", \"category_key\": \"additives\", \"category_name\": \"Additive\", \"name\": \"string\", \"temperature\": \"string\", \"reasoning\": \"string\" }\n"
            "  ]\n"
            "}\n\n"
            "CRITICAL RULE: You MAY generate multiple objects for the same category_key (e.g. two sweeteners). If a recipe has multiple distinct flavors (e.g. 'Lemon Blueberry'), you MUST generate multiple distinct 'additives' objects (one for Lemon, one for Blueberry).\n"
            "ABSOLUTE CATEGORY RULES — violating any of these is a critical error:\n"
            "  - The 'liquids' key MUST only contain true fluid media: water, milk, cream, buttermilk, juice, coffee, or similar pourable liquids.\n"
            "  - Eggs (whole eggs, egg whites, yolks) and aquafaba are NEVER liquids. They are protein-based binders. Always place them under 'binders'.\n"
            "  - Fats (butter, oil, lard, shortening) are NEVER liquids. Always place them under 'lipids'.\n"
            "  - If a recipe does not require a liquid medium (e.g., cookies or shortbread where all moisture comes from eggs and butter), set 'liquids' to null.\n"
            "Do not include markdown blocks, just raw JSON."
        )
    
    engine = router.get_engine_for_preset(recipe_slug, category_slug)
    permissible_actions = engine.production_profile.get("permissible_action_types", [])
    if target in ["all", "base"]:
        system_prompt += f"\n\n🚨 [PERMISSIBLE REQUIRED ACTIONS]\nYou MUST ONLY use actions from this list for 'required_actions': {permissible_actions}"

    culinary_directive = engine.get_ai_culinary_directive()
    if culinary_directive:
        system_prompt += f"\n\n🚨 [ENGINE CULINARY DIRECTIVE]\n{culinary_directive}"

    additive_directive = getattr(engine, "get_additive_scaling_directive", lambda: "")()
    if additive_directive and target in ["all", "ingredients"]:
        system_prompt += f"\n\n🚨 [ADDITIVE SCALING DIRECTIVE]\n{additive_directive}"

    if ai_thinking_enabled:
        system_prompt += f"\n[CRITICAL] Use thorough reasoning and step-by-step thinking (thinking effort: {ai_thinking_effort}) before responding."
    else:
        system_prompt += "\n[CRITICAL] Do NOT use thinking/reasoning steps. Respond immediately with the direct answer."

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "recipe_slug": recipe_slug,
        "recipe_name": recipe_name,
        "selected_grains": selected_grains,
        "category_slug": category_slug
    })
    import logging
    logger = logging.getLogger("grainlab.gemma")
    logger.info(f"[Gemma Client] - Phase 3 AI PROMPT FED TO STREAM_RECIPE_DETAILS (target={target}): {user_prompt}")

    from apps.core.gemma.core_client import stream_gemma_api
    for chunk in stream_gemma_api(system_prompt, user_prompt, yield_raw=True):
        yield chunk



    return get_local_recipe_details(recipe_slug, engine_id, active_archetype_id, selected_grains, recipe_name=recipe_name)

def get_local_recipe_details(recipe_slug: str, engine_id: str, active_archetype_id: str, selected_grains: str, recipe_name: str = None, mill_type: str = "", is_sifted: bool = False) -> dict:
    """
    Returns realistic local fallback recipe details with specific flavor matching.
    """
    slug = (recipe_slug or "").lower()
    name = (recipe_name or "").lower()
    category = (engine_id or "").lower()
    
    # Defaults
    sec_lipids = [{
        "category_name": "Fat / Lipid",
        "name": "Unsalted Butter",
        "ratio": 1.0,
        "temperature": "Room Temp",
        "reasoning": "Butter provides optimal crumb tenderness and dairy notes."
    }]
    sec_liquids = [{
        "category_name": "Liquid Medium",
        "name": "Whole Milk",
        "ratio": 1.0,
        "temperature": "Room Temp",
        "reasoning": "Whole milk provides the perfect balance of hydration, fats, and milk sugars for a soft and supple dough."
    }]
    sec_binders = [{
        "category_name": "Binder",
        "name": "Whole Eggs",
        "ratio": 1.0,
        "temperature": "Room Temp",
        "reasoning": "Whole eggs offer structural binding and additional fat, creating a sturdy yet pillowy crumb that holds its shape."
    }]
    sec_sweeteners = [{
        "category_name": "Sweetener",
        "name": "Granulated Sugar",
        "ratio": 1.0,
        "temperature": "Room Temp",
        "reasoning": "Sugar provides both sweetness and crucial tenderization, while also assisting in the Maillard reaction for a golden crust."
    }]
    sec_leaveners = [{
        "category_name": "Leavener",
        "name": "Baking Soda",
        "ratio": 1.0,
        "temperature": "Room Temp",
        "reasoning": "Baking soda provides immediate lift without requiring fermentation time, ideal for this dough archetype."
    }]
    sec_additives = []
    flavor_inclusions = []
    
    # Grains ratio defaults
    flour_blend_ratios = {}
    if selected_grains:
        grains = [g.strip() for g in selected_grains.split(",") if g.strip()]
        if grains:
            equal_share = round(100.0 / len(grains), 2)
            for g in grains:
                slug = g.lower().replace(" ", "_").replace("-", "_")
                flour_blend_ratios[slug] = equal_share
            flour_blend_ratios[slug] += round(100.0 - sum(flour_blend_ratios.values()), 2)
    flour_blend = {"ratios": flour_blend_ratios, "reasoning": "Standard mathematical even split applied automatically."}
    
    fat_starting_temp = "room_temp"
    required_actions = ["knead"]
    required_hardware = ["stand_mixer"]
    
    if category in ["cookies-shortbread", "cakes-batters", "cookies_shortbread", "cakes_batters", "cookie", "batter"]:
#         sec_lipids = {"required": "unsalted_butter", "options": ["unsalted_butter", "avocado_oil", "coconut_oil"]}
#         sec_liquids = {"required": "pure_water", "options": ["pure_water"]}
#         sec_binders = {"required": "whole_eggs", "options": ["none", "whole_eggs", "egg_whites"]}
        flavor_inclusions = [
            {"name": "Dark Chocolate Chunks", "volume_description": "1/2 cup"},
            {"name": "Maldon Sea Salt", "volume_description": "1 tsp flaky"}
        ]
    elif category in ["pastry-lamination", "pastry_lamination", "pastry", "choux-paste", "choux_paste", "choux", "fry", "fried-doughs"]:
        pass
#         sec_lipids = {"required": "unsalted_butter", "options": ["unsalted_butter", "salted_butter"]}
#         sec_liquids = {"required": "whole_milk", "options": ["whole_milk", "pure_water"]}
#         sec_binders = {"required": "whole_eggs", "options": ["whole_eggs", "egg_whites"]}
    elif category in ["enriched-soft", "enriched_soft", "pan"]:
        pass
#         sec_lipids = {"required": "unsalted_butter", "options": ["unsalted_butter", "avocado_oil"]}
#         sec_liquids = {"required": "whole_milk", "options": ["whole_milk", "pure_water"]}
#         sec_binders = {"required": "none", "options": ["none", "whole_eggs"]}
        flavor_inclusions = [
            {"name": "Cinnamon Sugar Swirl", "volume_description": "3 tbsp"},
            {"name": "Raisins", "volume_description": "1/2 cup"}
        ]
    elif category in ["alkaline-bath", "alkaline_bath", "bath", "flatbreads-griddles", "flatbreads_griddles", "flat"]:
        pass
#         sec_lipids = {"required": "none", "options": ["none", "unsalted_butter"]}
#         sec_liquids = {"required": "pure_water", "options": ["pure_water", "whole_milk"]}
        
    pref_slugs = []
    if selected_grains:
        pref_slugs = [g.strip().lower().replace(" ", "_") for g in selected_grains.split(",") if g.strip()]
    if not pref_slugs:
        pref_slugs = ["hard_red_spring_wheat"]
        
    return {
        "default_yield_amount": 1,
        "yield_unit": "loaf",
        "is_portionable": False,
        "menu_description": f"A balanced formulation of {recipe_name or slug} optimized for target mechanics.",
        "recommended_grain_ids": pref_slugs,
        "flour_blend": flour_blend,
        "fat_starting_temp": fat_starting_temp,
        "required_actions": required_actions,
        "required_hardware": required_hardware,
        "flavor_inclusions": flavor_inclusions,
        "secondary_ingredients": {
            "lipids": sec_lipids,
            "liquids": sec_liquids,
            "binders": sec_binders,
            "sweeteners": sec_sweeteners,
            "leaveners": sec_leaveners,
            "additives": sec_additives
        }
    }

def generate_substitutes(engine_id: str, active_archetype_id: str, recipe_slug: str, recipe_name: str, selected_grains: str, target_category: str, original_recommendation: dict, exclude_names: list = None) -> dict | None:
    logger.info(f"[Gemma Client] - Info - Calling generate_substitutes for: {recipe_slug}, category: {target_category}")

    try:
        exclude_text = ""
        if exclude_names:
            names_str = ", ".join(exclude_names)
            exclude_text = f"\nCRITICAL: Do NOT recommend any of the following ingredients: {names_str}. Provide entirely new alternatives."

        system_prompt = (
            f"You are a baking science expert. You are providing substitutes for a specific secondary ingredient category.\n"
            f"Given the recipe context, the target ingredient category, and the originally recommended ingredient, "
            f"generate 3-5 suitable substitute options.{exclude_text}\n"
            f"For each option, you MUST explain the structural and flavor differences compared to the original recommendation (e.g., how it impacts crumb, flakiness, or hydration).\n"
            f"Each response must match this JSON schema exactly:\n"
            f"{{\n"
            f"  \"substitutes\": [\n"
            f"    {{\n"
            f"      \"name\": \"string\",\n"
            f"      \"temperature\": \"string\",\n"
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
            "selected_grains": selected_grains,
            "target_category": target_category,
            "original_recommendation": original_recommendation
        })

        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["substitutes"])
        if result and isinstance(result, dict) and "substitutes" in result:
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_substitutes: {str(e)}")

    if True:
        return None

    return {"substitutes": []}

def stream_generate_substitutes(engine_id: str, active_archetype_id: str, recipe_slug: str, recipe_name: str, selected_grains: str, target_category: str, original_recommendation: dict, exclude_names: list = None):
    """
    Streaming version of generate_substitutes.
    """
    import json
    import time
    
    exclude_text = ""
    if exclude_names:
        names_str = ", ".join(exclude_names)
        exclude_text = f"\nCRITICAL: Do NOT recommend any of the following ingredients: {names_str}. Provide entirely new alternatives."

    system_prompt = (
        f"You are a baking science expert. You are providing substitutes for a specific secondary ingredient category.\n"
        f"Given the recipe context, the target ingredient category, and the originally recommended ingredient, "
        f"generate 3-5 suitable substitute options.{exclude_text}\n"
        f"For each option, you MUST explain the structural and flavor differences compared to the original recommendation (e.g., how it impacts crumb, flakiness, or hydration).\n"
        f"Each response must match this JSON schema exactly:\n"
        f"{{\n"
        f"  \"substitutes\": [\n"
        f"    {{\n"
        f"      \"name\": \"string\",\n"
        f"      \"temperature\": \"string\",\n"
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
        "selected_grains": selected_grains,
        "target_category": target_category,
        "original_recommendation": original_recommendation
    })

    from apps.core.gemma.core_client import stream_gemma_api
    for chunk in stream_gemma_api(system_prompt, user_prompt):
        yield chunk

def generate_recipe_percentages(engine_id: str, active_archetype_id: str, recipe_slug: str, recipe_name: str, secondary_ingredients: list) -> dict | None:
    """
    Asks the LLM to calculate strict Baker's Percentages for an already generated list of secondary ingredients.
    """
    import json
    
    ai_thinking_enabled = SystemSetting.get_val("ai_thinking_enabled", "True") == "True"
    ai_thinking_effort = SystemSetting.get_val("ai_thinking_effort", "medium")

    system_prompt = (
        "You are a baking science expert. Given an engine type, target archetype, a recipe name, and a list of secondary ingredients, "
        "your ONLY job is to calculate the precise optimal Baker's Percentage for each provided ingredient, as well as the base core ratios.\n"
        "CRITICAL RULE FOR CORE RATIOS (BAKER'S PERCENTAGES):\n"
        "You MUST output the optimal Baker's Percentages for the base recipe structure, where the total flour is always 100%. For example, a classic cookie needs 100-150% sugar and 80-100% fat. A bread might need 75% hydration and 0% sugar. Output these strictly as floats (e.g., 120.0 for 120%).\n"
        "CRITICAL RULE FOR INGREDIENT PERCENTAGES:\n"
        "Ensure the 'bakers_percentage' field for each ingredient is a true Baker's Percentage relative to flour weight and is expressed as a full number (e.g. output 15.0 for 15%, do NOT output 0.15).\n"
        "Each response must match this JSON schema exactly:\n"
        "{\n"
        "  \"target_fat_pct\": 85.0,\n"
        "  \"target_sugar_pct\": 120.0,\n"
        "  \"target_hydration_pct\": 0.0,\n"
        "  \"target_binder_pct\": 10.0,\n"
        "  \"target_leaven_pct\": 1.5,\n"
        "  \"target_salt_pct\": 2.0,\n"
        "  \"target_friction_factor\": 10.0,\n"
        "  \"target_bake_temp\": 450,\n"
        "  \"target_bake_time\": 45,\n"
        "  \"percentages\": {\n"
        "    \"Ingredient Name 1\": 20.0,\n"
        "    \"Ingredient Name 2\": 5.0\n"
        "  }\n"
        "}\n\n"
        "Do not include markdown blocks, just raw JSON."
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
        "secondary_ingredients": secondary_ingredients
    })

    logger.info(f"[Gemma Client] - Info - Calling generate_recipe_percentages for: {recipe_slug}")

    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["percentages"])
        if result and isinstance(result, dict) and "percentages" in result:
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_recipe_percentages: {str(e)}")

    return None
