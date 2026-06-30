from grainlab.engines.base_engine import BaseEngine

class CookieEngine(BaseEngine):
    name = "Cookies & Shortbread Engine"
    slug = "cookie"

    presets = [
        "Chewy Chocolate Chip Cookies", "Oatmeal Raisin Bakes", "Buttery Shortbread Wedges",
        "Italian Almond Biscotti", "Gingerbread People", "French Almond Macarons",
        "Snickerdoodles", "Classic Sugar Cookies"
    ]

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
