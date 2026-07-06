from grainlab.engines.base_engine import BaseEngine

class BatterEngine(BaseEngine):
    name = "Cakes & Batters Engine"
    slug = "batter"
    target_protein_min = 7.5
    target_protein_max = 9.5
    gluten_behavior = "Complete Absence of Gluten. High-ratio sugar and liquid dispersion requires structure built purely on starch gelatinization and egg protein coagulation."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Demands a completely neutral grain baseline to host delicate vanilla, citrus, or fruit fats."
    tannin_sensitive = True

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

    def apply_sub_class_constraints(self, hydration: float, fat: float, sugar: float, texture_score: int, crumb_score: int) -> tuple[float, float, float]:
        # High-ratio cake batters allow sugar and fat to scale independently and exceed 100% of flour weight
        # Thus, no downward ceilings are applied here.
        return hydration, fat, sugar

    def calculate_recipe(self, **kwargs) -> dict:
        recipe = super().calculate_recipe(**kwargs)
        
        # Emulsification style classification based on preset slug:
        preset_slug = kwargs.get("preset_slug", "")
        if "chiffon" in preset_slug.lower() or "angel" in preset_slug.lower():
            emuls_style = "[ Whipped Egg Foam ]"
        elif "cupcake" in preset_slug.lower() or "pancake" in preset_slug.lower() or "waffle" in preset_slug.lower():
            emuls_style = "[ Two-Stage Paste ]"
        else:
            emuls_style = "[ Creamed Butter ]"
            
        recipe["emulsification_style"] = emuls_style
        recipe["substitution_notes"] = recipe.get("substitution_notes", []) + [
            f"Emulsification Style: {emuls_style} logic applied. Focus on creating a stable, aerated fat-water emulsion.",
            "High-Ratio Baking Override: Sugar, fat, and hydration percentages scale independently of flour base weight."
        ]
        
        # Zero yeast for batters:
        recipe["yeast_weight"] = 0.0
        recipe["starter_weight"] = 0.0
        return recipe

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        emuls_style = recipe_data.get("emulsification_style", "[ Creamed Butter ]")
        
        if emuls_style == "[ Whipped Egg Foam ]":
            emuls_desc = "Whip egg whites/yolks with sugar to soft peaks. Creates the micro-bubbles needed for rise without chemical leavening."
        elif emuls_style == "[ Two-Stage Paste ]":
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
