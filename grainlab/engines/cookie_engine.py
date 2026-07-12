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
            }
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
            }
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
            }
        },
        "rolled_cutout": {
            "label": "Rolled Cutout",
            "icon": "⭐",
            "description": "Zero-spread formulation maintaining clean geometric edges post-bake.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "9.0% - 11.0%"
            }
        },
    }

    def calculate_recipe(self, **kwargs) -> dict:
        recipe = super().calculate_recipe(**kwargs)
        
        # Calculate horizontal cookie spread coefficient based on fat & sugar percentages
        fat_pct = recipe["effective_fat_pct"] / 100.0
        sugar_pct = recipe["effective_sugar_pct"] / 100.0
        hydration_pct = recipe["effective_hydration_pct"] / 100.0
        
        # Spread coefficient formula: fat and sugar promote spreading, water/moisture holds structure.
        spread_coef = round((fat_pct * 1.5 + sugar_pct * 1.2) / (hydration_pct if hydration_pct > 0 else 1.0), 2)
        recipe["spread_coefficient"] = spread_coef
        
        # Textural slider chew/crisp balances
        texture_score = kwargs.get("texture_score", 50)
        chew_pct = texture_score
        crisp_pct = 100 - texture_score
        
        recipe["substitution_notes"] = recipe.get("substitution_notes", []) + [
            f"Horizontal Spread Coefficient: {spread_coef} (Fat/sugar melt threshold balance). High spread means wider, thinner cookies.",
            f"Textural Balance: Recipe is adjusted for {chew_pct}% chewy chewiness vs. {crisp_pct}% snap crispiness."
        ]
        
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
