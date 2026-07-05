import json
import logging
import requests
from django.conf import settings
from apps.core.models import SystemSetting
from apps.core.bakers_math import (
    get_local_sensory_benchmark,
    get_local_contextual_pitfalls,
)

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
            "Analyze the bread recipe variables and identify potential baking pitfalls "
            "or custom step additions (e.g., pretzel soda boiling, high-hydration sticky dough). "
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
def get_sensory_benchmark(grain_type: str, flour_maturity: str, effective_hydration: float) -> str:
    """
    Retrieves sensory text from Gemma, falling back to local description mappings.
    """
    if _is_ai_enabled():
        system_prompt = (
            "Synthesize a descriptive sensory benchmark describing what the rising dough should look "
            "and feel like (texture, touch resilience, visual swelling, surface air bubbles) "
            "based on the flour maturity and grain type. Return a JSON object with the key 'sensory_description'."
        )
        user_prompt = json.dumps({
            "grain_type": grain_type,
            "flour_maturity": flour_maturity,
            "hydration": effective_hydration,
        })
        
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["sensory_description"])
        if result and result.get("sensory_description"):
            return result["sensory_description"]

    # Fallback
    return get_local_sensory_benchmark(grain_type, flour_maturity, effective_hydration)


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


def get_grain_advisory_ai(preset_slug: str) -> dict | None:
    """
    Submits a prompt to Gemma asking for recommended and high risk stocks for the preset.
    """
    if _is_ai_enabled():
        system_prompt = (
            "You are a baking science expert. Analyze the given bread/pastry preset and identify the recommended stock and the high risk stock. "
            "Return a JSON object containing the following keys:\n"
            "- 'recommended_name': Name of the ideal grain variant (e.g., 'Soft White Wheat' or 'Hard Red Spring Wheat')\n"
            "- 'recommended_reason': 1-2 sentence food science explanation of why it fits the crumb structure\n"
            "- 'high_risk_name': Name of the high risk grain variant that will ruin the bake\n"
            "- 'high_risk_reason': 1-2 sentence food science explanation of why it ruins the bake"
        )
        user_prompt = json.dumps({"preset_slug": preset_slug})
        return call_gemma_api(system_prompt, user_prompt, expected_keys=[
            "recommended_name", "recommended_reason", "high_risk_name", "high_risk_reason"
        ])
    return None


def get_local_grain_advisory(preset_slug: str) -> dict:
    """
    Local fallback logic providing structured recommended and high risk stocks for presets.
    """
    slug = preset_slug.lower()
    
    if slug in ["cookies", "biscuits", "yellow-cake"]:
        return {
            "recommended_name": "Soft White Wheat",
            "recommended_reason": "Low protein content preserves tenderness and maximizes spread control, ensuring a delicate crumb.",
            "high_risk_name": "Hard Red Spring Wheat",
            "high_risk_reason": "Excessive 14.5% protein matrix will develop rubbery, bread-like gluten and cause structural tightening."
        }
    elif slug in ["baguette", "sourdough-boule", "ciabatta", "artisan-pizza", "bagel", "eclairs"]:
        return {
            "recommended_name": "Hard Red Spring Wheat",
            "recommended_reason": "High protein content (14.5%) developments a strong, elastic gluten network required to hold high hydration and support oven spring.",
            "high_risk_name": "Soft White Wheat",
            "high_risk_reason": "Insufficient gluten strength will lead to a slack, runny dough that collapses in the oven and lacks structure."
        }
    elif slug in ["everyday-sandwich", "challah", "cinnamon-rolls", "burger-buns", "naan", "donuts", "tagliatelle"]:
        return {
            "recommended_name": "Hard White Wheat",
            "recommended_reason": "Provides a balanced 12.5% protein content that supports mild structure while retaining a tender, soft, and uniform crumb.",
            "high_risk_name": "Soft White Wheat",
            "high_risk_reason": "Will fail to hold shape during baking, causing flat rolls or weak sandwich loaves that tear easily."
        }
    elif slug in ["french-loaf", "brioche", "pretzel", "croissants"]:
        return {
            "recommended_name": "Hard Red Winter Wheat",
            "recommended_reason": "Moderate 13.0% protein content develops clean, classic gluten structure suitable for rich enriched doughs and lamination.",
            "high_risk_name": "Soft White Wheat",
            "high_risk_reason": "Weaker protein structure will melt under high fat enrichment, yielding dense, oily, or unrisen products."
        }
    
    return {
        "recommended_name": "Hard Red Winter Wheat",
        "recommended_reason": "A versatile choice providing reliable gluten development and water absorption across standard profiles.",
        "high_risk_name": "Soft White Wheat (for bread products)",
        "high_risk_reason": "Too weak to support yeasted rising structures, leading to dense bakes or collapse."
    }


