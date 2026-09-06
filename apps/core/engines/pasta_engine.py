from apps.core.engines.base_engine import BaseEngine


class PastaEngine(BaseEngine):
    name = "Fresh Pasta & Noodles Engine"
    slug = "pasta"
    default_binder_pct = 0.50
    default_leaven_pct = 0.0
    target_protein_min = 12.5
    target_protein_max = 15.0
    gluten_behavior = "High Plastic Deformation, Zero Leavening. Requires an ultra-dense, low-hydration network that maintains a firm, snap-resistant 'al dente' structural bite when boiled."
    flavor_affinity = "Tannin Tolerant (Rustic/Savory). Welcomes rich egg, nutty semolina, or distinctive alkaline noodle mineral complexities."
    tannin_sensitive = False
    variations = {
        "delicate_silky": {
            "label": "Delicate & Silky (Egg Pasta)",
            "mechanics_overrides": {
                "required_gluten_elasticity": "moderate_extensible",
                "optimal_protein_window": "8.5% - 10.0%",
            },
            "culinary_nuance_directive_append": (
                "CRITICAL: The user selected DELICATE & SILKY. This is ideal for ravioli or thin ribbons. "
                "Rely on low-protein soft wheats (like Type 00 or Soft White Wheat) to create a tender, melt-in-the-mouth "
                "texture. Rely heavily on whole eggs or egg yolks for hydration and structure."
            ),
        },
        "sturdy_chewy": {
            "label": "Sturdy & Chewy (Extruded/Rustic)",
            "mechanics_overrides": {
                "required_gluten_elasticity": "highly_elastic_rigid",
                "optimal_protein_window": "12.0% - 14.0%",
            },
            "culinary_nuance_directive_append": (
                "CRITICAL: The user selected STURDY & CHEWY. This pasta must hold up to heavy sauces and boiling. "
                "Favor extremely hard, high-protein grains (like Durum / Semolina or Hard Red Wheat). "
                "Limit egg usage and favor water to develop a rigid gluten structure with 'al dente' bite."
            ),
        },
    }
    production_profile = {
        "thermodynamic_focus": "hydration_binding_shock",
        "mechanical_energy_threshold": "mechanical_compaction",
        "permissible_action_types": ["knead", "roll"],
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
            "bake_temp_f": 0,
            "bake_time_min": 0,
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
            "bake_temp_f": 0,
            "bake_time_min": 0,
            "steam_required": False,
            "is_enriched_profile": False,
        },
    }

    presets = [
        "Fresh Egg Tagliatelle",
        "Fettuccine Sheets",
        "Ravioli / Tortellini Dough",
        "Semolina Extruded Rigatoni",
        "Thick Hand-Cut Udon",
        "Alkaline Wheat Ramen Noodles",
        "Gyoza / Dumpling Wrappers",
    ]

    archetypes = {
        "sheeted_ribbon": {
            "default_form_factor": "mechanical-sheeter",
            "default_salt_pct": 0.0,
            "label": "Sheeted Ribbon Pastas",
            "icon": "🍝",
            "description": "Gradual reduction sheeting cut into strands like Tagliatelle or Fettuccine.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "default_form_factor": "mechanical-sheeter",
                "default_salt_pct": 0.0,
                "default_form_factor": "mechanical-sheeter",
                "default_salt_pct": 0.0,
                "default_form_factor": "mechanical-sheeter",
                "default_salt_pct": 0.0,
                "default_form_factor": "mechanical-sheeter",
                "default_salt_pct": 0.0,
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "12.5% - 15.0%",
            },
            "culinary_nuance_directive": (
                "Focus on structural deformation and rolling mechanics. Grains must allow the matrix "
                "to be sheeted down to sub-millimeter thickness through sequential mechanical passes without tearing, "
                "accommodating either a firm 'al dente' bite or a silky-smooth texture depending on the variation."
            ),
        },
        "stuffed_pocket": {
            "default_form_factor": "mechanical-sheeter",
            "default_salt_pct": 0.0,
            "label": "Stuffed / Encased Pockets",
            "icon": "🥟",
            "description": "High-elasticity envelopes meant to seal wet fillings securely like Ravioli.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "12.0% - 14.5%",
            },
            "culinary_nuance_directive": (
                "Focus on high structural extensibility and watertight protein cross-linking. The matrix must form a dense, flexible "
                "envelope that seals damp fillings securely, stretching cleanly without tearing or leaching starches when dropped into "
                "rolling boiling water."
            ),
        },
        "extruded_shape": {
            "default_form_factor": "mechanical-sheeter",
            "default_salt_pct": 0.0,
            "label": "Extruded Die Shapes",
            "icon": "🔩",
            "description": "High-pressure compression matrix tubes or hollows like Rigatoni.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "13.0% - 15.0%",
            },
            "culinary_nuance_directive": (
                "Focus on maximum high-pressure compaction stability. The flour must yield an ultra-dense, non-elastic protein web "
                "that forces smoothly through mechanical dies, retaining sharp structural ridges and hollows without losing shape or "
                "turning gummy when boiled."
            ),
        },
        "alkaline_noodles": {
            "default_form_factor": "mechanical-sheeter",
            "default_salt_pct": 0.0,
            "label": "Alkaline Cut Noodles",
            "icon": "🍜",
            "description": "Mineral-fortified strings built for snap and yellow coloration like Ramen.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "12.0% - 14.5%",
            },
            "culinary_nuance_directive": (
                "Focus on high tensile snap and mineral-induced protein compaction. Grains must provide a clean, high-protein background "
                "that interacts with alkaline salts to accelerate snapping elasticity, keeping the strands firm and springy while "
                "resisting grey structural discoloration."
            ),
        },
    }

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
        return "Pasta requires zero chemical or biological leavening. Focus on mechanical compaction and zero yeast. This is pasta/noodles. NEVER include leaveners or sweeteners. Focus purely on liquids and binders (eggs). CRITICAL: For fresh pasta, target_bake_temp MUST ALWAYS be 212."

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
        preset_slug = kwargs.get("preset_slug") or ""

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

        if "extrud" in preset_slug.lower() or "rigatoni" in preset_slug.lower():
            steps.extend(
                [
                    {
                        "key": "roll_pass",
                        "name": "High-Pressure Extrusion",
                        "duration_sec": roll_min * 60,
                        "desc": "Extrude dough through high-pressure bronze or teflon dies, cutting to desired length.",
                    },
                    {
                        "key": "bake",
                        "name": "Air-Dry / Cook",
                        "duration_sec": cut_min * 60,
                        "desc": "Let the extruded shapes air dry slightly on a mesh rack, or cook immediately in boiling salted water.",
                        "is_bake": True,
                    },
                ]
            )
            return steps

        steps.append(
            {
                "key": "roll_pass",
                "name": "Mechanical Roller Passes",
                "duration_sec": roll_min * 60,
                "desc": "Divide dough into portions. Run through roller Setting 0, fold, and repeat. Set thickness down incrementally one setting at a time until reaching Setting 6 or 7 (~1.2mm).",
            }
        )

        if "stuffed" in preset_slug.lower() or "ravioli" in preset_slug.lower() or "tortellini" in preset_slug.lower():
            steps.append(
                {
                    "key": "bake",
                    "name": "Fill, Seal & Cut",
                    "duration_sec": cut_min * 60,
                    "desc": "Pipe filling in mounds along sheet, lay second sheet on top (or fold over), press out air to seal edges tightly, and cut into pockets.",
                    "is_bake": True,
                }
            )
        else:
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
