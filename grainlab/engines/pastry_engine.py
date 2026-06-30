from grainlab.engines.base_engine import BaseEngine

class PastryEngine(BaseEngine):
    name = "Pastry & Lamination Engine"
    slug = "pastry"

    presets = [
        "Classic Croissants", "Pain au Chocolat", "All-Butter Puff Pastry",
        "Danish Pastry Dough", "Flaky Pie Crust (Pâte Brisée)",
        "Sweet Tart Dough (Pâte Sucrée)", "Palmiers", "Vol-au-vents"
    ]

    def calculate_recipe(self, **kwargs) -> dict:
        recipe = super().calculate_recipe(**kwargs)
        
        # Butter block roll-in fat ratio (butter block relative to dough sheet targeting a 25% to 30% boundary)
        target_mass = recipe["target_mass"]
        butter_block_g = round(target_mass * 0.28, 1)
        
        preset_slug = kwargs.get("preset_slug", "")
        if "puff" in preset_slug.lower() or "danish" in preset_slug.lower():
            fold_style = "[ Double Book Fold (4x) ]"
            layers = 4 * 4 * 4  # 64 layers
        elif "croissant" in preset_slug.lower() or "chocolat" in preset_slug.lower():
            fold_style = "[ Single Letter Fold (3x) ]"
            layers = 3 * 3 * 3  # 27 layers
        else:
            fold_style = "[ Rubbed Fat Crumble ]"
            layers = 1
            
        recipe["butter_block_weight"] = butter_block_g
        recipe["fold_style"] = fold_style
        recipe["lamination_layers"] = layers
        
        recipe["substitution_notes"] = recipe.get("substitution_notes", []) + [
            f"Butter Block Roll-in: Prepare a separate cold butter block of {butter_block_g}g (targets 28% roll-in boundary relative to total dough).",
            f"Layer Accumulation: Apply {fold_style} to achieve {layers} layers of fat and dough."
        ]
        return recipe

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        fold_style = recipe_data.get("fold_style", "[ Single Letter Fold (3x) ]")
        layers = recipe_data.get("lamination_layers", 27)
        
        if "Book" in fold_style:
            fold_desc = "Roll dough to a rectangle. Fold both outer edges to meet in the middle, then fold in half like a book (4 layers generated)."
        elif "Letter" in fold_style:
            fold_desc = "Roll dough to a rectangle. Fold one-third over the center, then the opposite third over that like a letter (3 layers generated)."
        else:
            fold_desc = "Rub cold butter chunks into flour until pea-sized. Keep cool; do not laminate."

        return [
            {
                "key": "mix",
                "name": "Détrempe Base Mix",
                "duration_sec": 6 * 60,
                "desc": "Mix base dough (détrempe) until combined. Do not over-knead to prevent excess gluten toughness.",
                "is_mix": True
            },
            {
                "key": "butter_encase",
                "name": "Butter Block Encasement",
                "duration_sec": 10 * 60,
                "desc": f"Roll the détrempe out. Place the cold butter block ({recipe_data.get('butter_block_weight', 0.0)}g) in the center. Fold the corners of the dough over to fully seal the butter block."
            },
            {
                "key": "fold_one",
                "name": "First Fold Set",
                "duration_sec": 10 * 60,
                "desc": f"Perform the first fold set: {fold_desc} Work quickly so butter remains cold."
            },
            {
                "key": "chill_lock_one",
                "name": "Low-Temp Chill Lock 1",
                "duration_sec": 30 * 60,
                "desc": "Mandatory low-temperature environmental chill-rest step. Chill in freezer/fridge to solidify butter and relax gluten sheets."
            },
            {
                "key": "fold_two",
                "name": "Second Fold Set",
                "duration_sec": 10 * 60,
                "desc": f"Roll dough out and perform the second fold set: {fold_desc}"
            },
            {
                "key": "chill_lock_two",
                "name": "Low-Temp Chill Lock 2",
                "duration_sec": 30 * 60,
                "desc": "Second mandatory chill lock. Keeps laminated butter solid so layers do not bleed together."
            },
            {
                "key": "bake",
                "name": "Laminated Steam Rise Bake",
                "duration_sec": bake_time_min * 60,
                "desc": "Bake in hot oven. Water in butter boils instantly, creating steam which puffs the pastry layers apart while fat setting locks the crumb.",
                "is_bake": True
            }
        ]
