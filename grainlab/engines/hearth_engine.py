from grainlab.engines.base_engine import BaseEngine

class HearthEngine(BaseEngine):
    name = "Lean & Crusty Engine"
    slug = "hearth"
    target_protein_min = 12.0
    target_protein_max = 14.5
    gluten_behavior = "High Elasticity, maximum gas retention, capability to withstand long fermentation arcs."
    flavor_affinity = "Tannin Tolerant (Rustic/Savory). Welcomes deep caramelization, complex bran expressions, and lactic/acetic sourness."
    tannin_sensitive = False
    
    presets = [
        "Sourdough Boule", "Classic French Baguette", "Ciabatta", 
        "Rustic French Loaf (Pain de Campagne)", "Artisan Neapolitan Pizza Crust", 
        "Calzone Dough", "Focaccia Barese", "Pane di Altamura"
    ]

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        # Desired Dough Temp (DDT) factoring friction is processed in water temp calculations.
        # Hearth bread uses extended autolyse, stretch-and-folds, and dual-phase baking (steam vs dry).
        
        # Calculate dynamic times
        autolyse_min = 30
        mix_min = 5
        knead_min = 10 if mixing_method == "stand_mixer" else 15
        
        # Stretch and Fold duration (45 mins total: 3 folds every 15 mins)
        sf_min = 45
        
        # Bulk ferment adjusts for stretch and folds
        bulk_min = max(30, estimated_bulk_minutes - sf_min)
        
        # Dual-phase bake: Steam phase is 25 mins (or less if bake_time is short)
        steam_bake_min = min(25, max(15, bake_time_min - 15))
        dry_bake_min = max(10, bake_time_min - steam_bake_min)

        return [
            {
                "key": "autolyse",
                "name": "Autolyse Rest",
                "duration_sec": autolyse_min * 60,
                "desc": "Mix only flour and water. Let rest to kickstart enzymatic activity and build gluten extensibility without yeast interference."
            },
            {
                "key": "mix",
                "name": "Mix Leaven & Salt",
                "duration_sec": mix_min * 60,
                "desc": "Incorporate leaven/yeast and salt. Mix until fully combined and uniform.",
                "is_mix": True
            },
            {
                "key": "knead",
                "name": "Gluten Development",
                "duration_sec": knead_min * 60,
                "desc": f"Develop the gluten network. Knead using '{mixing_method.replace('_', ' ').title()}' until dough passes the windowpane test.",
                "is_knead": True
            },
            {
                "key": "stretch_fold",
                "name": "Stretch & Fold Sets",
                "duration_sec": sf_min * 60,
                "desc": "Perform 3 sets of stretch-and-folds every 15 minutes to align the gluten sheets and incorporate air pockets."
            },
            {
                "key": "bulk",
                "name": "Bulk Fermentation",
                "duration_sec": bulk_min * 60,
                "desc": "Primary fermentation. Allow dough to build structure, volume, and carbon dioxide pockets."
            },
            {
                "key": "proof",
                "name": "Final Proofing",
                "duration_sec": estimated_proof_minutes * 60,
                "desc": "Shape dough into a tight boule/batard and place in banneton/pan. Allow to rise until puffy.",
                "is_proof": True
            },
            {
                "key": "steam_bake",
                "name": "Steam Injection Bake",
                "duration_sec": steam_bake_min * 60,
                "desc": f"Bake in a covered Dutch oven or with steam injection. Steam gelatinizes surface starch for maximum oven spring and a crispy crust.",
                "is_bake": True
            },
            {
                "key": "dry_bake",
                "name": "Dry Vent Finish",
                "duration_sec": dry_bake_min * 60,
                "desc": "Remove Dutch oven lid or vent oven steam. Reduce heat slightly to dry out the crust and achieve a deep golden blistered finish.",
                "is_bake": True
            }
        ]
