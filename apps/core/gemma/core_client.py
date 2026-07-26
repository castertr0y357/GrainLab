import json
import logging
import hashlib
import requests
from django.conf import settings
from django.core.cache import cache
from apps.core.models import SystemSetting
from apps.core.bakers_math import get_local_contextual_pitfalls, get_local_sensory_benchmark


logger = logging.getLogger("grainlab.gemma")


def _get_val(obj, key, default=None):
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

def _is_ai_enabled() -> bool:
    """Checks if AI integration is active."""
    # Check database settings to see if AI is active
    return SystemSetting.get_val("ai_enabled", "False").lower() in ("true", "1", "t")

def _get_api_config() -> tuple[str, str]:
    """Retrieves API details from SystemSettings."""
    url = SystemSetting.get_val("ai_api_url", "http://host.docker.internal:11434/v1")
    model = SystemSetting.get_val("ai_model_name", "gemma:12b")
    # Clean completions URL if it doesn't end with chat/completions
    if not url.endswith("/chat/completions"):
        url = url.rstrip("/") + "/chat/completions"
    return url, model

def get_mock_gemma_response(system_prompt: str, user_prompt: str, expected_keys: list = None) -> dict | None:
    """
    Generates realistic, schema-compliant mock responses for offline testing/development.
    """
    import json
    try:
        user_data = json.loads(user_prompt)
    except Exception:
        user_data = {}

    if expected_keys and "evaluation_result" in expected_keys:
        grain_name = user_data.get("grain_name", "")
        from apps.core.models import WheatBerry
        wb = WheatBerry.objects.filter(name=grain_name).first()
        if not wb:
            grain_id = user_data.get("grain_id", "")
            wb = WheatBerry.objects.filter(id=grain_id).first()
        
        from grainlab.engines import router
        engine_id = user_data.get("engine_id", "hearth")
        active_archetype_id = user_data.get("active_archetype_id")
        
        engine = None
        try:
            engine = router.get_engine_by_id(engine_id)
        except Exception:
            pass
        if not engine:
            try:
                engine = router.get_engine_for_preset("", engine_id)
            except Exception:
                pass
            
        res = calculate_local_compatibility_from_specs(wb, engine, active_archetype_id=active_archetype_id)
        return {
            "evaluation_result": {
                "compatibility_tier": res["tier"].upper().replace("-", "_"),
                "technical_justification": res["reasoning"]
            }
        }

    if expected_keys and "shares" in expected_keys:
        berries = user_data.get("active_berries", [])
        shares = {}
        warning = None
        if not berries:
            return {"shares": {}, "structural_warning": None}
            
        if len(berries) == 2:
            shares[berries[0]["name"]] = 0.70
            shares[berries[1]["name"]] = 0.30
            warning = "This split is optimized to balance the strong gluten of the first grain with the extensibility or flavor profile of the second."
        else:
            equal_share = round(1.0 / len(berries), 2)
            for b in berries:
                shares[b["name"]] = equal_share
            shares[berries[-1]["name"]] += round(1.0 - sum(shares.values()), 2)
        return {"shares": shares, "structural_warning": warning}

    elif expected_keys and ("grain_evaluations" in expected_keys or "elevate_recipe" in expected_keys):
        preset_slug = user_data.get("preset_slug", "")
        category_slug = user_data.get("category_slug", "")
        preset_name = user_data.get("preset_name", "")
        inventory = user_data.get("inventory", [])
        
        from grainlab.engines import router
        engine = router.get_engine_for_preset(preset_slug, category_slug)
        
        evaluations = []
        for b in inventory:
            class MockBerry:
                def __init__(self, name, protein, hardness):
                    self.name = name
                    self.protein_content = protein
                    self.hardness = hardness
            wb = MockBerry(b.get("name"), b.get("protein", 12.0), b.get("hardness", "hard"))
            res = calculate_local_compatibility_from_specs(wb, engine, preset_slug)
            evaluations.append({
                "grain_id": b.get("id"),
                "tier": res["tier"],
                "reasoning": res["reasoning"]
            })
            
        elevate_recipe = [
            "Adjust initial water temperature to regulate yeast/enzymatic activity under current ambient conditions.",
            "Incorporate a 30-minute autolyse stage to fully hydrate raw bran and soften the structural network.",
            "Utilize gradual, gentle folding rather than intensive mechanical mixing to control gluten elasticity."
        ]
        
        return {
            "grain_evaluations": evaluations,
            "elevate_recipe": elevate_recipe,
            "mill_recommendation": {
                "mill_id": "mock-mill",
                "reasoning": "[MOCK] A stone mill is ideal to retain volatile aromatics for this category."
            },
            "sifted_recommendation": {
                "should_sift": False,
                "reasoning": "[MOCK] Whole grain bran provides essential structure and flavor depth."
            }
        }

    elif expected_keys and "recipes" in expected_keys:
        engine_id = user_data.get("engine_id", "hearth")
        active_archetype_id = user_data.get("active_archetype_id", "classic_sourdough")
        inventory = user_data.get("inventory", [])
        
        def grain_slug(g):
            return g.get("name", "").lower().replace(" ", "_").replace("/", "").replace("-", "_")

        hard_grains = [b for b in inventory if "hard" in b.get("hardness", "").lower()]
        soft_grains = [b for b in inventory if "soft" in b.get("hardness", "").lower() or b.get("hardness") == "ancient"]
        hard_slugs = [grain_slug(g) for g in hard_grains[:2]] or ["hard_red_spring_wheat"]
        soft_slugs = [grain_slug(g) for g in soft_grains[:2]] or ["soft_white_wheat"]
        pref_slugs = hard_slugs if engine_id in ["hearth", "pan", "bath", "pasta", "lean-crusty", "alkaline-bath", "fresh-pasta-noodles", "enriched-soft"] else soft_slugs

        from apps.core.gemma.phase3_client import get_fallback_creativity_recipes
        return get_fallback_creativity_recipes(engine_id, active_archetype_id, pref_slugs)

    elif expected_keys and "generated_variants" in expected_keys:
        engine_id = user_data.get("engine_id", "hearth")
        active_archetype_id = user_data.get("active_archetype_id", "")
        creativity_level = user_data.get("creativity_level")
        exclude_names = user_data.get("exclude_names", [])

        inventory = user_data.get("inventory", [])
        hard_grains = [b for b in inventory if "hard" in b.get("hardness", "").lower()]
        soft_grains = [b for b in inventory if "soft" in b.get("hardness", "").lower() or b.get("hardness") == "ancient"]

        def grain_slug(g):
            return g.get("name", "").lower().replace(" ", "_").replace("/", "").replace("-", "_")

        hard_slugs = [grain_slug(g) for g in hard_grains[:2]] or ["hard_red_spring_wheat"]
        soft_slugs = [grain_slug(g) for g in soft_grains[:2]] or ["soft_white_wheat"]
        pref_slugs = hard_slugs if engine_id in ["hearth", "pan", "bath", "pasta", "lean-crusty", "alkaline-bath", "fresh-pasta-noodles", "enriched-soft"] else soft_slugs

        c_lvl = int(creativity_level) if creativity_level is not None else 1
        from apps.core.gemma.phase3_client import get_fallback_variants
        return get_fallback_variants(engine_id, active_archetype_id, c_lvl, pref_slugs, exclude_names=exclude_names)

    elif expected_keys and "pitfalls" in expected_keys:
        return {
            "pitfalls": [
                {
                    "title": "High Hydration Sticky Zone",
                    "message": "The formula hydration is high relative to your grain blend. Ensure you use stretch-and-fold techniques rather than intensive mechanical kneading to maintain structure without tearing the gluten sheets."
                }
            ]
        }

    elif expected_keys and "sensory_description" in expected_keys:
        return {
            "sensory_description": "The dough should feel smooth, highly extensible, and slightly tacky but not sticky. It should hold its shape when rounded and show early signs of gas bubbles forming under the surface skin."
        }

    elif expected_keys and "geometry_evaluation" in expected_keys:
        return {
            "geometry_evaluation": {
                "status": "recommended",
                "advisory_label": "Excellent heat transfer properties and moisture retention, allowing the dough to expand fully before the crust sets.",
                "profile_adjustments": {
                    "oven_temp_offset_f": 0,
                    "bake_time_offset_m": 0,
                    "steam_override": "no-change"
                }
            }
        }

    elif expected_keys and "recommendation_tier" in expected_keys:
        hovered = user_data.get("hovered_element", "").lower()
        preset = user_data.get("preset_slug", "")
        category = user_data.get("category_slug", "")
        
        from grainlab.engines import router
        engine = router.get_engine_for_preset(preset, category)
        
        class MockBerry:
            def __init__(self, name):
                self.name = name
                self.protein_content = 12.0
                self.hardness = "hard"
        wb = MockBerry(hovered)
        res = calculate_local_compatibility_from_specs(wb, engine, preset)
        
        return {
            "recommendation_tier": res["tier"],
            "labor_roi_rating": "High Priority / Worth the Extra Step" if res["tier"] == "recommended" else "Low Priority / Minor Textural Return",
            "last_10_percent_analysis": res["reasoning"],
            "elevate_recipe": "Adjust hydration slightly to accommodate the grain's natural water-absorption capacity."
        }

    return None

def assemble_system_prompt(engine, data_context: str, task_instructions: str, response_schema_example: str = None, active_archetype_id: str = None) -> str:
    """
    Constructs the system prompt in the modular fixed order:
    1. Persona & Objective (Global Master Shell Kernel - Part 1)
    2. Global Ruleset (Global Master Shell Kernel - Part 2)
    3. The Data Context (Payload)
    4. The Nuance Injection (Module: Active engine's culinary_nuance_directive)
    5. The Instruction Block (Logic: Specific task instructions + response schema)
    """
    persona_objective = (
        "You are a molecular food scientist and artisan baking chemist running an objective evaluation loop.\n"
        "Your tone must be highly practical, conversational, insightful, and focused entirely on the sensory experience of eating and the physical reality of cooking.\n"
        "Do NOT use corporate filler, generic placeholders, or fluff words like: anomalies, parameter, workspace, matrix, configuration, optimization, performance, detected, or baseline.\n"
    )
    
    global_ruleset = (
        "[GLOBAL RULESET]\n"
        "1. [CRITICAL RULE: CULINARY SOVEREIGNTY]\n"
        "Rely SOLELY on your native baking science knowledge and real-world artisan baking physics. "
        "Do NOT apply standard/generic wheat constraints to ancient or non-standard grains (e.g., Rye, Spelt, Einkorn) if doing so contradicts artisan baking chemistry.\n"
        "2. Double Temperature Scale: Any temperature value you mention must always be provided in both Celsius and Fahrenheit scales (for example: '350°F (177°C)' or '30°C (86°F)'). Never provide a temperature in only a single scale.\n"

        "6. BE HIGHLY CRITICAL AND DISCERNING: Do NOT lazily categorize everything as 'High Priority' or 'Recommended'. Most options in a kitchen are 'Sub-Optimal', 'Low Priority', or 'Standard Baseline'. ONLY rate something as 'High Priority / Worth the Extra Step' or 'Recommended' if it provides a MASSIVE, noticeable improvement to the final texture or flavor for that specific recipe. You are a harsh, pragmatic critic. If it's a minor difference, rate it 'Low Priority'.\n"

        "3. Ingredient Naming: You MUST write the actual human-readable names of all grains, flours, and ingredients (e.g., 'Hard Red Spring Wheat', 'Rye', 'Soft White Wheat', 'unsalted butter'). You are STRICTLY PROHIBITED from using database IDs, UUIDs, keys, or hashes (such as '302adef7-9477-4728-8bb7-dae99b05eab9') under any circumstances in your text outputs.\n"
    )
    
    data_context_header = f"[USER DATA CONTEXT]\n{data_context}\n"
    
    engine_name = getattr(engine, "name", "Default Baking Engine")
    
    # Overhaul Nuance Injection: invoke culinary_nuance_directive method passing active_archetype_id
    if hasattr(engine, "culinary_nuance_directive") and callable(engine.culinary_nuance_directive):
        nuance_directive = engine.culinary_nuance_directive(active_archetype_id)
    else:
        nuance_directive = getattr(engine, "culinary_nuance_directive", "Standard baking physics and generic flour interactions.")
        
    nuance_injection = (
        f"\n[CRITICAL ENGINE FOCUS: {engine_name}]\n"
        f"{nuance_directive}\n"
    )
    
    schema_text = ""
    if response_schema_example:
        schema_text = f"\nReturn ONLY raw JSON with no markdown fences, matching this schema:\n{response_schema_example}"
        
    instruction_block = (
        f"\n[SPECIFIC TASK INSTRUCTIONS]\n"
        f"{task_instructions}\n"
        f"{schema_text}"
    )
    
    prompt = [
        persona_objective,
        global_ruleset,
        data_context_header,
        nuance_injection,
        instruction_block
    ]
    return "".join(prompt)

def heal_json_string(raw_str: str) -> str:
    """
    Sanitizes raw text streams before they are evaluated by the strict system JSON interpreter.
    Repairs mismatched braces/brackets due to truncation and strips trailing commas.
    """
    if not raw_str:
        return ""

    cleaned = raw_str.strip()

    # Find starting brace/bracket
    first_brace = cleaned.find('{')
    first_bracket = cleaned.find('[')
    
    start_idx = -1
    if first_brace != -1 and first_bracket != -1:
        start_idx = min(first_brace, first_bracket)
    elif first_brace != -1:
        start_idx = first_brace
    elif first_bracket != -1:
        start_idx = first_bracket
        
    if start_idx != -1:
        cleaned = cleaned[start_idx:]

    # Clean markdown code blocks fences if they are at the end
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()

    # Balance structural truncations: count open vs closed braces and brackets in a stack
    stack = []
    in_string = False
    escape = False
    
    import re
    i = 0
    n = len(cleaned)
    while i < n:
        char = cleaned[i]
        if escape:
            escape = False
        elif char == '\\':
            escape = True
        elif char == '"':
            in_string = not in_string
        elif not in_string:
            if char in ('{', '['):
                stack.append(char)
            elif char == '}':
                if '{' in stack:
                    while stack:
                        pop_char = stack.pop()
                        if pop_char == '{':
                            break
            elif char == ']':
                if '[' in stack:
                    while stack:
                        pop_char = stack.pop()
                        if pop_char == '[':
                            break
        i += 1

    if in_string:
        cleaned += '"'

    # Strip dangling separators: trailing commas right before closing braces or brackets,
    # or at the very end of the string.
    cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
    cleaned = re.sub(r',\s*$', '', cleaned)

    # Append missing closing delimiters in LIFO order
    while stack:
        pop_char = stack.pop()
        if pop_char == '{':
            cleaned += '}'
        elif pop_char == '[':
            cleaned += ']'

    # Double check trailing commas again after healing
    cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
    
    return cleaned

def call_gemma_api(system_prompt: str, user_prompt: str, expected_keys: list = None) -> dict | None:
    """
    Submits a structured prompt to local Gemma and parses the JSON response.
    Caches results persistently using Django file cache framework.
    Returns None if any step fails.
    """
    if not _is_ai_enabled():
        return None

    import hashlib
    # Normalize user_prompt to ensure consistent caching key
    normalized_user_prompt = user_prompt
    try:
        data = json.loads(user_prompt)
        if isinstance(data, dict):
            # Sort lists to avoid cache misses due to order variance
            for k, v in list(data.items()):
                if isinstance(v, list):
                    try:
                        data[k] = sorted(v)
                    except Exception:
                        pass
            normalized_user_prompt = json.dumps(data, sort_keys=True)
    except Exception:
        pass

    # Compute MD5 hash of prompts as cache key
    raw_key = f"{system_prompt}|||{normalized_user_prompt}"
    cache_key = hashlib.md5(raw_key.encode("utf-8")).hexdigest()

    cached_val = cache.get(cache_key)
    if cached_val:
        logger.info(f"[AI] - Cache Hit - Key: {cache_key}")
        return cached_val

    logger.info(f"[AI] - API Call Init -\nSYSTEM PROMPT:\n{system_prompt}\nUSER PROMPT:\n{normalized_user_prompt}")

    # Check if offline mock mode is active
    if getattr(settings, "MOCK_MODE", True):
        res = get_mock_gemma_response(system_prompt, normalized_user_prompt, expected_keys)
        logger.info(f"[AI] - Mock Mode Response: {res}")
        if res:
            cache.set(cache_key, res, timeout=None)
        return res

    url, model = _get_api_config()
    headers = {
        "Content-Type": "application/json"
    }
    
    # Retrieve thinking mode settings
    ai_thinking_enabled = SystemSetting.get_val("ai_thinking_enabled", "True") == "True"
    ai_thinking_effort = SystemSetting.get_val("ai_thinking_effort", "medium")

    # Inject directives into system prompt
    if ai_thinking_enabled:
        system_prompt += f"\n[CRITICAL] Use thorough reasoning and step-by-step thinking (thinking effort: {ai_thinking_effort}) before responding."
    else:
        system_prompt += "\n[CRITICAL] Do NOT use thinking/reasoning steps. Respond immediately with the direct answer."

    # Force JSON format if supported
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt + " You MUST respond with raw JSON ONLY. No markdown formatting, no codeblocks."},
            {"role": "user", "content": normalized_user_prompt}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    # Pass reasoning_effort if supported by target endpoint (e.g. OpenAI/Ollama compatible)
    if ai_thinking_enabled:
        payload["reasoning_effort"] = ai_thinking_effort

    try:
        # Enforce a 60-second timeout to allow the model sufficient time to load and generate responses
        response = requests.post(url, headers=headers, json=payload, timeout=60.0)
        logger.info(f"[AI] - HTTP Response Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            content_str = data["choices"][0]["message"]["content"].strip()
            logger.info(f"[AI] - Raw Content Received: {content_str}")
            
            # Clean possible markdown wrap ```json ... ```
            if content_str.startswith("```"):
                lines = content_str.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    content_str = "\n".join(lines[1:-1])
            
            # Resilient JSON Processing Gate: heal the JSON string
            healed_content_str = heal_json_string(content_str)
            try:
                parsed_json = json.loads(healed_content_str)
            except Exception as parse_err:
                logger.error(f"[AI] - Parsing Failed - Error: {parse_err}. Raw: {content_str}. Healed: {healed_content_str}")
                parsed_json = json.loads(content_str)
            logger.info(f"[AI] - Parsed JSON: {parsed_json}")
            
            # Validate keys if requested
            if expected_keys:
                if not all(k in parsed_json for k in expected_keys):
                    logger.warning(f"[AI] - Parsing - Response missing expected keys {expected_keys}")
                    return None
            
            cache.set(cache_key, parsed_json, timeout=None)
            return parsed_json
        else:
            logger.error(f"[AI] - HTTP Error - Endpoint returned status {response.status_code}\nRESPONSE BODY:\n{response.text}")
    except requests.Timeout:
        logger.warning("[AI] - Timeout - Gemma server timed out.")
    except Exception as e:
        logger.error(f"[AI] - Error - Failed calling local Gemma: {str(e)}")
        
    return None


# Moved from top of file
FACTUAL_DICTIONARY = {
    'refined': 'Store refined commercial flour. High shelf stability and consistent protein levels, but stripped of bran and germ.',
    'milled': 'Freshly milled whole grain. Retains 100% of germ and bran oils. High enzyme activity and complex rustic flavor profile.',
    'grain_hard_red_spring': 'High-protein hard wheat. Strong, elastic gluten structure.',
    'grain_hard_red_winter': 'Moderate-high protein wheat. Balanced gluten elasticity and extensibility.',
    'grain_soft_white': 'Low-protein soft wheat. Weak, tender gluten structure.',
    'grain_hard_white': 'Mild, light-colored hard wheat. Structural strength without bitter red wheat tannins.',
    'grain_spelt': 'Ancient hulled wheat species. Extensible but weak gluten strength; water-absorbent.',
    'grain_kamut': 'Ancient Khorasan wheat. High protein, lower elasticity; absorbs water slowly.',
    'grain_rye': 'Ancient rye grass grain. High pentosan concentration and weak gluten strength.',
    'stand_mixer': 'Planetary stand mixer. Delivers intensive mechanical shearing, building fast gluten structures but adding heat.',
    'bread_machine': 'Automated high-torque chamber mixer. Fully enclosed, creating high friction heat and rapid development.',
    'food_processor': 'High-velocity steel blade shearing. Forces hydration and gluten alignment rapidly but risks blade damage.',
    'hand_beaters': 'Light whipping beaters. Aerates liquid and fat emulsions without building strong gluten networks.',
    'whisk': 'Manual aerating whisk. Incorporates gas bubbles into fluid batters to support leavening lift.',
    'spatula_bowl': 'Zero-friction manual mixing. Minimal mechanical energy transfer to prevent any accidental gluten formation.',
    'knead': 'Mechanical folding and stretching of dough to align glutenin and gliadin proteins into a structural matrix.',
    'cream': 'Aeration of solid fat and sugar. Traps micro-bubbles to form the foundation of crumb leavening.',
    'fold': 'Gentle folding layers the dough and develops structure without degassing. Crucial for retaining large, irregular open crumb cells.',
    'cut_in': 'Distribution of cold fat pieces into dry flour. Forms flat fat pockets for flaky pastry lamination.',
    'sheet': 'Compressing dough through rollers to achieve a uniform thin sheet, aligning starch and gluten strands.',
    'extrude': 'Forcing dense dough through a shaped die to form structured shapes under high compaction pressure.',
    'ambient': 'Countertop proofing. Relies on local ambient room temperature (70-75°F (21-24°C)) for steady biological activity.',
    'mat': 'Open heated proofing mat. Warms the bottom of the vessel to accelerate yeast and lactic acid production.',
    'box': 'Warm, humid enclosed proofing chamber. Maximizes biological activity while preventing surface skin drying.',
    'refrigerator': 'Cold retardation (34-40°F (1-4°C)). Solidifies fats and slows yeast while enzymes continue developing complex sugars.',
    'bench_rest': 'Relaxation rest under a damp cloth. Releases elastic tension in the gluten matrix to allow final shaping.',
    'cast-iron-dutch-oven': 'Heavy cast iron pot. Retains heat and traps steam released from the dough. Ensures optimal starch gelatinization and maximum oven spring.',
    'open-baking-stone-steel': 'High-conduction hearth surface. Transports heat immediately into the base of the loaf for maximum oven spring.',
    'standard-9x5-pan': 'Metal loaf pan. Restricts lateral movement, forcing the rising dough vertically into a uniform sandwich shape.',
    'perforated-baking-sheet': 'Airflow baking tray. Promotes dry skin dehydration on all sides, crucial for crispy pretzels or bagels.',
    'butter': 'Emulsified fat containing 80% fat, 18% water, and milk solids. Adds rich dairy flavor and tender crumb structures.',
    'unsalted_butter': 'Pure unsalted cream butter. Allows precise salt control while introducing emulsified dairy fats.',
    'salted_butter': 'Salted cream butter. Contributes dairy fats and adds a baseline salinity to the dough mixture.',
    'olive_oil': '100% monounsaturated plant fat. Highly fluid liquid state, coats gluten strands for a moist, extensible crumb.',
    'canola_oil': 'Neutral plant seed oil. Provides 100% pure fat coating to tenderize structures without clashing flavors.',
    'vegetable_oil': 'Clean liquid plant fat. Retains moisture in baked goods by keeping fat phase fluid at room temperature.',
    'whole_milk': 'Milky liquid containing 87% water, fat, sugar, and proteins. Enhances caramelization and softens crumb structures.',
    'almond_milk': 'Nut-based dairy substitute. Adds water and micro-solids, requiring slight liquid adjustments due to lack of animal fats.',
    'coconut_oil': 'Plant-based solid lipid. Solidifies at cooler room temperatures, imparting a faint tropical aroma and a melt-in-the-mouth crumb.',
    'avocado_oil': 'Neutral liquid lipid that remains fluid at room temperature. Coats gluten strands completely for a soft and long-lasting crumb.',
    'pure_water': 'Clean, zero-interference hydration. The absolute optimal choice for lean hearth loaves to keep the crumb airy and the crust crispy.',
    'heavy_cream': 'Immense dairy fat richness (37% fat) and milk sugars. Tenderizes the crumb dramatically, yielding an ultra-soft slice.',
    'buttermilk': 'Acidic dairy medium. Tenderizes gluten chemically and reacts with chemical leaveners for a flaky, tender structure.',
    'none': 'No binder. Relies purely on the gluten network and hydration matrix to establish structural integrity.',
    'whole_eggs': 'Rich binder contributing fat, moisture, and lecithin. Promotes rich browning and a soft, custard-like crumb.',
    'egg_whites': 'Pure albumin protein and hydration. Dries and solidifies during baking to create a taller, lighter, and crisper crust.',
    'aquafaba_vegan': 'Vegan binder made from legume starch liquid. Mimics the foam stability of egg whites but lacks animal protein fats.'
}
logger = logging.getLogger("grainlab.gemma")
ENGINE_FLAVORS = {
    "alkaline-bath": {
        1: [
            {"name": "Classic Salted Pretzel/Bagel", "desc": "A baseline standard profile featuring traditional crust browning and coarse sea salt finish."},
            {"name": "Cinnamon Raisin Swirl", "desc": "A sweet-spiced profile with sweet raisin inclusions throughout a dense, chewy crumb."},
            {"name": "Sesame Seed Crunch", "desc": "A nutty, toasted sesame seed coated crust pairing with a soft, low-hydration crumb."},
            {"name": "Garlic Parmesan Glaze", "desc": "A savory garlic infused dough with a crispy, parmesan-crusted outer shell."},
            {"name": "Honey Whole Wheat", "desc": "A mellow honey-sweetened bagel/pretzel base with high chewiness."}
        ],
        2: [
            {"name": "Jalapeno White Cheddar", "desc": "An advanced variation with spicy jalapeno slices and pockets of melted aged white cheddar."},
            {"name": "Malted Caramel Onion", "desc": "A modern savory profile featuring slow-caramelized sweet onion folding and malt glaze."},
            {"name": "Everything Bagel Herb", "desc": "An aromatic toasted garlic, onion, poppy seed, and herb crusted variation."},
            {"name": "Asiago Rosemary Crust", "desc": "An advanced formulation utilizing fresh rosemary infusion and baked asiago topping."},
            {"name": "Sweet Maple Pecan Glaze", "desc": "A sweet, dessert-inspired bagel/pretzel with maple syrup infusion and toasted pecans."}
        ]
    },
    "cakes-batters": {
        1: [
            {"name": "Vanilla Bean Sponge Cake", "desc": "A classic vanilla bean sponge with a light, airy crumb structure and high moisture retention."},
            {"name": "Double Chocolate Chip Muffins", "desc": "A rich dark chocolate batter loaded with chocolate chunks for rich meltability."},
            {"name": "Blueberry Lemon Zest Muffins", "desc": "A bright lemon-perfumed muffin base bursting with sweet whole blueberries."},
            {"name": "Spiced Carrot Walnut Cake", "desc": "A traditional spiced batter containing grated carrots and toasted walnuts for texture."},
            {"name": "Classic Golden Butter Cake", "desc": "A rich, tender butter cake with fine crumb and excellent structure."}
        ],
        2: [
            {"name": "Toasted Coconut Lime Cream Cake", "desc": "An advanced cake featuring fresh lime zest and coconut cream emulsions."},
            {"name": "Salted Caramel Banana Muffin", "desc": "A modern profile with caramelized banana paste and salted toffee swirl inserts."},
            {"name": "Red Velvet Espresso Infusion", "desc": "A sophisticated cocoa-red velvet cake elevated by espresso micro-crystals."},
            {"name": "Cardamom Pistachio Sponge", "desc": "An advanced delicate cake scented with ground cardamom and layered with toasted pistachios."},
            {"name": "Lavender Honey Poppyseed Cake", "desc": "A modern floral cake sweetened with lavender-infused honey and poppyseeds."}
        ]
    },
    "choux-paste": {
        1: [
            {"name": "Vanilla Bean Cream Puffs", "desc": "A traditional hollow choux shell filled with rich vanilla bean pastry cream."},
            {"name": "Classic Chocolate Glazed Eclairs", "desc": "Standard elongated choux shells topped with a glossy dark chocolate ganache."},
            {"name": "Salted Caramel Profiteroles", "desc": "Bite-sized choux puffs drizzled with warm, salty caramel glaze."},
            {"name": "Espresso Mocha Cream Puffs", "desc": "Standard puffs filled with mocha coffee-infused light custard cream."},
            {"name": "Lemon Curd Choux Puffs", "desc": "Traditional crisp choux filled with a tart, vibrant lemon curd."}
        ],
        2: [
            {"name": "Pistachio Praline Eclairs", "desc": "Advanced choux pastry filled with toasted pistachio praline paste and pastry cream."},
            {"name": "Hazelnut Gianduja Cream Puffs", "desc": "A modern variant filled with hazelnut-chocolate gianduja mousse."},
            {"name": "Raspberry Rose Chantilly Puff", "desc": "An advanced floral choux containing fresh raspberry compote and rosewater cream."},
            {"name": "Spiced Cardamom Pear Choux", "desc": "A modern choux pastry featuring poached pear cubes and cardamom cream."},
            {"name": "Dark Chocolate Grand Marnier Eclair", "desc": "Advanced orange-liqueur infused pastry cream in a dark chocolate shell."}
        ]
    },
    "cookies-shortbread": {
        1: [
            {"name": "Classic Chocolate Chip Cookie", "desc": "A baseline standard cookie prioritizing chocolate chips, balanced horizontal spread, and brown sugar chew."},
            {"name": "Golden Sugar Cookie", "desc": "Standard soft-baked cookie with a balanced white sugar ratio for crisp edges and chewy centers."},
            {"name": "Traditional Oatmeal Raisin", "desc": "Reliable rolled oats base bound by butter and eggs, generating a chewy, fibrous structure."},
            {"name": "Spiced Ginger Snaps", "desc": "Standard molasses-sweetened cookie with high crispness and regular surface cracks."},
            {"name": "Old-Fashioned Peanut Butter", "desc": "A dense, rich drop cookie using peanut paste fats to shorten gluten strands."}
        ],
        2: [
            {"name": "Triple-Valrhona Malted Cookie", "desc": "Advanced recipe utilizing malted milk powder and three chocolate chunk inclusions."},
            {"name": "Lactic-Fermented Buttermilk Cookie", "desc": "Modern profile incorporating buttermilk powder for a faint lactic tang and tender center."},
            {"name": "Espresso-Infused Brown Butter", "desc": "Advanced cookie with espresso micro-crystals dispersed throughout browned butter fat."},
            {"name": "Salted Toffee Pecan drop cookie", "desc": "Advanced cookie containing homemade toasted pecan brittle and butter toffee shards."},
            {"name": "Chilled Honey-Lavender Cookie", "desc": "Modern floral cookie sweetened with wildflower honey and infused lavender."}
        ]
    },
    "enriched-soft": {
        1: [
            {"name": "Classic Buttery Brioche", "desc": "A rich, egg-and-butter enriched dough yielding an ultra-soft, pillowy feather crumb."},
            {"name": "Cinnamon Sugar Swirl Buns", "desc": "Standard sweet rolls filled with dark brown sugar and aromatic cinnamon paste."},
            {"name": "Cardamom Spiced Sweet Bread", "desc": "A traditional Scandinavian recipe scented with freshly ground cardamom seed."},
            {"name": "Honey Glazed Soft Dinner Rolls", "desc": "Baseline dinner rolls with a shiny honey glaze and exceptionally soft interior."},
            {"name": "Orange Zest Morning Buns", "desc": "Sweet morning buns infused with refreshing orange zest sugar."}
        ],
        2: [
            {"name": "Chocolate Hazelnut Babka", "desc": "Advanced twisted loaf layered with dark chocolate ganache and hazelnut spread."},
            {"name": "Pecan Sticky Buns", "desc": "Advanced morning pastry baked in a pool of caramelized butter, honey, and pecans."},
            {"name": "Vanilla Bean Glazed Yeasted Donuts", "desc": "Modern light yeasted dough, fried and dipped in a real vanilla bean glaze."},
            {"name": "Maple Pecan Braided Crown", "desc": "An advanced braided crown dough filled with pure maple butter and chopped pecans."},
            {"name": "Sourdough Enriched Swirl Loaf", "desc": "Modern sourdough brioche base utilizing wild yeast acidity to balance butter richness."}
        ]
    },
    "flatbreads-griddles": {
        1: [
            {"name": "Garlic Herb Naan", "desc": "A classic flatbread brushed with garlic-infused ghee and fresh cilantro leaves."},
            {"name": "Rosemary Sea Salt Focaccia", "desc": "Traditional dimpled olive oil flatbread topped with sea salt flakes and rosemary."},
            {"name": "Toasted Sesame Pita Bread", "desc": "A baseline pocket pita coated with nutty toasted sesame seeds."},
            {"name": "Scallion Green Onion Flatbread", "desc": "Standard griddle flatbread layered with green scallions and sesame oil."},
            {"name": "Spicy Chili Flakes Roti", "desc": "Traditional thin unleavened flatbread seasoned with red chili flakes."}
        ],
        2: [
            {"name": "Honey Butter English Crumpets", "desc": "Advanced high-hydration griddle bread with characteristic honeycomb internal holes."},
            {"name": "Cumin Spiced Garlic Pita", "desc": "A modern pocket bread seasoned with roasted cumin and garlic paste."},
            {"name": "Smoked Paprika Olive Flatbread", "desc": "Advanced flatbread topped with kalamata olives and smoked Spanish paprika."},
            {"name": "Blue Cheese Fig Focaccia", "desc": "A modern flavor profile featuring sweet fig jam and aged blue cheese crumbs."},
            {"name": "Caramelized Shallot Herb Flatbread", "desc": "Advanced griddle flatbread topped with slow-cooked sweet shallots."}
        ]
    },
    "fresh-pasta-noodles": {
        1: [
            {"name": "Classic Egg Semolina Fettuccine", "desc": "Traditional rich golden pasta utilizing whole egg yolks and durum semolina flour."},
            {"name": "Spinach Herb Green Tagliatelle", "desc": "A vibrant green spinach-puree infused dough with fresh garden herbs."},
            {"name": "Roasted Garlic Ravioli Dough", "desc": "Standard pasta sheet seasoned with sweet roasted garlic paste."},
            {"name": "Cracked Black Pepper Pappardelle", "desc": "Egg pasta dough studded with coarse cracked black pepper grains."},
            {"name": "Vibrant Tomato Basil Penne", "desc": "A red-hued tomato paste and fresh basil infused pasta dough."}
        ],
        2: [
            {"name": "Beet Root Pink Lasagna Sheets", "desc": "Advanced pasta sheets colored with concentrated sweet beet juice."},
            {"name": "Squid Ink Black Linguine", "desc": "A modern savory seafood pasta colored and flavored with natural squid ink."},
            {"name": "Porcini Mushroom Fettuccine", "desc": "Advanced pasta dough incorporating dehydrated wild porcini mushroom powder."},
            {"name": "Golden Saffron Capellini", "desc": "A premium pasta dough infused with luxury saffron threads and white wine."},
            {"name": "Herb-Laminated Silk Handkerchiefs", "desc": "Advanced pasta with whole parsley leaves pressed between translucent sheets."}
        ]
    },
    "fried-doughs": {
        1: [
            {"name": "Glazed Vanilla Ring Donut", "desc": "A baseline standard donut with a light, airy crumb and vanilla sugar glaze."},
            {"name": "Cinnamon Sugar Churros", "desc": "Crispy ridged fried dough coated in sweet cinnamon sugar."},
            {"name": "Raspberry Jelly Filled Beignets", "desc": "Traditional square puffed donuts filled with seedless raspberry jam."},
            {"name": "Chocolate Frosted Sprinkles Donut", "desc": "A rich yeasted donut topped with dark chocolate icing."},
            {"name": "Powdered Sugar Funnel Cake", "desc": "Classic crispy fried batter ribbons dusted with powdered sugar."}
        ],
        2: [
            {"name": "Maple Bacon Glazed Fritter", "desc": "An advanced yeast donut topped with maple glaze and crispy smoked bacon bits."},
            {"name": "Apple Cider Spiced Donut", "desc": "A modern cake donut flavored with boiled apple cider reduction and fall spices."},
            {"name": "Blueberry Glazed Cruller", "desc": "Advanced choux-based fried ring donut with a sweet blueberry glaze."},
            {"name": "Meyer Lemon Filled Berliner", "desc": "A modern Berliner donut filled with tart Meyer lemon curd."},
            {"name": "Cardamom Spiced Beignets", "desc": "Advanced beignets flavored with ground cardamom and orange blossom honey."}
        ]
    },
    "lean-crusty": {
        1: [
            {"name": "Classic Sourdough Boule", "desc": "A traditional country sourdough boule with an open, airy crumb and blistered crust."},
            {"name": "Roasted Garlic Herb Batard", "desc": "A baseline lean batard filled with roasted sweet garlic cloves and fresh herbs."},
            {"name": "Rosemary Sea Salt French Loaf", "desc": "A fragrant, long loaf topped with fresh rosemary and sea salt flakes."},
            {"name": "Black Olive Oregano Batard", "desc": "Standard Mediterranean loaf filled with sliced kalamata olives and oregano."},
            {"name": "Simple Hearth Sourdough Batard", "desc": "A traditional, highly reliable sourdough batard prioritizing pure grain expression."}
        ],
        2: [
            {"name": "Fig & Walnut Sourdough Boule", "desc": "Advanced modern boule combining sweet dried black mission figs and toasted walnuts."},
            {"name": "Cranberry Pecan Hearth Loaf", "desc": "A modern flavor profile featuring tart dried cranberries and toasted pecans."},
            {"name": "Toasted Sesame Crust Sourdough", "desc": "An advanced sourdough loaf coated completely in toasted sesame seeds for a nutty crunch."},
            {"name": "Beer Batter Sourdough Rye", "desc": "A modern dark rye bread utilizing craft stout beer instead of water for hydration."},
            {"name": "Multigrain Honey Seeded Loaf", "desc": "Advanced lean bread packed with pre-soaked flax, sunflower, and pumpkin seeds."}
        ]
    },
    "pastry-lamination": {
        1: [
            {"name": "Classic Butter Croissant", "desc": "Traditional laminated pastry featuring hundreds of paper-thin buttery layers."},
            {"name": "Pain au Chocolat", "desc": "A baseline standard laminated roll filled with sweet dark chocolate bars."},
            {"name": "Cinnamon Swirl Danish", "desc": "Standard laminated danish dough swirled with sweet cinnamon butter fill."},
            {"name": "Almond Frangipane Turnover", "desc": "Traditional turnover filled with sweet almond frangipane paste."},
            {"name": "Raspberry Jam Laminated Twist", "desc": "A simple laminated twist filled with red raspberry jam."}
        ],
        2: [
            {"name": "Meyer Lemon Cheese Danish", "desc": "Advanced laminated danish topped with sweet cream cheese and tart lemon curd."},
            {"name": "Cardamom Twist Laminated Danish", "desc": "A modern danish flavored with Swedish cardamom sugar and orange glaze."},
            {"name": "Maple Pecan Plait Danish", "desc": "Advanced braided danish pastry filled with maple syrup butter and toasted pecans."},
            {"name": "Vanilla Custard Fruit Danish", "desc": "Advanced danish filled with vanilla pastry cream and seasonal fruits."},
            {"name": "Apple Chausson Laminated Turnover", "desc": "A modern flaky turnover filled with caramelized apple compote."}
        ]
    },
    "quick-breads-scones": {
        1: [
            {"name": "Banana Walnut Quick Bread", "desc": "A traditional sweet quick bread loaded with ripe mashed bananas and walnuts."},
            {"name": "Blueberry Lemon Scones", "desc": "Classic flaky scones bursting with blueberries and glazed with fresh lemon juice."},
            {"name": "Cranberry Sweet Orange Bread", "desc": "Standard quick bread featuring tart dried cranberries and sweet orange zest."},
            {"name": "Spiced Pumpkin Scones", "desc": "A baseline pumpkin scone flavored with ginger, nutmeg, and cinnamon spices."},
            {"name": "Classic Cheddar Chive Scones", "desc": "Standard savory scones layered with sharp cheddar cheese and fresh chives."}
        ],
        2: [
            {"name": "Zucchini Chocolate Chip Quick Bread", "desc": "Advanced quick bread with shredded zucchini for moisture and dark chocolate chips."},
            {"name": "Maple Pecan Scones", "desc": "Modern scones sweetened with maple syrup and packed with toasted pecans."},
            {"name": "Cinnamon Apple Streusel Bread", "desc": "Advanced quick bread topped with apple slices and a brown sugar streusel."},
            {"name": "Lemon Glazed Poppyseed Bread", "desc": "A modern quick bread with blue poppyseeds and a tart lemon icing glaze."},
            {"name": "Ginger Molasses Scones", "desc": "Advanced spiced scones flavored with dark molasses and candied ginger."}
        ]
    }
}
CATEGORY_TO_ENGINE = {
    "lean-crusty": "hearth",
    "enriched-soft": "pan",
    "alkaline-bath": "bath",
    "flatbreads-griddles": "flat",
    "quick-breads-scones": "quick",
    "cakes-batters": "batter",
    "pastry-lamination": "pastry",
    "choux-paste": "choux",
    "cookies-shortbread": "cookie",
    "fried-doughs": "fry",
    "fresh-pasta-noodles": "pasta",
}


def load_grain_registry():
    import os
    import json
    path = os.path.join(os.path.dirname(__file__), "grain_registry.json")
    with open(path, "r") as f:
        return json.load(f)

def get_grain_registry_profile(grain_name: str) -> dict:
    import re
    slug = re.sub(r'[^a-z0-9]', '_', grain_name.lower()).strip('_')
    slug = re.sub(r'_+', '_', slug)
    try:
        registry = load_grain_registry()
        grains = registry.get("grains", {})
        if slug in grains:
            return grains[slug]["intrinsic_chemical_profile"]
        for k, val in grains.items():
            if k in slug or slug in k:
                return val["intrinsic_chemical_profile"]
    except Exception:
        pass
    return {
        "crude_protein_percentage": "12.0%",
        "gluten_binding_capacity": "high",
        "pentosan_concentration": "low_standard",
        "bran_tannin_profile": "none_neutral"
    }

def get_archetype_mechanics(engine, active_archetype_id=None, preset_slug=None) -> tuple[str, dict]:
    archetypes = getattr(engine, "archetypes", {})
    archetype_data = None
    archetype_display = "Default Archetype"
    
    if active_archetype_id and active_archetype_id in archetypes:
        archetype_data = archetypes[active_archetype_id]
        archetype_display = archetype_data.get("label", active_archetype_id)
    elif preset_slug:
        slug_lower = preset_slug.lower()
        for k, v in archetypes.items():
            k_clean = k.replace("_", "-")
            label_clean = v.get("label", "").lower()
            if k_clean in slug_lower or slug_lower in k_clean or label_clean in slug_lower:
                archetype_data = v
                active_archetype_id = k
                archetype_display = v.get("label", k)
                break
                
    if archetype_data is None and archetypes:
        first_key = list(archetypes.keys())[0]
        archetype_data = archetypes[first_key]
        active_archetype_id = first_key
        archetype_display = archetype_data.get("label", first_key)

    if archetype_data:
        return archetype_display, archetype_data.get("target_archetype_mechanics", {
            "required_gluten_elasticity": "high_retention",
            "desired_horizontal_flow": "controlled_expansion",
            "moisture_lipid_ratio": "balanced_emulsion",
            "optimal_protein_window": "11.0% - 13.0%"
        })
    
    return "Default Archetype", {
        "required_gluten_elasticity": "high_retention",
        "desired_horizontal_flow": "controlled_expansion",
        "moisture_lipid_ratio": "balanced_emulsion",
        "optimal_protein_window": "11.0% - 13.0%"
    }

def get_contextual_pitfalls(category_slug: str, effective_hydration: float, grain_type: str, preset_slug: str = None) -> list:
    """
    Retrieves pitfall analysis from Gemma, falling back to local python rules.
    """
    from apps.core.gemma.core_client import _is_ai_enabled
    if _is_ai_enabled():
        system_prompt = (
            "Analyze the recipe variables and identify potential baking pitfalls "
            "or custom step additions (e.g., pretzel soda boiling, high-hydration sticky dough). "
            "You MUST tailor your critique specifically to the active baking category and preset. "
            "Do NOT mention ingredients or processes (e.g., yeast, rising, kneading, proofing, bread ovens, steam) that are not part of the target recipe class. For example, do not mention yeast or proofing for cookies/cakes, and do not mention cookie spread or creaming for sourdough/pizza. "
            "Return a JSON object containing a list called 'pitfalls' where each item has "
            "'title' and 'message' keys."
        )
        user_prompt = json.dumps({
            "category": category_slug,
            "hydration_pct": effective_hydration,
            "grain_type": grain_type,
            "preset": preset_slug,
        })
        
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["pitfalls"])
        if result and isinstance(result.get("pitfalls"), list):
            return result["pitfalls"]

    # Fallback to local python rule engine
    return get_local_contextual_pitfalls(category_slug, effective_hydration, grain_type, preset_slug)

def get_sensory_benchmark(grain_type: str, flour_maturity: str, effective_hydration: float, category_slug: str = None, preset_slug: str = None) -> str:
    """
    Retrieves sensory text from Gemma, falling back to local description mappings.
    """
    from apps.core.gemma.core_client import _is_ai_enabled
    if _is_ai_enabled():
        system_prompt = (
            "You are a baking science expert. Synthesize a descriptive sensory benchmark describing what the mixture (dough, batter, or paste) should look "
            "and feel like (texture, touch resilience, structure, visual indicators) "
            "based on the flour maturity and grain type. "
            "You MUST tailor your description specifically to the active recipe category and preset. Do NOT mention ingredients or processes "
            "(e.g., yeast, rising, kneading, proofing, bubbles) that are not part of the target recipe class. For example, do not mention rising or yeast for cookies, and do not mention cookie spread or creaming for sourdough."
            "Return a JSON object with the key 'sensory_description'."
        )
        user_prompt = json.dumps({
            "grain_type": grain_type,
            "flour_maturity": flour_maturity,
            "hydration": effective_hydration,
            "category": category_slug,
            "preset": preset_slug,
        })
        
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["sensory_description"])
        if result and result.get("sensory_description"):
            return result["sensory_description"]

    # Fallback
    return get_local_sensory_benchmark(grain_type, flour_maturity, effective_hydration, category_slug, preset_slug)
