from apps.core.engines.base_engine import BaseEngine

class BathEngine(BaseEngine):
    name = "Alkaline Bath Engine"
    slug = "bath"
    target_protein_min = 12.0
    target_protein_max = 14.0
    gluten_behavior = "Tight interior structure. Matrix must withstand a pre-bake boiling step without dissolving or losing shape."
    flavor_affinity = "Tannin Tolerant (Rustic/Savory). Designed to complement high Maillard browning, maltiness, and alkaline surface chemistry."
    tannin_sensitive = False
    production_profile = {
        "thermodynamic_focus": "biological_yeast_activity",
        "mechanical_energy_threshold": "high_kneading",
        "permissible_action_types": ["knead"],
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
        }
    }

    presets = [
        "Soft Bavarian Pretzels", "Traditional Boiled New York Bagels", "Pretzel Buns",
        "Sesame Simit", "Chewy Montreal Bagels", "Bavarian Pretzel Bites"
    ]

    archetypes = {
        "twisted_pretzel": {
            "default_form_factor": "perforated-baking-sheet",
            "label": "Twisted Pretzel",
            "icon": "🥨",
            "description": "Traditional knot shapes, maximize surface area for Maillard browning.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
            "default_form_factor": "perforated-baking-sheet",
            "default_form_factor": "perforated-baking-sheet",
            "default_form_factor": "perforated-baking-sheet",
            "default_form_factor": "perforated-baking-sheet",
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "12.0% - 14.5%"
            },
            "culinary_nuance_directive": (
                "Focus on extreme tensile alignment paired with zero horizontal flow. Grains must survive high mechanical "
                "pulling into micro-thin strands that maintain distinct structural knot vectors under intense heat. "
                "Maximize surface area structural stability to host the hot alkaline-dipped Maillard browning "
                "without core collapsing."
            )
        },
        "boiled_bagel": {
            "default_form_factor": "perforated-baking-sheet",
            "label": "Boiled Bagel",
            "icon": "🥯",
            "description": "Ring geometry, dense core structure, high tensile strength.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "extreme_tensile",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "high_hydration_lean",
                "optimal_protein_window": "13.0% - 15.0%"
            },
            "culinary_nuance_directive": (
                "Focus on extreme long-chain protein cross-linking and a highly compact core network. Grains must yield "
                "maximum elasticity to withstand extended fermentation arcs followed by a rolling water boil. "
                "The brief surface starch gelatinization must establish a thick, chew-resistant skin barrier that "
                "locks in internal moisture."
            )
        },
        "laugen_bun": {
            "default_form_factor": "perforated-baking-sheet",
            "label": "Laugen Bun / Roll",
            "icon": "🫓",
            "description": "Spherical soft-crumb interior protected by a thick glossy skin.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "11.5% - 13.5%"
            },
            "culinary_nuance_directive": (
                "Focus on high structural retention and controlled gas expansion. Grains must provide enough tensile strength "
                "to encapsulate standard yeast activity while supporting moderate lipid enrichment, ensuring a uniform, "
                "soft interior crumb wrapped securely in a thick, glossy, alkaline-blistered skin."
            )
        },
        "pretzel_stick": {
            "default_form_factor": "perforated-baking-sheet",
            "label": "Pretzel Stick / Cracker",
            "icon": "🥖",
            "description": "Ultra-low hydration, brittle, snapping structure.",
            "grain_affinity": "high_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "11.0% - 13.0%"
            },
            "culinary_nuance_directive": (
                "Focus on ultra-low hydration mechanics and maximum crisp brittleness. Minimize protein stretch; look for "
                "high-hardness grains that pack tightly during compaction rolling, allowing rapid surface moisture loss to "
                "achieve a clean, snapping structural break post-bake."
            )
        },
    }

    def apply_sub_class_constraints(self, hydration: float, fat: float, sugar: float, leaven: float, salt: float, leaven_type: str = 'yeast') -> tuple[float, float, float, float, float]:
        hyd = max(0.0, min(0.65, hydration))
        f = max(0.0, min(0.20, fat))
        s = max(0.0, min(0.20, sugar))
        if leaven_type == 'sourdough':
            leaven = max(0.0, min(0.60, leaven))
        elif leaven_type == 'chemical':
            leaven = max(0.0, min(0.10, leaven))
        else:
            leaven = max(0.0, min(0.015, leaven))
        salt = max(0.0, min(0.10, salt))
        return hyd, f, s, leaven, salt

    def get_contextual_pitfalls(self, effective_hydration: float, grain_type: str, preset_slug: str = None) -> list:
        pitfalls = super().get_contextual_pitfalls(effective_hydration, grain_type, preset_slug)
        pitfalls.insert(0, {
            "title": "Mandatory Alkaline Bath",
            "message": "To achieve the signature deep mahogany color and unique flavor, you must boil the shaped dough in a 3% baking soda bath (or carefully dip in a 3% lye solution) for 30 seconds before baking."
        })
        return pitfalls

    def get_ai_culinary_directive(self) -> str:
        return "Instruct the user to prepare an alkaline bath (lye or malted water) to gelatinize starches prior to baking. This is a boiled-bath bread (bagels, pretzels). Yeast-leavened with a dense structure. Requires a liquid medium. Modest or no lipids. Use sweet additions (cinnamon/sugar) for sweet variants, and savory additions/toppings (garlic, salt, cheese) for savory variants."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives (like cinnamon raisins or pretzel toppings), use true baker's percentages (flour = 100%). For boiled-bath doughs, these typically range from 5.0 to 20.0. CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile. CRITICAL: For commercial yeast (active/instant), strictly limit to 0.5 to 1.5. For sourdough starter, strictly limit to 10.0 to 25.0."

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        mix_min = 6
        knead_min = 10 if mixing_method == "stand_mixer" else 15
        
        # Alkaline bath doughs need skin drying to hold shape
        dry_min = 20
        # Boiling/dipping starch pre-gelatinization countdown (60 seconds)
        boil_sec = 60
        
        # Baking
        bake_min = bake_time_min
        
        preset_slug = kwargs.get("preset_slug") or ""
        
        steps = [
            {
                "key": "mix",
                "name": "Stiff Dough Mix",
                "duration_sec": mix_min * 60,
                "desc": "Combine ingredients. Hydration is capped at 50% to 55% for stiffness. Mix until no dry pockets remain.",
                "is_mix": True
            },
            {
                "key": "knead",
                "name": "Compaction Knead",
                "duration_sec": knead_min * 60,
                "desc": f"Intensely knead the stiff dough using '{mixing_method.replace('_', ' ').title()}' to force starch cell hydration.",
                "is_knead": True
            }
        ]

        # Crackers / Pretzel Sticks don't need a bulk ferment or a boiling bath.
        if "stick" in preset_slug.lower() or "cracker" in preset_slug.lower():
            steps.extend([
                {
                    "key": "shape",
                    "name": "Roll & Cut",
                    "duration_sec": 15 * 60,
                    "desc": "Roll dough out thinly and cut into sticks or cracker tiles.",
                    "is_proof": True
                },
                {
                    "key": "boil",
                    "name": "Alkaline Spray / Dip",
                    "duration_sec": boil_sec,
                    "desc": "Quickly dip the cut pieces in a warm 3% lye or malt solution, or spray heavily. No boiling required for brittle crackers."
                },
                {
                    "key": "bake",
                    "name": "Dehydrating Convection Bake",
                    "duration_sec": bake_min * 60,
                    "desc": "Bake on parchment until deeply browned and completely dried out for maximum snap.",
                    "is_bake": True
                },
                {
                    "key": "cool",
                    "name": "Wire Rack Cooling",
                    "duration_sec": 30 * 60,
                    "desc": "Transfer to a wire rack. Allow to cool completely to ensure maximum crunch."
                }
            ])
            return steps

        # Standard Bagel / Soft Pretzel / Bun flow
        steps.append({
            "key": "bulk",
            "name": "Rest & Relax",
            "duration_sec": max(15, estimated_bulk_minutes - 45) * 60,
            "desc": "Short bulk proof to relax the dense gluten mesh before shaping."
        })

        if "bun" in preset_slug.lower() or "roll" in preset_slug.lower():
            shape_desc = "Divide dough into equal portions and roll into tight spheres. Rest uncovered on greaseproof paper to form a dry outer skin; this prevents water-logging."
        else:
            shape_desc = "Shape dough into pretzels or bagels. Rest uncovered on greaseproof paper to form a dry outer skin; this prevents water-logging."

        steps.extend([
            {
                "key": "shape",
                "name": "Shape & Skin Dry",
                "duration_sec": dry_min * 60,
                "desc": shape_desc,
                "is_proof": True
            },
            {
                "key": "boil",
                "name": "Alkaline Bath Soak",
                "duration_sec": boil_sec,
                "desc": "Dip shaped dough into the warm 3% lye bath or boiling malt/soda bath for 30s per side. Starch pre-gelatinization locks shape and creates the classic chewy skin."
            },
            {
                "key": "bake",
                "name": "High Convection Bake",
                "duration_sec": bake_min * 60,
                "desc": "Bake immediately on parchment. The alkaline surface reacts with oven heat to produce a beautiful, glossy mahogany color.",
                "is_bake": True
            },
            {
                "key": "cool",
                "name": "Wire Rack Cooling",
                "duration_sec": 30 * 60,
                "desc": "Transfer immediately to a wire rack to cool. Allow to cool at least 30 minutes before serving."
            }
        ])

        return steps
