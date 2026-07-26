from grainlab.engines.base_engine import BaseEngine

class PanEngine(BaseEngine):
    name = "Enriched & Soft Engine"
    slug = "pan"
    target_protein_min = 11.5
    target_protein_max = 13.0
    gluten_behavior = "High Shreddability. Must possess enough structural lift to support heavy lipid loads (butter, sugar, milk, egg yolks) without collapsing."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Demands a clean, sweet, milky baseline; whole-grain bitterness is an active defect."
    tannin_sensitive = True
    supported_tweaks = ["hydration", "leavening", "enrichment"]
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
        "standard-9x5-pan": {
            "name": "Standard 9x5 Loaf Pan",
            "tier": "recommended",
            "is_portioned": False,
            "unit_weight": 900.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "loaf",
            "unit_label_plural": "loaves",
            "bake_temp_f": 375,
            "bake_time_min": 45,
            "steam_required": False,
            "is_enriched_profile": False,
        },
        "pullman-pan-lidded": {
            "name": "Pullman Pan (Lidded)",
            "tier": "recommended",
            "is_portioned": False,
            "unit_weight": 900.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "loaf",
            "unit_label_plural": "loaves",
            "bake_temp_f": 375,
            "bake_time_min": 45,
            "steam_required": False,
            "is_enriched_profile": False,
        },
        "individual-portion-sheet": {
            "name": "Individual Portion Sheet",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 90.0,
            "base_count": 12,
            "step_increment": 12,
            "unit_label": "bun",
            "unit_label_plural": "buns",
            "bake_temp_f": 375,
            "bake_time_min": 20,
            "steam_required": False,
            "is_enriched_profile": True,
        }
    }

    presets = [
        "Everyday White Sandwich Loaf", "Rich Brioche", "Traditional Challah",
        "Hokkaido Milk Bread", "Soft Burger Buns", "Dinner Rolls",
        "Cinnamon Rolls", "Chocolate Babka", "Monkey Bread"
    ]

    archetypes = {
        "sandwich_pan": {
            "label": "Sandwich Pan Loaf",
            "icon": "🍞",
            "description": "Straight sidewall containment maximizing volume and thin slicing.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "11.0% - 13.0%"
            },
            "culinary_nuance_directive": (
                "Focus on maximizing vertical volume and achieving a uniform, tight cell structure. Grains must provide high protein "
                "retention to support thin sidewall pans, ensuring a soft, elastic crumb that slices cleanly without crumbling."
            )
        },
        "freeform_braided": {
            "label": "Freeform Braided Loaf",
            "icon": "🥯",
            "description": "High-tensile strands capable of holding shape without pan walls like Challah or Brioche.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "11.5% - 13.5%"
            },
            "culinary_nuance_directive": (
                "Focus on high structural retention and zero horizontal flow without pan walls. Grains must yield an elastic, highly "
                "cohesive protein backbone capable of holding intricate braided definition under heavy lipid and sugar enrichment "
                "weights without collapsing or slumping."
            )
        },
        "soft_dinner_roll": {
            "label": "Soft Dinner Roll",
            "icon": "🫓",
            "description": "Small batch pull-apart clusters prioritizing maximum steam-trapped softness.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "11.0% - 12.5%"
            },
            "culinary_nuance_directive": (
                "Focus on steam-trapped softness and excellent cluster lift. The protein web must remain extensible and resilient, "
                "allowing small batch dough clusters to crowd together and climb vertically, trapping internal moisture for a classic "
                "feather-light, pull-apart tear texture."
            )
        },
        "filled_sweet_roll": {
            "label": "Filled Sweet Roll",
            "icon": "🌀",
            "description": "Laminated or sheeted scroll structures built to contain heavy interior fillings.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "11.5% - 13.0%"
            },
            "culinary_nuance_directive": (
                "Focus on uniform dough-sheet stretch and high filling containment. The flour must provide an elastic, robust backbone "
                "capable of being rolled thin, scroll-shaped, and baked without rupturing or allowing heavy sweet fillings to cause "
                "structural collapse."
            )
        },
    }
    def get_ai_culinary_directive(self) -> str:
        return "Warn the user if the dough mass will overflow or underfill a standard 9x5 loaf pan."

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        mix_min = 6
        knead_min = 12 if mixing_method == "stand_mixer" else 18
        
        # Warm rise: enriched doughs rise slower, warm bulk rise is helpful
        bulk_min = estimated_bulk_minutes
        proof_min = estimated_proof_minutes

        return [
            {
                "key": "mix",
                "name": "Lipid Mix Phase",
                "duration_sec": mix_min * 60,
                "desc": "Combine flour, liquids, yeast, sugar, and egg yolks. Mix on low speed to establish the gluten base. Keep butter/fat separate for now to avoid premature coating of gluten proteins.",
                "is_mix": True
            },
            {
                "key": "knead",
                "name": "Intensive Dough Hook Knead",
                "duration_sec": knead_min * 60,
                "desc": "Slowly incorporate softened butter/fat in pieces while running the stand mixer. Knead intensively until the dough is silky, elastic, and clears the sides of the bowl.",
                "is_knead": True
            },
            {
                "key": "bulk",
                "name": "Enriched Bulk Ferment",
                "duration_sec": bulk_min * 60,
                "desc": "Enriched doughs ferment slower due to fat and sugar retardants. Keep in a warm, draft-free place."
            },
            {
                "key": "divide_portion",
                "name": "Loaf Sizing & Portioning",
                "duration_sec": 10 * 60,
                "desc": "Divide the dough into uniform portions for multi-loaf scaling. Shape into tight rounds or logs for baking."
            },
            {
                "key": "proof",
                "name": "Loaf Pan Final Proof",
                "duration_sec": proof_min * 60,
                "desc": "Transfer dough pieces into the greased baking pan. Proof until the dough reaches 1 inch above the pan rim.",
                "is_proof": True
            },
            {
                "key": "bake",
                "name": "Soft Crumb Bake",
                "duration_sec": bake_time_min * 60,
                "desc": "Bake at moderate heat (350-375°F). Rich sugars caramelize rapidly; shield loaf with foil if top browns too early.",
                "is_bake": True
            }
        ]
