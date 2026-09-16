from apps.core.engines.base_engine import BaseEngine


class PastaEngine(BaseEngine):
    name = "Fresh Pasta & Noodles Engine"
    slug = "pasta"
    default_starter_recipes = {
        "sheeted_ribbon": [
            {
                "recipe_id": "sheeted_ribbon_classic_1",
                "recipe_name": "Fettuccine",
                "description": "Flat, thick ribbons perfect for heavy cream or cheese sauces.",
                "menu_description": "Flat, thick ribbons perfect for heavy cream or cheese sauces.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "sheeted_ribbon_classic_2",
                "recipe_name": "Pappardelle",
                "description": "Wide, rustic ribbons designed to hold hearty ragù.",
                "menu_description": "Wide, rustic ribbons designed to hold hearty ragù.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "sheeted_ribbon_classic_3",
                "recipe_name": "Tagliatelle",
                "description": "Classic Bolognese ribbon pasta, slightly thinner than fettuccine.",
                "menu_description": "Classic Bolognese ribbon pasta, slightly thinner than fettuccine.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "sheeted_ribbon_classic_4",
                "recipe_name": "Lasagna Sheets",
                "description": "Wide, flat sheets used for layering with cheese and sauce.",
                "menu_description": "Wide, flat sheets used for layering with cheese and sauce.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "sheeted_ribbon_classic_5",
                "recipe_name": "Linguine",
                "description": "Flattened oval noodles, delicate enough for seafood sauces.",
                "menu_description": "Flattened oval noodles, delicate enough for seafood sauces.",
                "creativity_level": 1,
            },
        ],
        "stuffed_pocket": [
            {
                "recipe_id": "stuffed_pocket_classic_1",
                "recipe_name": "Cheese Ravioli",
                "description": "Square pasta pockets filled with ricotta and parmesan.",
                "menu_description": "Square pasta pockets filled with ricotta and parmesan.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "stuffed_pocket_classic_2",
                "recipe_name": "Tortellini",
                "description": "Small, ring-shaped stuffed pasta typically filled with meat or cheese.",
                "menu_description": "Small, ring-shaped stuffed pasta typically filled with meat or cheese.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "stuffed_pocket_classic_3",
                "recipe_name": "Agnolotti",
                "description": "Piedmontese pinched pasta pockets with savory fillings.",
                "menu_description": "Piedmontese pinched pasta pockets with savory fillings.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "stuffed_pocket_classic_4",
                "recipe_name": "Mezzaluna",
                "description": "Half-moon shaped stuffed pasta.",
                "menu_description": "Half-moon shaped stuffed pasta.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "stuffed_pocket_classic_5",
                "recipe_name": "Pierogi",
                "description": "Thicker dough pockets stuffed with potato and cheese.",
                "menu_description": "Thicker dough pockets stuffed with potato and cheese.",
                "creativity_level": 1,
            },
        ],
        "extruded_shape": [
            {
                "recipe_id": "extruded_shape_classic_1",
                "recipe_name": "Penne Rigate",
                "description": "Ridged tubes cut on a bias to hold thick sauces.",
                "menu_description": "Ridged tubes cut on a bias to hold thick sauces.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "extruded_shape_classic_2",
                "recipe_name": "Rigatoni",
                "description": "Large, straight, ridged tubes perfect for chunky meat sauces.",
                "menu_description": "Large, straight, ridged tubes perfect for chunky meat sauces.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "extruded_shape_classic_3",
                "recipe_name": "Macaroni",
                "description": "Small, curved tubes ubiquitous in cheese sauces.",
                "menu_description": "Small, curved tubes ubiquitous in cheese sauces.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "extruded_shape_classic_4",
                "recipe_name": "Fusilli",
                "description": "Corkscrew shaped pasta that traps sauce in its spirals.",
                "menu_description": "Corkscrew shaped pasta that traps sauce in its spirals.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "extruded_shape_classic_5",
                "recipe_name": "Bucatini",
                "description": "Thick, spaghetti-like pasta with a hole running through the center.",
                "menu_description": "Thick, spaghetti-like pasta with a hole running through the center.",
                "creativity_level": 1,
            },
        ],
        "alkaline_noodles": [
            {
                "recipe_id": "alkaline_noodles_classic_1",
                "recipe_name": "Tokyo Ramen",
                "description": "Thin, firm, slightly wavy alkaline noodles.",
                "menu_description": "Thin, firm, slightly wavy alkaline noodles.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "alkaline_noodles_classic_2",
                "recipe_name": "Hakata Ramen",
                "description": "Ultra-thin, straight, low-hydration noodles for tonkotsu broth.",
                "menu_description": "Ultra-thin, straight, low-hydration noodles for tonkotsu broth.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "alkaline_noodles_classic_3",
                "recipe_name": "Tsukemen",
                "description": "Thick, highly chewy alkaline noodles meant for dipping.",
                "menu_description": "Thick, highly chewy alkaline noodles meant for dipping.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "alkaline_noodles_classic_4",
                "recipe_name": "Lo Mein",
                "description": "Soft, thick Chinese egg noodles for stir-frying.",
                "menu_description": "Soft, thick Chinese egg noodles for stir-frying.",
                "creativity_level": 1,
            },
            {
                "recipe_id": "alkaline_noodles_classic_5",
                "recipe_name": "Wonton Noodles",
                "description": "Thin, incredibly springy egg and alkaline noodles.",
                "menu_description": "Thin, incredibly springy egg and alkaline noodles.",
                "creativity_level": 1,
            },
        ],
    }
    primary_cooking_method = "Boiling"
    default_yield_unit = "portions"
    default_binder_pct = 0.50
    default_leaven_pct = 0.0
    target_protein_min = 12.5
    target_protein_max = 15.0
    gluten_behavior = "High Plastic Deformation, Zero Leavening. Requires an ultra-dense, low-hydration network that maintains a firm, snap-resistant 'al dente' structural bite when boiled."
    flavor_affinity = "Tannin Tolerant (Rustic/Savory). Welcomes rich egg, nutty semolina, or distinctive alkaline noodle mineral complexities."
    tannin_sensitive = False
    production_profile = {
        "thermodynamic_focus": "hydration_binding_shock",
        "mechanical_energy_threshold": "mechanical_compaction",
        "environmental_rest_strategy": "gluten_relaxation",
    }
    secondary_ingredients = {
        "liquids": {
            "default": "pure_water",
            "options": ["pure_water", "whole_milk", "heavy_cream", "buttermilk"],
            "math_modifiers": {"buttermilk": {"trigger_chemical_leavening_acid_flag": True}},
        },
        "binders": {"default": "whole_eggs", "options": ["none", "whole_eggs", "egg_whites", "aquafaba_vegan"]},
    }

    permissible_form_factors = {
        "mechanical-sheeter": {
            "name": "Mechanical Sheeter Sheets / Cutters",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 120.0,
            "base_count": 4,
            "step_increment": 2,
            "unit_label": "serving",
            "unit_label_plural": "servings",
            "cook_temp_f": 212,
            "bake_time_min": 3,
            "steam_required": False,
            "is_enriched_profile": False,
        },
        "high-pressure-dies": {
            "name": "High-Pressure Extrusion Dies",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 120.0,
            "base_count": 4,
            "step_increment": 2,
            "unit_label": "serving",
            "unit_label_plural": "servings",
            "cook_temp_f": 212,
            "bake_time_min": 3,
            "steam_required": False,
            "is_enriched_profile": False,
        },
    }

    dynamic_flavor_bases = [
        "Saffron Egg Tagliatelle",
        "Spinach Ricotta Ravioli",
        "Beet Root Pink Lasagna",
        "Squid Ink Black Linguine",
        "Porcini Mushroom Fettuccine",
        "Roasted Garlic Pappardelle",
        "Black Pepper Semolina Pasta",
        "Basil Pesto Penne",
        "Tomato Paste Fettuccine",
        "Lemon Herb Tagliolini",
        "Spiced Red Pepper Pappardelle",
        "Whole Grain Durum Noodle",
    ]

    ai_cook_temp_override = 212
    ai_cook_time_override = 3

    presets = [
        "Fresh Egg Tagliatelle",
        "Fettuccine Sheets",
        "Ravioli / Tortellini Dough",
        "Semolina Extruded Rigatoni",
        "Thick Hand-Cut Udon",
        "Alkaline Wheat Ramen Noodles",
        "Gyoza / Dumpling Wrappers",
    ]

    _archetypes_cache = None

    @property
    def archetypes(self):
        if self.__class__._archetypes_cache is None:
            self.__class__._archetypes_cache = {}
            for subclass in PastaEngine.__subclasses__():
                slug = getattr(subclass, "archetype_slug", None)
                if slug:
                    self.__class__._archetypes_cache[slug] = {
                        "default_form_factor": getattr(subclass, "default_form_factor", "mechanical-sheeter"),
                        "default_salt_pct": getattr(subclass, "default_salt_pct", 0.0),
                        "label": getattr(subclass, "label", ""),
                        "yield_unit": getattr(subclass, "yield_unit", "portions"),
                        "icon": getattr(subclass, "icon", ""),
                        "description": getattr(subclass, "description", ""),
                        "grain_affinity": getattr(subclass, "grain_affinity", "high_protein"),
                        "target_archetype_mechanics": getattr(subclass, "target_archetype_mechanics", {}),
                        "culinary_nuance_directive": getattr(subclass, "culinary_nuance_directive", ""),
                        "preset_matchers": getattr(subclass, "preset_matchers", []),
                        "ingredient_prep_directive": getattr(
                            subclass,
                            "ingredient_prep_directive",
                            getattr(self.__class__, "ingredient_prep_directive", ""),
                        ),
                        "shaping_directive": getattr(
                            subclass, "shaping_directive", getattr(self.__class__, "shaping_directive", "")
                        ),
                    }
        return self.__class__._archetypes_cache

    def get_diagnostic_insight(self, item_id: str) -> dict:
        from .insights_fallbacks import PASTA_FALLBACKS

        insight = PASTA_FALLBACKS.get(item_id)
        if not insight and item_id.startswith("grain_"):
            for k, val in PASTA_FALLBACKS.items():
                if k.startswith("grain_") and (k in item_id or item_id in k):
                    insight = val
                    break
        return insight or {
            "labor_roi": "Low Priority / Minor Textural Return",
            "last_10_percent_analysis": "An objective workspace configuration parameter. No significant performance anomalies or hidden labor opportunities detected.",
        }

    def get_flavor_bases(self, creativity_level: int) -> list:
        return ["Rich Egg Yolk & Semolina", "Spinach & Herb", "Squid Ink & Lemon"]

    def get_ai_flavor_directive(self) -> str:
        return (
            "Do not call them 'Spelt Noodle'. Use creative but clear culinary names like 'Rustic Einkorn Tagliatelle'."
        )

    def get_ai_structural_directive(self) -> str:
        return "For example, pasta generally does not need a 'proofing_environment', it needs resting and sheeting."

    def get_sensory_benchmark(
        self,
        grain_type: str,
        flour_maturity: str,
        effective_hydration: float,
        category_slug: str = None,
        preset_slug: str = None,
    ) -> str:
        grain_name = grain_type.replace("_", " ").title()
        desc = f"For fresh-milled {grain_name} pasta: "
        desc += "Expect a very dense, dry, and crumbly initial mixture. It should consolidate into a firm, non-sticky mass after firm pressure. "

        if flour_maturity == "just_milled":
            desc += "Today's fresh-milled flour hydrates rapidly but the gluten needs extra resting time. Let the wrapped dough sit for 45 minutes before sheeting."
        elif flour_maturity == "dead_zone":
            desc += "Caution: Flour is in the 1-2 week dead zone. The dough might feel slightly brittle during sheeting; roll out slowly to prevent edge cracking."
        else:
            desc += "Flour is fully matured. Gluten structure is stable and resilient, providing an excellent al dente bite when boiled."
        return desc

    def apply_sub_class_constraints(
        self, hydration: float, fat: float, sugar: float, leaven: float, salt: float, leaven_type: str = "yeast"
    ) -> tuple[float, float, float, float, float]:
        hyd = max(0.0, min(0.50, hydration))
        f = max(0.0, min(0.20, fat))
        s = max(0.0, min(0.10, sugar))
        if leaven_type == "sourdough":
            leaven = max(0.0, min(0.60, leaven))
        elif leaven_type == "chemical":
            leaven = max(0.0, min(0.10, leaven))
        else:
            leaven = max(0.0, min(0.015, leaven))
        salt = max(0.0, min(0.10, salt))
        return hyd, f, s, leaven, salt

    def get_ai_culinary_directive(self) -> str:
        return "Pasta requires zero chemical or biological leavening. Focus on mechanical compaction and zero yeast. This is pasta/noodles. NEVER include leaveners or sweeteners. Focus purely on liquids and binders (eggs). CRITICAL: For fresh pasta, target_cook_temp MUST ALWAYS be 212."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives (like herbs or squid ink), use true baker's percentages (flour = 100%). For pastas, these typically range from 1.0 to 5.0. CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile."

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
        knead_min = 10
        rest_min = 30
        roll_min = 15
        cut_min = 10

        steps = [
            {
                "key": "mix",
                "name": "Compaction Mix",
                "duration_sec": mix_min * 60,
                "desc": "Combine flour/semolina and eggs/water. The mixture will look extremely dry and crumbly; press firmly to compact into a solid mass.",
                "is_mix": True,
            },
            {
                "key": "knead",
                "name": "Compaction Knead",
                "duration_sec": knead_min * 60,
                "desc": "Knead vigorously by hand on a clean surface. Press and fold to force hydration of dense semolina starches. The dough will become smooth and very firm.",
                "is_knead": True,
            },
            {
                "key": "proof",
                "name": "Plastic Hydration Rest",
                "duration_sec": rest_min * 60,
                "desc": "Wrap dough tightly in plastic wrap. Rest at room temperature. Allows moisture to equilibrate and the rigid gluten matrix to relax.",
                "is_proof": True,
            },
        ]

        finish_steps = getattr(self, "finish_steps", [])
        if finish_steps:
            for s in finish_steps:
                steps.append(
                    {
                        "key": s["key"],
                        "name": s["name"],
                        "duration_sec": (roll_min if s["key"] == "roll_pass" else cut_min) * 60,
                        "desc": s["desc"],
                        **({"is_bake": True} if s.get("is_bake") else {}),
                    }
                )
        else:
            steps.append(
                {
                    "key": "roll_pass",
                    "name": "Mechanical Roller Passes",
                    "duration_sec": roll_min * 60,
                    "desc": "Divide dough into portions. Run through roller Setting 0, fold, and repeat. Set thickness down incrementally one setting at a time until reaching Setting 6 or 7 (~1.2mm).",
                }
            )
            steps.append(
                {
                    "key": "bake",
                    "name": "Dust, Cut & Air-Dry",
                    "duration_sec": cut_min * 60,
                    "desc": "Dust sheet with semolina flour. Cut into noodles (e.g. tagliatelle) or wrappers. Let dry on a rack or cook immediately in boiling salted water.",
                    "is_bake": True,
                }
            )

        return steps


class SheetedRibbonArchetype(PastaEngine):
    archetype_slug = "sheeted_ribbon"
    guardrails = {
        "hydration_min": 30,
        "hydration_max": 55,
        "fat_min": 0,
        "fat_max": 10,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "knead", "rest", "sheet", "extrude", "boil"],
        "cook_temp_min_f": 0,
        "cook_temp_max_f": 0,
        "cook_time_min_m": 0,
        "cook_time_max_m": 0,
        "boil_required": False,
    }
    label = "Sheeted Ribbon Pastas"
    icon = "🍝"
    description = "Gradual reduction sheeting cut into strands like Tagliatelle or Fettuccine."
    default_form_factor = "mechanical-sheeter"
    default_salt_pct = 0.0
    grain_affinity = "high_protein"
    preset_matchers = ["tagliatelle", "fettuccine", "ribbon", "sheet"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "extreme_tensile",
        "desired_horizontal_flow": "zero_spread_stable",
        "moisture_lipid_ratio": "balanced_emulsion",
        "optimal_protein_window": "12.5% - 15.0%",
    }
    culinary_nuance_directive = (
        "Focus on structural deformation and rolling mechanics. Grains must allow the matrix "
        "to be sheeted down to sub-millimeter thickness through sequential mechanical passes without tearing, "
        "accommodating either a firm 'al dente' bite or a silky-smooth texture depending on the variation."
    )
    finish_steps = [
        {
            "key": "roll_pass",
            "name": "Mechanical Roller Passes",
            "desc": "Divide dough into portions. Run through roller Setting 0, fold, and repeat. Set thickness down incrementally one setting at a time until reaching Setting 6 or 7 (~1.2mm).",
        },
        {
            "key": "bake",
            "name": "Dust, Cut & Air-Dry",
            "desc": "Dust sheet with semolina flour. Cut into noodles (e.g. tagliatelle) or wrappers. Let dry on a rack or cook immediately in boiling salted water.",
            "is_bake": True,
        },
    ]


class StuffedPocketArchetype(PastaEngine):
    archetype_slug = "stuffed_pocket"
    guardrails = {
        "hydration_min": 30,
        "hydration_max": 55,
        "fat_min": 0,
        "fat_max": 10,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "knead", "rest", "sheet", "extrude", "boil"],
        "cook_temp_min_f": 0,
        "cook_temp_max_f": 0,
        "cook_time_min_m": 0,
        "cook_time_max_m": 0,
        "boil_required": False,
    }
    label = "Stuffed / Encased Pockets"
    icon = "🥟"
    description = "High-elasticity envelopes meant to seal wet fillings securely like Ravioli."
    default_form_factor = "mechanical-sheeter"
    default_salt_pct = 0.0
    grain_affinity = "high_protein"
    preset_matchers = ["stuffed", "ravioli", "tortellini", "gyoza", "dumpling"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "extreme_tensile",
        "desired_horizontal_flow": "zero_spread_stable",
        "moisture_lipid_ratio": "balanced_emulsion",
        "optimal_protein_window": "12.0% - 14.5%",
    }
    culinary_nuance_directive = (
        "Focus on high structural extensibility and watertight protein cross-linking. The matrix must form a dense, flexible "
        "envelope that seals damp fillings securely, stretching cleanly without tearing or leaching starches when dropped into "
        "rolling boiling water."
    )
    finish_steps = [
        {
            "key": "roll_pass",
            "name": "Mechanical Roller Passes",
            "desc": "Divide dough into portions. Run through roller Setting 0, fold, and repeat. Set thickness down incrementally one setting at a time until reaching Setting 6 or 7 (~1.2mm).",
        },
        {
            "key": "bake",
            "name": "Fill, Seal & Cut",
            "desc": "Pipe filling in mounds along sheet, lay second sheet on top (or fold over), press out air to seal edges tightly, and cut into pockets.",
            "is_bake": True,
        },
    ]


class ExtrudedShapeArchetype(PastaEngine):
    archetype_slug = "extruded_shape"
    guardrails = {
        "hydration_min": 30,
        "hydration_max": 55,
        "fat_min": 0,
        "fat_max": 10,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "knead", "rest", "sheet", "extrude", "boil"],
        "cook_temp_min_f": 0,
        "cook_temp_max_f": 0,
        "cook_time_min_m": 0,
        "cook_time_max_m": 0,
        "boil_required": False,
    }
    label = "Extruded Die Shapes"
    icon = "🔩"
    description = "High-pressure compression matrix tubes or hollows like Rigatoni."
    default_form_factor = "high-pressure-dies"
    default_salt_pct = 0.0
    grain_affinity = "high_protein"
    preset_matchers = ["extrud", "rigatoni", "macaroni"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "extreme_tensile",
        "desired_horizontal_flow": "zero_spread_stable",
        "moisture_lipid_ratio": "balanced_emulsion",
        "optimal_protein_window": "13.0% - 15.0%",
    }
    culinary_nuance_directive = (
        "Focus on maximum high-pressure compaction stability. The flour must yield an ultra-dense, non-elastic protein web "
        "that forces smoothly through mechanical dies, retaining sharp structural ridges and hollows without losing shape or "
        "turning gummy when boiled."
    )
    finish_steps = [
        {
            "key": "roll_pass",
            "name": "High-Pressure Extrusion",
            "desc": "Extrude dough through high-pressure bronze or teflon dies, cutting to desired length.",
        },
        {
            "key": "bake",
            "name": "Air-Dry / Cook",
            "desc": "Let the extruded shapes air dry slightly on a mesh rack, or cook immediately in boiling salted water.",
            "is_bake": True,
        },
    ]


class AlkalineNoodlesArchetype(PastaEngine):
    archetype_slug = "alkaline_noodles"
    guardrails = {
        "hydration_min": 30,
        "hydration_max": 55,
        "fat_min": 0,
        "fat_max": 10,
        "sugar_min": 0.0,
        "sugar_max": 20.0,
        "salt_min": 0.5,
        "salt_max": 3.0,
        "permissible_actions": ["mix", "knead", "rest", "sheet", "extrude", "boil"],
        "cook_temp_min_f": 0,
        "cook_temp_max_f": 0,
        "cook_time_min_m": 0,
        "cook_time_max_m": 0,
        "boil_required": False,
    }
    label = "Alkaline Cut Noodles"
    icon = "🍜"
    description = "Mineral-fortified strings built for snap and yellow coloration like Ramen."
    default_form_factor = "mechanical-sheeter"
    default_salt_pct = 0.0
    grain_affinity = "high_protein"
    preset_matchers = ["ramen", "alkaline", "udon"]
    target_archetype_mechanics = {
        "required_gluten_elasticity": "extreme_tensile",
        "desired_horizontal_flow": "zero_spread_stable",
        "moisture_lipid_ratio": "balanced_emulsion",
        "optimal_protein_window": "12.0% - 14.5%",
    }
    culinary_nuance_directive = (
        "Focus on high tensile snap and mineral-induced protein compaction. Grains must provide a clean, high-protein background "
        "that interacts with alkaline salts to accelerate snapping elasticity, keeping the strands firm and springy while "
        "resisting grey structural discoloration."
    )
    finish_steps = [
        {
            "key": "roll_pass",
            "name": "Mechanical Roller Passes",
            "desc": "Divide dough into portions. Run through roller Setting 0, fold, and repeat. Set thickness down incrementally one setting at a time until reaching Setting 6 or 7 (~1.2mm).",
        },
        {
            "key": "bake",
            "name": "Dust, Cut & Air-Dry",
            "desc": "Dust sheet with semolina flour. Cut into noodles (e.g. tagliatelle) or wrappers. Let dry on a rack or cook immediately in boiling salted water.",
            "is_bake": True,
        },
    ]
