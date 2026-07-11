from grainlab.engines.base_engine import BaseEngine

class BathEngine(BaseEngine):
    name = "Alkaline Bath Engine"
    slug = "bath"
    target_protein_min = 12.0
    target_protein_max = 14.0
    gluten_behavior = "Tight interior structure. Matrix must withstand a pre-bake boiling step without dissolving or losing shape."
    flavor_affinity = "Tannin Tolerant (Rustic/Savory). Designed to complement high Maillard browning, maltiness, and alkaline surface chemistry."
    tannin_sensitive = False
    production_profile = {
        "thermodynamic_focus": "biological_yeast_activity",
        "mechanical_energy_threshold": "high_kneading",
        "permissible_action_types": ["knead"],
        "environmental_rest_strategy": "gas_proofing",
    }
    secondary_ingredients = {}

    permissible_form_factors = {
        "perforated-baking-sheet": {
            "name": "Perforated Baking Sheet",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 110.0,
            "base_count": 8,
            "step_increment": 6,
            "unit_label": "portion",
            "unit_label_plural": "portions",
            "bake_temp_f": 425,
            "bake_time_min": 20,
            "steam_required": False,
            "is_enriched_profile": False,
        },
        "standard-silicon-mat-sheet": {
            "name": "Standard Silicon Mat Sheet",
            "tier": "sub-optimal",
            "is_portioned": True,
            "unit_weight": 110.0,
            "base_count": 8,
            "step_increment": 6,
            "unit_label": "portion",
            "unit_label_plural": "portions",
            "bake_temp_f": 425,
            "bake_time_min": 25,
            "steam_required": False,
            "is_enriched_profile": False,
        }
    }

    presets = [
        "Soft Bavarian Pretzels", "Traditional Boiled New York Bagels", "Pretzel Buns",
        "Sesame Simit", "Chewy Montreal Bagels", "Bavarian Pretzel Bites"
    ]

    archetypes = {
        "twisted_pretzel": {
            "label": "Twisted Pretzel",
            "icon": "🥨",
            "description": "Traditional knot shapes, maximize surface area for Maillard browning.",
            "grain_affinity": "high_protein",
        },
        "boiled_bagel": {
            "label": "Boiled Bagel",
            "icon": "🥯",
            "description": "Ring geometry, dense core structure, high tensile strength.",
            "grain_affinity": "high_protein",
        },
        "laugen_bun": {
            "label": "Laugen Bun / Roll",
            "icon": "🫓",
            "description": "Spherical soft-crumb interior protected by a thick glossy skin.",
            "grain_affinity": "high_protein",
        },
        "pretzel_stick": {
            "label": "Pretzel Stick / Cracker",
            "icon": "🥖",
            "description": "Ultra-low hydration, brittle, snapping structure.",
            "grain_affinity": "high_protein",
        },
    }

    def apply_sub_class_constraints(self, hydration: float, fat: float, sugar: float, texture_score: int, crumb_score: int) -> tuple[float, float, float]:
        # Stiff dough structural constraints with strict low-hydration boundary ceilings (50% to 55%)
        stiff_hyd = max(0.50, min(0.55, hydration))
        return stiff_hyd, fat, sugar

    def calculate_recipe(self, **kwargs) -> dict:
        recipe = super().calculate_recipe(**kwargs)
        
        # Chemical solution concentration scaling:
        # Pretzels typically use 3% lye bath (warm, no boil). Bagels use 1-3% barley malt syrup / soda boil.
        preset_slug = kwargs.get("preset_slug", "")
        if "pretzel" in preset_slug.lower():
            bath_info = "Chemical Solution: Prepare a 3% active Lye dip (30g food-grade lye dissolved in 1L warm water). Handle with rubber gloves and safety goggles! Do NOT heat the lye bath."
        else:
            bath_info = "Chemical Solution: Prepare a 2-3% malted water boiling loop (20-30g barley malt syrup or baking soda in 1L boiling water)."
            
        recipe["substitution_notes"] = recipe.get("substitution_notes", []) + [bath_info]
        return recipe

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        mix_min = 6
        knead_min = 10 if mixing_method == "stand_mixer" else 15
        
        # Alkaline bath doughs need skin drying to hold shape
        dry_min = 20
        # Boiling/dipping starch pre-gelatinization countdown (60 seconds)
        boil_sec = 60
        
        # Baking
        bake_min = bake_time_min

        return [
            {
                "key": "mix",
                "name": "Stiff Dough Mix",
                "duration_sec": mix_min * 60,
                "desc": "Combine ingredients. Hydration is capped at 50% to 55% for stiffness. Mix until no dry pockets remain.",
                "is_mix": True
            },
            {
                "key": "knead",
                "name": "Compaction Knead",
                "duration_sec": knead_min * 60,
                "desc": f"Intensely knead the stiff dough using '{mixing_method.replace('_', ' ').title()}' to force starch cell hydration.",
                "is_knead": True
            },
            {
                "key": "bulk",
                "name": "Rest & Relax",
                "duration_sec": max(15, estimated_bulk_minutes - 45) * 60,
                "desc": "Short bulk proof to relax the dense gluten mesh before shaping."
            },
            {
                "key": "shape",
                "name": "Shape & Skin Dry",
                "duration_sec": dry_min * 60,
                "desc": "Shape dough into pretzels or bagels. Rest uncovered on greaseproof paper to form a dry outer skin; this prevents water-logging.",
                "is_proof": True
            },
            {
                "key": "boil",
                "name": "Alkaline Bath Soak",
                "duration_sec": boil_sec,  # Coded in seconds
                "desc": "Dip shaped dough into the warm 3% lye bath or boiling malt/soda bath for 30s per side. Starch pre-gelatinization locks shape and creates the classic chewy skin."
            },
            {
                "key": "bake",
                "name": "High Convection Bake",
                "duration_sec": bake_min * 60,
                "desc": "Bake immediately on parchment. The alkaline surface reacts with oven heat to produce a beautiful, glossy mahogany color.",
                "is_bake": True
            }
        ]
