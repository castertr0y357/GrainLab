from grainlab.engines.base_engine import BaseEngine

class ChouxEngine(BaseEngine):
    name = "Choux Paste Engine"
    slug = "choux"
    target_protein_min = 12.0
    target_protein_max = 13.5
    gluten_behavior = "High Starch Gelatinization & High Elasticity. Matrix must actively bind massive egg moisture volumes, expanding violently into a hollow, self-supporting structural shell via steam inflation."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Requires a neutral background to allow rich egg-custard components to dominate."
    tannin_sensitive = True
    production_profile = {
        "thermodynamic_focus": "hydration_binding_shock",
        "mechanical_energy_threshold": "moderate_shearing",
        "permissible_action_types": ["knead", "cream"],
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
            "default": "whole_eggs",
            "options": ["none", "whole_eggs", "egg_whites", "aquafaba_vegan"]
        }
    }

    permissible_form_factors = {
        "extrusion-piping-sheet": {
            "name": "Extrusion Piping Sheet / Silpat",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 45.0,
            "base_count": 12,
            "step_increment": 12,
            "unit_label": "portion",
            "unit_label_plural": "portions",
            "bake_temp_f": 425,
            "bake_time_min": 20,
            "steam_required": True,
            "is_enriched_profile": True,
        }
    }

    presets = [
        "Chocolate Éclairs", "Cream Puffs (Profiteroles)", "Savory Cheese Gougères",
        "French Crullers", "Traditional Churros", "Paris-Brest Pastries"
    ]

    archetypes = {
        "eclair_log": {
            "label": "Éclair / Log",
            "icon": "🍫",
            "description": "Piped oblong tube. Steam from the high-water paste creates a hollow interior for cream filling. Precise piping width controls surface expansion.",
            "grain_affinity": "low_protein",
        },
        "puff_sphere": {
            "label": "Cream Puff / Sphere",
            "icon": "🧁",
            "description": "Piped round mound. Convex dome created by uniform steam expansion. Hollow center sized by paste stiffness and egg ratio.",
            "grain_affinity": "low_protein",
        },
        "savory_gougere": {
            "label": "Savory Gougère",
            "icon": "🧀",
            "description": "Cheese-enriched choux sphere. Cheese adds fat that reduces steam drive slightly, requiring slightly stiffer paste consistency.",
            "grain_affinity": "low_protein",
        },
        "piped_churro": {
            "label": "Piped / Extruded (Churro)",
            "icon": "🌀",
            "description": "Star-piped log for direct frying or baking. Must be stiff enough to hold its star shape during extrusion.",
            "grain_affinity": "low_protein",
        },
    }

    def calculate_recipe(self, **kwargs) -> dict:
        recipe = super().calculate_recipe(**kwargs)
        
        # Calculate egg weight (typically 110% of flour weight for classic choux paste)
        flour_g = recipe["flour_weight"]
        egg_g = round(flour_g * 1.10, 1)
        
        recipe["egg_weight"] = egg_g
        recipe["substitution_notes"] = recipe.get("substitution_notes", []) + [
            f"Progressive Egg Integration: Prepare approximately {egg_g}g of beaten whole eggs (roughly 2-3 medium eggs). Add incrementally to check consistency.",
            "Gelatinization Cook: Starch must be cooked in boiling water/butter before mixing in eggs to allow moisture-absorption."
        ]
        
        recipe["yeast_weight"] = 0.0
        recipe["starter_weight"] = 0.0
        return recipe

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        boil_min = 3
        cook_min = 4
        cool_min = 5
        egg_min = 8
        
        # Split bake time into high expansion puffing and drying phases
        puff_min = 15
        dry_min = max(10, bake_time_min - puff_min)

        return [
            {
                "key": "boil",
                "name": "Boil Liquid & Fat",
                "duration_sec": boil_min * 60,
                "desc": "Heat water, milk, butter, and salt in a saucepan until boiling and fat is fully melted."
            },
            {
                "key": "cook",
                "name": "Pan Gelatinization Cook",
                "duration_sec": cook_min * 60,
                "desc": "Add all flour at once. Cook over medium-high heat, stirring vigorously, until the mixture pulls away from the pan sides and forms a film on the bottom (pre-gelatinizes starch).",
                "is_mix": True
            },
            {
                "key": "cool",
                "name": "Cooling Rest",
                "duration_sec": cool_min * 60,
                "desc": "Transfer dough ball to a mixing bowl. Let rest to cool below 140°F so eggs do not scramble when added."
            },
            {
                "key": "eggs",
                "name": "Egg Integration & V-Stage",
                "duration_sec": egg_min * 60,
                "desc": "Add eggs incrementally, mixing thoroughly after each. Evaluate the paste structure: stop adding eggs when it achieves a glossy, smooth 'V-stage' ribbon droop from the spatula.",
                "is_knead": True
            },
            {
                "key": "puff_bake",
                "name": "Oven Expansion Bake",
                "duration_sec": puff_min * 60,
                "desc": "Bake at high heat (425°F). Moisture steam-flashes inside the paste, expanding shells to triple their volume. Do NOT open the oven door during this phase!",
                "is_bake": True
            },
            {
                "key": "dry_bake",
                "name": "Dry Setting Bake",
                "duration_sec": dry_min * 60,
                "desc": "Reduce heat to 375°F. Pierce shell walls to vent trapped steam and dry until golden, crisp, and hollow.",
                "is_bake": True
            }
        ]
