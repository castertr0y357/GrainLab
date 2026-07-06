from grainlab.engines.base_engine import BaseEngine

class QuickEngine(BaseEngine):
    name = "Quick Breads & Scones Engine"
    slug = "quick"
    target_protein_min = 8.5
    target_protein_max = 10.5
    gluten_behavior = "Zero Gluten Development. Mechanical kneading is banned; structure relies entirely on chemical leavening reactions to yield a tender, crumbly interior."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Requires clean, buttery fats to come forward without whole-grain astringency."
    tannin_sensitive = True

    presets = [
        "Southern Buttermilk Biscuits", "Flaky Cream Scones", "Irish Soda Bread",
        "Classic Banana Bread", "Spiced Pumpkin Loaf", "Sweet Skillet Cornbread",
        "Blueberry Muffins", "Zucchini Bread"
    ]

    def calculate_recipe(self, **kwargs) -> dict:
        recipe = super().calculate_recipe(**kwargs)
        
        # Acid-to-base chemical neutralization balancing:
        # Standard: 1 tsp baking powder (acid+base) per cup of flour, or 1/4 tsp baking soda (base) per cup of sour liquid.
        flour_g = recipe["flour_weight"]
        # Baking powder estimate (1.5% of flour weight)
        bp_g = round(flour_g * 0.015, 1)
        # Baking soda estimate (0.5% of flour weight if acid present)
        bs_g = round(flour_g * 0.005, 1)
        
        substitute = kwargs.get("substitution", {}).get("substitute", "") if kwargs.get("substitution") else ""
        has_acid = recipe["liquid_label"] == "Whole Milk" or "milk" in substitute.lower()
        
        leaven_notes = []
        if has_acid:
            leaven_notes.append(f"Chemical Neutralization Balance: Add {bp_g}g Baking Powder AND {bs_g}g Baking Soda to neutralize liquid acids.")
        else:
            leaven_notes.append(f"Chemical Neutralization Balance: Add {bp_g}g Baking Powder to flour.")
            
        # Strict mixing threshold friction warning:
        mixing_method = kwargs.get("mixing_method", "hand_knead")
        if mixing_method in ["stand_mixer", "bread_machine"]:
            leaven_notes.append("⚠️ Structural Warning: Mechanical mixing creates high friction and triggers early gluten activation, making quick breads tough. Hand mixing is strongly recommended!")

        recipe["substitution_notes"] = recipe.get("substitution_notes", []) + leaven_notes
        # Yeast is zero for quick breads:
        recipe["yeast_weight"] = 0.0
        recipe["starter_weight"] = 0.0
        return recipe

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        dry_min = 2
        fat_min = 5
        fold_min = 3

        return [
            {
                "key": "mix",
                "name": "Dry & Leavener Blend",
                "duration_sec": dry_min * 60,
                "desc": "Whisk flour, sugar, salt, and chemical leaveners. Ensures uniform distribution for immediate chemical neutralization.",
                "is_mix": True
            },
            {
                "key": "fat_cut",
                "name": "Fat Cutting & Cold Lock",
                "duration_sec": fat_min * 60,
                "desc": "Cut cold butter/fat into the dry mix until it forms pea-sized crumbs. Keep ingredients cold to form steam pocket layers."
            },
            {
                "key": "fold",
                "name": "Minimal Spatula Fold",
                "duration_sec": fold_min * 60,
                "desc": "Pour in liquid. Fold gently by hand using a spatula just until dry pockets disappear. Do NOT over-mix or knead to avoid structural gluten activation!",
                "is_knead": True
            },
            {
                "key": "bake",
                "name": "Zero-Rise Thermal Bake",
                "duration_sec": bake_time_min * 60,
                "desc": "Bake immediately in preheated oven. Chemical carbon dioxide releases instantly and sets the tender crumb structure.",
                "is_bake": True
            }
        ]
