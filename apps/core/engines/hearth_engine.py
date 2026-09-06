from apps.core.engines.base_engine import BaseEngine


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
        },
    }

    presets = [
        "Sourdough Boule",
        "Classic French Baguette",
        "Ciabatta",
        "Rustic French Loaf (Pain de Campagne)",
        "Artisan Neapolitan Pizza Crust",
        "Calzone Dough",
        "Focaccia Barese",
        "Pane di Altamura",
    ]

    archetypes = {
        "hearth_boule": {
            "default_form_factor": "cast-iron-dutch-oven",
            "label": "Hearth Boule / Batard",
            "icon": "🫓",
            "description": "Freeform oval or round configurations baked on radiant stone floors.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "default_form_factor": "cast-iron-dutch-oven",
                "default_form_factor": "cast-iron-dutch-oven",
                "default_form_factor": "cast-iron-dutch-oven",
                "default_form_factor": "cast-iron-dutch-oven",
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "high_hydration_lean",
                "optimal_protein_window": "11.5% - 14.5%",
            },
            "culinary_nuance_directive": (
                "Focus on long-chain protein cross-linking, extreme gas retention, and structural tensile elasticity. Grains must "
                "yield maximum elasticity to hold high water weights and shape boundaries without pan walls, maximizing explosive "
                "oven spring under initial steam injection."
            ),
        },
        "high_hydration_slab": {
            "default_form_factor": "cast-iron-dutch-oven",
            "label": "High-Hydration Slab",
            "icon": "🍞",
            "description": "Wet, un-kneaded cellular matrices poured out into pans like Focaccia or Ciabatta.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "high_hydration_lean",
                "optimal_protein_window": "12.5% - 14.5%",
            },
            "culinary_nuance_directive": (
                "Focus on high water-absorption kinetics and open cellular networks. Grains must allow wet, un-kneaded slack "
                "doughs to hold massive moisture values, using gentle gas production to lift large irregular cell walls "
                "without slumping across continuous sheet pans."
            ),
        },
        "tapered_baguette": {
            "default_form_factor": "cast-iron-dutch-oven",
            "label": "Tapered Baguette",
            "icon": "🥖",
            "description": "Elongated, thin cylinder format optimizing the crust-to-crumb ratio.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "high_hydration_lean",
                "optimal_protein_window": "11.5% - 14.5%",
            },
            "culinary_nuance_directive": (
                "Focus on intense gluten alignment and high crust-to-crumb ratio mapping. The protein network must allow the dough "
                "to be shaped into long, uniform cylinders that maintain surface tension during proofing, scoring cleanly to "
                "yield sharp ears and blistered textures."
            ),
        },
        "flash_pizza": {
            "default_form_factor": "cast-iron-dutch-oven",
            "label": "Flash Pizza Crust",
            "icon": "🍕",
            "description": "Ultra-thin center with a blistered gas-filled rim set under extreme thermal environments.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "high_hydration_lean",
                "optimal_protein_window": "12.5% - 14.5%",
            },
            "culinary_nuance_directive": (
                "Focus on extreme tensile strength and high structural extensibility. Grains must allow the dough to be stretched "
                "paper-thin in the center without tearing, holding a robust, gas-filled rim that blisters instantly into dark charred "
                "spots under intense thermal conduction."
            ),
        },
    }

    def get_ai_culinary_directive(self) -> str:
        return "This is a lean hearth bread (e.g. sourdough, artisan loaf). For traditional lean loaves, omit lipids, sweeteners, and eggs. For specific hybrid savory or sweet artisan loaves, use minimal fats/sweeteners. Always include a yeast/sourdough leavener and a liquid medium."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives (like seeds, nuts, or olives), use true baker's percentages (flour = 100%). For lean hearth doughs, these typically range from 10.0 to 25.0. CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile. CRITICAL: For commercial yeast (active/instant), strictly limit to 0.5 to 1.5. For sourdough starter, strictly limit to 10.0 to 25.0."

    def get_live_timeline_steps(
        self,
        recipe_data: dict,
        estimated_bulk_minutes: int,
        estimated_proof_minutes: int,
        bake_time_min: int,
        mixing_method: str = "stand_mixer",
        **kwargs,
    ) -> list[dict]:
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

        # Dual-phase bake: Steam phase is max 25 mins, dry phase is at least 10 mins (if possible)
        steam_bake_min = min(25, max(10, bake_time_min - 15))
        if steam_bake_min >= bake_time_min:
            steam_bake_min = max(5, int(bake_time_min * 0.6))
        dry_bake_min = bake_time_min - steam_bake_min
        preset_slug = kwargs.get("preset_slug") or ""

        steps = [
            {
                "key": "autolyse",
                "name": "Autolyse Rest",
                "duration_sec": autolyse_min * 60,
                "desc": "Mix only flour and water. Let rest to kickstart enzymatic activity and build gluten extensibility without yeast interference.",
            },
            {
                "key": "mix",
                "name": "Mix Leaven & Salt",
                "duration_sec": mix_min * 60,
                "desc": "Incorporate leaven/yeast and salt. Mix until fully combined and uniform.",
                "is_mix": True,
            },
            {
                "key": "knead",
                "name": "Intensive Mechanical Knead",
                "duration_sec": knead_min * 60,
                "desc": f"Knead using '{mixing_method.replace('_', ' ').title()}' to build a strong initial gluten mesh capable of holding high hydration.",
                "is_knead": True,
            },
            {
                "key": "stretch_fold",
                "name": "Stretch & Folds",
                "duration_sec": sf_min * 60,
                "desc": "Perform 3 sets of stretch and folds spaced 15 minutes apart. This aligns the gluten network gently while introducing oxygen.",
            },
            {
                "key": "bulk",
                "name": "Bulk Ferment",
                "duration_sec": bulk_min * 60,
                "desc": "Allow dough to ferment until volume increases by 50-75% with visible bubbles throughout the matrix.",
            },
            {
                "key": "preshape",
                "name": "Pre-Shape & Bench Rest",
                "duration_sec": 20 * 60,
                "desc": "Divide dough into required portions. Gently round them up and let rest on the bench. Relaxes dough before final tensioning.",
            },
        ]

        if "pizza" in preset_slug.lower() or "calzone" in preset_slug.lower():
            steps.extend(
                [
                    {
                        "key": "final_shape",
                        "name": "Pizza Stretching",
                        "duration_sec": 10 * 60,
                        "desc": "Gently stretch the dough ball outward from the center, preserving the gas in the outer rim (cornicione).",
                    },
                    {
                        "key": "proof",
                        "name": "Brief Rest",
                        "duration_sec": 15 * 60,
                        "desc": "Allow the stretched dough to relax briefly before topping.",
                        "is_proof": True,
                    },
                    {
                        "key": "bake",
                        "name": "Flash Stone Bake",
                        "duration_sec": bake_time_min * 60,
                        "desc": "Bake on an extremely hot stone/steel. The intense conduction heat causes immediate oven spring and crust blistering.",
                        "is_bake": True,
                    },
                ]
            )
            return steps
        elif "slab" in preset_slug.lower() or "focaccia" in preset_slug.lower() or "ciabatta" in preset_slug.lower():
            steps.extend(
                [
                    {
                        "key": "final_shape",
                        "name": "Pan Transfer & Dimpling",
                        "duration_sec": 10 * 60,
                        "desc": "Gently stretch and transfer the slack dough to a heavily oiled pan. Dimple deeply with oiled fingers.",
                    },
                    {
                        "key": "proof",
                        "name": "Pan Proof",
                        "duration_sec": estimated_proof_minutes * 60,
                        "desc": "Proof in the pan until very bubbly and jiggly.",
                        "is_proof": True,
                    },
                    {
                        "key": "bake",
                        "name": "High-Heat Oil Bake",
                        "duration_sec": bake_time_min * 60,
                        "desc": "Bake in the hot oven. The oiled pan acts to shallow-fry the bottom crust while the top sets crisp.",
                        "is_bake": True,
                    },
                    {
                        "key": "cool",
                        "name": "Wire Rack Cooling",
                        "duration_sec": 30 * 60,
                        "desc": "Remove from pan to prevent a soggy bottom. Cool on a wire rack.",
                    },
                ]
            )
            return steps

        # Default Hearth Loaf Pipeline
        steps.extend(
            [
                {
                    "key": "final_shape",
                    "name": "Final Shaping",
                    "duration_sec": 10 * 60,
                    "desc": "Shape into a tight boule or batard to build surface tension. Place seam-side up in a floured banneton basket.",
                },
                {
                    "key": "proof",
                    "name": "Final Proofing",
                    "duration_sec": estimated_proof_minutes * 60,
                    "desc": "Shape dough into a tight boule/batard and place in banneton/pan. Allow to rise until puffy.",
                    "is_proof": True,
                },
                {
                    "key": "steam_bake",
                    "name": "Steam Injection Bake",
                    "duration_sec": steam_bake_min * 60,
                    "desc": "Bake in a covered Dutch oven or with steam injection. Steam gelatinizes surface starch for maximum oven spring and a crispy crust.",
                    "is_bake": True,
                },
                {
                    "key": "dry_bake",
                    "name": "Dry Vent Finish",
                    "duration_sec": dry_bake_min * 60,
                    "desc": "Remove Dutch oven lid or vent oven steam. Reduce heat slightly to dry out the crust and achieve a deep golden blistered finish.",
                    "is_bake": True,
                },
            ]
        )

        steps.append(
            {
                "key": "cool",
                "name": "Wire Rack Cooling",
                "duration_sec": 120 * 60,
                "desc": "Transfer the loaf immediately to a wire rack. Allow to cool completely (1-2 hours) before slicing. Slicing warm hearth bread will result in a gummy, damaged crumb.",
            }
        )

        return steps
