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

    if expected_keys and "shares" in expected_keys:
        # Mock optimize_grain_blend
        preset_slug = user_data.get("preset_slug", "")
        preset_name = user_data.get("preset_name", "")
        berries = user_data.get("active_berries", [])
        
        shares = {}
        warning = None
        if not berries:
            return {"shares": {}, "structural_warning": None}
            
        # Determine if high-rise
        is_high_rise = preset_slug in ["sourdough-boule", "baguette", "ciabatta", "artisan-pizza", "bagel", "french-loaf"]
        has_hard = any("hard" in b.get("name", "").lower() for b in berries)
        
        if is_high_rise and not has_hard:
            warning = f"❌ Structural Hazard: Selected grain blend lacks the gluten strength required for a {preset_name}. Adjusting blend to include 70% Hard Red Spring Wheat for safety."
            
        # Simple default distribution favoring soft & rye for cookies
        if "cookie" in preset_slug or "cookie" in preset_name.lower():
            soft_berry = next((b for b in berries if "soft" in b.get("name", "").lower()), None)
            rye_berry = next((b for b in berries if "rye" in b.get("name", "").lower()), None)
            if soft_berry and rye_berry:
                shares[soft_berry["name"]] = 0.8
                shares[rye_berry["name"]] = 0.2
            elif soft_berry:
                shares[soft_berry["name"]] = 1.0
            elif rye_berry:
                shares[rye_berry["name"]] = 1.0
            else:
                shares[berries[0]["name"]] = 1.0
        else:
            hard_berry = next((b for b in berries if "hard red spring" in b.get("name", "").lower()), None)
            if not hard_berry:
                hard_berry = next((b for b in berries if "hard" in b.get("name", "").lower()), None)
            if hard_berry:
                shares[hard_berry["name"]] = 1.0
            else:
                shares[berries[0]["name"]] = 1.0
                
        # Fill in 0.0 for others
        for b in berries:
            if b["name"] not in shares:
                shares[b["name"]] = 0.0
                
        return {"shares": shares, "structural_warning": warning}

    elif expected_keys and ("grain_evaluations" in expected_keys or "elevate_recipe" in expected_keys):
        # Mock get_grain_advisory_ai
        preset_slug = user_data.get("preset_slug", "")
        category_slug = user_data.get("category_slug", "")
        inventory = user_data.get("inventory", [])
        
        evaluations = []
        is_cookie = "cookie" in preset_slug or "cookie" in (category_slug or "").lower()
        
        for b in inventory:
            name_lower = b.get("name", "").lower()
            b_id = b.get("id", "")
            prot = b.get("protein", 12.0)
            
            if is_cookie:
                # Sovereignty rules override for cookies: Rye and Soft are recommended, Hard is sub-optimal or not-recommended
                if "soft" in name_lower:
                    tier = "recommended"
                    reasoning = f"At {prot}% protein, Soft White Wheat provides tender, delicate structures perfect for cookies, avoiding any gluten toughness."
                elif "rye" in name_lower:
                    tier = "recommended"
                    reasoning = "Rye is highly recommended for cookies due to pentosans blocking gluten development, maximizing tenderness and moisture retention."
                elif "hard red spring" in name_lower:
                    tier = "not-recommended"
                    reasoning = f"High protein content ({prot}%) creates excessive gluten elasticity, causing the cookies to bake into tough, cakey domes."
                elif "hard red winter" in name_lower:
                    tier = "sub-optimal"
                    reasoning = f"Moderate protein content ({prot}%) creates slightly too much gluten structure, leading to a somewhat tough cookie spread."
                elif "hard white" in name_lower:
                    tier = "sub-optimal"
                    reasoning = f"Ideal neutral flavor, but the {prot}% protein content is too high for optimal cookie tenderness."
                elif "spelt" in name_lower:
                    tier = "sub-optimal"
                    reasoning = "Extensible but weak gluten provides decent tenderness, but the nutty flavor may overpower delicate recipe notes."
                else:
                    tier = "sub-optimal"
                    reasoning = f"At {prot}% protein, this grain is slightly too strong for optimal cookie tenderness."
            else:
                # Standard bread rules
                if "hard red spring" in name_lower or "hard red winter" in name_lower or "hard white" in name_lower:
                    tier = "recommended"
                    reasoning = f"High protein content ({prot}%) provides the optimal gluten strength and elasticity needed for a tall, open-crumb rise."
                elif "soft" in name_lower:
                    tier = "not-recommended"
                    reasoning = f"Low protein ({prot}%) and weak gluten structure will fail to retain gas, resulting in a flat, dense, and gummy loaf."
                elif "rye" in name_lower:
                    tier = "sub-optimal"
                    reasoning = "Savory flavor matches hearth profiles, but high pentosans and low gluten elasticity will produce a denser, stickier crumb."
                elif "spelt" in name_lower:
                    tier = "sub-optimal"
                    reasoning = "Highly extensible but weak gluten structure requires careful hydration management to avoid structural collapse."
                else:
                    tier = "sub-optimal"
                    reasoning = f"Provides pleasant flavor and {prot}% protein, but low elasticity results in reduced oven spring."
                    
            evaluations.append({
                "grain_id": b_id,
                "tier": tier,
                "reasoning": reasoning
            })
            
        selected_names = user_data.get("selected_grains") or []
        selected_names_lower = [n.lower() for n in selected_names]
        
        elevate_recipe = []
        if is_cookie:
            elevate_recipe.append("Substitute 1/3 of the flour blend with Soft White Wheat to maximize tenderness and ensure a melt-in-your-mouth quality.")
            if "rye" in "".join(selected_names_lower):
                elevate_recipe.append("Rye selection detected: Brown the butter during the creaming stage to pair nuttiness with Rye's deep flavor notes.")
                elevate_recipe.append("Add a pinch of dark brown sugar to balance the earthy rye profile with rich molasses tones.")
            else:
                elevate_recipe.append("To introduce complex nuttiness without heavy gluten, substitute 15% of the flour blend with Spelt or Rye (Ancient).")
                elevate_recipe.append("Chill the cookie dough for at least 24 hours before baking to allow starch hydration and concentrate flavors.")
            elevate_recipe.append("Use a low-gluten mixing method to keep the cookie spread wide and prevent a tough, cakey texture.")
        else:
            elevate_recipe.append("Introduce a 20% poolish pre-ferment to enhance crumb extensibility and promote a golden, caramelized crust.")
            if "hard red spring" in "".join(selected_names_lower):
                elevate_recipe.append("Hard Red Spring Wheat active: increase hydration by 3-5% to accommodate its high protein absorption rate.")
                elevate_recipe.append("Perform 3 rounds of stretch-and-folds during bulk fermentation to build robust gluten structure.")
            else:
                elevate_recipe.append("To elevate extensibility, incorporate 10% Spelt or Kamut (Ancient) into your active grain blend.")
                elevate_recipe.append("Ensure you preheat your baking stone or steel at 450°F (230°C) for at least 45 minutes prior to bake.")
            elevate_recipe.append("Extend the final proofing time by 20% if using freshly milled whole grains to allow natural enzymes to mellow.")

        return {
            "grain_evaluations": evaluations,
            "elevate_recipe": elevate_recipe
        }

    elif expected_keys and "recipes" in expected_keys:
        engine_id = user_data.get("engine_id", "hearth")
        active_archetype_id = user_data.get("active_archetype_id", "classic_sourdough")
        inventory = user_data.get("inventory", [])
        
        # Build grain name slug list from inventory for recommended_grain_ids
        hard_grains = [b for b in inventory if "hard" in b.get("hardness", "").lower()]
        soft_grains = [b for b in inventory if "soft" in b.get("hardness", "").lower() or b.get("hardness") == "ancient"]
        
        def grain_slug(g):
            return g.get("name", "").lower().replace(" ", "_").replace("/", "").replace("-", "_")

        hard_slugs = [grain_slug(g) for g in hard_grains[:2]] or ["hard_red_spring_wheat"]
        soft_slugs = [grain_slug(g) for g in soft_grains[:2]] or ["soft_white_wheat"]
        pref_slugs = hard_slugs if engine_id in ["hearth", "pan", "bath", "pasta"] else soft_slugs

        recipes = []
        arch_title = active_archetype_id.replace("_", " ").title()

        # Premium Predefined Recipe DB for select archetypes
        db = {
            "drop_cookie": {
                1: [
                    {"name": "Brown Butter Chocolate Chip", "desc": "A baseline standard cookie prioritizing partial butter browning for a rich nutty aroma and consistent horizontal spread.", "science": "Traditional drop cookie matrix where partially browned lipids emulsify with sugars, preventing premature crystallization.", "roi": "Low Effort / Immediate Aromatics Payoff", "tip": "Chill the dough for exactly 4 hours to consolidate solid fats before portioning."},
                    {"name": "Golden Sugar Cookie", "desc": "Standard soft-baked cookie with a balanced white and brown sugar ratio for a crisp edge and chewy center.", "science": "Balanced sucrose and fructose levels dictate moderate caramelization rate and crust humidity threshold.", "roi": "Absolute Baseline / 100% Reliable", "tip": "Dust lightly with fine caster sugar before baking for a sparkling finish."},
                    {"name": "Traditional Oatmeal Raisin", "desc": "Reliable rolled oats base bound by unsalted butter and whole eggs, generating a chewy, fibrous structure.", "science": "Oat beta-glucans absorb ambient moisture, buffering gluten starches from building excessive elasticity.", "roi": "High Fiber / Stable Structure", "tip": "Soak oats in warm water for 5 minutes if they appear excessively dry."},
                    {"name": "Spiced Ginger Snaps", "desc": "Standard molasses-sweetened drop cookie with high crispness and regular surface cracks.", "science": "Acidic molasses triggers chemical leaveners, releasing carbon dioxide rapidly during the initial thermal phase.", "roi": "Low Effort / High Spice Expression", "tip": "Roll in coarse turbinado sugar for a premium crunch."},
                    {"name": "Old-Fashioned Peanut Butter", "desc": "A dense, rich drop cookie using nut fats to shorten gluten strands, marked with traditional fork cross-hatching.", "science": "High lipid content from peanut paste coats proteins, limiting water absorption and gluten network formation.", "roi": "Low Effort / Rich Protein Bite", "tip": "Bake immediately after scoring to preserve the distinct structural fork ridges."}
                ],
                2: [
                    {"name": "Triple-Valrhona Malted Cookie", "desc": "Advanced recipe utilizing malted milk powder and three varieties of dark chocolate chunk inclusions.", "science": "Diastatic malt flour modifies starches into simple sugars, accelerating Maillard browning and crumb softness.", "roi": "High Ingredient Cost / Premium Quality Payoff", "tip": "Incorporate chocolate chunks by hand folding to prevent melting into the dough."},
                    {"name": "Lactic-Fermented Cookie", "desc": "Modern profile incorporating cultured buttermilk powder for a faint lactic tang and tender center.", "science": "Lactic acid weakens gluten networks chemically, keeping the horizontal spread highly uniform and soft.", "roi": "Skill Intensive / Unique Tangy Profile", "tip": "Rest dough in the refrigerator for 24 hours to maximize lactic acid hydration."},
                    {"name": "Espresso-Infused Brown Butter", "desc": "Advanced drop cookie with dehydrated espresso micro-crystals dispersed throughout the lipid phase.", "science": "Hydrophobic fat phase encapsulates espresso particles, releasing intense roasted flavor during heat dissipation.", "roi": "Moderate Effort / Complex Dessert Flavor", "tip": "Sift espresso powder with dry ingredients to ensure a streak-free distribution."},
                    {"name": "Salted Toffee Pecan drop cookie", "desc": "Advanced cookie containing homemade toasted pecan brittle and butter toffee shards.", "science": "Toffee shards melt locally during baking, creating localized caramel pockets with higher sugar concentration.", "roi": "Preparation Intensive / Premium Textural Contrast", "tip": "Use silpat mats rather than parchment to prevent sticky caramel leaks."},
                    {"name": "Chilled Honey-Lavender Cookie", "desc": "Modern floral cookie sweetened with wildflower honey and infused with lavender-infused butter.", "science": "Hygroscopic honey retains moisture after cooling, ensuring long-term softness and slow starch retrogradation.", "roi": "Moderate Return / Sophisticated Botanical Aroma", "tip": "Do not over-bake, as honey-rich doughs brown rapidly and can burn easily."}
                ],
                3: [
                    {"name": "Ancient Spelt & Miso Fudge", "desc": "Savory, umami-rich cookie combining ancient spelt flour and dark red miso paste for a deep savory chew.", "science": "Spelt's high extensibility coupled with miso's high salinity creates a soft, hyper-hydrated, dense structure.", "roi": "High Risk & Skill / Deep Savory Complexity", "tip": "Cream miso paste thoroughly with butter before sugar introduction to prevent lumps."},
                    {"name": "Sourdough Discard Chocolate Chunk", "desc": "Experimental drop cookie utilizing wild yeast discard to ferment starches and add complex organic acids.", "science": "Acidity from sourdough discard lowers pH, optimizing enzymatic activity and reducing starch viscosity.", "roi": "Resource Optimization / Complex Crust Aesthetics", "tip": "Use cold discard straight from the fridge to prevent butter fat melting."},
                    {"name": "Buckwheat Hazelnut drop cookie", "desc": "Experimental buckwheat cookie with toasted hazelnut oil adjustments.", "science": "Buckwheat's lack of gluten proteins results in zero elasticity, requiring egg lecithin to bind the cookie matrix.", "roi": "Dietary Friendly / Intense Earthy Nutty Profile", "tip": "Shape into tight domes before baking, as buckwheat dough lacks elasticity."},
                    {"name": "Smoked Malt & Rye Cookie", "desc": "Experimental cookie utilizing dark rye flour and cherrywood smoked barley malt.", "science": "Rye pentosans absorb immense water, yielding a dense, fudgy, bread-like center with high structural integrity.", "roi": "Experimental / Heavy Smoked Aromatics", "tip": "Slightly flatten the portioned dough balls to encourage spreading."},
                    {"name": "Einkorn Bourbon Toffee", "desc": "Experimental profile with ancient einkorn flour, bourbon-soaked vanilla bean, and charred sugar shards.", "science": "Einkorn's weak gluten structure and high carotenoids produce a tender, bright yellow crumb with high meltability.", "roi": "Artisanal / Sophisticated Cocktail Profile", "tip": "Bake at a slightly lower temperature (325F) to preserve einkorn's fragile starches."}
                ]
            },
            "hearth_boule": {
                1: [
                    {"name": "Baseline Country Sourdough", "desc": "Standard reliable sourdough boule with 70% hydration and straightforward bulk fermentation.", "science": "Traditional yeast and lactic fermentation producing a uniform wild crumb and crisp crust.", "roi": "Low Effort / 100% Reliable", "tip": "Maintain dough temperature at 75-78F throughout bulk fermentation."},
                    {"name": "Classic San Francisco Hearth", "desc": "Standard sour loaf with an extended cold retardation phase to highlight acetic acid notes.", "science": "Extended cold rest allows heterofermentative bacteria to produce high ratios of acetic acid.", "roi": "Patience Required / Intense Sour Tang", "tip": "Use a mature, slightly acidic starter to kickstart the cold souring."},
                    {"name": "Everyday Sourdough Boule", "desc": "Standard no-knead sourdough utilizing simple stretch-and-folds for steady gluten strength.", "science": "Autolytic hydration activates protease enzymes, naturally relaxing the gluten matrix.", "roi": "Hands-off / High Volume return", "tip": "Do three sets of coil folds spaced 45 minutes apart during bulk fermentation."},
                    {"name": "Rustic Sourdough Batard", "desc": "Standard oval loaf utilizing a small addition of whole rye flour for fermentation activity.", "science": "Rye minerals act as biological stimulants, accelerating wild yeast multiplication rates.", "roi": "Low Effort / Reliable Yeast Activity", "tip": "Score with a single deep slash at a 45-degree angle for an optimal ear."},
                    {"name": "Simple Whole Wheat Sourdough", "desc": "Standard loaf with 20% fresh-milled whole wheat for rustic color and balanced gluten strength.", "science": "Bran particles cut gluten sheets slightly, which is balanced by high-protein white wheat.", "roi": "Low Effort / Balanced Nutty Crumb", "tip": "Sift out large bran flakes if you want a taller, lighter loaf."}
                ],
                2: [
                    {"name": "High-Hydration Open Crumb batard", "desc": "Advanced modern sourdough with 82% hydration and intensive lamination folds.", "science": "High hydration levels create steam expansion channels, producing a glossy, open alveolar structure.", "roi": "Skill Intensive / Exceptional Glossy Crumb", "tip": "Perform a lamination stretch on a wet bench to build early structural memory."},
                    {"name": "Polenta & Toasted Seed Sourdough", "desc": "Advanced loaf with cooked heirloom corn polenta and toasted sesame and flax seed inclusions.", "science": "Gelatinized polenta starches hold moisture, while toasted seed lipids add crunch.", "roi": "Preparation Intensive / Superior Moisture Retention", "tip": "Let polenta cool completely to room temperature before folding it into the dough."},
                    {"name": "Porridge-Infused Sourdough", "desc": "Advanced modern loaf featuring a cooked oat porridge gel folded in during lamination.", "science": "Cooked oats lock water inside gelatinized starch matrices, preventing crumb staling.", "roi": "Skill Intensive / Extremely Soft Custard Crumb", "tip": "Adjust bulk fermentation time down, as warm porridge can speed up yeast activity."},
                    {"name": "Purple Barley & Sesame loaf", "desc": "Advanced recipe utilizing fresh-milled purple barley flour and black sesame seeds.", "science": "Barley anthocyanins react with acidity, turning the crumb a gorgeous violet shade.", "roi": "Artisanal / Unique Visual Appeal", "tip": "Toast sesame seeds to release oils before incorporating them."},
                    {"name": "Double-Fermented Sourdough", "desc": "Advanced loaf incorporating a yeast liquid ferment (levain) alongside a mature lactic starter.", "science": "Symbiotic yeast and lactic bacterial balances maximize gas production and flavor depth.", "roi": "Time Intensive / Maximum Oven Spring", "tip": "Ensure the liquid ferment is active and bubbly before mixing."}
                ],
                3: [
                    {"name": "Ancient Einkorn & Wild Honey Sourdough", "desc": "Experimental loaf combining ancient einkorn flour with raw wildflower honey and elderberry ferment.", "science": "Einkorn's weak gluten proteins and sticky starch require precise low hydration and quick baking.", "roi": "High Risk / Historic Ancestral Flavor Profile", "tip": "Dust generously with flour and bake in a hot preheated dutch oven to hold shape."},
                    {"name": "Spiced Emmer & Fig Sourdough", "desc": "Experimental recipe utilizing fresh-milled ancient emmer wheat and dry black mission figs.", "science": "Emmer's high gluten strength is balanced by enzymatic activity from dried fruit sugar.", "roi": "Artisanal / Complex Sweet & Savory Profile", "tip": "Chop figs finely to prevent large gas pocket voids around fruit zones."},
                    {"name": "Smoked Water & Spelt Sourdough", "desc": "Experimental loaf using wood-smoked water and fresh-milled spelt grains.", "science": "Spelt's high extensibility allows massive gas bubbles, while smoke phenols preserve the crumb.", "roi": "High Effort / Heavy Campfire Aromatics", "tip": "Bake in a cast iron pot to capture the escaping aromatic smoke oils."},
                    {"name": "Spontaneous Wild Berry Ferment", "desc": "Experimental sourdough using a starter cultivated from wild juniper and blackberry skins.", "science": "Wild yeasts present on berry skins add unique ester profiles and ester-based aromas.", "roi": "High Risk / Hyper-Local Botanical Profile", "tip": "Keep ambient room warm (78F) to encourage wild microbes."},
                    {"name": "Khorasan & Kamut Hearth Loaf", "desc": "Experimental high-hydration ancient Khorasan loaf featuring a golden crumb and sweet flavor.", "science": "Khorasan starches are highly soluble, creating a rich cream-colored custard interior.", "roi": "High Skill / Rich Creamy Crumb Structure", "tip": "Use cold water for mixing to maintain dough structure during folding."}
                ]
            }
        }

        # Check if active archetype is in the predefined database
        if active_archetype_id in db:
            for lvl in [1, 2, 3]:
                for idx, item in enumerate(db[active_archetype_id][lvl]):
                    recipes.append({
                        "recipe_id": f"{active_archetype_id}_level{lvl}_{idx+1}",
                        "recipe_name": item["name"],
                        "creativity_level": lvl,
                        "description": item["desc"],
                        "recommended_grain_ids": [grain_slug(g) for g in inventory[:2]] if lvl == 3 and len(inventory) >= 2 else pref_slugs,
                        "sidebar_science_profile": item["science"],
                        "sidebar_ai_insight": {
                            "labor_roi": item["roi"],
                            "last_10_percent_magic": item["tip"]
                        }
                    })
        else:
            # High quality fallback generator using rich descriptors to avoid placeholders
            fallbacks = {
                1: [
                    {"suffix": "Traditional Base", "desc": "A traditional, highly reliable base recipe prioritizing pure grain expression and standard, steady fermentation cycles.", "science": "Relies on standard hydration and predictable microbial activity for stable, consistent gluten sheet development.", "roi": "Low Effort / 100% Reliable", "tip": "Keep mixing times brief to avoid building excessive elastic memory in the gluten chains."},
                    {"suffix": "Daily Standard", "desc": "An optimized daily formula designed for consistent, high-yield crumb structure under standard kitchen conditions.", "science": "Utilizes simple ambient proof cycles to match moderate, stable moisture conditions.", "roi": "High Volume / Safe Daily Return", "tip": "Cover the vessel with a damp lint-free cloth to prevent dry flour skinning."},
                    {"suffix": "Farmhouse Homestead", "desc": "A rustic farmhouse recipe incorporating a small percentage of whole-grain flour to enhance mineral complexity.", "science": "Bran minerals act as biological stimulants, accelerating yeast activity and cell wall expansion.", "roi": "Low Effort / Balanced Crust Flavor", "tip": "Slash the loaf with a quick, assertive blade motion at 45 degrees to optimize oven spring."},
                    {"suffix": "Heritage Country Style", "desc": "Traditional country style formula featuring clean yeast activity and balanced hydration.", "science": "Focuses on steady CO2 release to form regular, medium-sized cell distributions.", "roi": "Minimal Supervision / Classic Crumb", "tip": "Sprinkle fine semolina flour on the loader to prevent sticking during high-heat transfers."},
                    {"suffix": "Simple Hearth Formula", "desc": "A baseline, no-fuss formulation designed for beginner bakers using standard home ovens.", "science": "Relies on extended autolytic hydration to naturally relax gluten sheets without machine kneading.", "roi": "Hands-off / High Success Rate", "tip": "Place a preheated cast-iron skillet on the bottom rack to act as a heat buffer."}
                ],
                2: [
                    {"name_addon": "High-Hydration Modernist", "desc": "An advanced variation with optimized hydration ratios and pre-ferments to create a glossy, open alveolar crumb.", "science": "Pushes water saturation to the starch ceiling, maximizing steam expansion channels during bake.", "roi": "High Return / Open Glossy Structure", "tip": "Perform a lamination stretch on a wet work surface to build early structural memory."},
                    {"name_addon": "Cultured Lactic Infusion", "desc": "A modern profile incorporating cultured dairy or preferments to achieve a subtle lactic tang and soft center.", "science": "Lactic acids weaken the gluten matrix chemically, rendering the crumb highly uniform and tender.", "roi": "Skill Intensive / Tangy Aromatics", "tip": "Extend bulk fermentation by 30 minutes to maximize lactic acid buildup."},
                    {"name_addon": "Double-Preferment Blend", "desc": "A multi-stage build using both poolish and biga preferments for complex organic flavor profile.", "science": "Dual ferment dynamics yield high enzyme variety, breaking down complex starches into simple sugars.", "roi": "Patience Required / Deep Flavor Profile", "tip": "Mix the preferments at least 12 hours ahead at a cool 65°F environment."},
                    {"name_addon": "Enzymatic Malt Boosted", "desc": "An advanced recipe utilizing diastatic malt adjustments to accelerate starch modification and crust coloration.", "science": "Amylase enzymes break down starches into fermentable maltose, boosting yeast activity and Maillard browning.", "roi": "Moderate Effort / Deep Amber Crust", "tip": "Do not exceed 0.5% malt concentration to prevent a sticky, gummy crumb structure."},
                    {"name_addon": "Autolysed Honey Glazed", "desc": "Modern formulation utilizing an extended autolyse phase and wildflower honey hydration.", "science": "Hygroscopic honey molecules retain moisture post-bake, extending crumb softness and freshness.", "roi": "Moderate Return / Soft Custard Interior", "tip": "Keep the oven steam high for the first 10 minutes to prevent the honey sugars from caramelizing too quickly."}
                ],
                3: [
                    {"name_addon": "Ancient Emmer & Fig", "desc": "An experimental profile utilizing ancient emmer wheat flour and dried organic fruit inclusions.", "science": "Emmer's dense protein content is balanced by fruit enzymes, creating a rich savory-sweet contrast.", "roi": "Artisanal / Unique Sweet & Savory Complexity", "tip": "Add dried fruit only during the final folding sequence to prevent tearing the gluten sheet."},
                    {"name_addon": "Spelt & Charred Oak Smoke", "desc": "Experimental recipe using wood-smoked water hydration and high-extensibility ancient spelt flour.", "science": "Weak spelt gluten is supported by high-absorption starch matrices, yielding a dense, rich savory bite.", "roi": "High Risk & Skill / Smoky Complex Aromatics", "tip": "Use a preheated heavy dutch oven to hold the steam and capture the smoky aromatic oils."},
                    {"name_addon": "Spontaneous Berry Ferment", "desc": "An experimental recipe relying on a wild ferment cultivated directly from wild berry skins.", "science": "Wild yeasts present on botanical skins introduce unique ester profiles and floral aromas.", "roi": "High Risk / Hyper-Local Botanical Expression", "tip": "Maintain a warm 78°F proofing box to sustain the delicate wild microbes."},
                    {"name_addon": "Savory Dark Rye & Stout", "desc": "Experimental formulation replacing water with local dark stout beer and using dark rye flour.", "science": "High pentosan content in rye starch binds water tightly, creating a sticky, fudgy, highly savory structure.", "roi": "High Skill / Heavy Roasted Malt Savory Bite", "tip": "Dust the proofing basket generously with rice flour to prevent sticky rye from clinging."},
                    {"name_addon": "Heirloom Einkorn & Bourbon", "desc": "An experimental profile with weak-gluten ancient einkorn and bourbon-soaked vanilla bean.", "science": "Einkorn's high carotenoid content produces a beautiful yellow crumb with high melt-in-the-mouth tenderness.", "roi": "Artisanal / Complex Dessert Aromatics", "tip": "Bake at a slightly lower temperature (325°F) to avoid scorching the fragile ancient starches."}
                ]
            }

            for lvl in [1, 2, 3]:
                for idx, fallback_item in enumerate(fallbacks[lvl]):
                    if lvl == 1:
                        name = f"{arch_title} - {fallback_item['suffix']}"
                    else:
                        name = f"{fallback_item['name_addon']} {arch_title}"
                    recipes.append({
                        "recipe_id": f"{active_archetype_id}_level{lvl}_{idx+1}",
                        "recipe_name": name,
                        "creativity_level": lvl,
                        "description": fallback_item["desc"],
                        "recommended_grain_ids": [grain_slug(g) for g in inventory[:2]] if lvl == 3 and len(inventory) >= 2 else pref_slugs,
                        "sidebar_science_profile": fallback_item["science"],
                        "sidebar_ai_insight": {
                            "labor_roi": fallback_item["roi"],
                            "last_10_percent_magic": fallback_item["tip"]
                        }
                    })

        return {"recipes": recipes}

    elif expected_keys and "generated_variants" in expected_keys:
        engine_id = user_data.get("engine_id", "hearth")
        archetype_id = user_data.get("active_archetype_id", "")
        creativity_level = user_data.get("creativity_level")

        # Build grain name slug list from inventory for recommended_grain_ids
        inventory = user_data.get("inventory", [])
        hard_grains = [b for b in inventory if "hard" in b.get("hardness", "").lower()]
        soft_grains = [b for b in inventory if "soft" in b.get("hardness", "").lower() or b.get("hardness") == "ancient"]

        def grain_slug(g):
            return g.get("name", "").lower().replace(" ", "_").replace("/", "").replace("-", "_")

        hard_slugs = [grain_slug(g) for g in hard_grains[:2]] or ["hard_red_spring_wheat"]
        soft_slugs = [grain_slug(g) for g in soft_grains[:2]] or ["soft_white_wheat"]
        pref_slugs = hard_slugs if engine_id in ["hearth", "pan", "bath", "pasta"] else soft_slugs

        if creativity_level is not None:
            c_lvl = int(creativity_level)
            if c_lvl == 1:
                variants = [
                    {
                        "variant_id": f"{archetype_id}_l1_alt1",
                        "variant_name": f"Traditional Country {engine_id.title()}",
                        "recommended_grain_ids": pref_slugs[:1],
                        "sidebar_science_profile": "Traditional low-hydration approach focusing on structural strength and regular hole distribution.",
                        "sidebar_ai_insight": {
                            "labor_roi": "Low Effort / High Reliability",
                            "last_10_percent_magic": "Extend bulk fermentation by 20 minutes if room temperature drops below 70°F."
                        }
                    },
                    {
                        "variant_id": f"{archetype_id}_l1_alt2",
                        "variant_name": f"Rustic Farmhouse {engine_id.title()}",
                        "recommended_grain_ids": pref_slugs[:2] if len(pref_slugs) >= 2 else pref_slugs,
                        "sidebar_science_profile": "Baseline standard with a small whole-wheat addition for increased tannin and ash content.",
                        "sidebar_ai_insight": {
                            "labor_roi": "Low Effort / Balanced Flavor",
                            "last_10_percent_magic": "Use a light dusting of rye flour on the proofing basket to enhance crust crispiness."
                        }
                    },
                    {
                        "variant_id": f"{archetype_id}_l1_alt3",
                        "variant_name": f"Quick-Rise {engine_id.title()}",
                        "recommended_grain_ids": pref_slugs[:1],
                        "sidebar_science_profile": "Adjusted yeast percentage to accelerate bulk fermentation without collapsing gluten walls.",
                        "sidebar_ai_insight": {
                            "labor_roi": "Fast Turnaround / Commercial Standard",
                            "last_10_percent_magic": "Add 0.5% malt powder to promote yeast activity and speed up browning."
                        }
                    }
                ]
            elif c_lvl == 2:
                variants = [
                    {
                        "variant_id": f"{archetype_id}_l2_alt1",
                        "variant_name": f"High-Hydration Modern {engine_id.title()}",
                        "recommended_grain_ids": pref_slugs,
                        "sidebar_science_profile": "Elevated hydration profile demanding double-hydration mixing techniques to trap maximum water.",
                        "sidebar_ai_insight": {
                            "labor_roi": "High Effort / Maximum Extensibility",
                            "last_10_percent_magic": "Add the final 5% of formula water slowly at the end of the mixing cycle to avoid breaking gluten bonds."
                        }
                    },
                    {
                        "variant_id": f"{archetype_id}_l2_alt2",
                        "variant_name": f"Long-Cold Ferment {engine_id.title()}",
                        "recommended_grain_ids": pref_slugs,
                        "sidebar_science_profile": "Starch conversion optimization through a 24-hour cold retardation, developing organic acids.",
                        "sidebar_ai_insight": {
                            "labor_roi": "Medium Effort / Premium Flavor Complex",
                            "last_10_percent_magic": "Bake immediately from the refrigerator to maximize oven spring contrast."
                        }
                    },
                    {
                        "variant_id": f"{archetype_id}_l2_alt3",
                        "variant_name": f"Autolysed Modern {engine_id.title()}",
                        "recommended_grain_ids": pref_slugs,
                        "sidebar_science_profile": "Enzymatic flour self-development stage before yeast addition, maximizing extensibility.",
                        "sidebar_ai_insight": {
                            "labor_roi": "Low Active Effort / Great Yield",
                            "last_10_percent_magic": "Perform a 60-minute autolyse at room temperature before adding starter or yeast."
                        }
                    }
                ]
            else:
                variants = [
                    {
                        "variant_id": f"{archetype_id}_l3_alt1",
                        "variant_name": f"Spontaneous Ancient {engine_id.title()}",
                        "recommended_grain_ids": [grain_slug(g) for g in soft_grains] or pref_slugs,
                        "sidebar_science_profile": "Highly experimental formula using 100% Spelt or ancient grains for a soft, weak gluten profile.",
                        "sidebar_ai_insight": {
                            "labor_roi": "Delicate Handling / Unique Crumb Texture",
                            "last_10_percent_magic": "Reduce final proofing time by 30% to prevent over-acidification from weakening the weak ancient gluten."
                        }
                    },
                    {
                        "variant_id": f"{archetype_id}_l3_alt2",
                        "variant_name": f"Wild Inclusion {engine_id.title()}",
                        "recommended_grain_ids": pref_slugs,
                        "sidebar_science_profile": "Incorporation of secondary solids at 20% baker's weight. Gluten network must sustain the weight of inclusion particles.",
                        "sidebar_ai_insight": {
                            "labor_roi": "High Effort / Premium Culinary Value",
                            "last_10_percent_magic": "Fold inclusions in during the second stretch-and-fold cycle to distribute them evenly without tearing gluten sheets."
                        }
                    },
                    {
                        "variant_id": f"{archetype_id}_l3_alt3",
                        "variant_name": f"Extreme Hydration Porridge {engine_id.title()}",
                        "recommended_grain_ids": pref_slugs,
                        "sidebar_science_profile": "Gelatinized flour porridge addition (tangzhong method) to carry water up to 90% baker's math equivalent.",
                        "sidebar_ai_insight": {
                            "labor_roi": "High Effort / Ultra-Soft Custardy Crumb",
                            "last_10_percent_magic": "Cook the porridge portion to exactly 150°F (65°C) and let it cool completely before mixing."
                        }
                    }
                ]
        else:
            # Original fallback behavior
            from grainlab.engines.router import ENGINES
            engine = ENGINES.get(engine_id)
            archetype_data = getattr(engine, "archetypes", {}).get(archetype_id, {})
            affinity = archetype_data.get("grain_affinity", "high_protein")

            if affinity == "high_protein":
                preferred = hard_grains or inventory
            elif affinity == "medium_protein":
                preferred = hard_grains or inventory
            else:
                preferred = soft_grains or inventory

            preferred_slugs = [grain_slug(g) for g in preferred[:2]] or ["hard_red_spring_wheat"]
            archetype_label = archetype_data.get("label", archetype_id.replace("_", " ").title())

            variants = [
                {
                    "variant_id": f"{archetype_id}_v1_classic",
                    "variant_name": f"Classic {archetype_label}",
                    "recommended_grain_ids": preferred_slugs[:1],
                    "sidebar_science_profile": (
                        f"The Classic {archetype_label} formula follows traditional baker's percentages with a conservative hydration ceiling. "
                        f"High-protein grain stocks in the recommended tier supply the gluten elasticity ceiling required for oven spring."
                    ),
                    "sidebar_ai_insight": {
                        "labor_roi": "High Priority / Absolute Foundation",
                        "last_10_percent_magic": (
                            f"Focus on a 30-minute bench rest after shaping to relax the gluten sheets before the final bake. "
                            f"This single step transforms a good {archetype_label} into an exceptional one."
                        )
                    }
                },
                {
                    "variant_id": f"{archetype_id}_v2_high_hydration",
                    "variant_name": f"High-Hydration {archetype_label}",
                    "recommended_grain_ids": preferred_slugs,
                    "sidebar_science_profile": (
                        f"An elevated hydration profile pushes starch gelatinization beyond the baseline threshold. "
                        f"Open crumb development accelerates but gluten must compensate with additional folding cycles. "
                        f"Grain selection is critical — only high-absorption stocks can carry the extra water without structural collapse."
                    ),
                    "sidebar_ai_insight": {
                        "labor_roi": "Medium Priority / High-Skill Payoff",
                        "last_10_percent_magic": (
                            f"Incorporate 3 sets of stretch-and-fold during the first 90 minutes of bulk fermentation. "
                            f"This aligns gluten sheets without mechanical kneading, preserving the open crumb structure."
                        )
                    }
                },
                {
                    "variant_id": f"{archetype_id}_v3_heritage_blend",
                    "variant_name": f"Heritage Grain {archetype_label}",
                    "recommended_grain_ids": [grain_slug(g) for g in inventory[:2]] if len(inventory) >= 2 else preferred_slugs,
                    "sidebar_science_profile": (
                        f"A multi-grain heritage blend introduces pentosan content and varied protein profiles. "
                        f"The blend complexity adds depth of flavor and subtle textural contrast, but demands careful water absorption calibration."
                    ),
                    "sidebar_ai_insight": {
                        "labor_roi": "High Priority / Flavor Differentiation",
                        "last_10_percent_magic": (
                            f"Pre-soak ancient or soft grain portions in 20% of the formula water for 30 minutes before mixing. "
                            f"This equalizes hydration rates across the diverse grain matrix and prevents gummy pockets."
                        )
                    }
                }
            ]

        return {"generated_variants": variants}

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
        # Mock get_sidebar_insight_ai
        hovered = user_data.get("hovered_element", "").lower()
        preset = user_data.get("preset_slug", "")
        category = user_data.get("category_slug", "")
        
        is_cookie = "cookie" in preset or "cookie" in (category or "").lower()
        
        if "soft white" in hovered:
            if is_cookie:
                return {
                    "recommendation_tier": "recommended",
                    "labor_roi_rating": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Soft White Wheat provides an exceptionally tender crumb for Chewy Chocolate Chip Cookies by avoiding gluten toughness, which is critical for achieving a perfect melting spread.",
                    "elevate_recipe": "Substitute 10% of the soft white wheat with fresh-milled Rye to introduce pentosans that keep the cookie center chewy and gooey."
                }
            else:
                return {
                    "recommendation_tier": "not-recommended",
                    "labor_roi_rating": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Soft White Wheat completely lacks the gluten strength and elasticity required to support the rise of this bread, causing structural collapse.",
                    "elevate_recipe": "Use a high-protein hard wheat instead to ensure gas retention and optimal oven spring."
                }
        elif "rye" in hovered:
            if is_cookie:
                return {
                    "recommendation_tier": "recommended",
                    "labor_roi_rating": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Rye is highly recommended for Chewy Chocolate Chip Cookies due to pentosans blocking gluten to maximize cookie tenderness and moisture retention.",
                    "elevate_recipe": "Mix in 20% fresh-milled Rye with Soft White Wheat to create a unique flavor profile with caramelized notes."
                }
            else:
                return {
                    "recommendation_tier": "sub-optimal",
                    "labor_roi_rating": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Rye adds excellent complex, savory notes but its low gluten elasticity will produce a denser, stickier crumb structure.",
                    "elevate_recipe": "Blend 80% Hard Red Spring Wheat with 20% Rye to retain structural loft while capturing Rye's complex rustic flavor."
                }
        else:
            return {
                "recommendation_tier": "recommended",
                "labor_roi_rating": "High Priority / Worth the Extra Step",
                "last_10_percent_analysis": f"Using {hovered.title()} matches the target recipe requirements, contributing to optimal crumb texture and flavor balance.",
                "elevate_recipe": "Ensure high-quality fresh ingredients are used and maintain precise hydration levels."
            }

    return None


_gemma_cache = {}


def call_gemma_api(system_prompt: str, user_prompt: str, expected_keys: list = None) -> dict | None:
    """
    Submits a structured prompt to local Gemma and parses the JSON response.
    Caches results in memory using a hash of the prompts.
    Returns None if any step fails.
    """
    if not _is_ai_enabled():
        return None

    import hashlib
    # Compute MD5 hash of prompts as cache key
    raw_key = f"{system_prompt}|||{user_prompt}"
    cache_key = hashlib.md5(raw_key.encode("utf-8")).hexdigest()

    if cache_key in _gemma_cache:
        logger.info(f"[AI] - Cache Hit - Key: {cache_key}")
        return _gemma_cache[cache_key]

    # Check if offline mock mode is active
    if getattr(settings, "MOCK_MODE", True):
        res = get_mock_gemma_response(system_prompt, user_prompt, expected_keys)
        if res:
            _gemma_cache[cache_key] = res
        return res

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
        # Enforce a 30-second timeout to allow the model sufficient time to load and generate responses
        response = requests.post(url, headers=headers, json=payload, timeout=30.0)
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
            
            _gemma_cache[cache_key] = parsed_json
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


def get_grain_advisory_ai(preset_slug: str, category_slug: str = None, selected_grains: str = None, only_evaluations: bool = False, only_elevate: bool = False) -> dict | None:
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
            return {"grain_evaluations": [], "elevate_recipe": []}
            
        selected_ids = [s.strip() for s in selected_grains.split(",") if s.strip()] if selected_grains else []
        selected_berries = [wb for wb in active_berries if str(wb.id) in selected_ids]
        selected_names = [wb.name for wb in selected_berries]

        expected_keys = ["grain_evaluations", "elevate_recipe"]

        if only_evaluations:
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
            expected_keys = ["grain_evaluations"]
        elif only_elevate:
            system_prompt = (
                "You are a baking science expert. Analyze the given bread/pastry preset and the active grain selections checked by the user.\n"
                "Provide 3 to 5 distinct, highly specific ways to enhance the outcome (e.g. methods like autolyse, preferments, cold retardation, or specific fat/liquid ratio tweaks), tailored specifically to build upon the user's active grain selections.\n"
                "\n"
                "Return a JSON object matching this schema:\n"
                "{\n"
                "  \"elevate_recipe\": [\n"
                "    \"string suggestion 1\",\n"
                "    \"string suggestion 2\",\n"
                "    \"string suggestion 3\"\n"
                "  ]\n"
                "}"
            )
            expected_keys = ["elevate_recipe"]
        else:
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
                "  ],\n"
                "  \"elevate_recipe\": [\n"
                "    \"string suggestion 1\",\n"
                "    \"string suggestion 2\",\n"
                "    \"string suggestion 3 (provide 3 to 5 distinct ways to enhance the outcome, specifically tailored to build upon the user's active grain selections)\"\n"
                "  ]\n"
                "}"
            )
        
        payload = {
            "preset_slug": preset_slug,
            "preset_name": preset.name if preset else preset_slug,
            "category_slug": category_slug,
            "selected_grains": selected_names,
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
        import re
        res = call_gemma_api(system_prompt, user_prompt, expected_keys=expected_keys)
        if res and isinstance(res, dict) and "grain_evaluations" in res:
            evaluations = res["grain_evaluations"]
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


def generate_recipe_variants(engine_id: str, active_archetype_id: str, inventory: list) -> dict | None:
    """
    Given the active engine slug, selected archetype ID, and inventory grain list,
    asks the LLM to generate a list of recipe variants with sidebar science profiles,
    AI insights, and recommended_grain_ids for golden highlight ring binding.
    Returns: { 'generated_variants': [ {...}, ... ] } or None on failure.
    """
    import json

    system_prompt = (
        "You are a baking science variant generator. Given an engine type and structural archetype, "
        "generate 3 distinct recipe variants optimized for fresh-milled whole grains. "
        f"CRITICAL: The variants must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        "You are strictly prohibited from generating recipes crossing over into other archetypes or categories. "
        "Each variant must match this JSON schema:\n"
        "{\n"
        "  \"generated_variants\": [\n"
        "    {\n"
        "      \"variant_id\": \"unique_slug\",\n"
        "      \"variant_name\": \"Human readable variant label\",\n"
        "      \"recommended_grain_ids\": [\"grain_name_slug\"],\n"
        "      \"sidebar_science_profile\": \"1-2 sentence technical science profile for this variant\",\n"
        "      \"sidebar_ai_insight\": {\n"
        "        \"labor_roi\": \"One-liner labor return on investment\",\n"
        "        \"last_10_percent_magic\": \"Specific craft tip to elevate from good to exceptional\"\n"
        "      }\n"
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
    })

    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["generated_variants"])
        if result and isinstance(result.get("generated_variants"), list):
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_recipe_variants: {str(e)}")

    # Fall back to mock in all cases when AI is not active or fails
    mock = get_mock_gemma_response(system_prompt, user_prompt, expected_keys=["generated_variants"])
    return mock


def generate_creativity_recipes(engine_id: str, active_archetype_id: str, inventory: list) -> dict | None:
    """
    Given the engine slug, selected archetype ID, and inventory grain list, asks the LLM to generate
    exactly 15 recipe profiles (5 per Creativity Level: 1, 2, and 3).
    """
    import json

    system_prompt = (
        "You are a baking science expert. Given an engine type, target archetype, and inventory grain list, "
        "generate exactly 15 distinct recipe profiles matching these three Creativity Levels (exactly 5 recipes per level):\n"
        f"CRITICAL: All 15 generated recipe profiles must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        "You are strictly prohibited from generating recipes crossing over into other archetypes or categories.\n"
        "- Creativity Level 1: Baseline Standard Profiles. (Simple, standard, reliable profiles).\n"
        "- Creativity Level 2: Advanced Modern Profiles. (More advanced hydration, techniques, or modern touches).\n"
        "- Creativity Level 3: Experimental/Complex Profiles. (Unusual grain blends, high hydration, complex preferments, or inclusions).\n"
        "\n"
        "Each recipe must match this JSON schema:\n"
        "{\n"
        "  \"recipes\": [\n"
        "    {\n"
        "      \"recipe_id\": \"unique_slug\",\n"
        "      \"recipe_name\": \"Human readable title\",\n"
        "      \"creativity_level\": 1,  // must be 1, 2, or 3\n"
        "      \"description\": \"1-2 sentence description explaining the recipe structure\",\n"
        "      \"recommended_grain_ids\": [\"grain_name_slug\"],\n"
        "      \"sidebar_science_profile\": \"1-2 sentence technical science profile\",\n"
        "      \"sidebar_ai_insight\": {\n"
        "        \"labor_roi\": \"One-liner labor return on investment\",\n"
        "        \"last_10_percent_magic\": \"Specific craft tip to elevate the bake\"\n"
        "      }\n"
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
    })

    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["recipes"])
        if result and isinstance(result.get("recipes"), list):
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_creativity_recipes: {str(e)}")

    # Fall back to mock
    mock = get_mock_gemma_response(system_prompt, user_prompt, expected_keys=["recipes"])
    return mock


def generate_creativity_variants(engine_id: str, creativity_level: int, active_archetype_id: str, inventory: list) -> dict | None:
    """
    Given the engine, target creativity level, parent recipe, and inventory grain list,
    asks the LLM to generate 3 alternative recipe variations matching ONLY that creativity level.
    """
    import json

    system_prompt = (
        f"You are a baking science expert. Given an engine type, a parent recipe ID, and a target Creativity Level of {creativity_level}, "
        f"generate exactly 3 alternative structural profile variations matching ONLY that creativity level.\n"
        f"CRITICAL: The variations must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        f"You are strictly prohibited from generating recipes crossing over into other archetypes or categories.\n"
        "\n"
        "Each variation must match this JSON schema:\n"
        "{\n"
        "  \"generated_variants\": [\n"
        "    {\n"
        "      \"variant_id\": \"unique_slug\",\n"
        "      \"variant_name\": \"Human readable variant label\",\n"
        "      \"recommended_grain_ids\": [\"grain_name_slug\"],\n"
        "      \"sidebar_science_profile\": \"1-2 sentence technical science profile for this variant\",\n"
        "      \"sidebar_ai_insight\": {\n"
        "        \"labor_roi\": \"One-liner labor return on investment\",\n"
        "        \"last_10_percent_magic\": \"Specific craft tip to elevate from good to exceptional\"\n"
        "      }\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "IMPORTANT: recommended_grain_ids must be lowercase name slugs matching grains from the provided inventory. "
        "Return ONLY raw JSON with no markdown fences."
    )

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "creativity_level": creativity_level,
        "active_archetype_id": active_archetype_id,
        "inventory": inventory,
    })

    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["generated_variants"])
        if result and isinstance(result.get("generated_variants"), list):
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_creativity_variants: {str(e)}")

    # Fall back to mock
    mock = get_mock_gemma_response(system_prompt, user_prompt, expected_keys=["generated_variants"])
    return mock

