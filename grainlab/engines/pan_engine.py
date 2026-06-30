from grainlab.engines.base_engine import BaseEngine

class PanEngine(BaseEngine):
    name = "Enriched & Soft Engine"
    slug = "pan"

    presets = [
        "Everyday White Sandwich Loaf", "Rich Brioche", "Traditional Challah",
        "Hokkaido Milk Bread", "Soft Burger Buns", "Dinner Rolls",
        "Cinnamon Rolls", "Chocolate Babka", "Monkey Bread"
    ]

    def calculate_recipe(self, **kwargs) -> dict:
        recipe = super().calculate_recipe(**kwargs)
        
        # Calculate Cumulative Lipid Enrichment Coefficient (fat + sugar + milk/egg adjustments)
        fat_pct = recipe["effective_fat_pct"] / 100.0
        sugar_pct = recipe["effective_sugar_pct"] / 100.0
        
        # Let's check milk substitution to add to lipids (whole milk contains ~4% fats)
        milk_contrib = 0.0
        if recipe.get("liquid_label") == "Whole Milk":
            milk_contrib = 0.04
            
        lipid_coef = fat_pct + sugar_pct + milk_contrib
        recipe["lipid_enrichment_coef"] = round(lipid_coef, 3)
        
        # Pan sizing check / volumetric Pan-Geometry sizing constraint notes:
        # A standard 9x5 loaf pan fits 800g to 1000g of dough.
        target_mass = recipe["target_mass"]
        pan_notes = []
        if target_mass < 700:
            pan_notes.append("⚠️ Pan Geometry Warning: Dough mass may be too low to fill a standard 9x5 loaf pan. Consider scaling yield upward (+20%).")
        elif target_mass > 1100:
            pan_notes.append("⚠️ Pan Geometry Warning: Dough mass exceeds standard 9x5 loaf pan capacity. Consider dividing into two smaller loaves to prevent overflow.")
            
        recipe["substitution_notes"] = recipe.get("substitution_notes", []) + pan_notes
        recipe["substitution_notes"].append(f"Cumulative Lipid Enrichment Coefficient: {recipe['lipid_enrichment_coef']} (Fat/Sugar/Dairy share).")
        return recipe

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
