from apps.core.engines.base_engine import BaseEngine


class CookieEngine(BaseEngine):
    name = "Cookies & Shortbread Engine"
    slug = "cookie"
    default_starter_recipes = {
        "drop_cookie": [
            {
                "recipe_id": "drop_cookie_classic_1",
                "recipe_name": "Classic Chocolate Chip",
                "description": "Crispy edges, chewy center, loaded with semi-sweet chips.",
                "menu_description": "Crispy edges, chewy center, loaded with semi-sweet chips.",
                "creativity_level": 1
            },
            {
                "recipe_id": "drop_cookie_classic_2",
                "recipe_name": "Snickerdoodle",
                "description": "Soft, tangy cookie rolled generously in cinnamon sugar.",
                "menu_description": "Soft, tangy cookie rolled generously in cinnamon sugar.",
                "creativity_level": 1
            },
            {
                "recipe_id": "drop_cookie_classic_3",
                "recipe_name": "Oatmeal Raisin",
                "description": "Chewy, hearty, spiced cookie loaded with oats and raisins.",
                "menu_description": "Chewy, hearty, spiced cookie loaded with oats and raisins.",
                "creativity_level": 1
            },
            {
                "recipe_id": "drop_cookie_classic_4",
                "recipe_name": "Peanut Butter Criss-Cross",
                "description": "Dense, crumbly, peanut-heavy cookie with fork marks.",
                "menu_description": "Dense, crumbly, peanut-heavy cookie with fork marks.",
                "creativity_level": 1
            },
            {
                "recipe_id": "drop_cookie_classic_5",
                "recipe_name": "Double Chocolate Chunk",
                "description": "Cocoa-based dough with massive dark chocolate chunks.",
                "menu_description": "Cocoa-based dough with massive dark chocolate chunks.",
                "creativity_level": 1
            },
        ],
        "bar_cookie": [
            {
                "recipe_id": "bar_cookie_classic_1",
                "recipe_name": "Fudgy Brownie",
                "description": "Dense, incredibly rich chocolate square with a crinkly top.",
                "menu_description": "Dense, incredibly rich chocolate square with a crinkly top.",
                "creativity_level": 1
            },
            {
                "recipe_id": "bar_cookie_classic_2",
                "recipe_name": "Chewy Blondie",
                "description": "Brown sugar and vanilla base, dense like a brownie but without cocoa.",
                "menu_description": "Brown sugar and vanilla base, dense like a brownie but without cocoa.",
                "creativity_level": 1
            },
            {
                "recipe_id": "bar_cookie_classic_3",
                "recipe_name": "Lemon Bars",
                "description": "Shortbread crust heavily topped with tart lemon curd.",
                "menu_description": "Shortbread crust heavily topped with tart lemon curd.",
                "creativity_level": 1
            },
            {
                "recipe_id": "bar_cookie_classic_4",
                "recipe_name": "Pecan Pie Bars",
                "description": "Shortbread base with a gooey, caramelized pecan topping.",
                "menu_description": "Shortbread base with a gooey, caramelized pecan topping.",
                "creativity_level": 1
            },
            {
                "recipe_id": "bar_cookie_classic_5",
                "recipe_name": "Millionaire's Shortbread",
                "description": "Layers of shortbread, caramel, and a snappy chocolate shell.",
                "menu_description": "Layers of shortbread, caramel, and a snappy chocolate shell.",
                "creativity_level": 1
            },
        ],
        "slice_bake": [
            {
                "recipe_id": "slice_bake_classic_1",
                "recipe_name": "Vanilla Icebox",
                "description": "Simple, buttery slice-and-bake cookies with crisp edges.",
                "menu_description": "Simple, buttery slice-and-bake cookies with crisp edges.",
                "creativity_level": 1
            },
            {
                "recipe_id": "slice_bake_classic_2",
                "recipe_name": "Pinwheels",
                "description": "Swirled chocolate and vanilla dough sliced into spirals.",
                "menu_description": "Swirled chocolate and vanilla dough sliced into spirals.",
                "creativity_level": 1
            },
            {
                "recipe_id": "slice_bake_classic_3",
                "recipe_name": "Pistachio Cranberry",
                "description": "Nutty and tart studded dough logs sliced thin.",
                "menu_description": "Nutty and tart studded dough logs sliced thin.",
                "creativity_level": 1
            },
            {
                "recipe_id": "slice_bake_classic_4",
                "recipe_name": "Checkerboard Cookies",
                "description": "Meticulously stacked square logs sliced for a checkerboard effect.",
                "menu_description": "Meticulously stacked square logs sliced for a checkerboard effect.",
                "creativity_level": 1
            },
            {
                "recipe_id": "slice_bake_classic_5",
                "recipe_name": "Sablé Breton",
                "description": "Rich, salted butter French cookies, baked incredibly crisp.",
                "menu_description": "Rich, salted butter French cookies, baked incredibly crisp.",
                "creativity_level": 1
            },
        ],
        "rolled_cutout": [
            {
                "recipe_id": "rolled_cutout_classic_1",
                "recipe_name": "Gingerbread Men",
                "description": "Sturdy, heavily spiced cookie dough designed for intricate shapes.",
                "menu_description": "Sturdy, heavily spiced cookie dough designed for intricate shapes.",
                "creativity_level": 1
            },
            {
                "recipe_id": "rolled_cutout_classic_2",
                "recipe_name": "Sugar Cookie",
                "description": "Soft, flat cookie specifically formulated to hold royal icing.",
                "menu_description": "Soft, flat cookie specifically formulated to hold royal icing.",
                "creativity_level": 1
            },
            {
                "recipe_id": "rolled_cutout_classic_3",
                "recipe_name": "Linzer Cookies",
                "description": "Nutty cutout dough sandwiched with bright raspberry jam.",
                "menu_description": "Nutty cutout dough sandwiched with bright raspberry jam.",
                "creativity_level": 1
            },
            {
                "recipe_id": "rolled_cutout_classic_4",
                "recipe_name": "Shortbread",
                "description": "Classic Scottish 3-ingredient cookie, crumbly and rich.",
                "menu_description": "Classic Scottish 3-ingredient cookie, crumbly and rich.",
                "creativity_level": 1
            },
            {
                "recipe_id": "rolled_cutout_classic_5",
                "recipe_name": "Alfajores",
                "description": "Tender cornstarch cookies sandwiching dulce de leche.",
                "menu_description": "Tender cornstarch cookies sandwiching dulce de leche.",
                "creativity_level": 1
            },
        ],
    }
    recipe_classification = "Sweet"
    default_yield_unit = "cookies"
    default_binder_pct = 0.35
    default_salt_pct = 0.008
    target_protein_min = 8.5
    target_protein_max = 10.5
    gluten_behavior = "Minimal Gluten Interaction. Flour must allow melting fats and sugars to spread horizontally before the crumb structure sets in the oven."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Designed for toasted brown sugars and confections; whole-grain bitterness clashes aggressively."
    tannin_sensitive = True
    default_flavor_inclusions = [
        {"name": "Dark Chocolate Chunks", "volume_description": "1/2 cup"},
        {"name": "Maldon Sea Salt", "volume_description": "1 tsp flaky"},
    ]
    supported_tweaks = ["enrichment"]
    tweak_labels = {"enrichment": ["Crispy / Chewy", "Soft / Cakey"]}
    variations = {
        "thin_crispy": {
            "guardrails": {
                "permissible_actions": ["mix", "cream", "fold", "chill", "portion", "bake", "cool"],
                "cook_temp_min_f": 325,
                "cook_temp_max_f": 375,
                "cook_time_min_m": 6,
                "cook_time_max_m": 25,
                "boil_required": False,
            },
            "label": "Thin & Crispy",
            "mechanics_overrides": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "high_spread",
                "optimal_protein_window": "8.0% - 9.5%",
            },
            "culinary_nuance_directive_append": (
                "CRITICAL: The user selected THIN & CRISPY. Maximize spread by using high proportions of white sugar "
                "and melted or liquid fats. Favor low-protein soft wheats (e.g., Pastry Flour, Soft White Wheat) "
                "to completely inhibit gluten formation and ensure a delicate, brittle snap. Increase cook time slightly. "
                "GRAIN SELECTION: Select grains that bring sweet, nutty, or buttery notes (like Spelt or Khorasan) "
                "but avoid high-tannin or grassy grains (like Rye) which disrupt the sweet, delicate flavor profile."
            ),
        },
        "soft_chewy": {
            "guardrails": {
                "permissible_actions": ["mix", "cream", "fold", "chill", "portion", "bake", "cool"],
                "cook_temp_min_f": 325,
                "cook_temp_max_f": 375,
                "cook_time_min_m": 6,
                "cook_time_max_m": 25,
                "boil_required": False,
            },
            "label": "Soft & Chewy",
            "mechanics_overrides": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "minimal_spread",
                "optimal_protein_window": "10.0% - 12.0%",
            },
            "culinary_nuance_directive_append": (
                "CRITICAL: The user selected SOFT & CHEWY. Prevent excessive spread by using creamed cold fats "
                "and higher proportions of brown sugar/molasses. Favor higher-protein hard wheats (e.g., Hard White Wheat, "
                "Bread Flour) to build enough gluten structure to maintain thickness and deliver a chewy bite. "
                "Reduce cook time to keep the center doughy. "
                "GRAIN SELECTION: Grains with darker, maltier, or molasses-like flavor profiles (such as Red Fife or whole Rye) "
                "can work beautifully here to complement the brown sugars, provided their bran is milled finely to avoid cutting gluten."
            ),
        },
    }
    production_profile = {
        "thermodynamic_focus": "lipid_emulsification",
        "mechanical_energy_threshold": "low_emulsifying",
        "environmental_rest_strategy": "fat_solidification",
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
        "binders": {"default": "none", "options": ["none", "whole_eggs", "large_eggs", "egg_whites", "aquafaba_vegan"]},
    }

    permissible_form_factors = {
        "heavy-aluminum-sheet": {
            "name": "Heavy Aluminum Cookie Sheet",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 40.0,
            "base_count": 24,
            "step_increment": 12,
            "unit_label": "cookie",
            "unit_label_plural": "cookies",
            "cook_temp_f": 350,
            "bake_time_min": 12,
            "steam_required": False,
            "is_enriched_profile": True,
        },
        "continuous-bar-pan": {
            "name": "Continuous Bar Pan / Single Layer",
            "tier": "sub-optimal",
            "is_portioned": False,
            "unit_weight": 960.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "pan",
            "unit_label_plural": "pans",
            "cook_temp_f": 350,
            "bake_time_min": 25,
            "steam_required": False,
            "is_enriched_profile": True,
        },
    }

    dynamic_flavor_bases = [
        "Snickerdoodle Cinnamon",
        "Triple Chocolate Chunk",
        "White Chocolate Macadamia",
        "Chewy Oatmeal Raisin",
        "Lemon Zest Butter",
        "Spiced Ginger Molasses",
        "Classic Sugar Sparkle",
        "Toasted Pecan Shortbread",
        "Double Fudge Brownie Drop",
        "Maple Walnut Cookie",
        "Cranberry Orange Drop",
        "Almond Butter Sandies",
    ]

    max_liquid_percentage = 80.0
    max_lipid_percentage = 80.0


    presets = [
        "Chewy Chocolate Chip Cookies",
        "Oatmeal Raisin Bakes",
        "Buttery Shortbread Wedges",
        "Italian Almond Biscotti",
        "Gingerbread People",
        "French Almond Macarons",
        "Snickerdoodles",
        "Classic Sugar Cookies",
    ]

    _archetypes_cache = None

    @property
    def archetypes(self):
        if self.__class__._archetypes_cache is None:
            self.__class__._archetypes_cache = {}
            for subclass in CookieEngine.__subclasses__():
                slug = getattr(subclass, "archetype_slug", None)
                if slug:
                    self.__class__._archetypes_cache[slug] = {
                        "default_form_factor": getattr(subclass, "default_form_factor", "heavy-aluminum-sheet"),
                        "default_salt_pct": getattr(subclass, "default_salt_pct", 0.0075),
                        "label": getattr(subclass, "label", ""),
                        "yield_unit": getattr(subclass, "yield_unit", "cookies"),
                        "icon": getattr(subclass, "icon", ""),
                        "description": getattr(subclass, "description", ""),
                        "grain_affinity": getattr(subclass, "grain_affinity", "low_protein"),
                        "target_archetype_mechanics": getattr(subclass, "target_archetype_mechanics", {}),
                        "culinary_nuance_directive": getattr(subclass, "culinary_nuance_directive", ""),
                        "preset_matchers": getattr(subclass, "preset_matchers", []),
                        "ingredient_prep_directive": getattr(subclass, "ingredient_prep_directive", getattr(self.__class__, "ingredient_prep_directive", "")),
                        "shaping_directive": getattr(subclass, "shaping_directive", getattr(self.__class__, "shaping_directive", "")),
                    }
        return self.__class__._archetypes_cache

    def get_diagnostic_insight(self, item_id: str) -> dict:
        from .insights_fallbacks import SWEET_FALLBACKS

        insight = SWEET_FALLBACKS.get(item_id)
        if not insight and item_id.startswith("grain_"):
            for k, val in SWEET_FALLBACKS.items():
                if k.startswith("grain_") and (k in item_id or item_id in k):
                    insight = val
                    break
        return insight or {
            "labor_roi": "Low Priority / Minor Textural Return",
            "last_10_percent_analysis": "An objective workspace configuration parameter. No significant performance anomalies or hidden labor opportunities detected.",
        }

    def get_flavor_bases(self, creativity_level: int) -> list:
        if creativity_level <= 3:
            return ["Vanilla Bean & Brown Butter", "Double Chocolate", "Lemon Zest & Buttermilk"]
        else:
            return ["Matcha & White Chocolate", "Earl Grey & Lavender", "Miso Caramel & Pecan"]

    def get_ai_flavor_directive(self) -> str:
        return "Do not call them 'Spelt Cookie' or 'Rye Cake'. Use creative but clear culinary names."

    def get_ai_structural_directive(self) -> str:
        return "For example, tender confections generally do not need a 'proofing_environment' or 'shaping_surface'."

    def get_sensory_benchmark(
        self,
        grain_type: str,
        flour_maturity: str,
        effective_hydration: float,
        category_slug: str = None,
        preset_slug: str = None,
    ) -> str:
        grain_name = grain_type.replace("_", " ").title()
        desc = f"For fresh-milled {grain_name} confections: "
        if category_slug == "cookies-shortbread":
            desc += "Expect a thick, soft paste or firm chilled dough. The fat should be fully creamed with flour particles evenly coated to control spread. "
        elif category_slug == "cakes-batters":
            desc += "Expect a highly aerated, smooth fluid batter. It should hold micro-air bubbles from egg/fat whipping with zero large pockets. "
        else:
            desc += "The batter/dough should be delicate and soft. Mixing should be kept to an absolute minimum to ensure a tender crumb. "

        if flour_maturity == "just_milled":
            desc += "As this flour was milled today, its enzymes will promote fast browning. Keep mixing short to avoid any accidental gluten development."
        elif flour_maturity == "dead_zone":
            desc += "Caution: Flour is in the 1-2 week dead zone. The structural proteins are slightly unstable. Bake promptly after mixing to ensure the rise sets correctly."
        else:
            desc += "Flour is fully matured. It will provide a highly stable, predictable structure and excellent tender mouthfeel."
        return desc

    def apply_sub_class_constraints(
        self,
        hydration: float,
        fat: float,
        sugar: float,
        leaven: float,
        salt: float,
        leaven_type: str = "yeast",
        **kwargs,
    ) -> tuple[float, float, float, float, float]:
        sec_liquids = kwargs.get("sec_liquids", [])
        has_liquid = False
        for liq in sec_liquids:
            name = str(liq.get("name", "")).lower()
            if name and name not in ["none", "pure water", "water"]:
                has_liquid = True
                break

        cookie_hyd = 0.05 if has_liquid else 0.0

        flavor_inclusions = kwargs.get("flavor_inclusions", [])
        total_inclusion_pct = 0.0
        for inc in flavor_inclusions:
            if isinstance(inc, dict) and "bakers_percentage" in inc:
                try:
                    total_inclusion_pct += float(inc["bakers_percentage"])
                except (ValueError, TypeError):
                    pass

        if total_inclusion_pct < 15.0:
            cookie_fat = max(0.20, min(0.70, fat))
            cookie_sugar = max(0.40, min(0.95, sugar))
        else:
            cookie_fat = max(0.20, min(1.20, fat))
            cookie_sugar = max(0.40, min(2.00, sugar))

        if leaven_type == "sourdough":
            leaven = max(0.0, min(0.60, leaven))
        elif leaven_type == "chemical":
            leaven = max(0.0, min(0.10, leaven))
        else:
            leaven = max(0.0, min(0.015, leaven))
        salt = max(0.0, min(0.10, salt))
        return cookie_hyd, cookie_fat, cookie_sugar, leaven, salt

    def get_ai_culinary_directive(self) -> str:
        return (
            "Cookies require a careful balance of chemical leavening and zero yeast. This is a cookie archetype, "
            "so you MUST include a chemical leavener (baking soda/powder). SPREAD DYNAMICS MATRIX: Fat and Sugar act as liquefiers "
            "(causing spread), while Flour and Inclusions act as stabilizers (restricting spread). For 'Loaded Doughs' "
            "(with heavy structural inclusions like chocolate chips or oats), you may push Fat to 70-100% and Sugar to 100-130% "
            "to bind the extra matter. For 'Bare Doughs' (like snickerdoodles or plain sugar cookies), you MUST strictly limit "
            "Fat (45-65%) and Sugar (50-85%) to prevent the cookie from melting into a puddle. For savory shortbreads, omit sugar "
            "and use savory fats. Liquids are rarely needed unless specified."
        )

    def get_additive_scaling_directive(self) -> str:
        return (
            "When generating ratios for inclusions or additives (like chocolate chips or nuts), use true baker's percentages (flour = 100%). "
            "For loaded cookies (e.g. chocolate chip), bulk inclusions scale heavily (50.0 to 150.0). "
            "For bare cookies, inclusions may be zero or limited to light sprinkles. "
            "CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile. "
            "CRITICAL: For chemical leaveners (baking powder, baking soda), strictly limit to 1.0 to 5.0 to avoid chemical taste. If total lipid fat exceeds 30.0%, total liquid MUST NOT exceed 85.0%."
        )

    def get_live_timeline_steps(
        self,
        recipe_data: dict,
        estimated_bulk_minutes: int,
        estimated_proof_minutes: int,
        bake_time_min: int,
        mixing_method: str = "stand_mixer",
        **kwargs,
    ) -> list[dict]:
        cream_min = 5
        fold_min = 3
        chill_min = 60
        bake_min = bake_time_min

        steps = [
            {
                "key": "mix",
                "name": "Cream Fat & Sugar",
                "duration_sec": cream_min * 60,
                "desc": "Beat butter and sugar together until light and fluffy. Dissolving sugar partially in fat helps manage the final oven spread coefficient.",
                "is_mix": True,
            },
            {
                "key": "fold",
                "name": "Fold Dry & Inclusions",
                "duration_sec": fold_min * 60,
                "desc": "Fold in flour, salt, and inclusions (chocolate chips, oats) just until combined. Do not over-work to keep the crumb tender.",
            },
        ]

        steps.append(
            {
                "key": "chill",
                "name": "Fridge Chilling Rest",
                "duration_sec": chill_min * 60,
                "desc": "Mandatory refrigeration rest for at least 1 hour (up to 24-48 hours for optimal flavor). Chilling solidifies butter fat (slowing spread) and hydrates flour completely for a chewier center.",
            }
        )

        steps.extend(
            [
                {
                    "key": "bake",
                    "name": "Horizontal Spread Bake",
                    "duration_sec": bake_min * 60,
                    "desc": "Scoop dough balls onto sheet pan. Bake until edges are set and golden, watching horizontal expansion spread. Center will set soft.",
                    "is_bake": True,
                },
                {
                    "key": "cool",
                    "name": "Pan & Wire Rack Cooling",
                    "duration_sec": 15 * 60,
                    "desc": "Allow the cookies to cool on the hot baking/pan for 5 minutes before transferring to a wire rack to cool completely. This carryover cooking sets the soft centers.",
                },
            ]
        )
        return steps


class DropCookieArchetype(CookieEngine):
    archetype_slug = "drop_cookie"
    guardrails = {
        "hydration_min": 0,
        "hydration_max": 20,
        "fat_min": 30,
        "fat_max": 85,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "cream", "fold", "chill", "portion", "bake", "cool"],
        "cook_temp_min_f": 325,
        "cook_temp_max_f": 375,
        "cook_time_min_m": 6,
        "cook_time_max_m": 25,
        "boil_required": False,
    }
    label = "Drop Cookie"
    icon = "🍪"
    description = "Irregular mounds designed to flow into tender discs."
    default_form_factor = "half-sheet-pan"
    default_salt_pct = 0.0075
    grain_affinity = "low_protein"
    preset_matchers = ["cookie", "macaron", "snickerdoodle", "bake"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "minimal_to_none",
        "desired_horizontal_flow": "high_spread",
        "moisture_lipid_ratio": "low_moisture_high_fat",
        "optimal_protein_window": "8.5% - 10.5%",
    }
    culinary_nuance_directive = (
        "For drop cookies, the balance of gluten development and moisture retention determines the final texture. "
        "CRITICAL PHYSICS: High pentosan concentrations (found in grains like Rye) can aggressively absorb water, "
        "starving wheat proteins of hydration. This can be used to inhibit gluten for tender textures, or to trap moisture for a gooey chew. "
        "FLAVOR COMPATIBILITY: Strictly sensitive to high-astringent red wheat tannins, which create bitter notes. "
        "Tannin-free Hard White Wheats, Soft White Wheats, or low-malty ancient profiles (like Spelt or Kamut) are excellent choices "
        "that introduce desirable culinary depth without clashing with confections."
    )
    shaping_directive = "Scoop into balls (approx 2 tablespoons). Lightly press down the tops of the dough balls before baking to encourage horizontal spread and even baking edges."
    ingredient_prep_directive = "Butter MUST be properly softened (room temperature, ~65°F) for creaming unless explicitly stated otherwise. Eggs should also be at room temperature to prevent the butter from seizing."

    # Inherits base bake steps


class BarCookieArchetype(CookieEngine):
    archetype_slug = "bar_cookie"
    guardrails = {
        "hydration_min": 0,
        "hydration_max": 20,
        "fat_min": 30,
        "fat_max": 85,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "cream", "fold", "chill", "portion", "bake", "cool"],
        "cook_temp_min_f": 325,
        "cook_temp_max_f": 375,
        "cook_time_min_m": 6,
        "cook_time_max_m": 25,
        "boil_required": False,
    }
    label = "Bar / Slab"
    icon = "🍫"
    description = "Continuous uniform block baking, minimizing perimeter crisping."
    default_form_factor = "heavy-aluminum-sheet"
    default_salt_pct = 0.0075
    yield_unit = "bars"
    grain_affinity = "low_protein"
    preset_matchers = ["bar", "brownie", "blondie", "slab", "continuous"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "minimal_to_none",
        "desired_horizontal_flow": "controlled_expansion",
        "moisture_lipid_ratio": "low_moisture_high_fat",
        "optimal_protein_window": "8.5% - 10.5%",
    }
    culinary_nuance_directive = (
        "Focus on perimeter stability and controlled horizontal expansion. Grains must preserve a tender, short crumb "
        "that slices cleanly without shattering, while providing enough uniform starch walls to hold heavy inclusion "
        "weights across a continuous slab pan without center sinking."
    )
    shaping_directive = "Press dough or spread batter evenly into a parchment-lined baking pan. Ensure corners are filled and the surface is flat for uniform baking."
    ingredient_prep_directive = "If using melted butter or chocolate, allow it to cool slightly before adding eggs to prevent scrambling."

    def get_live_timeline_steps(
        self,
        recipe_data,
        estimated_bulk_minutes,
        estimated_proof_minutes,
        bake_time_min,
        mixing_method="stand_mixer",
        **kwargs,
    ):
        steps = super().get_live_timeline_steps(
            recipe_data, estimated_bulk_minutes, estimated_proof_minutes, bake_time_min, mixing_method, **kwargs
        )
        for step in steps:
            if step["key"] == "bake":
                step["name"] = "Continuous Slab Bake"
                step["desc"] = (
                    "Press dough evenly into a prepared continuous pan. Bake until edges are set and golden. Center will set soft."
                )
        return steps


class SliceBakeArchetype(CookieEngine):
    archetype_slug = "slice_bake"
    guardrails = {
        "hydration_min": 0,
        "hydration_max": 20,
        "fat_min": 30,
        "fat_max": 85,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "cream", "fold", "chill", "portion", "bake", "cool"],
        "cook_temp_min_f": 325,
        "cook_temp_max_f": 375,
        "cook_time_min_m": 6,
        "cook_time_max_m": 25,
        "boil_required": False,
    }
    label = "Slice & Bake"
    icon = "🔪"
    description = "Log configuration, highly compressed fat crystals for crisp rings."
    default_form_factor = "heavy-aluminum-sheet"
    default_salt_pct = 0.0075
    grain_affinity = "low_protein"
    preset_matchers = ["biscotti", "slice"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "minimal_to_none",
        "desired_horizontal_flow": "controlled_expansion",
        "moisture_lipid_ratio": "low_moisture_high_fat",
        "optimal_protein_window": "8.5% - 10.0%",
    }
    culinary_nuance_directive = (
        "Focus on high compression crystal arrays and clean circular margins. Dough demands maximum fat-crystal packing "
        "with minimal protein resilience, allowing chilled logs to be sheeted or sliced cleanly without dragging crumbs, "
        "baking into uniform, crisp rings."
    )
    shaping_directive = "Form dough into a tight, even log, wrap tightly in plastic, and chill until completely firm. Slice evenly (approx 1/4 to 1/2 inch thick) using a sharp knife before baking."
    ingredient_prep_directive = "Butter must be properly softened for initial mixing, but the final dough MUST be thoroughly chilled before slicing."

    def get_live_timeline_steps(
        self,
        recipe_data,
        estimated_bulk_minutes,
        estimated_proof_minutes,
        bake_time_min,
        mixing_method="stand_mixer",
        **kwargs,
    ):
        steps = super().get_live_timeline_steps(
            recipe_data, estimated_bulk_minutes, estimated_proof_minutes, bake_time_min, mixing_method, **kwargs
        )

        chill_idx = next((i for i, s in enumerate(steps) if s["key"] == "chill"), 2)
        steps.insert(
            chill_idx,
            {
                "key": "shape_log",
                "name": "Form Dough Cylinder",
                "duration_sec": 10 * 60,
                "desc": "Form dough into a tight cylinder or log on parchment paper before chilling.",
            },
        )

        for step in steps:
            if step["key"] == "bake":
                step["name"] = "Sliced Disc Bake"
                step["desc"] = (
                    "Slice chilled log into uniform discs and arrange on a baking sheet. Bake until crisp and golden."
                )
        return steps


class RolledCutoutArchetype(CookieEngine):
    archetype_slug = "rolled_cutout"
    shaping_directive = "Roll dough out evenly (approx 1/4 inch thick) on a lightly floured surface or between parchment sheets. Cut into desired shapes, minimizing re-rolling to prevent tough cookies."
    ingredient_prep_directive = "Dough usually requires chilling before rolling to maintain sharp edges during cutting and baking."
    guardrails = {
        "hydration_min": 0,
        "hydration_max": 20,
        "fat_min": 30,
        "fat_max": 85,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "cream", "fold", "chill", "portion", "bake", "cool"],
        "cook_temp_min_f": 325,
        "cook_temp_max_f": 375,
        "cook_time_min_m": 6,
        "cook_time_max_m": 25,
        "boil_required": False,
    }
    label = "Rolled Cutout"
    icon = "📐"
    description = "Zero-spread formulation maintaining clean geometric edges post-bake."
    default_form_factor = "half-sheet-pan"
    default_salt_pct = 0.0075
    grain_affinity = "medium_protein"
    preset_matchers = ["gingerbread", "shortbread", "cutout", "sugar"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "moderate_extensible",
        "desired_horizontal_flow": "zero_spread_stable",
        "moisture_lipid_ratio": "low_moisture_high_fat",
        "optimal_protein_window": "9.0% - 11.0%",
    }
    culinary_nuance_directive = (
        "Focus on moderate structural extensibility and zero thermal flow. Grains must allow the dough to accept "
        "sharp die-cutting and release cleanly from rolling mats, holding precise geometric definitions and sharp "
        "borders under immediate oven heat."
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
        steps = super().get_live_timeline_steps(
            recipe_data, estimated_bulk_minutes, estimated_proof_minutes, bake_time_min, mixing_method, **kwargs
        )
        for step in steps:
            if step["key"] == "bake":
                step["name"] = "Geometric Rolled Bake"
                step["desc"] = (
                    "Roll out chilled dough on a floured surface, cut with geometric dies/cutters, and place on sheet pan. Bake until edges are set."
                )
        return steps
