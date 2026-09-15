from apps.core.engines.base_engine import BaseEngine


class PanEngine(BaseEngine):
    name = "Enriched & Soft Engine"
    slug = "pan"
    default_starter_recipes = {
        "sandwich_pan": [
            {
                "recipe_id": "sandwich_pan_classic_1",
                "recipe_name": "White Pullman",
                "description": "Perfectly square, tight crumb, incredibly soft sandwich loaf.",
                "menu_description": "Perfectly square, tight crumb, incredibly soft sandwich loaf.",
                "creativity_level": 1
            },
            {
                "recipe_id": "sandwich_pan_classic_2",
                "recipe_name": "Honey Wheat",
                "description": "Soft 100% whole wheat enriched with a touch of honey.",
                "menu_description": "Soft 100% whole wheat enriched with a touch of honey.",
                "creativity_level": 1
            },
            {
                "recipe_id": "sandwich_pan_classic_3",
                "recipe_name": "Japanese Shokupan",
                "description": "Milk bread made with tangzhong for an ultra-fluffy texture.",
                "menu_description": "Milk bread made with tangzhong for an ultra-fluffy texture.",
                "creativity_level": 1
            },
            {
                "recipe_id": "sandwich_pan_classic_4",
                "recipe_name": "Oat & Honey Loaf",
                "description": "Toasted oats sprinkled over a sweet, enriched crumb.",
                "menu_description": "Toasted oats sprinkled over a sweet, enriched crumb.",
                "creativity_level": 1
            },
            {
                "recipe_id": "sandwich_pan_classic_5",
                "recipe_name": "Classic Brioche Loaf",
                "description": "High butter content, golden crust, pull-apart tenderness.",
                "menu_description": "High butter content, golden crust, pull-apart tenderness.",
                "creativity_level": 1
            },
        ],
        "freeform_braided": [
            {
                "recipe_id": "freeform_braided_classic_1",
                "recipe_name": "Classic Challah",
                "description": "Glossy, egg-enriched braided loaf, slightly sweet.",
                "menu_description": "Glossy, egg-enriched braided loaf, slightly sweet.",
                "creativity_level": 1
            },
            {
                "recipe_id": "freeform_braided_classic_2",
                "recipe_name": "Swiss Zopf",
                "description": "Butter-enriched Sunday braid with a golden crust.",
                "menu_description": "Butter-enriched Sunday braid with a golden crust.",
                "creativity_level": 1
            },
            {
                "recipe_id": "freeform_braided_classic_3",
                "recipe_name": "Babka Swirl",
                "description": "Rich dough twisted with deep chocolate ribbons.",
                "menu_description": "Rich dough twisted with deep chocolate ribbons.",
                "creativity_level": 1
            },
            {
                "recipe_id": "freeform_braided_classic_4",
                "recipe_name": "Garlic Herb Braid",
                "description": "Savory braided loaf stuffed with roasted garlic and herbs.",
                "menu_description": "Savory braided loaf stuffed with roasted garlic and herbs.",
                "creativity_level": 1
            },
            {
                "recipe_id": "freeform_braided_classic_5",
                "recipe_name": "Festive Wreath",
                "description": "Circular braided loaf often baked with colored eggs.",
                "menu_description": "Circular braided loaf often baked with colored eggs.",
                "creativity_level": 1
            },
        ],
        "soft_dinner_roll": [
            {
                "recipe_id": "soft_dinner_roll_classic_1",
                "recipe_name": "Parker House Rolls",
                "description": "Buttery, folded dinner rolls with a soft, flaky bite.",
                "menu_description": "Buttery, folded dinner rolls with a soft, flaky bite.",
                "creativity_level": 1
            },
            {
                "recipe_id": "soft_dinner_roll_classic_2",
                "recipe_name": "Potato Rolls",
                "description": "Incredibly soft burger buns enriched with potato starch.",
                "menu_description": "Incredibly soft burger buns enriched with potato starch.",
                "creativity_level": 1
            },
            {
                "recipe_id": "soft_dinner_roll_classic_3",
                "recipe_name": "Hawaiian Sweet Rolls",
                "description": "Pineapple juice sweetened, fluffy tear-and-share rolls.",
                "menu_description": "Pineapple juice sweetened, fluffy tear-and-share rolls.",
                "creativity_level": 1
            },
            {
                "recipe_id": "soft_dinner_roll_classic_4",
                "recipe_name": "Cloverleaf Rolls",
                "description": "Three dough balls baked in a muffin tin for pull-apart layers.",
                "menu_description": "Three dough balls baked in a muffin tin for pull-apart layers.",
                "creativity_level": 1
            },
            {
                "recipe_id": "soft_dinner_roll_classic_5",
                "recipe_name": "Garlic Knots",
                "description": "Tied dough bathed in garlic butter and parsley.",
                "menu_description": "Tied dough bathed in garlic butter and parsley.",
                "creativity_level": 1
            },
        ],
        "filled_sweet_roll": [
            {
                "recipe_id": "filled_sweet_roll_classic_1",
                "recipe_name": "Classic Cinnamon Roll",
                "description": "Soft, spiraled dough with dark brown sugar and cinnamon.",
                "menu_description": "Soft, spiraled dough with dark brown sugar and cinnamon.",
                "creativity_level": 1
            },
            {
                "recipe_id": "filled_sweet_roll_classic_2",
                "recipe_name": "Sticky Pecan Buns",
                "description": "Caramel-coated inverted sweet rolls heavily studded with pecans.",
                "menu_description": "Caramel-coated inverted sweet rolls heavily studded with pecans.",
                "creativity_level": 1
            },
            {
                "recipe_id": "filled_sweet_roll_classic_3",
                "recipe_name": "Cardamom Knots",
                "description": "Scandinavian style twisted buns heavily spiced with cardamom.",
                "menu_description": "Scandinavian style twisted buns heavily spiced with cardamom.",
                "creativity_level": 1
            },
            {
                "recipe_id": "filled_sweet_roll_classic_4",
                "recipe_name": "Orange Sweet Rolls",
                "description": "Citrus zest dough with a bright orange glaze.",
                "menu_description": "Citrus zest dough with a bright orange glaze.",
                "creativity_level": 1
            },
            {
                "recipe_id": "filled_sweet_roll_classic_5",
                "recipe_name": "Chocolate Babka Knot",
                "description": "Individual twisted buns layered with rich fudge filling.",
                "menu_description": "Individual twisted buns layered with rich fudge filling.",
                "creativity_level": 1
            },
        ],
    }
    default_yield_unit = "loaves"
    target_protein_min = 11.5
    target_protein_max = 13.0
    gluten_behavior = "High Shreddability. Must possess enough structural lift to support heavy lipid loads (butter, sugar, milk, egg yolks) without collapsing."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Demands a clean, sweet, milky baseline; whole-grain bitterness is an active defect."
    tannin_sensitive = True
    default_flavor_inclusions = [
        {"name": "Cinnamon Sugar Swirl", "volume_description": "3 tbsp"},
        {"name": "Raisins", "volume_description": "1/2 cup"},
    ]
    supported_tweaks = ["enrichment", "hydration", "leavening"]
    production_profile = {
        "thermodynamic_focus": "biological_yeast_activity",
        "mechanical_energy_threshold": "high_kneading",
        "environmental_rest_strategy": "gas_proofing",
    }
    secondary_ingredients = {
        "lipids": {
            "default": "unsalted_butter",
            "options": ["unsalted_butter", "salted_butter", "coconut_oil", "avocado_oil"],
            "math_modifiers": {"salted_butter": {"target_target": "salt", "subtract_percentage": 0.015}},
        },
        "liquids": {
            "default": "pure_water",
            "options": ["pure_water", "whole_milk", "heavy_cream", "buttermilk"],
            "math_modifiers": {"buttermilk": {"trigger_chemical_leavening_acid_flag": True}},
        },
        "binders": {"default": "none", "options": ["none", "whole_eggs", "egg_whites", "aquafaba_vegan"]},
    }

    permissible_form_factors = {
        "standard-9x5-pan": {
            "name": "Standard 9x5 Loaf Pan",
            "tier": "recommended",
            "is_portioned": False,
            "unit_weight": 900.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "loaf",
            "unit_label_plural": "loaves",
            "cook_temp_f": 375,
            "bake_time_min": 45,
            "steam_required": False,
            "is_enriched_profile": False,
        },
        "pullman-pan-lidded": {
            "name": "Pullman Pan (Lidded)",
            "tier": "recommended",
            "is_portioned": False,
            "unit_weight": 900.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "loaf",
            "unit_label_plural": "loaves",
            "cook_temp_f": 375,
            "bake_time_min": 45,
            "steam_required": False,
            "is_enriched_profile": False,
        },
        "individual-portion-sheet": {
            "name": "Individual Portion Sheet",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 90.0,
            "base_count": 12,
            "step_increment": 12,
            "unit_label": "bun",
            "unit_label_plural": "buns",
            "cook_temp_f": 375,
            "bake_time_min": 20,
            "steam_required": False,
            "is_enriched_profile": True,
        },
    }

    dynamic_flavor_bases = [
        "Chocolate Fudge Babka",
        "Cinnamon Streusel Swirl",
        "Sweet Maple Braid",
        "Orange Blossom Honey Rolls",
        "Cardamom Almond Crown",
        "Buttermilk Parker House",
        "Spiced Pumpkin Brioche",
        "Vanilla Custard Roll",
        "Toasted Coconut Buns",
        "Raspberry Jam Twists",
        "Apple Cinnamon Morning Buns",
        "Golden Egg Dinner Rolls",
    ]


    presets = [
        "Everyday White Sandwich Loaf",
        "Rich Brioche",
        "Traditional Challah",
        "Hokkaido Milk Bread",
        "Soft Burger Buns",
        "Dinner Rolls",
        "Cinnamon Rolls",
        "Chocolate Babka",
        "Monkey Bread",
    ]

    _archetypes_cache = None

    @property
    def archetypes(self):
        if self.__class__._archetypes_cache is None:
            self.__class__._archetypes_cache = {}
            for subclass in PanEngine.__subclasses__():
                slug = getattr(subclass, "archetype_slug", None)
                if slug:
                    self.__class__._archetypes_cache[slug] = {
                        "default_form_factor": getattr(subclass, "default_form_factor", "standard-9x5-pan"),
                        "label": getattr(subclass, "label", ""),
                        "yield_unit": getattr(subclass, "yield_unit", "loaves"),
                        "icon": getattr(subclass, "icon", ""),
                        "description": getattr(subclass, "description", ""),
                        "grain_affinity": getattr(subclass, "grain_affinity", "medium_protein"),
                        "target_archetype_mechanics": getattr(subclass, "target_archetype_mechanics", {}),
                        "culinary_nuance_directive": getattr(subclass, "culinary_nuance_directive", ""),
                        "preset_matchers": getattr(subclass, "preset_matchers", []),
                        "ingredient_prep_directive": getattr(subclass, "ingredient_prep_directive", getattr(self.__class__, "ingredient_prep_directive", "")),
                        "shaping_directive": getattr(subclass, "shaping_directive", getattr(self.__class__, "shaping_directive", "")),
                    }
        return self.__class__._archetypes_cache

    def apply_sub_class_constraints(
        self,
        hydration: float,
        fat: float,
        sugar: float,
        leaven: float,
        salt: float,
        leaven_type: str = "yeast",
        flavor_profile: str = "neutral",
        **kwargs,
    ) -> tuple[float, float, float, float, float]:
        hyd = max(0.0, min(1.00, hydration))
        f = max(0.0, min(0.60, fat))
        s = max(0.0, min(0.50, sugar))

        if flavor_profile == "savory":
            f = max(0.05, min(0.10, f))
            s = 0.0
            # Scrub eggs if they exist
            sec_binders = kwargs.get("sec_binders", [])
            for binder in list(sec_binders):
                if isinstance(binder, dict) and "egg" in binder.get("name", "").lower():
                    sec_binders.remove(binder)

        if leaven_type == "sourdough":
            leaven = max(0.0, min(0.60, leaven))
        elif leaven_type == "chemical":
            leaven = max(0.0, min(0.10, leaven))
        else:
            leaven = max(0.0, min(0.015, leaven))
        salt = max(0.0, min(0.10, salt))
        return hyd, f, s, leaven, salt

    def get_contextual_pitfalls(self, effective_hydration: float, grain_type: str, preset_slug: str = None) -> list:
        pitfalls = super().get_contextual_pitfalls(effective_hydration, grain_type, preset_slug)
        pitfalls.insert(
            0,
            {
                "title": "Fermentation Retardation",
                "message": "Fats and sugars slow down yeast fermentation. Allow for a longer bulk proof or create a warm, moist proofing box to encourage active rising.",
            },
        )
        return pitfalls

    def get_ai_culinary_directive(self) -> str:
        return "Warn the user if the dough mass will overflow or underfill the selected form factor (e.g. 9x5 loaf pan, pullman pan, or individual rolls). This is an enriched pan bread (e.g. brioche, sandwich loaf). For sweet profiles, use sugar, butter, and eggs. For savory profiles (like garlic herb), STRICTLY OMIT sweeteners and eggs (never use eggs as binders for savory pan breads), and ensure total lipid fat is precisely between 5.0% and 10.0%. Always include a liquid medium and yeast leavener."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives (like seeds), use true baker's percentages (flour = 100%). For sandwich breads, these typically range from 5.0 to 15.0. CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile. CRITICAL: For commercial yeast (active/instant), strictly limit to 0.5 to 1.5. For sourdough starter, limit to 10.0 to 25.0. If total lipid fat exceeds 30.0%, total liquid MUST NOT exceed 85.0% to prevent emulsification failure."

    def get_live_timeline_steps(
        self,
        recipe_data: dict,
        estimated_bulk_minutes: int,
        estimated_proof_minutes: int,
        bake_time_min: int,
        mixing_method: str = "stand_mixer",
        **kwargs,
    ) -> list[dict]:
        mix_min = 6
        knead_min = 12 if mixing_method == "stand_mixer" else 18
        bulk_min = estimated_bulk_minutes
        proof_min = estimated_proof_minutes

        steps = [
            {
                "key": "mix",
                "name": "Lipid Mix Phase",
                "duration_sec": mix_min * 60,
                "desc": "Combine flour, liquids, yeast, sugar, and egg yolks. Mix on low speed to establish the gluten base. Keep butter/fat separate for now to avoid premature coating of gluten proteins.",
                "is_mix": True,
            },
            {
                "key": "knead",
                "name": "Intensive Dough Hook Knead",
                "duration_sec": knead_min * 60,
                "desc": "Slowly incorporate softened butter/fat in pieces while running the stand mixer. Knead intensively until the dough is silky, elastic, and clears the sides of the bowl.",
                "is_knead": True,
            },
            {
                "key": "bulk",
                "name": "Enriched Bulk Ferment",
                "duration_sec": bulk_min * 60,
                "desc": "Enriched doughs ferment slower due to fat and sugar retardants. Keep in a warm, draft-free place.",
            },
        ]

        shape_name = getattr(self, "shape_name", "Loaf Sizing & Portioning")
        shape_desc = getattr(
            self,
            "shape_desc",
            "Divide the dough into uniform portions for multi-loaf scaling. Shape into tight rounds or logs for baking.",
        )
        proof_name = getattr(self, "proof_name", "Loaf Pan Final Proof")
        proof_desc = getattr(
            self,
            "proof_desc",
            "Transfer dough pieces into the greased baking pan. Proof until the dough reaches 1 inch above the pan rim.",
        )
        cooling_desc = getattr(
            self,
            "cooling_desc",
            "Allow the bread to cool in the pan for 10 minutes to stabilize, then carefully turn out onto a wire rack to cool completely. Slicing warm bread will crush the crumb.",
        )
        cooling_duration = getattr(self, "cooling_duration", 60)

        steps.extend(
            [
                {"key": "divide_portion", "name": shape_name, "duration_sec": 10 * 60, "desc": shape_desc},
                {
                    "key": "proof",
                    "name": proof_name,
                    "duration_sec": proof_min * 60,
                    "desc": proof_desc,
                    "is_proof": True,
                },
                {
                    "key": "bake",
                    "name": "Soft Crumb Bake",
                    "duration_sec": bake_time_min * 60,
                    "desc": "Bake at moderate heat (350-375°F). Rich sugars caramelize rapidly; shield loaf/rolls with foil if top browns too early.",
                    "is_bake": True,
                },
            ]
        )

        steps.append(
            {
                "key": "cool",
                "name": "Pan & Wire Rack Cooling",
                "duration_sec": cooling_duration * 60,
                "desc": cooling_desc,
            }
        )

        return steps


class SandwichPanArchetype(PanEngine):
    archetype_slug = "sandwich_pan"
    guardrails = {
        "hydration_min": 50,
        "hydration_max": 95,
        "fat_min": 0,
        "fat_max": 60,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "knead", "bulk_ferment", "shape", "proof", "bake", "cool"],
        "cook_temp_min_f": 350,
        "cook_temp_max_f": 400,
        "cook_time_min_m": 30,
        "cook_time_max_m": 55,
        "boil_required": False,
    }
    label = "Sandwich Pan Loaf"
    icon = "🍞"
    description = "Straight sidewall containment maximizing volume and thin slicing."
    default_form_factor = "standard-9x5-pan"
    grain_affinity = "medium_protein"
    preset_matchers = ["sandwich", "loaf", "pullman", "milk_bread"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "high_retention",
        "desired_horizontal_flow": "controlled_expansion",
        "moisture_lipid_ratio": "balanced_emulsion",
        "optimal_protein_window": "11.0% - 13.0%",
    }
    culinary_nuance_directive = (
        "Focus on maximizing vertical volume and achieving a uniform, tight cell structure. Grains must provide high protein "
        "retention to support thin sidewall pans, ensuring a soft, elastic crumb that slices cleanly without crumbling."
    )
    shape_name = "Loaf Sizing & Portioning"
    shape_desc = (
        "Divide the dough into uniform portions for multi-loaf scaling. Shape into tight rounds or logs for baking."
    )
    proof_name = "Loaf Pan Final Proof"
    proof_desc = (
        "Transfer dough pieces into the greased baking pan. Proof until the dough reaches 1 inch above the pan rim."
    )
    cooling_desc = "Allow the bread to cool in the pan for 10 minutes to stabilize, then carefully turn out onto a wire rack to cool completely. Slicing warm bread will crush the crumb."
    cooling_duration = 60


class FreeformBraidedArchetype(PanEngine):
    archetype_slug = "freeform_braided"
    guardrails = {
        "hydration_min": 50,
        "hydration_max": 95,
        "fat_min": 0,
        "fat_max": 60,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "knead", "bulk_ferment", "shape", "proof", "bake", "cool"],
        "cook_temp_min_f": 350,
        "cook_temp_max_f": 400,
        "cook_time_min_m": 30,
        "cook_time_max_m": 55,
        "boil_required": False,
    }
    label = "Freeform Braided Loaf"
    icon = "🥯"
    description = "High-tensile strands capable of holding shape without pan walls like Challah or Brioche."
    default_form_factor = "standard-9x5-pan"
    grain_affinity = "medium_protein"
    preset_matchers = ["braid", "challah", "brioche"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "high_retention",
        "desired_horizontal_flow": "zero_spread_stable",
        "moisture_lipid_ratio": "balanced_emulsion",
        "optimal_protein_window": "11.5% - 13.5%",
    }
    culinary_nuance_directive = (
        "Focus on high structural retention and zero horizontal flow without pan walls. Grains must yield an elastic, highly "
        "cohesive protein backbone capable of holding intricate braided definition under heavy lipid and sugar enrichment "
        "weights without collapsing or slumping."
    )
    shape_name = "Strand Division & Braiding"
    shape_desc = "Divide dough into equal strands. Roll out and braid tightly. Transfer to a parchment-lined sheet pan."
    proof_name = "Freeform Final Proof"
    proof_desc = "Proof freeform on the baking sheet until nearly doubled in size. Brush with egg wash before baking."
    cooling_desc = "Allow the bread to cool in the pan for 10 minutes to stabilize, then carefully turn out onto a wire rack to cool completely. Slicing warm bread will crush the crumb."
    cooling_duration = 60


class SoftDinnerRollArchetype(PanEngine):
    archetype_slug = "soft_dinner_roll"
    guardrails = {
        "hydration_min": 50,
        "hydration_max": 95,
        "fat_min": 0,
        "fat_max": 60,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "knead", "bulk_ferment", "shape", "proof", "bake", "cool"],
        "cook_temp_min_f": 350,
        "cook_temp_max_f": 400,
        "cook_time_min_m": 30,
        "cook_time_max_m": 55,
        "boil_required": False,
    }
    label = "Soft Dinner Roll"
    yield_unit = "rolls"
    icon = "🫓"
    description = "Small batch pull-apart clusters prioritizing maximum steam-trapped softness."
    default_form_factor = "individual-portion-sheet"
    grain_affinity = "medium_protein"
    preset_matchers = ["roll", "bun"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "high_retention",
        "desired_horizontal_flow": "controlled_expansion",
        "moisture_lipid_ratio": "balanced_emulsion",
        "optimal_protein_window": "11.0% - 12.5%",
    }
    culinary_nuance_directive = (
        "Focus on steam-trapped softness and excellent cluster lift. The protein web must remain extensible and resilient, "
        "allowing small batch dough clusters to crowd together and climb vertically, trapping internal moisture for a classic "
        "feather-light, pull-apart tear texture."
    )
    shape_name = "Roll Portioning"
    shape_desc = "Divide dough into small uniform portions (e.g., 50g-70g). Roll into tight balls and cluster together in a buttered pan."
    proof_name = "Clustered Final Proof"
    proof_desc = "Proof in the pan until the rolls expand, touch each other, and reach the pan rim."
    cooling_desc = "Allow the rolls/buns to cool in the pan for 5-10 minutes. They can be served warm, or transferred to a wire rack to cool completely."
    cooling_duration = 15


class FilledSweetRollArchetype(PanEngine):
    archetype_slug = "filled_sweet_roll"
    guardrails = {
        "hydration_min": 50,
        "hydration_max": 95,
        "fat_min": 0,
        "fat_max": 60,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "knead", "bulk_ferment", "shape", "proof", "bake", "cool"],
        "cook_temp_min_f": 350,
        "cook_temp_max_f": 400,
        "cook_time_min_m": 30,
        "cook_time_max_m": 55,
        "boil_required": False,
    }
    label = "Filled Sweet Roll"
    yield_unit = "rolls"
    icon = "🌀"
    description = "Laminated or sheeted scroll structures built to contain heavy interior fillings."
    default_form_factor = "individual-portion-sheet"
    grain_affinity = "medium_protein"
    preset_matchers = ["cinnamon", "sweet_roll", "babka", "monkey_bread"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "high_retention",
        "desired_horizontal_flow": "controlled_expansion",
        "moisture_lipid_ratio": "balanced_emulsion",
        "optimal_protein_window": "11.5% - 13.0%",
    }
    culinary_nuance_directive = (
        "Focus on uniform dough-sheet stretch and high filling containment. The flour must provide an elastic, robust backbone "
        "capable of being rolled thin, scroll-shaped, and baked without rupturing or allowing heavy sweet fillings to cause "
        "structural collapse."
    )
    shape_name = "Lamination & Filling"
    shape_desc = "Roll dough into a large rectangle. Spread filling evenly, roll into a tight cylinder, and slice into rounds. Place in a prepared pan."
    proof_name = "Filled Pan Proof"
    proof_desc = "Proof the sliced rounds in the pan until puffy and pressing against one another."
    cooling_desc = "Allow the rolls/buns to cool in the pan for 5-10 minutes. They can be served warm, or transferred to a wire rack to cool completely."
    cooling_duration = 15
