from grainlab.engines.base_engine import BaseEngine

class PastaEngine(BaseEngine):
    name = "Fresh Pasta & Noodles Engine"
    slug = "pasta"

    presets = [
        "Fresh Egg Tagliatelle", "Fettuccine Sheets", "Ravioli / Tortellini Dough",
        "Semolina Extruded Rigatoni", "Thick Hand-Cut Udon", "Alkaline Wheat Ramen Noodles",
        "Gyoza / Dumpling Wrappers"
    ]

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
