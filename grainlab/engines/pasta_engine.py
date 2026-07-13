from grainlab.engines.base_engine import BaseEngine

class PastaEngine(BaseEngine):
    name = "Fresh Pasta & Noodles Engine"
    slug = "pasta"
    target_protein_min = 12.5
    target_protein_max = 15.0
    gluten_behavior = "High Plastic Deformation, Zero Leavening. Requires an ultra-dense, low-hydration network that maintains a firm, snap-resistant 'al dente' structural bite when boiled."
    flavor_affinity = "Tannin Tolerant (Rustic/Savory). Welcomes rich egg, nutty semolina, or distinctive alkaline noodle mineral complexities."
    tannin_sensitive = False
    production_profile = {
        "thermodynamic_focus": "hydration_binding_shock",
        "mechanical_energy_threshold": "mechanical_compaction",
        "permissible_action_types": ["knead", "sheet", "extrude"],
        "environmental_rest_strategy": "gluten_relaxation",
    }
    secondary_ingredients = {
        "liquids": {
            "default": "pure_water",
            "options": ["pure_water", "whole_milk", "heavy_cream", "buttermilk"],
            "math_modifiers": {
                "buttermilk": { "trigger_chemical_leavening_acid_flag": True }
            }
        },
        "binders": {
            "default": "whole_eggs",
            "options": ["none", "whole_eggs", "egg_whites", "aquafaba_vegan"]
        }
    }

    permissible_form_factors = {
        "mechanical-sheeter": {
            "name": "Mechanical Sheeter Sheets / Cutters",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 120.0,
            "base_count": 4,
            "step_increment": 2,
            "unit_label": "serving",
            "unit_label_plural": "servings",
            "bake_temp_f": 0,
            "bake_time_min": 0,
            "steam_required": False,
            "is_enriched_profile": False,
        },
        "high-pressure-dies": {
            "name": "High-Pressure Extrusion Dies",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 120.0,
            "base_count": 4,
            "step_increment": 2,
            "unit_label": "serving",
            "unit_label_plural": "servings",
            "bake_temp_f": 0,
            "bake_time_min": 0,
            "steam_required": False,
            "is_enriched_profile": False,
        }
    }

    presets = [
        "Fresh Egg Tagliatelle", "Fettuccine Sheets", "Ravioli / Tortellini Dough",
        "Semolina Extruded Rigatoni", "Thick Hand-Cut Udon", "Alkaline Wheat Ramen Noodles",
        "Gyoza / Dumpling Wrappers"
    ]

    archetypes = {
        "sheeted_ribbon": {
            "label": "Sheeted Ribbon Pastas",
            "icon": "🍝",
            "description": "Gradual reduction sheeting cut into strands like Tagliatelle or Fettuccine.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "12.5% - 15.0%"
            },
            "culinary_nuance_directive": (
                "Focus on extreme protein density and absolute plastic deformation. Grains must allow the stiff, low-hydration matrix "
                "to be rolled down to sub-millimeter thickness through sequential mechanical passes without snapping back, locking "
                "starches inside the web to ensure a firm 'al dente' bite when boiled."
            )
        },
        "stuffed_pocket": {
            "label": "Stuffed / Encased Pockets",
            "icon": "🥟",
            "description": "High-elasticity envelopes meant to seal wet fillings securely like Ravioli.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "12.0% - 14.5%"
            },
            "culinary_nuance_directive": (
                "Focus on high structural extensibility and watertight protein cross-linking. The matrix must form a dense, flexible "
                "envelope that seals damp fillings securely, stretching cleanly without tearing or leaching starches when dropped into "
                "rolling boiling water."
            )
        },
        "extruded_shape": {
            "label": "Extruded Die Shapes",
            "icon": "🔩",
            "description": "High-pressure compression matrix tubes or hollows like Rigatoni.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "13.0% - 15.0%"
            },
            "culinary_nuance_directive": (
                "Focus on maximum high-pressure compaction stability. The flour must yield an ultra-dense, non-elastic protein web "
                "that forces smoothly through mechanical dies, retaining sharp structural ridges and hollows without losing shape or "
                "turning gummy when boiled."
            )
        },
        "alkaline_noodles": {
            "label": "Alkaline Cut Noodles",
            "icon": "🍜",
            "description": "Mineral-fortified strings built for snap and yellow coloration like Ramen.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "12.0% - 14.5%"
            },
            "culinary_nuance_directive": (
                "Focus on high tensile snap and mineral-induced protein compaction. Grains must provide a clean, high-protein background "
                "that interacts with alkaline salts to accelerate snapping elasticity, keeping the strands firm and springy while "
                "resisting grey structural discoloration."
            )
        },
    }

    def apply_sub_class_constraints(self, hydration: float, fat: float, sugar: float, texture_score: int, crumb_score: int) -> tuple[float, float, float]:
        # Egg-to-semolina hydration boundary limits restricted to strict 35% to 40% metrics
        pasta_hyd = max(0.35, min(0.40, hydration))
        return pasta_hyd, fat, sugar

    def calculate_recipe(self, **kwargs) -> dict:
        recipe = super().calculate_recipe(**kwargs)
        
        # Heavy mechanical dough compaction metrics:
        # Strict zero-leavening calculation maps:
        recipe["yeast_weight"] = 0.0
        recipe["starter_weight"] = 0.0
        
        recipe["substitution_notes"] = recipe.get("substitution_notes", []) + [
            "Dense Pasta Compaction: Zero-leavening recipe. Hydration is locked to 35-40% for pasta structure.",
            "Roller Passes: Sheet dough down using sequential passes (from Setting 0 to Setting 6/7) to align proteins."
        ]
        return recipe

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        mix_min = 6
        knead_min = 10
        rest_min = 30
        roll_min = 15
        cut_min = 10

        return [
            {
                "key": "mix",
                "name": "Compaction Mix",
                "duration_sec": mix_min * 60,
                "desc": "Combine flour/semolina and eggs/water. The mixture will look extremely dry and crumbly; press firmly to compact into a solid mass.",
                "is_mix": True
            },
            {
                "key": "knead",
                "name": "Compaction Knead",
                "duration_sec": knead_min * 60,
                "desc": "Knead vigorously by hand on a clean surface. Press and fold to force hydration of dense semolina starches. The dough will become smooth and very firm.",
                "is_knead": True
            },
            {
                "key": "proof", # Use proof key to fit the countertop proof alerts if needed
                "name": "Plastic Hydration Rest",
                "duration_sec": rest_min * 60,
                "desc": "Wrap dough tightly in plastic wrap. Rest at room temperature. Allows moisture to equilibrate and the rigid gluten matrix to relax.",
                "is_proof": True
            },
            {
                "key": "roll_pass",
                "name": "Mechanical Roller Passes",
                "duration_sec": roll_min * 60,
                "desc": "Divide dough into portions. Run through roller Setting 0, fold, and repeat. Set thickness down incrementally one setting at a time until reaching Setting 6 or 7 (~1.2mm)."
            },
            {
                "key": "bake",  # Use bake key for final phase cook/dry tracking
                "name": "Dust, Cut & Air-Dry",
                "duration_sec": cut_min * 60,
                "desc": "Dust sheet with semolina flour. Cut into noodles (e.g. tagliatelle) or wrappers. Let dry on a rack or cook immediately in boiling salted water.",
                "is_bake": True
            }
        ]
