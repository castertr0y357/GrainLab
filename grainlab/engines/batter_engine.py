from grainlab.engines.base_engine import BaseEngine

class BatterEngine(BaseEngine):
    name = "Cakes & Batters Engine"
    slug = "batter"
    target_protein_min = 7.5
    target_protein_max = 9.5
    gluten_behavior = "Complete Absence of Gluten. High-ratio sugar and liquid dispersion requires structure built purely on starch gelatinization and egg protein coagulation."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Demands a completely neutral grain baseline to host delicate vanilla, citrus, or fruit fats."
    tannin_sensitive = True
    production_profile = {
        "thermodynamic_focus": "lipid_emulsification",
        "mechanical_energy_threshold": "low_emulsifying",
        "permissible_action_types": ["cream", "fold"],
        "environmental_rest_strategy": "gluten_relaxation",
    }
    secondary_ingredients = {
        "lipids": {
            "default": "unsalted_butter",
            "options": ["unsalted_butter", "salted_butter", "coconut_oil", "avocado_oil"],
            "math_modifiers": {
                "salted_butter": { "target_target": "salt", "subtract_percentage": 0.015 }
            }
        },
        "liquids": {
            "default": "pure_water",
            "options": ["pure_water", "whole_milk", "heavy_cream", "buttermilk"],
            "math_modifiers": {
                "buttermilk": { "trigger_chemical_leavening_acid_flag": True }
            }
        },
        "binders": {
            "default": "none",
            "options": ["none", "whole_eggs", "egg_whites", "aquafaba_vegan"]
        }
    }

    permissible_form_factors = {
        "straight-sided-round-tin": {
            "name": "Straight-Sided Round Tin",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 500.0,
            "base_count": 2,
            "step_increment": 2,
            "unit_label": "layer",
            "unit_label_plural": "layers",
            "bake_temp_f": 350,
            "bake_time_min": 30,
            "steam_required": False,
            "is_enriched_profile": True,
        },
        "high-border-sheet-pan": {
            "name": "High-Border Sheet Cake Pan",
            "tier": "recommended",
            "is_portioned": False,
            "unit_weight": 1000.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "pan",
            "unit_label_plural": "pans",
            "bake_temp_f": 350,
            "bake_time_min": 25,
            "steam_required": False,
            "is_enriched_profile": True,
        },
        "cupcake-liner-matrix": {
            "name": "Cupcake Liner Matrix",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 41.67,
            "base_count": 24,
            "step_increment": 24,
            "unit_label": "cupcake",
            "unit_label_plural": "cupcakes",
            "bake_temp_f": 350,
            "bake_time_min": 20,
            "steam_required": False,
            "is_enriched_profile": True,
        }
    }

    presets = [
        "Yellow Layer Cake", "Fudgy Chocolate Cake", "Victoria Sponge",
        "Chiffon Cake", "Angel Food Cake", "Traditional Pound Cake",
        "Madeleines", "Vanilla Cupcakes", "Buttermilk Pancakes",
        "Belgian Waffles"
    ]

    archetypes = {
        "sponge_cake": {
            "label": "Foam / Sponge Cake",
            "icon": "🍰",
            "description": "Fat-free or low-fat aeration systems like Genoise or Chiffon.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "8.0% - 9.5%"
            },
            "culinary_nuance_directive": (
                "Focus entirely on egg-protein foam stabilization and complete gluten suppression. Grains must have minimal "
                "protein content to prevent structural toughness, allowing delicate egg-cell walls to expand unhindered "
                "while relying purely on gentle liquid starch gelatinization to set a feather-light, aerated crumb."
            )
        },
        "creamed_cake": {
            "label": "Creamed Layer Cake",
            "icon": "🎂",
            "description": "Emulsified lipid-sugar crystal structures for standard layers.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "8.0% - 10.0%"
            },
            "culinary_nuance_directive": (
                "Focus on lipid-sugar crystal aeration and uniform emulsion stability. Low-protein grains are mandatory to "
                "prevent unwanted gluten strands during liquid integration. Flour starches must absorb moisture smoothly "
                "to encapsulate fat phases uniformly, preventing batter separation and ensuring a velvety, tender layered structure."
            )
        },
        "pound_cake": {
            "label": "High-Ratio Pound Cake",
            "icon": "🍫",
            "description": "Dense, uniform crumb carrying massive sugar and fat weights.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.5%"
            },
            "culinary_nuance_directive": (
                "Focus on managing high-ratio sugar and lipid loads within a dense, uniform crumb matrix. Grains must maximize "
                "tender starch swelling without developing elastic protein networks, allowing the batter to hold massive "
                "butter and sugar weights without collapsing or leaving greasy pockets."
            )
        },
        "griddle_batter": {
            "label": "Fluid Griddle Batter",
            "icon": "🥞",
            "description": "High-moisture pourable structures like Pancakes, Waffles, and Crepes.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "high_spread",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "8.5% - 10.5%"
            },
            "culinary_nuance_directive": (
                "Focus on pourable hydration mechanics and rapid surface heat transfer. Grains must allow instant liquid "
                "dispersion and minimal viscosity development. Texture relies on swift starch gelatinization upon hot "
                "iron contact, forming crisp outer grids while keeping the interior soft and aerated."
            )
        },
    }

    def apply_sub_class_constraints(self, hydration: float, fat: float, sugar: float, texture_score: int, crumb_score: int) -> tuple[float, float, float]:
        # High-ratio cake batters allow sugar and fat to scale independently and exceed 100% of flour weight
        # Thus, no downward ceilings are applied here.
        return hydration, fat, sugar

    def get_ai_culinary_directive(self) -> str:
        return "This is a batter. Recommend a specific emulsification style (e.g. whipped egg foam, creamed butter) to aerate the dough, and ensure zero yeast is used."

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        preset_slug = kwargs.get("preset_slug", "")
        if "chiffon" in preset_slug.lower() or "angel" in preset_slug.lower():
            emuls_desc = "Whip egg whites/yolks with sugar to soft peaks. Creates the micro-bubbles needed for rise without chemical leavening."
        elif "cupcake" in preset_slug.lower() or "pancake" in preset_slug.lower() or "waffle" in preset_slug.lower():
            emuls_desc = "Mix flour, sugar, leavening, and butter together first until sandy. Prevents excess gluten structure from forming when liquid is added."
        else:
            emuls_desc = "Cream softened butter and sugar at medium-high speed for 5-6 minutes until pale and fluffy. Traps air bubbles inside the fat crystals."

        return [
            {
                "key": "mix",
                "name": "Emulsification Phase",
                "duration_sec": 6 * 60,
                "desc": emuls_desc,
                "is_mix": True
            },
            {
                "key": "fold",
                "name": "Dry Sift & Fold",
                "duration_sec": 4 * 60,
                "desc": "Fold in sifted flour and dry ingredients gently using a rubber spatula. Avoid over-mixing to maintain emulsion structure."
            },
            {
                "key": "liquid_stream",
                "name": "Liquid Stream Addition",
                "duration_sec": 3 * 60,
                "desc": "Stream in eggs/milk/liquids slowly while mixing on low speed to maintain emulsion stability."
            },
            {
                "key": "bake",
                "name": "Cake Stencil Bake",
                "duration_sec": bake_time_min * 60,
                "desc": "Bake in prepared pans. Air bubbles expand and starches gelatinize to form a tender crumb structure.",
                "is_bake": True
            }
        ]
