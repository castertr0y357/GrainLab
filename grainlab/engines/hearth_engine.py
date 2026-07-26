from grainlab.engines.base_engine import BaseEngine

class HearthEngine(BaseEngine):
    name = "Lean & Crusty Engine"
    slug = "hearth"
    target_protein_min = 12.0
    target_protein_max = 14.5
    gluten_behavior = "High Elasticity, maximum gas retention, capability to withstand long fermentation arcs."
    flavor_affinity = "Tannin Tolerant (Rustic/Savory). Welcomes deep caramelization, complex bran expressions, and lactic/acetic sourness."
    tannin_sensitive = False
    supported_tweaks = ["hydration", "leavening"]
    production_profile = {
        "thermodynamic_focus": "biological_yeast_activity",
        "mechanical_energy_threshold": "high_kneading",
        "permissible_action_types": ["knead", "fold"],
        "environmental_rest_strategy": "gas_proofing",
    }
    secondary_ingredients = {}

    permissible_form_factors = {
        "cast-iron-dutch-oven": {
            "name": "Cast Iron Dutch Oven",
            "tier": "recommended",
            "is_portioned": False,
            "unit_weight": 750.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "loaf",
            "unit_label_plural": "loaves",
            "bake_temp_f": 450,
            "bake_time_min": 40,
            "steam_required": True,
            "is_enriched_profile": False,
        },
        "open-baking-stone-steel": {
            "name": "Open Baking Stone / Steel",
            "tier": "recommended",
            "is_portioned": False,
            "unit_weight": 750.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "loaf",
            "unit_label_plural": "loaves",
            "bake_temp_f": 450,
            "bake_time_min": 35,
            "steam_required": True,
            "is_enriched_profile": False,
        },
        "standard-9x5-pan": {
            "name": "Standard 9x5 Loaf Pan",
            "tier": "sub-optimal",
            "is_portioned": False,
            "unit_weight": 750.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "loaf",
            "unit_label_plural": "loaves",
            "bake_temp_f": 375,
            "bake_time_min": 45,
            "steam_required": False,
            "is_enriched_profile": False,
        }
    }
    
    presets = [
        "Sourdough Boule", "Classic French Baguette", "Ciabatta", 
        "Rustic French Loaf (Pain de Campagne)", "Artisan Neapolitan Pizza Crust", 
        "Calzone Dough", "Focaccia Barese", "Pane di Altamura"
    ]

    archetypes = {
        "hearth_boule": {
            "label": "Hearth Boule / Batard",
            "icon": "🫓",
            "description": "Freeform oval or round configurations baked on radiant stone floors.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "high_hydration_lean",
                "optimal_protein_window": "11.5% - 14.5%"
            },
            "culinary_nuance_directive": (
                "Focus on long-chain protein cross-linking, extreme gas retention, and structural tensile elasticity. Grains must "
                "yield maximum elasticity to hold high water weights and shape boundaries without pan walls, maximizing explosive "
                "oven spring under initial steam injection."
            )
        },
        "high_hydration_slab": {
            "label": "High-Hydration Slab",
            "icon": "🍞",
            "description": "Wet, un-kneaded cellular matrices poured out into pans like Focaccia or Ciabatta.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "high_hydration_lean",
                "optimal_protein_window": "12.5% - 14.5%"
            },
            "culinary_nuance_directive": (
                "Focus on high water-absorption kinetics and open cellular networks. Grains must allow wet, un-kneaded slack "
                "doughs to hold massive moisture values, using gentle gas production to lift large irregular cell walls "
                "without slumping across continuous sheet pans."
            )
        },
        "tapered_baguette": {
            "label": "Tapered Baguette",
            "icon": "🥖",
            "description": "Elongated, thin cylinder format optimizing the crust-to-crumb ratio.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "high_hydration_lean",
                "optimal_protein_window": "11.5% - 14.5%"
            },
            "culinary_nuance_directive": (
                "Focus on intense gluten alignment and high crust-to-crumb ratio mapping. The protein network must allow the dough "
                "to be shaped into long, uniform cylinders that maintain surface tension during proofing, scoring cleanly to "
                "yield sharp ears and blistered textures."
            )
        },
        "flash_pizza": {
            "label": "Flash Pizza Crust",
            "icon": "🍕",
            "description": "Ultra-thin center with a blistered gas-filled rim set under extreme thermal environments.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "high_hydration_lean",
                "optimal_protein_window": "12.5% - 14.5%"
            },
            "culinary_nuance_directive": (
                "Focus on extreme tensile strength and high structural extensibility. Grains must allow the dough to be stretched "
                "paper-thin in the center without tearing, holding a robust, gas-filled rim that blisters instantly into dark charred "
                "spots under intense thermal conduction."
            )
        },
    }

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
