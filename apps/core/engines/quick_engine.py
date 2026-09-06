from apps.core.engines.base_engine import BaseEngine


class QuickEngine(BaseEngine):
    name = "Quick Breads & Scones Engine"
    slug = "quick"
    default_binder_pct = 0.20
    default_leaven_pct = 0.025
    target_protein_min = 8.5
    target_protein_max = 10.5
    gluten_behavior = "Zero Gluten Development. Mechanical kneading is banned; structure relies entirely on chemical leavening reactions to yield a tender, crumbly interior."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Requires clean, buttery fats to come forward without whole-grain astringency."
    tannin_sensitive = True
    variations = {
        "light_fluffy": {
            "label": "Light & Fluffy",
            "mechanics_overrides": {
                "required_gluten_elasticity": "minimal_to_none",
                "optimal_protein_window": "8.0% - 9.5%",
            },
            "culinary_nuance_directive_append": (
                "CRITICAL: The user selected LIGHT & FLUFFY. The crumb must be extremely tender and well-aerated. "
                "Favor low-protein soft wheats (Pastry flour, Spelt) and rely heavily on chemical leavening. "
                "Use liquid fats (oil or melted butter) and buttermilk to keep the crumb perfectly soft."
            ),
        },
        "dense_moist": {
            "label": "Dense & Moist (Bakery Style)",
            "mechanics_overrides": {"required_gluten_elasticity": "moderate", "optimal_protein_window": "9.5% - 11.0%"},
            "culinary_nuance_directive_append": (
                "CRITICAL: The user selected DENSE & MOIST. The crumb should be rich, heavy, and satisfying. "
                "You can use slightly stronger grains or whole grains here. Increase heavy inclusions, use sour cream "
                "or yogurt for moisture, and ensure the batter is thick enough to suspend large chunks of fruit or chocolate."
            ),
        },
    }
    production_profile = {
        "thermodynamic_focus": "crystalline_fat_preservation",
        "mechanical_energy_threshold": "minimal_folding",
        "permissible_action_types": ["cut_in", "fold"],
        "environmental_rest_strategy": "gluten_relaxation",
    }
    secondary_ingredients = {
        "lipids": {
            "default": "unsalted_butter",
            "options": ["unsalted_butter", "salted_butter", "coconut_oil", "avocado_oil"],
            "math_modifiers": {"salted_butter": {"target_target": "salt", "subtract_percentage": 0.015}},
        },
        "liquids": {
            "default": "pure_water",
            "options": ["pure_water", "whole_milk", "heavy_cream", "buttermilk"],
            "math_modifiers": {"buttermilk": {"trigger_chemical_leavening_acid_flag": True}},
        },
        "binders": {"default": "none", "options": ["none", "whole_eggs", "egg_whites", "aquafaba_vegan"]},
    }

    permissible_form_factors = {
        "standard-8x4-loaf-pan": {
            "name": "Standard 8x4 Loaf Pan",
            "tier": "recommended",
            "is_portioned": False,
            "unit_weight": 800.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "loaf",
            "unit_label_plural": "loaves",
            "bake_temp_f": 350,
            "bake_time_min": 50,
            "steam_required": False,
            "is_enriched_profile": True,
        },
        "muffin-cupcake-tin": {
            "name": "Muffin / Cupcake Tin",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 70.0,
            "base_count": 12,
            "step_increment": 12,
            "unit_label": "muffin",
            "unit_label_plural": "muffins",
            "bake_temp_f": 375,
            "bake_time_min": 20,
            "steam_required": False,
            "is_enriched_profile": True,
        },
        "individual-wedge-sheet": {
            "name": "Individual Wedge Sheet",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 70.0,
            "base_count": 12,
            "step_increment": 12,
            "unit_label": "scone",
            "unit_label_plural": "scones",
            "bake_temp_f": 400,
            "bake_time_min": 18,
            "steam_required": False,
            "is_enriched_profile": True,
        },
    }

    presets = [
        "Southern Buttermilk Biscuits",
        "Flaky Cream Scones",
        "Irish Soda Bread",
        "Classic Banana Bread",
        "Spiced Pumpkin Loaf",
        "Sweet Skillet Cornbread",
        "Blueberry Muffins",
        "Zucchini Bread",
    ]

    archetypes = {
        "chemical_loaf": {
            "default_form_factor": "standard-8x4-loaf-pan",
            "default_salt_pct": 0.0075,
            "label": "Chemical Loaf",
            "icon": "🍞",
            "description": "Thick pourable batters baked slowly in high-walled pans like Banana or Soda Bread.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "8.5% - 10.5%",
            },
            "culinary_nuance_directive": (
                "Focus on uniform gas retention from rapid acid-base neutralization within a thick, pourable matrix. "
                "Gluten development must be suppressed to ensure a tender, cake-like slice. Look for low-protein grains "
                "or high-pentosan ancient grains that absorb liquid smoothly, allowing fruit sugars or starches to stabilize "
                "the high-walled crumb walls slowly during the long baking window without developing elasticity."
            ),
        },
        "layered_scone": {
            "default_form_factor": "individual-wedge-sheet",
            "default_salt_pct": 0.0075,
            "label": "Layered Wedge Scone",
            "icon": "🍰",
            "description": "Laminated dry-shred flakes cut into solid clean triangles.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.0%",
            },
            "culinary_nuance_directive": (
                "Focus on the strict preservation of solid fat crystal domains to drive physical steam lamination. Grains must "
                "exhibit low protein binding capacity to prevent moisture from initiating a continuous dough web. Highly reward "
                "highly friable starch profiles that maintain clean, non-elastic geometric wedge cuts, flashing into short, "
                "flaky layers as the fat melts out in the oven."
            ),
        },
        "dropped_biscuit": {
            "default_form_factor": "individual-wedge-sheet",
            "default_salt_pct": 0.0075,
            "label": "Dropped / Cut Biscuit",
            "icon": "🧁",
            "description": "High vertical expansion rounds utilizing shortening pockets for flaky separation.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.0%",
            },
            "culinary_nuance_directive": (
                "Focus on maximizing sudden vertical steam expansion while maintaining zero horizontal spread. Grains must have "
                "low protein elasticity to ensure complete tenderness. Look for soft white wheats that tolerate brief, "
                "delicate hand-folding around cold fat pockets, allowing rapid chemical carbon dioxide release to lift the biscuit "
                "into distinct, flaky layers."
            ),
        },
        "textured_muffin": {
            "default_form_factor": "muffin-cupcake-tin",
            "default_salt_pct": 0.0075,
            "label": "Textured Muffin",
            "icon": "🧁",
            "description": "Individual cup-bounded portions prioritizing a domed, porous crown.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "8.5% - 10.5%",
            },
            "culinary_nuance_directive": (
                "Focus on pourable emulsion physics and rapid outer starch setting. Passing quick-acting chemical leavening "
                "must expand the inner crumb, pushing the center upward into a high, porous, beautifully domed crown "
                "before the perimeter structural walls set."
            ),
        },
    }

    def get_diagnostic_insight(self, item_id: str) -> dict:
        from .insights_fallbacks import SWEET_FALLBACKS

        insight = SWEET_FALLBACKS.get(item_id)
        if not insight and item_id.startswith("grain_"):
            for k, val in SWEET_FALLBACKS.items():
                if k.startswith("grain_") and (k in item_id or item_id in k):
                    insight = val
                    break
        return insight or {
            "labor_roi": "Low Priority / Minor Textural Return",
            "last_10_percent_analysis": "An objective workspace configuration parameter. No significant performance anomalies or hidden labor opportunities detected.",
        }

    def get_flavor_bases(self, creativity_level: int) -> list:
        if creativity_level <= 3:
            return ["Vanilla Bean & Brown Butter", "Double Chocolate", "Lemon Zest & Buttermilk"]
        else:
            return ["Matcha & White Chocolate", "Earl Grey & Lavender", "Miso Caramel & Pecan"]

    def get_ai_flavor_directive(self) -> str:
        return "Do not call them 'Spelt Cookie' or 'Rye Cake'. Use creative but clear culinary names."

    def get_ai_structural_directive(self) -> str:
        return "For example, tender confections generally do not need a 'proofing_environment' or 'shaping_surface'."

    def get_sensory_benchmark(
        self,
        grain_type: str,
        flour_maturity: str,
        effective_hydration: float,
        category_slug: str = None,
        preset_slug: str = None,
    ) -> str:
        grain_name = grain_type.replace("_", " ").title()
        desc = f"For fresh-milled {grain_name} confections: "
        if category_slug == "cookies-shortbread":
            desc += "Expect a thick, soft paste or firm chilled dough. The fat should be fully creamed with flour particles evenly coated to control spread. "
        elif category_slug == "cakes-batters":
            desc += "Expect a highly aerated, smooth fluid batter. It should hold micro-air bubbles from egg/fat whipping with zero large pockets. "
        else:
            desc += "The batter/dough should be delicate and soft. Mixing should be kept to an absolute minimum to ensure a tender crumb. "

        if flour_maturity == "just_milled":
            desc += "As this flour was milled today, its enzymes will promote fast browning. Keep mixing short to avoid any accidental gluten development."
        elif flour_maturity == "dead_zone":
            desc += "Caution: Flour is in the 1-2 week dead zone. The structural proteins are slightly unstable. Bake promptly after mixing to ensure the rise sets correctly."
        else:
            desc += "Flour is fully matured. It will provide a highly stable, predictable structure and excellent tender mouthfeel."
        return desc

    def apply_sub_class_constraints(
        self, hydration: float, fat: float, sugar: float, leaven: float, salt: float, leaven_type: str = "yeast"
    ) -> tuple[float, float, float, float, float]:
        hyd = max(0.0, min(0.80, hydration))
        f = max(0.0, min(0.80, fat))
        s = max(0.0, min(0.80, sugar))
        if leaven_type == "sourdough":
            leaven = max(0.0, min(0.60, leaven))
        elif leaven_type == "chemical":
            leaven = max(0.0, min(0.10, leaven))
        else:
            leaven = max(0.0, min(0.015, leaven))
        salt = max(0.0, min(0.10, salt))
        return hyd, f, s, leaven, salt

    def get_ai_culinary_directive(self) -> str:
        return "Quick breads require chemical leavening. Specify the correct amount of baking powder, and if acidic liquids are present, include baking soda. Zero yeast should be used. This is a quick bread (biscuits, scones, muffins). For sweet profiles (muffins, sweet scones), use sugar and sweet inclusions. For savory profiles (savory biscuits), omit sugar and use savory additions. You MUST include a chemical leavener (baking powder/soda), lipids, and liquids."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives (like berries, nuts, or chocolate chips), use true baker's percentages (flour = 100%). For quick breads, these typically range from 30.0 to 100.0. CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile. CRITICAL: For chemical leaveners (baking powder, baking soda), strictly limit to 1.0 to 5.0 to avoid chemical taste. If total lipid fat exceeds 30.0%, total liquid MUST NOT exceed 85.0%."

    def get_live_timeline_steps(
        self,
        recipe_data: dict,
        estimated_bulk_minutes: int,
        estimated_proof_minutes: int,
        bake_time_min: int,
        mixing_method: str = "stand_mixer",
        **kwargs,
    ) -> list[dict]:
        dry_min = 2
        fat_min = 5
        fold_min = 3

        preset_slug = kwargs.get("preset_slug") or ""

        is_muffin_method = False
        if "loaf" in preset_slug.lower() or "muffin" in preset_slug.lower() or "bread" in preset_slug.lower():
            is_muffin_method = True

        if is_muffin_method:
            steps = [
                {
                    "key": "mix",
                    "name": "Dry & Leavener Blend",
                    "duration_sec": dry_min * 60,
                    "desc": "Whisk flour, sugar, salt, and chemical leaveners. Ensures uniform distribution for immediate chemical neutralization.",
                    "is_mix": True,
                },
                {
                    "key": "fat_cut",
                    "name": "Wet Mix (Muffin Method)",
                    "duration_sec": fat_min * 60,
                    "desc": "Whisk wet ingredients and melted fat together thoroughly.",
                },
                {
                    "key": "fold",
                    "name": "Wet into Dry Fold",
                    "duration_sec": fold_min * 60,
                    "desc": "Fold the wet mixture into the dry ingredients gently using a spatula, just until dry pockets disappear. Do NOT over-mix or batter will be tough!",
                    "is_knead": True,
                },
                {
                    "key": "bake",
                    "name": "Zero-Rise Thermal Bake",
                    "duration_sec": bake_time_min * 60,
                    "desc": "Bake immediately in preheated oven. Chemical carbon dioxide releases instantly and sets the tender crumb structure.",
                    "is_bake": True,
                },
            ]
        else:
            steps = [
                {
                    "key": "mix",
                    "name": "Dry & Leavener Blend",
                    "duration_sec": dry_min * 60,
                    "desc": "Whisk flour, sugar, salt, and chemical leaveners. Ensures uniform distribution for immediate chemical neutralization.",
                    "is_mix": True,
                },
                {
                    "key": "fat_cut",
                    "name": "Fat Cutting & Cold Lock",
                    "duration_sec": fat_min * 60,
                    "desc": "Cut cold butter/fat into the dry mix until it forms pea-sized crumbs. Keep ingredients cold to form steam pocket layers.",
                },
                {
                    "key": "fold",
                    "name": "Minimal Spatula Fold",
                    "duration_sec": fold_min * 60,
                    "desc": "Pour in liquid. Fold gently by hand using a spatula just until dry pockets disappear. Do NOT over-mix or knead to avoid structural gluten activation!",
                    "is_knead": True,
                },
                {
                    "key": "bake",
                    "name": "Zero-Rise Thermal Bake",
                    "duration_sec": bake_time_min * 60,
                    "desc": "Bake immediately in preheated oven. Chemical carbon dioxide releases instantly and sets the tender crumb structure.",
                    "is_bake": True,
                },
            ]

        preset_slug = kwargs.get("preset_slug", "")
        if "muffin" in preset_slug.lower() or "scone" in preset_slug.lower():
            cooling_desc = "Allow to cool in the pan for 5 minutes before transferring to a wire rack. Serve warm or at room temperature."
            cooling_duration = 15
        else:
            cooling_desc = "Allow the quick bread to cool in the pan for 10-15 minutes, then turn out onto a wire rack to cool completely before slicing."
            cooling_duration = 60

        steps.append(
            {
                "key": "cool",
                "name": "Pan & Wire Rack Cooling",
                "duration_sec": cooling_duration * 60,
                "desc": cooling_desc,
            }
        )

        return steps
