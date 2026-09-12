from apps.core.engines.base_engine import BaseEngine


class BathEngine(BaseEngine):
    name = "Alkaline Bath Engine"
    slug = "bath"
    default_yield_unit = "pieces"
    target_protein_min = 12.0
    target_protein_max = 14.0
    gluten_behavior = (
        "Tight interior structure. Matrix must withstand a pre-bake boiling step without dissolving or losing shape."
    )
    flavor_affinity = "Tannin Tolerant (Rustic/Savory). Designed to complement high Maillard browning, maltiness, and alkaline surface chemistry."
    tannin_sensitive = False
    production_profile = {
        "thermodynamic_focus": "biological_yeast_activity",
        "mechanical_energy_threshold": "high_kneading",
        "permissible_action_types": ["knead", "mix"],
        "environmental_rest_strategy": "gas_proofing",
    }
    secondary_ingredients = {}

    permissible_form_factors = {
        "perforated-baking-sheet": {
            "name": "Perforated Baking Sheet",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 110.0,
            "base_count": 8,
            "step_increment": 6,
            "unit_label": "portion",
            "unit_label_plural": "portions",
            "bake_temp_f": 425,
            "bake_time_min": 20,
            "steam_required": False,
            "is_enriched_profile": False,
        },
        "standard-silicon-mat-sheet": {
            "name": "Standard Silicon Mat Sheet",
            "tier": "sub-optimal",
            "is_portioned": True,
            "unit_weight": 110.0,
            "base_count": 8,
            "step_increment": 6,
            "unit_label": "portion",
            "unit_label_plural": "portions",
            "bake_temp_f": 425,
            "bake_time_min": 25,
            "steam_required": False,
            "is_enriched_profile": False,
        },
    }

    presets = [
        "Soft Bavarian Pretzels",
        "Traditional Boiled New York Bagels",
        "Pretzel Buns",
        "Sesame Simit",
        "Chewy Montreal Bagels",
        "Bavarian Pretzel Bites",
    ]

    _archetypes_cache = None

    @property
    def archetypes(self):
        if BathEngine._archetypes_cache is None:
            cache = {}
            for subclass in BathEngine.__subclasses__():
                cache[subclass.archetype_slug] = {
                    "default_form_factor": getattr(subclass, "default_form_factor", "perforated-baking-sheet"),
                    "label": subclass.label,
                    "yield_unit": subclass.yield_unit,
                    "icon": subclass.icon,
                    "description": subclass.description,
                    "grain_affinity": subclass.grain_affinity,
                    "target_archetype_mechanics": subclass.target_archetype_mechanics,
                    "culinary_nuance_directive": subclass.culinary_nuance_directive,
                    "preset_matchers": getattr(subclass, "preset_matchers", []),
                }
            BathEngine._archetypes_cache = cache
        return BathEngine._archetypes_cache

    def __init__(self):
        super().__init__()

    def apply_sub_class_constraints(self, hydration, fat, sugar, leaven, salt, leaven_type="yeast"):
        hyd = max(0.0, min(0.65, hydration))
        f = max(0.0, min(0.20, fat))
        s = max(0.0, min(0.20, sugar))
        if leaven_type == "sourdough":
            leaven = max(0.0, min(0.60, leaven))
        elif leaven_type == "chemical":
            leaven = max(0.0, min(0.10, leaven))
        else:
            leaven = max(0.0, min(0.015, leaven))
        salt = max(0.0, min(0.10, salt))
        return hyd, f, s, leaven, salt

    def get_contextual_pitfalls(self, effective_hydration, grain_type, preset_slug=None):
        pitfalls = super().get_contextual_pitfalls(effective_hydration, grain_type, preset_slug)
        pitfalls.insert(
            0,
            {
                "title": "Mandatory Alkaline Bath",
                "message": "To achieve the signature deep mahogany color and unique flavor, you must boil the shaped dough in a 3% baking soda bath (or carefully dip in a 3% lye solution) for 30 seconds before baking.",
            },
        )
        return pitfalls

    def get_ai_culinary_directive(self) -> str:
        return "Instruct the user to prepare an alkaline bath..."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions..."

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

        # Insert shape step before proof if it doesn't exist
        proof_idx = next((i for i, s in enumerate(steps) if s["key"] == "proof"), len(steps))
        if not any(s["key"] == "shape" for s in steps):
            steps.insert(proof_idx, {"key": "shape", "name": "Shape", "duration_sec": 15 * 60, "desc": "Shape dough."})

        # Insert bath step before bake
        bake_idx = next((i for i, s in enumerate(steps) if s["key"] == "bake"), len(steps))
        steps.insert(
            bake_idx,
            {
                "key": "boil",
                "name": "Alkaline Bath",
                "duration_sec": 5 * 60,
                "desc": "Boil in a 3% baking soda solution for 30 seconds per side.",
            },
        )
        return steps


class BoiledBagelArchetype(BathEngine):
    archetype_slug = "boiled_bagel"
    default_form_factor = "perforated-baking-sheet"
    label = "Boiled Bagel"
    yield_unit = "bagels"
    icon = "🥯"
    preset_matchers = ["bagel", "simit"]
    description = "Ring geometry, dense core structure, high tensile strength."
    grain_affinity = "high_protein"
    target_archetype_mechanics = {
        "required_gluten_elasticity": "extreme_tensile",
        "desired_horizontal_flow": "zero_spread_stable",
        "moisture_lipid_ratio": "high_hydration_lean",
        "optimal_protein_window": "13.0% - 15.0%",
    }
    culinary_nuance_directive = "Focus on extreme long-chain protein cross-linking..."

    def get_live_timeline_steps(
        self,
        recipe_data,
        estimated_bulk_minutes,
        estimated_proof_minutes,
        bake_time_min,
        mixing_method="stand_mixer",
        **kwargs,
    ):
        return super().get_live_timeline_steps(
            recipe_data, estimated_bulk_minutes, estimated_proof_minutes, bake_time_min, mixing_method, **kwargs
        )


class TwistedPretzelArchetype(BathEngine):
    archetype_slug = "twisted_pretzel"
    default_form_factor = "perforated-baking-sheet"
    label = "Twisted Pretzel"
    yield_unit = "pretzels"
    icon = "🥨"
    preset_matchers = ["pretzel", "twist"]
    description = "Classic Bavarian shape, thin crust, chewy interior."
    grain_affinity = "high_protein"
    target_archetype_mechanics = {
        "required_gluten_elasticity": "high_extensible",
        "desired_horizontal_flow": "minimal_spread",
        "moisture_lipid_ratio": "medium_hydration_lean",
        "optimal_protein_window": "12.0% - 14.0%",
    }
    culinary_nuance_directive = (
        "Focus on dough extensibility for twisting, and structural integrity for the alkaline bath."
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
        return super().get_live_timeline_steps(
            recipe_data, estimated_bulk_minutes, estimated_proof_minutes, bake_time_min, mixing_method, **kwargs
        )
