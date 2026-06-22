import math

def _get_val(obj, key, default=None):
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

# Coefficients and constants for Baker's Math
GRAIN_THIRST_MODIFIERS = {
    "all_purpose": 0.0,
    "whole_wheat": 0.03,
    "spelt": 0.05,
    "kamut": 0.06,
    "einkorn": 0.04,
}

MATURITY_HYDRATION_MODIFIERS = {
    "just_milled": 0.0,
    "dead_zone": -0.02,  # 1-2 weeks collapse window
    "matured": 0.0,      # 2+ weeks matured
}

# Mixing method / mill friction factors (in Fahrenheit)
FRICTION_FACTORS = {
    "hand_knead": 2.0,
    "stand_mixer": 10.0,
    "bread_machine": 15.0,
}

def calculate_wheat_berry_shares(active_berries, texture_score, crumb_score, preset_slug=None, preset_name=None):
    """
    Dynamically generates the wheat berry blend shares based on active berries and sliders.
    Returns: (shares_dict, weighted_absorption_coef, structural_warning)
        shares_dict: dict mapping wheat berry names to their blend fraction (0.0 to 1.0)
        weighted_absorption_coef: float multiplier for hydration adjustment
        structural_warning: warning string or None
    """
    if not active_berries:
        return {"House Blend": 1.0}, 1.0, None

    # Check if AI is active and query Gemma for optimized blend
    from apps.core.models import SystemSetting
    from django.conf import settings
    
    db_enabled = SystemSetting.get_val("ai_enabled", "False").lower() in ("true", "1", "t")
    env_mock = getattr(settings, "MOCK_MODE", True)
    ai_active = db_enabled and not env_mock

    if ai_active:
        from apps.core import gemma_client
        ai_res = gemma_client.optimize_grain_blend(preset_slug, preset_name, active_berries)
        if ai_res:
            shares, structural_warning = ai_res
            # Calculate weighted absorption coefficient
            weighted_absorption = 0.0
            for b in active_berries:
                name = _get_val(b, 'name')
                share = shares.get(name, 0.0)
                coef = _get_val(b, 'moisture_absorption_coef', 1.0)
                weighted_absorption += share * coef
            if weighted_absorption == 0.0:
                weighted_absorption = 1.0
            return shares, weighted_absorption, structural_warning

    # 1. Classify berries
    ancient_berries = []
    hard_berries = []
    soft_berries = []

    for b in active_berries:
        # Support both Django model instances and serialized dictionary attributes safely
        hardness = _get_val(b, 'hardness', 'hard')
        protein = _get_val(b, 'protein_content', 12.0)
        
        if hardness == 'ancient':
            ancient_berries.append(b)
        elif hardness == 'soft' or (protein < 12.0 and hardness != 'durum' and hardness != 'hard'):
            soft_berries.append(b)
        else:
            hard_berries.append(b)

    # 2. Determine target protein content based on Texture (Softness) and Crumb (Openness)
    target_protein = 11.5 - (texture_score / 100.0 * 2.5) + (crumb_score / 100.0 * 1.5) + 0.5
    target_protein = max(9.0, min(15.0, target_protein))

    # 3. Calculate blend shares
    shares = {}
    
    has_hard = len(hard_berries) > 0
    has_soft = len(soft_berries) > 0
    has_ancient = len(ancient_berries) > 0

    ancient_share = 0.15 if has_ancient else 0.0
    if has_ancient:
        share_per_ancient = ancient_share / len(ancient_berries)
        for b in ancient_berries:
            name = _get_val(b, 'name')
            shares[name] = share_per_ancient

    remaining_share = 1.0 - ancient_share

    if has_hard and has_soft:
        avg_p_hard = sum(_get_val(b, 'protein_content', 12.0) for b in hard_berries) / len(hard_berries)
        avg_p_soft = sum(_get_val(b, 'protein_content', 12.0) for b in soft_berries) / len(soft_berries)
        
        if avg_p_hard != avg_p_soft:
            x = (target_protein - avg_p_soft) / (avg_p_hard - avg_p_soft)
            x = max(0.0, min(1.0, x))
        else:
            x = 0.5
            
        hard_share = x * remaining_share
        soft_share = (1.0 - x) * remaining_share
        
        for b in hard_berries:
            name = _get_val(b, 'name')
            shares[name] = hard_share / len(hard_berries)
        for b in soft_berries:
            name = _get_val(b, 'name')
            shares[name] = soft_share / len(soft_berries)
            
    elif has_hard:
        for b in hard_berries:
            name = _get_val(b, 'name')
            shares[name] = remaining_share / len(hard_berries)
            
    elif has_soft:
        for b in soft_berries:
            name = _get_val(b, 'name')
            shares[name] = remaining_share / len(soft_berries)
            
    elif has_ancient:
        for b in ancient_berries:
            name = _get_val(b, 'name')
            shares[name] = 1.0 / len(ancient_berries)
            
    else:
        return {"House Blend": 1.0}, 1.0, None

    # 4. Enforce structural safety for high-rise presets
    is_high_rise = False
    preset_label = "High-Rise Bread"
    if preset_slug:
        preset_slug_lower = preset_slug.lower()
        is_high_rise = 'bagel' in preset_slug_lower or 'boule' in preset_slug_lower or 'artisan' in preset_slug_lower
        if preset_name:
            preset_label = preset_name
    elif preset_name:
        preset_name_lower = preset_name.lower()
        is_high_rise = 'bagel' in preset_name_lower or 'boule' in preset_name_lower or 'artisan' in preset_name_lower
        preset_label = preset_name

    structural_warning = None
    if is_high_rise:
        current_hard_share = sum(shares.get(_get_val(b, 'name'), 0.0) for b in hard_berries)
        if current_hard_share < 0.70:
            # We must adjust the blend so the hard grain is at 70%
            structural_warning_grain = "Hard Red Wheat"
            
            if not has_hard:
                # Get strongest hard grain from database
                from apps.core.models import WheatBerry
                strongest_db = WheatBerry.objects.filter(hardness='hard').order_by('-protein_content').first()
                if strongest_db:
                    injected_grain = strongest_db
                    structural_warning_grain = strongest_db.name
                else:
                    # Fallback structural grain
                    class MockBerry:
                        name = "Hard Red Winter Wheat"
                        protein_content = 13.0
                        hardness = "hard"
                        moisture_absorption_coef = 1.0
                    injected_grain = MockBerry()
                    structural_warning_grain = injected_grain.name
                hard_berries.append(injected_grain)
                if injected_grain not in active_berries:
                    active_berries = list(active_berries) + [injected_grain]
            else:
                strongest_selected = max(hard_berries, key=lambda b: _get_val(b, 'protein_content', 12.0))
                structural_warning_grain = _get_val(strongest_selected, 'name')

            structural_warning = f"❌ Structural Hazard: Selected grain blend lacks the gluten strength required for a {preset_label}. Adjusting blend to include 70% {structural_warning_grain} for safety."
            
            # Recalculate shares with 70% hard and 30% weak/ancient
            shares = {}
            share_per_hard = 0.70 / len(hard_berries)
            for b in hard_berries:
                name = _get_val(b, 'name')
                shares[name] = share_per_hard
            
            weak_berries = soft_berries + ancient_berries
            if weak_berries:
                share_per_weak = 0.30 / len(weak_berries)
                for b in weak_berries:
                    name = _get_val(b, 'name')
                    shares[name] = share_per_weak
            else:
                for b in hard_berries:
                    name = _get_val(b, 'name')
                    shares[name] = 1.0 / len(hard_berries)

    # 5. Calculate weighted absorption coefficient
    weighted_absorption = 0.0
    for b in active_berries:
        name = _get_val(b, 'name')
        share = shares.get(name, 0.0)
        coef = _get_val(b, 'moisture_absorption_coef', 1.0)
        weighted_absorption += share * coef

    if weighted_absorption == 0.0:
        weighted_absorption = 1.0

    return shares, weighted_absorption, structural_warning


def calculate_recipe(
    base_hydration,
    base_fat,
    base_sugar,
    target_mass,
    grain_type="all_purpose",
    flour_maturity="matured",
    leaven_type="yeast",
    leaven_pct=0.015,  # 1.5% yeast or 20% starter
    salt_pct=0.02,     # 2% salt
    room_temp_f=72.0,
    flour_temp_f=70.0,
    mixing_method="stand_mixer",
    substitution=None,  # Dict of {'original': 'water', 'substitute': 'whole_milk'}
    active_berries=None, # List of WheatBerry models/dicts
    texture_score=50,   # Used for custom berry blending
    crumb_score=50,     # Used for custom berry blending
    friction_override=None, # Custom mixer friction value
    preset_slug=None,
    preset_name=None
):
    """
    Computes recipe ingredient weights by applying Baker's Math.
    Incorporates thirst modifiers, flour maturity adjustments, and sourdough hydration offsets.
    """
    # 1. Apply Fail-Safe Hydration Modifiers
    structural_warning = None
    if active_berries:
        berry_shares, weighted_absorption, structural_warning = calculate_wheat_berry_shares(
            active_berries, texture_score, crumb_score, preset_slug=preset_slug, preset_name=preset_name
        )
        thirst_mod = weighted_absorption - 1.0
    else:
        berry_shares = {}
        thirst_mod = GRAIN_THIRST_MODIFIERS.get(grain_type, 0.0)

    maturity_mod = MATURITY_HYDRATION_MODIFIERS.get(flour_maturity, 0.0)
    
    effective_hydration = base_hydration + thirst_mod + maturity_mod
    effective_fat = base_fat
    effective_sugar = base_sugar

    # 2. Deconstruct and Balance Substitutions (Chemistry Re-Balancing)
    sub_notes = []
    sub_offsets = {"water": 0.0, "fat": 0.0, "sugar": 0.0}
    
    if substitution:
        original = substitution.get("original")
        substitute = substitution.get("substitute")
        
        # Whole milk swap: 87% water, 4% fat, 5% sugar
        if original == "water" and substitute == "whole_milk":
            sub_notes.append("Using Whole Milk instead of Water. Water and fat ratios adjusted to maintain equilibrium.")
            milk_ratio = effective_hydration / 0.87
            fat_excess = milk_ratio * 0.04
            sugar_excess = milk_ratio * 0.05
            
            effective_fat = max(0.0, effective_fat - fat_excess)
            effective_sugar = max(0.0, effective_sugar - sugar_excess)
            
            sub_offsets["milk_required"] = milk_ratio

        # Almond milk swap: 97% water, 1% fat, 0% sugar
        elif original == "water" and substitute == "almond_milk":
            sub_notes.append("Using Almond Milk instead of Water. Slightly adjusted liquid ratio (+3%) to compensate for milk solids.")
            almond_ratio = effective_hydration / 0.97
            fat_excess = almond_ratio * 0.01
            effective_fat = max(0.0, effective_fat - fat_excess)
            sub_offsets["almond_milk_required"] = almond_ratio

        # Butter replacing oil/fat: Butter is 80% fat, 18% water
        elif original == "fat" and substitute in ["butter", "salted_butter", "unsalted_butter"]:
            name_display = substitute.replace("_", " ").title()
            sub_notes.append(f"Using {name_display} instead of pure Oil. Butter is 80% fat; increased butter weight by 25% and reduced added liquid.")
            butter_ratio = effective_fat / 0.80
            water_excess = butter_ratio * 0.18
            effective_hydration = max(0.40, effective_hydration - water_excess)
            sub_offsets["butter_required"] = butter_ratio
        elif original == "fat" and substitute in ["olive_oil", "canola_oil", "vegetable_oil"]:
            name_display = substitute.replace("_", " ").title()
            sub_notes.append(f"Using {name_display} as pure fat enrichment.")

    # 3. Calculate Baker's Math Scaling
    total_ratios = 1.0 + effective_hydration + effective_fat + effective_sugar + salt_pct + leaven_pct
    
    # Base Flour Weight (100%)
    flour_weight = target_mass / total_ratios
    
    # Basic weights
    water_weight = flour_weight * effective_hydration
    fat_weight = flour_weight * effective_fat
    sugar_weight = flour_weight * effective_sugar
    salt_weight = flour_weight * salt_pct
    leaven_weight = flour_weight * leaven_pct

    # Adjustments for Sourdough Starter (which is 50% flour, 50% water)
    added_flour = flour_weight
    added_water = water_weight
    starter_weight = 0.0
    yeast_weight = 0.0

    if leaven_type == "sourdough":
        starter_weight = leaven_weight
        added_flour = flour_weight - (starter_weight / 2.0)
        added_water = water_weight - (starter_weight / 2.0)
    else:
        yeast_weight = leaven_weight

    # 4. Substitution Weight Conversions
    liquid_label = "Water"
    liquid_weight = added_water
    added_butter = 0.0
    added_oil = fat_weight
    fat_label = "Shortening/Oil"

    if substitution:
        substitute = substitution.get("substitute")
        if substitute == "whole_milk":
            liquid_label = "Whole Milk"
            liquid_weight = flour_weight * sub_offsets["milk_required"]
            if leaven_type == "sourdough":
                liquid_weight -= (starter_weight / 2.0)
        elif substitute == "almond_milk":
            liquid_label = "Almond Milk"
            liquid_weight = flour_weight * sub_offsets["almond_milk_required"]
            if leaven_type == "sourdough":
                liquid_weight -= (starter_weight / 2.0)
        elif substitute in ["butter", "salted_butter", "unsalted_butter"]:
            added_butter = flour_weight * sub_offsets["butter_required"]
            added_oil = 0.0
            fat_label = substitute.replace("_", " ").title()
        elif substitute in ["olive_oil", "canola_oil", "vegetable_oil"]:
            added_butter = 0.0
            added_oil = fat_weight
            fat_label = substitute.replace("_", " ").title()

    fat_weight_display = added_butter if added_butter > 0 else added_oil

    # 5. Desired Dough Temperature (DDT)
    # DDT target is 78°F. Water Temp = (3 * 78) - Room - Flour - Friction
    ddt_target_f = 78.0
    if friction_override is not None:
        friction = friction_override
    else:
        friction = FRICTION_FACTORS.get(mixing_method, 10.0)
    required_water_temp_f = (3.0 * ddt_target_f) - room_temp_f - flour_temp_f - friction

    # 6. Build the final output dictionary
    return {
        "target_mass": round(target_mass, 1),
        "flour_weight": round(flour_weight, 1),
        "water_weight": round(water_weight, 1),
        "effective_hydration_pct": round(effective_hydration * 100, 1),
        "effective_fat_pct": round(effective_fat * 100, 1),
        "effective_sugar_pct": round(effective_sugar * 100, 1),
        "added_flour": round(added_flour, 1),
        "added_water": round(added_water, 1),
        "liquid_label": liquid_label,
        "liquid_weight": round(liquid_weight, 1),
        "sugar_weight": round(sugar_weight, 1),
        "salt_weight": round(salt_weight, 1),
        "yeast_weight": round(yeast_weight, 1),
        "starter_weight": round(starter_weight, 1),
        "added_butter": round(added_butter, 1),
        "added_oil": round(added_oil, 1),
        "fat_label": fat_label,
        "fat_weight_display": round(fat_weight_display, 1),
        "thirst_modifier_applied": thirst_mod,
        "maturity_modifier_applied": maturity_mod,
        "required_water_temp_f": round(required_water_temp_f, 1),
        "required_water_temp_c": round((required_water_temp_f - 32) * 5 / 9, 1),
        "substitution_notes": sub_notes,
        "wheat_berry_mix": {name: round(flour_weight * share, 1) for name, share in berry_shares.items() if share > 0.0} if active_berries else None,
        "structural_warning": structural_warning,
    }


def get_local_sensory_benchmark(grain_type, flour_maturity, effective_hydration):
    """
    Fallback engine that returns high-quality, bread-science-aligned
    physical descriptions of the dough rise and sensory cues.
    """
    grain_name = grain_type.replace("_", " ").title()
    desc = f"For fresh-milled {grain_name} dough: "
    
    # Hydration impact
    if effective_hydration >= 0.75:
        desc += "The dough will be wet and sticky. Look for a glossy surface and a clean, dome-like rise. "
    elif effective_hydration >= 0.65:
        desc += "Expect a supple, holding structure. The dough should feel alive, resilient, and elastic when touched. "
    else:
        desc += "Dough is firm and tight. It will not double dramatically; monitor for a rounded dome and a smooth outer skin. "
        
    # Maturity impact
    if flour_maturity == "just_milled":
        desc += "As this flour was milled today, gluten activity is highly active but lacks extensibility. Expect rapid enzyme fermentation; handle gently to avoid tearing."
    elif flour_maturity == "dead_zone":
        desc += "Caution: Flour is in the 1-2 week enzyme dead zone. Gluten structure is relaxed and vulnerable. The dough will feel sticky and might lack holding power; do not over-proof."
    else:
        desc += "Flour is fully matured. Gluten bonds are stable and predictable. The rise will be steady with solid gas retention."
        
    return desc


def get_local_contextual_pitfalls(category_slug, effective_hydration, grain_type, preset_slug=None):
    """
    Fallback engine to generate warnings and special instructions.
    """
    pitfalls = []
    
    if preset_slug == "pretzel":
        pitfalls.append({
            "title": "Mandatory Alkaline Bath",
            "message": "To achieve the signature deep mahogany color and unique flavor, you must boil the shaped pretzels in a 3% baking soda bath (or carefully dip in a 3% lye solution) for 30 seconds before baking."
        })
    
    if effective_hydration >= 0.78:
        pitfalls.append({
            "title": "High Hydration Handling",
            "message": "With a hydration of over 78%, this dough is wet. Do not add raw flour to the workspace; instead, perform 'stretch-and-folds' with wet hands to build gluten structure."
        })

    if grain_type in ["spelt", "kamut", "einkorn"]:
        pitfalls.append({
            "title": "Ancient Grain Fragility",
            "message": f"{grain_type.title()} has weaker gluten networks. Avoid intensive machine mixing. Prefer short hand mixing followed by gentle folds to keep the structure from collapsing."
        })
        
    if category_slug == "enriched-soft":
        pitfalls.append({
            "title": "Fermentation Retardation",
            "message": "Fats and sugars slow down yeast fermentation. Allow for a longer bulk proof or create a warm, moist proofing box to encourage active rising."
        })

    # Default general fallback advice if empty
    if not pitfalls:
        pitfalls.append({
            "title": "Standard Proofing Check",
            "message": "Keep dough covered at a stable temp of 75-78°F. The poke test is your best guide: if a gentle indent springs back slowly, it is ready to bake."
        })
        
    return pitfalls
