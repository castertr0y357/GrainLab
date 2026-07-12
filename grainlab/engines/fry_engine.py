from grainlab.engines.base_engine import BaseEngine

class FryEngine(BaseEngine):
    name = "Fried Doughs Engine"
    slug = "fry"
    target_protein_min = 11.5
    target_protein_max = 13.0
    gluten_behavior = "Rapid Gas Expansion & Fat Resistance. Surface must expand immediately and seal against rapid convection liquid heat to lock out excess frying oil absorption."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Demands a warm, clean, light baseline suitable for immediate sugar/glaze applications."
    tannin_sensitive = True
    production_profile = {
        "thermodynamic_focus": "biological_yeast_activity",
        "mechanical_energy_threshold": "high_kneading",
        "permissible_action_types": ["knead"],
        "environmental_rest_strategy": "gas_proofing",
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
        "high-volume-oil-vat": {
            "name": "High-Volume Cast Iron Oil Vat",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 65.0,
            "base_count": 12,
            "step_increment": 12,
            "unit_label": "donut",
            "unit_label_plural": "donuts",
            "bake_temp_f": 375,
            "bake_time_min": 5,
            "steam_required": False,
            "is_enriched_profile": True,
        }
    }

    presets = [
        "Yeast-Raised Donuts", "Fluffy New Orleans Beignets", "Puffed Sopapillas",
        "Traditional Native Frybread", "Cake Donuts", "Apple Fritters",
        "Crullers (Fried Execution)"
    ]

    archetypes = {
        "yeast_raised_donut": {
            "label": "Yeast-Raised Donut",
            "icon": "🍩",
            "description": "Highly aerated, light, floating dough rings.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "11.0% - 13.0%"
            }
        },
        "cake_donut": {
            "label": "Cake / Chemical Donut",
            "icon": "🍩",
            "description": "Tender, friable, batter-based rings dropping directly into fat.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.5%"
            }
        },
        "fritter_beignet": {
            "label": "Batter Fritter / Beignet",
            "icon": "☁️",
            "description": "Irregular high-hydration moisture puffs expanding violently in oil.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "high_spread",
                "moisture_lipid_ratio": "high_hydration_lean",
                "optimal_protein_window": "9.0% - 11.0%"
            }
        },
        "fried_laminate": {
            "label": "Fried Laminated",
            "icon": "🫓",
            "description": "Alternating layers flashing open instantly in convection fat.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "10.0% - 12.0%"
            }
        },
    }

    def calculate_recipe(self, **kwargs) -> dict:
        recipe = super().calculate_recipe(**kwargs)
        
        # Oil recovery temperature dip calculations:
        # Frying target is 365°F. The oil temp drops ~10°F when cool dough is introduced.
        fry_temp_target = 365.0
        oil_preheat = fry_temp_target + 10.0
        
        recipe["substitution_notes"] = recipe.get("substitution_notes", []) + [
            f"Hydro-Convection Frying: Preheat frying oil to {oil_preheat}°F. Once dough is dropped, the active temperature recovery dip will stabilize near {fry_temp_target}°F.",
            "Drainage rest: Drain fried pieces on a elevated wire rack rather than flat paper towels to prevent soggy skin condensation."
        ]
        return recipe

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        mix_min = 8
        proof_min = estimated_proof_minutes or 45
        
        # Side A & B frying steps (measured in seconds!)
        side_a_sec = 120
        flip_sec = 10
        side_b_sec = 120
        
        return [
            {
                "key": "mix",
                "name": "Dough Mix & Knead",
                "duration_sec": mix_min * 60,
                "desc": "Mix ingredients to form a soft, supple leavened dough. Knead until smooth.",
                "is_mix": True
            },
            {
                "key": "proof",
                "name": "Portion & Proof",
                "duration_sec": proof_min * 60,
                "desc": "Roll out and cut into shapes. Proof on parchment squares until airy and delicate.",
                "is_proof": True
            },
            {
                "key": "preheat",
                "name": "Oil Preheat & Recovery Check",
                "duration_sec": 10 * 60,
                "desc": "Heat neutral fry oil to 375°F. Confirm your drainage racks, spider tools, and coatings are ready."
            },
            {
                "key": "fry_a",
                "name": "Fry Side A",
                "duration_sec": side_a_sec,  # 120 seconds
                "desc": "Gently drop proofed dough into hot oil. Fry Side A. Watch for rapid expansion and bubble formation.",
                "is_bake": True  # Treat fry as bake for countertop template readouts
            },
            {
                "key": "flip",
                "name": "Flip Prompt",
                "duration_sec": flip_sec,  # 10 seconds
                "desc": "⚠️ FLIP IMMEDIATELY! Use metal chopsticks or a spider tool to turn the dough over in the hot oil."
            },
            {
                "key": "fry_b",
                "name": "Fry Side B",
                "duration_sec": side_b_sec,  # 120 seconds
                "desc": "Fry Side B until golden brown and cooked through. Ensure internal temperature reaches 195°F.",
                "is_bake": True
            },
            {
                "key": "drain",
                "name": "Drain & Cool",
                "duration_sec": 5 * 60,
                "desc": "Transfer to wire rack to drain excess oil. Glaze or coat in sugar while warm."
            }
        ]
