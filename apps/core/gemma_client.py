import json
import logging
import requests
from django.conf import settings
from apps.core.models import SystemSetting
from apps.core.bakers_math import (
    get_local_sensory_benchmark,
    get_local_contextual_pitfalls,
)

FACTUAL_DICTIONARY = {
    'refined': 'Store refined commercial flour. High shelf stability and consistent protein levels, but stripped of bran and germ.',
    'milled': 'Freshly milled whole grain. Retains 100% of germ and bran oils. High enzyme activity and complex rustic flavor profile.',
    'grain_hard_red_spring': 'High-protein hard wheat. Strong, elastic gluten structure suitable for high-rise hearth loaves.',
    'grain_hard_red_winter': 'Moderate-high protein wheat. Balanced gluten elasticity and extensibility, highly versatile.',
    'grain_soft_white': 'Low-protein soft wheat. Weak, tender gluten structure ideal for tender pastries, cakes, and cookies.',
    'grain_hard_white': 'Mild, light-colored hard wheat. Provides structural strength without the bitter red wheat tannins.',
    'grain_spelt': 'Ancient hulled wheat species. Very extensible but weak gluten strength; highly water-absorbent.',
    'grain_kamut': 'Ancient Khorasan wheat. Rich, sweet flavor, high protein, but lower elasticity; absorbs water slowly.',
    'grain_rye': 'Ancient rye grass grain. High pentosans and weak gluten. Produces sticky, dense, complex savory doughs.',
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
    'ambient': 'Countertop proofing. Relies on local ambient room temperature (70-75°F) for steady biological activity.',
    'mat': 'Open heated proofing mat. Warms the bottom of the vessel to accelerate yeast and lactic acid production.',
    'box': 'Warm, humid enclosed proofing chamber. Maximizes biological activity while preventing surface skin drying.',
    'refrigerator': 'Cold retardation (34-40°F). Solidifies fats and slows yeast while enzymes continue developing complex sugars.',
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

def _get_val(obj, key, default=None):
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def _is_ai_enabled() -> bool:
    """Checks if AI integration is active."""
    # Check both environment variables and database settings
    db_enabled = SystemSetting.get_val("ai_enabled", "False").lower() in ("true", "1", "t")
    env_mock = getattr(settings, "MOCK_MODE", True)
    return db_enabled and not env_mock


def _get_api_config() -> tuple[str, str]:
    """Retrieves API details from SystemSettings."""
    url = SystemSetting.get_val("ai_api_url", "http://host.docker.internal:11434/v1")
    model = SystemSetting.get_val("ai_model_name", "gemma:12b")
    # Clean completions URL if it doesn't end with chat/completions
    if not url.endswith("/chat/completions"):
        url = url.rstrip("/") + "/chat/completions"
    return url, model


def call_gemma_api(system_prompt: str, user_prompt: str, expected_keys: list = None) -> dict | None:
    """
    Submits a structured prompt to local Gemma and parses the JSON response.
    Returns None if any step fails.
    """
    if not _is_ai_enabled():
        return None

    url, model = _get_api_config()
    headers = {
        "Content-Type": "application/json"
    }
    
    # Force JSON format if supported
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt + " You MUST respond with raw JSON ONLY. No markdown formatting, no codeblocks."},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }

    try:
        # Enforce a strict 3-second timeout for responsive HTTP cycles
        response = requests.post(url, headers=headers, json=payload, timeout=3.0)
        if response.status_code == 200:
            data = response.json()
            content_str = data["choices"][0]["message"]["content"].strip()
            
            # Clean possible markdown wrap ```json ... ```
            if content_str.startswith("```"):
                lines = content_str.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    content_str = "\n".join(lines[1:-1])
            
            parsed_json = json.loads(content_str)
            
            # Validate keys if requested
            if expected_keys:
                if not all(k in parsed_json for k in expected_keys):
                    logger.warning(f"[AI] - Parsing - Response missing expected keys {expected_keys}")
                    return None
                    
            return parsed_json
        else:
            logger.error(f"[AI] - HTTP Error - Endpoint returned status {response.status_code}")
    except requests.Timeout:
        logger.warning("[AI] - Timeout - Gemma server timed out.")
    except Exception as e:
        logger.error(f"[AI] - Error - Failed calling local Gemma: {str(e)}")
        
    return None


# 1. Contextual Pitfall Analysis & Special Step Injection
def get_contextual_pitfalls(category_slug: str, effective_hydration: float, grain_type: str, preset_slug: str = None) -> list:
    """
    Retrieves pitfall analysis from Gemma, falling back to local python rules.
    """
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


# 2. Custom Sensory Benchmark Synthesizer
def get_sensory_benchmark(grain_type: str, flour_maturity: str, effective_hydration: float, category_slug: str = None, preset_slug: str = None) -> str:
    """
    Retrieves sensory text from Gemma, falling back to local description mappings.
    """
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


# 3. Closed-Loop Chemistry Re-Balancing (Substitutions)
def get_substitution_offset(original_ing: str, substitute_ing: str, current_recipe: dict) -> dict:
    """
    Retrieves mathematical hydration/fat offsets from Gemma, falling back to local logic.
    """
    if _is_ai_enabled():
        system_prompt = (
            "Analyze an ingredient swap (substitution) in baking. Deconstruct the substitute "
            "into raw water, fat, and sugar contents. Return a JSON object with: "
            "'water_offset_pct' (float, hydration coefficient offset), "
            "'fat_offset_pct' (float, fat coefficient offset), "
            "'sugar_offset_pct' (float, sugar coefficient offset), "
            "and 'explanation' (string details)."
        )
        user_prompt = json.dumps({
            "original": original_ing,
            "substitute": substitute_ing,
            "current_hydration": current_recipe.get("effective_hydration_pct", 70.0) / 100.0,
            "current_fat": current_recipe.get("effective_fat_pct", 0.0) / 100.0,
            "current_sugar": current_recipe.get("effective_sugar_pct", 0.0) / 100.0,
        })
        
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["water_offset_pct", "fat_offset_pct"])
        if result:
            return result

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


# 4. Structured Milling Profile & Sourdough Diagnostic Calibration
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
    
    if _is_ai_enabled():
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

    if _is_ai_enabled():
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


def optimize_grain_blend(preset_slug: str, preset_name: str, active_berries: list) -> tuple[dict, str | None] | None:
    """
    Queries Gemma model to optimize the percentage blend of active wheat berries
    for a specific bread preset.
    Returns: (shares_dict, structural_warning) or None
    """
    if not _is_ai_enabled():
        return None
        
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


def get_grain_advisory_ai(preset_slug: str, category_slug: str = None) -> dict | None:
    """
    Submits a prompt to Gemma asking for evaluation of available kitchen inventory.
    """
    if _is_ai_enabled():
        from apps.core.models import WheatBerry, BreadPreset
        from grainlab.engines import router
        import json
        
        preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
        if not category_slug and preset and preset.dough_category:
            category_slug = preset.dough_category.slug
        engine = router.get_engine_for_preset(preset_slug, category_slug)
        
        active_berries = list(WheatBerry.objects.filter(is_active=True))
        if not active_berries:
            return {"grain_evaluations": []}
            
        system_prompt = (
            "You are a baking science expert. Analyze the given bread/pastry preset and evaluate the available wheat berries in the kitchen inventory.\n"
            "[CRITICAL RULE: CULINARY SOVEREIGNTY]\n"
            "Rely SOLELY on your native baking science knowledge and real-world artisan baking physics. "
            "Do NOT apply standard/generic wheat constraints to ancient or non-standard grains (e.g., Rye, Spelt, Einkorn) if doing so contradicts artisan baking chemistry. "
            "For example, Rye is highly recommended for cookies due to pentosans blocking gluten to maximize cookie tenderness, even though its protein is low. "
            "Evaluate each grain and assign:\n"
            "- 'recommended': Grains that are ideal for the preset.\n"
            "- 'sub-optimal': Grains that are usable but not ideal, or require workflow/hydration adjustments.\n"
            "- 'not-recommended': Grains that are inappropriate for the preset's required gluten structure, texture, or flavor characteristics.\n"
            "\n"
            "Return a JSON object matching this schema:\n"
            "{\n"
            "  \"grain_evaluations\": [\n"
            "    {\n"
            "      \"grain_id\": \"string (UUID of the grain)\",\n"
            "      \"tier\": \"recommended | sub-optimal | not-recommended\",\n"
            "      \"reasoning\": \"A concise 1-2 sentence analytical explanation tracking exactly how the grain alters the requested texture, and how its flavor profile impacts the target flavor profile.\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        
        payload = {
            "preset_slug": preset_slug,
            "preset_name": preset.name if preset else preset_slug,
            "category_slug": category_slug,
            "inventory": [
                {
                    "id": str(wb.id),
                    "name": wb.name,
                    "protein": wb.protein_content,
                    "hardness": wb.hardness,
                    "notes": wb.notes
                }
                for wb in active_berries
            ]
        }
        
        user_prompt = json.dumps(payload)
        res = call_gemma_api(system_prompt, user_prompt, expected_keys=["grain_evaluations"])
        if res and isinstance(res, dict) and "grain_evaluations" in res:
            return res
            
    return None


def evaluate_single_grain(wb, engine) -> dict:
    """
    Evaluates a single grain against the engine's protein and tannin rules.
    """
    p_min = getattr(engine, "target_protein_min", 11.0)
    p_max = getattr(engine, "target_protein_max", 13.0)
    g_behav = getattr(engine, "gluten_behavior", "standard")
    flavor_affinity = getattr(engine, "flavor_affinity", "")
    t_sens = getattr(engine, "tannin_sensitive", False)

    name = wb.name
    prot = wb.protein_content
    hard = wb.hardness

    # Heuristic 1: Structure/Protein Tier
    is_in_range = p_min <= prot <= p_max
    is_within_tolerance = (p_min - 1.5) <= prot <= (p_max + 1.5)
    
    # Hardness validation
    hardness_ok = True
    if p_min >= 11.5:  # Bread engines generally require hard/durum
        if hard not in ["hard", "durum"]:
            hardness_ok = False
    elif p_max <= 10.5:  # Weak engines (cookies/cake/quick) generally require soft
        if hard != "soft":
            hardness_ok = False

    if is_in_range and hardness_ok:
        base_tier = "recommended"
    elif is_within_tolerance:
        base_tier = "sub-optimal"
    else:
        base_tier = "not-recommended"

    # Heuristic 2: Tannin penalty
    is_tannin_heavy = any(x in name.lower() for x in ["red", "rye", "spelt", "einkorn"])
    final_tier = base_tier
    penalty_applied = False
    if t_sens and is_tannin_heavy:
        penalty_applied = True
        if base_tier == "recommended":
            final_tier = "sub-optimal"
        elif base_tier == "sub-optimal":
            final_tier = "not-recommended"

    # Analytical reasoning string construction
    if final_tier == "recommended":
        reasoning = f"At {prot}% protein content, {name} fits the {engine.name} target range ({p_min}%-{p_max}%) for optimal gluten behavior. Its sweet/neutral profile matches the recipe flavor."
    elif final_tier == "sub-optimal":
        if penalty_applied and is_in_range:
            reasoning = f"At {prot}% protein, {name} has ideal strength for this bake, but its tannin-rich red/rustic bran flavor profile clashes with this sweet/neutral recipe, dropping it to sub-optimal."
        else:
            reasoning = f"At {prot}% protein, {name} is slightly outside the ideal target range ({p_min}%-{p_max}%) for {engine.name}, which will require minor hydration adjustments."
    else:
        if penalty_applied:
            reasoning = f"At {prot}% protein, {name} is sub-optimal in strength and its bitter/astringent tannins clash aggressively with the sweet/neutral flavor profile."
        else:
            reasoning = f"At {prot}% protein, {name} completely violates the {engine.name} target range ({p_min}%-{p_max}%), which will cause gas retention failure or excessive toughness."

    return {
        "tier": final_tier,
        "reasoning": reasoning
    }


def get_local_grain_advisory(preset_slug: str, category_slug: str = None) -> dict:
    """
    Local fallback logic performing programmatic evaluation of kitchen inventory 
    using the active sub-engine heuristics.
    """
    from apps.core.models import WheatBerry, BreadPreset
    from grainlab.engines import router

    preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
    if not category_slug and preset and preset.dough_category:
        category_slug = preset.dough_category.slug
    engine = router.get_engine_for_preset(preset_slug, category_slug)

    active_berries = list(WheatBerry.objects.filter(is_active=True))
    evaluations = []

    for wb in active_berries:
        res = evaluate_single_grain(wb, engine)
        evaluations.append({
            "grain_id": str(wb.id),
            "tier": res["tier"],
            "reasoning": res["reasoning"]
        })

    return {
        "grain_evaluations": evaluations
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

ENGINE_GEOMETRIES = {
    "hearth": {
        "cast-iron-dutch-oven": {
            "status": "recommended",
            "advisory_label": "Direct conductive high-heat radiant envelope.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "no-change"}
        },
        "open-baking-stone-steel": {
            "status": "recommended",
            "advisory_label": "Maximum surface expansion; requires ambient steam injection.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "force-on"}
        },
        "standard-9x5-pan": {
            "status": "sub-optimal",
            "advisory_label": "Restricts lateral expansion; forces a tight, non-traditional crumb format.",
            "profile_adjustments": {"oven_temp_offset_f": -25, "bake_time_offset_m": 5, "steam_override": "force-off"}
        }
    },
    "pan": {
        "standard-9x5-pan": {
            "status": "recommended",
            "advisory_label": "Provides essential sidewall support for fragile, high-rising enriched crumbs.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "no-change"}
        },
        "pullman-pan-lidded": {
            "status": "recommended",
            "advisory_label": "Restricts vertical expansion to create perfectly square slice structures.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 5, "steam_override": "force-off"}
        },
        "individual-portion-sheet": {
            "status": "recommended",
            "advisory_label": "Optimal surface airflow for uniform bun/roll stabilization.",
            "profile_adjustments": {"oven_temp_offset_f": 15, "bake_time_offset_m": -10, "steam_override": "no-change"}
        }
    },
    "bath": {
        "perforated-baking-sheet": {
            "status": "recommended",
            "advisory_label": "Maximizes bottom crust airflow to flash-set the gelatinized alkaline skin.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "no-change"}
        },
        "standard-silicon-mat-sheet": {
            "status": "sub-optimal",
            "advisory_label": "Prevents sticking, but traps bottom moisture, softening the lower crust boundary.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 5, "steam_override": "no-change"}
        }
    },
    "flat": {
        "heavy-cast-iron-skillet": {
            "status": "recommended",
            "advisory_label": "High conduction intense floor-heat for rapid vapor-pocket puffing.",
            "profile_adjustments": {"oven_temp_offset_f": 25, "bake_time_offset_m": -5, "steam_override": "force-off"}
        },
        "high-heat-oven-stone": {
            "status": "recommended",
            "advisory_label": "Radiant flash-bake capability.",
            "profile_adjustments": {"oven_temp_offset_f": 50, "bake_time_offset_m": -8, "steam_override": "no-change"}
        }
    },
    "quick": {
        "standard-8x4-loaf-pan": {
            "status": "recommended",
            "advisory_label": "Direct core heat conduction for thick, chemically leavened batters.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "no-change"}
        },
        "muffin-cupcake-tin": {
            "status": "recommended",
            "advisory_label": "Rapid perimeter setting, maximizing crumb tenderness.",
            "profile_adjustments": {"oven_temp_offset_f": 15, "bake_time_offset_m": -15, "steam_override": "no-change"}
        },
        "individual-wedge-sheet": {
            "status": "recommended",
            "advisory_label": "Maximizes exterior flaky edge crusting for scones.",
            "profile_adjustments": {"oven_temp_offset_f": 10, "bake_time_offset_m": -10, "steam_override": "no-change"}
        }
    },
    "batter": {
        "straight-sided-round-tin": {
            "status": "recommended",
            "advisory_label": "Even structural expansion and predictable vertical scaling.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "no-change"}
        },
        "high-border-sheet-pan": {
            "status": "recommended",
            "advisory_label": "Uniform surface volume distribution for sheet slicing.",
            "profile_adjustments": {"oven_temp_offset_f": 10, "bake_time_offset_m": -10, "steam_override": "no-change"}
        },
        "cupcake-liner-matrix": {
            "status": "recommended",
            "advisory_label": "High surface area deployment for rapid protein coagulation.",
            "profile_adjustments": {"oven_temp_offset_f": 20, "bake_time_offset_m": -18, "steam_override": "no-change"}
        }
    },
    "pastry": {
        "perforated-sheet-air-mat": {
            "status": "recommended",
            "advisory_label": "Instant heat transfer to flash-vaporize layered butter sheets before melting occurs.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "no-change"}
        },
        "fluted-ring-tart-pan": {
            "status": "recommended",
            "advisory_label": "Structural wall support for short-crust fat distribution layouts.",
            "profile_adjustments": {"oven_temp_offset_f": -10, "bake_time_offset_m": 5, "steam_override": "force-off"}
        }
    },
    "choux": {
        "extrusion-piping-sheet": {
            "status": "recommended",
            "advisory_label": "Perfect non-stick release baseline matching thermal steam-lift dynamics.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "no-change"}
        }
    },
    "cookie": {
        "heavy-aluminum-sheet": {
            "status": "recommended",
            "advisory_label": "Balanced heat absorption preventing bottom scorching while driving uniform horizontal fat spread.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "no-change"}
        },
        "continuous-bar-pan": {
            "status": "sub-optimal",
            "advisory_label": "Concentrates perimeter mass into a continuous sheet block. Requires reduced bake temperature and extended duration to ensure the core sets fully without burning the edges.",
            "profile_adjustments": {"oven_temp_offset_f": -25, "bake_time_offset_m": 15, "steam_override": "force-off"}
        }
    },
    "fry": {
        "high-volume-oil-vat": {
            "status": "recommended",
            "advisory_label": "Extreme thermal mass retention keeping liquid fats stable during dough injection.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "force-off"}
        }
    },
    "pasta": {
        "mechanical-sheeter": {
            "status": "recommended",
            "advisory_label": "Gradual reduction tracking to thin structural pasta film specifications.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "force-off"}
        },
        "high-pressure-dies": {
            "status": "recommended",
            "advisory_label": "High compaction shaping matrix.",
            "profile_adjustments": {"oven_temp_offset_f": 0, "bake_time_offset_m": 0, "steam_override": "force-off"}
        }
    }
}

def get_geometry_advisory(preset_slug: str, preset_name: str, category_slug: str, form_factor_slug: str) -> dict:
    """
    Evaluates form factor suitability for the given recipe preset and category using Gemma.
    Falls back to a local heuristic dict if offline, disabled, or API error.
    """
    engine_slug = CATEGORY_TO_ENGINE.get(category_slug, "base")
    
    fallback_data = ENGINE_GEOMETRIES.get(engine_slug, {}).get(form_factor_slug, {
        "status": "recommended",
        "advisory_label": f"Standard baking geometry for {preset_name or category_slug}.",
        "profile_adjustments": {
            "oven_temp_offset_f": 0,
            "bake_time_offset_m": 0,
            "steam_override": "no-change"
        }
    })
    
    if not _is_ai_enabled():
        return {
            "geometry_evaluation": fallback_data
        }

    system_prompt = (
        "You are an expert baking science assistant. Evaluate the suitability of the selected baking geometry (form factor) "
        "for the active recipe type and return a structured JSON response.\n"
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
        f"bake time offset (minutes), and steam override choice. The default baseline parameters for this form factor are: "
        f"status = '{fallback_data['status']}', temp offset = {fallback_data['profile_adjustments']['oven_temp_offset_f']}°F, "
        f"time offset = {fallback_data['profile_adjustments']['bake_time_offset_m']}m, steam override = '{fallback_data['profile_adjustments']['steam_override']}'. "
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
            oven_temp_offset = int(adjustments.get("oven_temp_offset_f", fallback_data["profile_adjustments"]["oven_temp_offset_f"]))
            bake_time_offset = int(adjustments.get("bake_time_offset_m", fallback_data["profile_adjustments"]["bake_time_offset_m"]))
            steam_override = adjustments.get("steam_override", fallback_data["profile_adjustments"]["steam_override"])
            if steam_override not in ["no-change", "force-on", "force-off"]:
                steam_override = fallback_data["profile_adjustments"]["steam_override"]
                
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


def get_sidebar_insight_ai(element: str, category_slug: str, preset_slug: str) -> dict | None:
    """
    Queries Gemma to generate a custom labor ROI tag, recommendation tier, and 'Last 10%' critique/reasoning.
    """
    import json
    import re
    from apps.core.models import BreadPreset, WheatBerry
    from grainlab.engines import router
    
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
        "\n"
        "Return a JSON object containing:\n"
        "- 'recommendation_tier': a string of 'recommended', 'sub-optimal', or 'not-recommended' representing the rating of this choice for the active preset.\n"
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



