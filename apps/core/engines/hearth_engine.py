from apps.core.engines.base_engine import BaseEngine


class HearthEngine(BaseEngine):
    name = "Lean & Crusty Engine"
    slug = "hearth"
    default_starter_recipes = {
        "hearth_boule": [
            {
                "recipe_id": "hearth_boule_classic_1",
                "recipe_name": "San Francisco Sourdough",
                "description": "High hydration, blistered crust, sharp lactic tang.",
                "menu_description": "High hydration, blistered crust, sharp lactic tang.",
                "creativity_level": 1
            },
            {
                "recipe_id": "hearth_boule_classic_2",
                "recipe_name": "Country Miga",
                "description": "Rustic blend of whole wheat and white with an open crumb.",
                "menu_description": "Rustic blend of whole wheat and white with an open crumb.",
                "creativity_level": 1
            },
            {
                "recipe_id": "hearth_boule_classic_3",
                "recipe_name": "Seeded Levain",
                "description": "Toasted flax, sesame, and sunflower seeds throughout.",
                "menu_description": "Toasted flax, sesame, and sunflower seeds throughout.",
                "creativity_level": 1
            },
            {
                "recipe_id": "hearth_boule_classic_4",
                "recipe_name": "Dark Rye Pumpernickel",
                "description": "Dense, malty rye loaf with a chewy, robust crust.",
                "menu_description": "Dense, malty rye loaf with a chewy, robust crust.",
                "creativity_level": 1
            },
            {
                "recipe_id": "hearth_boule_classic_5",
                "recipe_name": "Pain de Campagne",
                "description": "Classic French peasant bread with a slight sourdough kick.",
                "menu_description": "Classic French peasant bread with a slight sourdough kick.",
                "creativity_level": 1
            },
        ],
        "high_hydration_slab": [
            {
                "recipe_id": "high_hydration_slab_classic_1",
                "recipe_name": "Classic Ciabatta",
                "description": "Airy, large holes, very high hydration slipper bread.",
                "menu_description": "Airy, large holes, very high hydration slipper bread.",
                "creativity_level": 1
            },
            {
                "recipe_id": "high_hydration_slab_classic_2",
                "recipe_name": "Rosemary Focaccia",
                "description": "Dimpled slab drowned in olive oil and fresh rosemary.",
                "menu_description": "Dimpled slab drowned in olive oil and fresh rosemary.",
                "creativity_level": 1
            },
            {
                "recipe_id": "high_hydration_slab_classic_3",
                "recipe_name": "Olive Slab",
                "description": "Studded with Kalamata olives and roasted garlic.",
                "menu_description": "Studded with Kalamata olives and roasted garlic.",
                "creativity_level": 1
            },
            {
                "recipe_id": "high_hydration_slab_classic_4",
                "recipe_name": "Tomato Basil Slab",
                "description": "Topped with sun-dried tomatoes and fresh basil.",
                "menu_description": "Topped with sun-dried tomatoes and fresh basil.",
                "creativity_level": 1
            },
            {
                "recipe_id": "high_hydration_slab_classic_5",
                "recipe_name": "Potato Sourdough Slab",
                "description": "Super soft crumb enriched with mashed potatoes.",
                "menu_description": "Super soft crumb enriched with mashed potatoes.",
                "creativity_level": 1
            },
        ],
        "tapered_baguette": [
            {
                "recipe_id": "tapered_baguette_classic_1",
                "recipe_name": "Parisian Baguette",
                "description": "Classic crusty baguette with an airy, irregular crumb.",
                "menu_description": "Classic crusty baguette with an airy, irregular crumb.",
                "creativity_level": 1
            },
            {
                "recipe_id": "tapered_baguette_classic_2",
                "recipe_name": "Demi-Baguette",
                "description": "Shorter, thicker baguette perfect for sandwiches.",
                "menu_description": "Shorter, thicker baguette perfect for sandwiches.",
                "creativity_level": 1
            },
            {
                "recipe_id": "tapered_baguette_classic_3",
                "recipe_name": "Sourdough Baguette",
                "description": "A traditional baguette shape with wild yeast tang.",
                "menu_description": "A traditional baguette shape with wild yeast tang.",
                "creativity_level": 1
            },
            {
                "recipe_id": "tapered_baguette_classic_4",
                "recipe_name": "Epi de Blé",
                "description": "Baguette cut to resemble a stalk of wheat.",
                "menu_description": "Baguette cut to resemble a stalk of wheat.",
                "creativity_level": 1
            },
            {
                "recipe_id": "tapered_baguette_classic_5",
                "recipe_name": "Multigrain Ficelle",
                "description": "Thin, crispy crust with a blend of ancient grains.",
                "menu_description": "Thin, crispy crust with a blend of ancient grains.",
                "creativity_level": 1
            },
        ],
        "flash_pizza": [
            {
                "recipe_id": "flash_pizza_classic_1",
                "recipe_name": "Neapolitan Margherita",
                "description": "Thin crust, blistered edges, crushed tomatoes, fresh mozzarella.",
                "menu_description": "Thin crust, blistered edges, crushed tomatoes, fresh mozzarella.",
                "creativity_level": 1
            },
            {
                "recipe_id": "flash_pizza_classic_2",
                "recipe_name": "New York Slice",
                "description": "Thin, flexible base with a sturdy rim, folding effortlessly.",
                "menu_description": "Thin, flexible base with a sturdy rim, folding effortlessly.",
                "creativity_level": 1
            },
            {
                "recipe_id": "flash_pizza_classic_3",
                "recipe_name": "Detroit Deep Dish",
                "description": "Thick, airy square base with caramelized cheese edges.",
                "menu_description": "Thick, airy square base with caramelized cheese edges.",
                "creativity_level": 1
            },
            {
                "recipe_id": "flash_pizza_classic_4",
                "recipe_name": "Sicilian Grandma",
                "description": "Pan-baked rectangular pie with a focaccia-like crumb.",
                "menu_description": "Pan-baked rectangular pie with a focaccia-like crumb.",
                "creativity_level": 1
            },
            {
                "recipe_id": "flash_pizza_classic_5",
                "recipe_name": "Roman Al Taglio",
                "description": "Long rectangular tray pizza with high hydration crisp.",
                "menu_description": "Long rectangular tray pizza with high hydration crisp.",
                "creativity_level": 1
            },
        ],
    }
    default_yield_unit = "loaves"
    target_protein_min = 12.0
    target_protein_max = 14.5
    gluten_behavior = "High Elasticity, maximum gas retention, capability to withstand long fermentation arcs."
    flavor_affinity = "Tannin Tolerant (Rustic/Savory). Welcomes deep caramelization, complex bran expressions, and lactic/acetic sourness."
    tannin_sensitive = False
    supported_tweaks = ["hydration", "leavening"]
    production_profile = {
        "thermodynamic_focus": "biological_yeast_activity",
        "mechanical_energy_threshold": "high_kneading",
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
            "cook_temp_f": 450,
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
            "cook_temp_f": 450,
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
            "cook_temp_f": 375,
            "bake_time_min": 45,
            "steam_required": False,
            "is_enriched_profile": False,
        },
    }

    dynamic_flavor_bases = [
        "Fig & Walnut Sourdough",
        "Cranberry Pecan Batard",
        "Toasted Sesame Boule",
        "Olive Oregano Sourdough",
        "Roasted Garlic Hearth Batard",
        "Rosemary French Baguette",
        "Multigrain Honey Seeded Boule",
        "Dark Beer Stout Rye",
        "Classic Country Sourdough",
        "Sun-Dried Tomato Batard",
        "Spiced Pumpkin Seed Hearth",
        "Ancient Grain Emmer Boule",
    ]


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

    _archetypes_cache = None

    @property
    def archetypes(self):
        if self.__class__._archetypes_cache is None:
            self.__class__._archetypes_cache = {}
            for subclass in HearthEngine.__subclasses__():
                slug = getattr(subclass, "archetype_slug", None)
                if slug:
                    self.__class__._archetypes_cache[slug] = {
                        "default_form_factor": getattr(subclass, "default_form_factor", "cast-iron-dutch-oven"),
                        "label": getattr(subclass, "label", ""),
                        "yield_unit": getattr(subclass, "yield_unit", "loaves"),
                        "icon": getattr(subclass, "icon", ""),
                        "description": getattr(subclass, "description", ""),
                        "grain_affinity": getattr(subclass, "grain_affinity", "high_protein"),
                        "target_archetype_mechanics": getattr(subclass, "target_archetype_mechanics", {}),
                        "culinary_nuance_directive": getattr(subclass, "culinary_nuance_directive", ""),
                        "preset_matchers": getattr(subclass, "preset_matchers", []),
                        "ingredient_prep_directive": getattr(subclass, "ingredient_prep_directive", getattr(self.__class__, "ingredient_prep_directive", "")),
                        "shaping_directive": getattr(subclass, "shaping_directive", getattr(self.__class__, "shaping_directive", "")),
                    }
        return self.__class__._archetypes_cache

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


class HearthBouleArchetype(HearthEngine):
    archetype_slug = "hearth_boule"
    guardrails = {
        "hydration_min": 60,
        "hydration_max": 100,
        "fat_min": 0,
        "fat_max": 10,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "autolyse", "knead", "bulk_ferment", "shape", "proof", "score", "bake", "cool"],
        "cook_temp_min_f": 425,
        "cook_temp_max_f": 500,
        "cook_time_min_m": 20,
        "cook_time_max_m": 45,
        "boil_required": False,
    }
    label = "Hearth Boule / Batard"
    icon = "🫓"
    description = "Freeform oval or round configurations baked on radiant stone floors."
    default_form_factor = "cast-iron-dutch-oven"
    grain_affinity = "high_protein"
    preset_matchers = ["boule", "batard", "sourdough", "campagne", "altamura"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "high_retention",
        "desired_horizontal_flow": "controlled_expansion",
        "moisture_lipid_ratio": "high_hydration_lean",
        "optimal_protein_window": "11.5% - 14.5%",
    }
    culinary_nuance_directive = (
        "Focus on long-chain protein cross-linking, extreme gas retention, and structural tensile elasticity. Grains must "
        "yield maximum elasticity to hold high water weights and shape boundaries without pan walls, maximizing explosive "
        "oven spring under initial steam injection."
    )


class HighHydrationSlabArchetype(HearthEngine):
    archetype_slug = "high_hydration_slab"
    guardrails = {
        "hydration_min": 60,
        "hydration_max": 100,
        "fat_min": 0,
        "fat_max": 10,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "autolyse", "knead", "bulk_ferment", "shape", "proof", "score", "bake", "cool"],
        "cook_temp_min_f": 425,
        "cook_temp_max_f": 500,
        "cook_time_min_m": 20,
        "cook_time_max_m": 45,
        "boil_required": False,
    }
    label = "High-Hydration Slab"
    yield_unit = "slabs"
    icon = "🍞"
    description = "Wet, un-kneaded cellular matrices poured out into pans like Focaccia or Ciabatta."
    default_form_factor = "cast-iron-dutch-oven"
    grain_affinity = "high_protein"
    preset_matchers = ["slab", "focaccia", "ciabatta"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "moderate_extensible",
        "desired_horizontal_flow": "controlled_expansion",
        "moisture_lipid_ratio": "high_hydration_lean",
        "optimal_protein_window": "12.5% - 14.5%",
    }
    culinary_nuance_directive = (
        "Focus on high water-absorption kinetics and open cellular networks. Grains must allow wet, un-kneaded slack "
        "doughs to hold massive moisture values, using gentle gas production to lift large irregular cell walls "
        "without slumping across continuous sheet pans."
    )

    def get_live_timeline_steps(
        self,
        recipe_data,
        estimated_bulk_minutes,
        estimated_proof_minutes,
        bake_time_min,
        mixing_method="stand_mixer",
        **kwargs,
    ):
        autolyse_min = 30
        mix_min = 5
        knead_min = 10 if mixing_method == "stand_mixer" else 15
        sf_min = 45
        bulk_min = max(30, estimated_bulk_minutes - sf_min)

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
        return steps


class TaperedBaguetteArchetype(HearthEngine):
    archetype_slug = "tapered_baguette"
    guardrails = {
        "hydration_min": 60,
        "hydration_max": 100,
        "fat_min": 0,
        "fat_max": 10,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "autolyse", "knead", "bulk_ferment", "shape", "proof", "score", "bake", "cool"],
        "cook_temp_min_f": 425,
        "cook_temp_max_f": 500,
        "cook_time_min_m": 20,
        "cook_time_max_m": 45,
        "boil_required": False,
    }
    label = "Tapered Baguette"
    yield_unit = "baguettes"
    icon = "🥖"
    description = "Elongated, thin cylinder format optimizing the crust-to-crumb ratio."
    default_form_factor = "cast-iron-dutch-oven"
    grain_affinity = "high_protein"
    preset_matchers = ["baguette", "french"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "high_retention",
        "desired_horizontal_flow": "controlled_expansion",
        "moisture_lipid_ratio": "high_hydration_lean",
        "optimal_protein_window": "11.5% - 14.5%",
    }
    culinary_nuance_directive = (
        "Focus on intense gluten alignment and high crust-to-crumb ratio mapping. The protein network must allow the dough "
        "to be shaped into long, uniform cylinders that maintain surface tension during proofing, scoring cleanly to "
        "yield sharp ears and blistered textures."
    )


class FlashPizzaArchetype(HearthEngine):
    archetype_slug = "flash_pizza"
    guardrails = {
        "hydration_min": 60,
        "hydration_max": 100,
        "fat_min": 0,
        "fat_max": 10,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "autolyse", "knead", "bulk_ferment", "shape", "proof", "score", "bake", "cool"],
        "cook_temp_min_f": 425,
        "cook_temp_max_f": 500,
        "cook_time_min_m": 20,
        "cook_time_max_m": 45,
        "boil_required": False,
    }
    label = "Flash Pizza Crust"
    yield_unit = "pizzas"
    icon = "🍕"
    description = "Ultra-thin center with a blistered gas-filled rim set under extreme thermal environments."
    default_form_factor = "cast-iron-dutch-oven"
    grain_affinity = "high_protein"
    preset_matchers = ["pizza", "calzone"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "extreme_tensile",
        "desired_horizontal_flow": "zero_spread_stable",
        "moisture_lipid_ratio": "high_hydration_lean",
        "optimal_protein_window": "12.5% - 14.5%",
    }
    culinary_nuance_directive = (
        "Focus on extreme tensile strength and high structural extensibility. Grains must allow the dough to be stretched "
        "paper-thin in the center without tearing, holding a robust, gas-filled rim that blisters instantly into dark charred "
        "spots under intense thermal conduction."
    )

    def get_live_timeline_steps(
        self,
        recipe_data,
        estimated_bulk_minutes,
        estimated_proof_minutes,
        bake_time_min,
        mixing_method="stand_mixer",
        **kwargs,
    ):
        autolyse_min = 30
        mix_min = 5
        knead_min = 10 if mixing_method == "stand_mixer" else 15
        sf_min = 45
        bulk_min = max(30, estimated_bulk_minutes - sf_min)

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
        return steps
