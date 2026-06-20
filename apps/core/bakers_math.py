import math

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
    substitution=None  # Dict of {'original': 'water', 'substitute': 'whole_milk'}
):
    """
    Computes recipe ingredient weights by applying Baker's Math.
    Incorporates thirst modifiers, flour maturity adjustments, and sourdough hydration offsets.
    """
    # 1. Apply Fail-Safe Hydration Modifiers
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
            # For whole milk, to get 100g of water equivalent, we need 100 / 0.87 = 115g of milk.
            # This adds 115 * 0.04 = 4.6g fat and 115 * 0.05 = 5.75g sugar.
            # We compensate by reducing added fat and sugar ratios.
            sub_notes.append("Using Whole Milk instead of Water. Water and fat ratios adjusted to maintain equilibrium.")
            # We adjust effective ratios for the math engine:
            # Let's say milk replaces all water. Liquid ratio is effective_hydration.
            # We need milk_ratio = effective_hydration / 0.87.
            # The fat contribution is milk_ratio * 0.04.
            # The sugar contribution is milk_ratio * 0.05.
            # We subtract these from the added fats and sugars.
            milk_ratio = effective_hydration / 0.87
            fat_excess = milk_ratio * 0.04
            sugar_excess = milk_ratio * 0.05
            
            # Reduce added fats/sugars, but don't let them drop below 0
            effective_fat = max(0.0, effective_fat - fat_excess)
            effective_sugar = max(0.0, effective_sugar - sugar_excess)
            
            # The liquid we measure is milk, not water
            sub_offsets["milk_required"] = milk_ratio

        # Almond milk swap: 97% water, 1% fat, 0% sugar
        elif original == "water" and substitute == "almond_milk":
            sub_notes.append("Using Almond Milk instead of Water. Slightly adjusted liquid ratio (+3%) to compensate for milk solids.")
            almond_ratio = effective_hydration / 0.97
            fat_excess = almond_ratio * 0.01
            effective_fat = max(0.0, effective_fat - fat_excess)
            sub_offsets["almond_milk_required"] = almond_ratio

        # Butter replacing oil/fat: Butter is 80% fat, 18% water
        elif original == "fat" and substitute == "butter":
            sub_notes.append("Using Butter instead of pure Oil. Butter is 80% fat; increased butter weight by 25% and reduced added liquid.")
            # For 1g fat, we need 1.25g butter, which adds 0.225g water.
            butter_ratio = effective_fat / 0.80
            water_excess = butter_ratio * 0.18
            effective_hydration = max(0.40, effective_hydration - water_excess)
            sub_offsets["butter_required"] = butter_ratio

    # 3. Calculate Baker's Math Scaling
    # Total Mass = Flour + Water + Fat + Sugar + Salt + Leaven
    # Let total ratios = 1 + Hydration% + Fat% + Sugar% + Salt% + Leaven%
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
        # Subtract starter components from main flour and water
        added_flour = flour_weight - (starter_weight / 2.0)
        added_water = water_weight - (starter_weight / 2.0)
    else:
        yeast_weight = leaven_weight

    # 4. Substitution Weight Conversions
    liquid_label = "Water"
    liquid_weight = added_water
    added_butter = 0.0
    added_oil = fat_weight

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
        elif substitute == "butter":
            added_butter = flour_weight * sub_offsets["butter_required"]
            added_oil = 0.0

    # 5. Desired Dough Temperature (DDT)
    # DDT target is 78°F. Water Temp = (3 * 78) - Room - Flour - Friction
    ddt_target_f = 78.0
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
        "salt_weight": round(salt_weight, 1),
        "yeast_weight": round(yeast_weight, 1),
        "starter_weight": round(starter_weight, 1),
        "added_butter": round(added_butter, 1),
        "added_oil": round(added_oil, 1),
        "thirst_modifier_applied": thirst_mod,
        "maturity_modifier_applied": maturity_mod,
        "required_water_temp_f": round(required_water_temp_f, 1),
        "required_water_temp_c": round((required_water_temp_f - 32) * 5 / 9, 1),
        "substitution_notes": sub_notes,
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
