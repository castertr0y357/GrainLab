from grainlab.engines.base_engine import BaseEngine

class CookieEngine(BaseEngine):
    name = "Cookies & Shortbread Engine"
    slug = "cookie"
    target_protein_min = 8.5
    target_protein_max = 10.5
    gluten_behavior = "Minimal Gluten Interaction. Flour must allow melting fats and sugars to spread horizontally before the crumb structure sets in the oven."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Designed for toasted brown sugars and confections; whole-grain bitterness clashes aggressively."
    tannin_sensitive = True
    production_profile = {
        "thermodynamic_focus": "lipid_emulsification",
        "mechanical_energy_threshold": "low_emulsifying",
        "permissible_action_types": ["cream", "fold"],
        "environmental_rest_strategy": "fat_solidification",
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
        "heavy-aluminum-sheet": {
            "name": "Heavy Aluminum Cookie Sheet",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 40.0,
            "base_count": 24,
            "step_increment": 12,
            "unit_label": "cookie",
            "unit_label_plural": "cookies",
            "bake_temp_f": 350,
            "bake_time_min": 12,
            "steam_required": False,
            "is_enriched_profile": True,
        },
        "continuous-bar-pan": {
            "name": "Continuous Bar Pan / Single Layer",
            "tier": "sub-optimal",
            "is_portioned": False,
            "unit_weight": 960.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "pan",
            "unit_label_plural": "pans",
            "bake_temp_f": 350,
            "bake_time_min": 25,
            "steam_required": False,
            "is_enriched_profile": True,
        }
    }

    presets = [
        "Chewy Chocolate Chip Cookies", "Oatmeal Raisin Bakes", "Buttery Shortbread Wedges",
        "Italian Almond Biscotti", "Gingerbread People", "French Almond Macarons",
        "Snickerdoodles", "Classic Sugar Cookies"
    ]

    archetypes = {
        "drop_cookie": {
            "label": "Drop Cookie",
            "icon": "🍪",
            "description": "Irregular mounds designed to flow into tender discs.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "high_spread",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.5%"
            },
            "culinary_nuance_directive": (
                "Focus heavily on achieving minimal gluten elasticity and maximum horizontal spread. "
                "CRITICAL PHYSICS: High pentosan concentrations (found in grains like Rye) are highly RECOMMENDED. "
                "Because pentosans aggressively absorb and hoard water, they starve wheat proteins of the hydration "
                "required to form gluten webs, naturally ensuring a perfectly tender, gooey center. "
                "FLAVOR COMPATIBILITY: Strictly sensitive to high-astringent red wheat tannins, which create bitter notes. "
                "However, neutral or low-malty ancient profiles (like Rye or Spelt) are excellent choices that introduce "
                "desirable culinary depth without clashing with confections."
            )
        },
        "bar_cookie": {
            "label": "Bar / Slab",
            "icon": "🍫",
            "description": "Continuous uniform block baking, minimizing perimeter crisping.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.5%"
            },
            "culinary_nuance_directive": (
                "Focus on perimeter stability and controlled horizontal expansion. Grains must preserve a tender, short crumb "
                "that slices cleanly without shattering, while providing enough uniform starch walls to hold heavy inclusion "
                "weights across a continuous slab pan without center sinking."
            )
        },
        "slice_bake": {
            "label": "Slice & Bake",
            "icon": "🔪",
            "description": "Log configuration, highly compressed fat crystals for crisp rings.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.0%"
            },
            "culinary_nuance_directive": (
                "Focus on high compression crystal arrays and clean circular margins. Dough demands maximum fat-crystal packing "
                "with minimal protein resilience, allowing chilled logs to be sheeted or sliced cleanly without dragging crumbs, "
                "baking into uniform, crisp rings."
            )
        },
        "rolled_cutout": {
            "label": "Rolled Cutout",
            "icon": "📐",
            "description": "Zero-spread formulation maintaining clean geometric edges post-bake.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "9.0% - 11.0%"
            },
            "culinary_nuance_directive": (
                "Focus on moderate structural extensibility and zero thermal flow. Grains must allow the dough to accept "
                "sharp die-cutting and release cleanly from rolling mats, holding precise geometric definitions and sharp "
                "borders under immediate oven heat."
            )
        }
    }

    def calculate_recipe(self, **kwargs) -> dict:
        recipe = super().calculate_recipe(**kwargs)
        recipe["yeast_weight"] = 0.0
        recipe["starter_weight"] = 0.0
        return recipe

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        cream_min = 5
        fold_min = 3
        chill_min = 60
        bake_min = bake_time_min

        return [
            {
                "key": "mix",
                "name": "Cream Fat & Sugar",
                "duration_sec": cream_min * 60,
                "desc": "Beat butter and sugar together until light and fluffy. Dissolving sugar partially in fat helps manage the final oven spread coefficient.",
                "is_mix": True
            },
            {
                "key": "fold",
                "name": "Fold Dry & Inclusions",
                "duration_sec": fold_min * 60,
                "desc": "Fold in flour, salt, and inclusions (chocolate chips, oats) just until combined. Do not over-work to keep the crumb tender."
            },
            {
                "key": "chill",
                "name": "Fridge Chilling Rest",
                "duration_sec": chill_min * 60,
                "desc": "Mandatory refrigeration rest. Chilling solidifies butter fat (slowing spread) and hydrates flour completely for a chewier center."
            },
            {
                "key": "bake",
                "name": "Horizontal Spread Bake",
                "duration_sec": bake_min * 60,
                "desc": "Scoop dough balls onto sheet pan. Bake until edges are set and golden, watching horizontal expansion spread. Center will set soft.",
                "is_bake": True
            }
        ]
