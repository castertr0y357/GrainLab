from grainlab.engines.base_engine import BaseEngine

class ChouxEngine(BaseEngine):
    name = "Choux Paste Engine"
    slug = "choux"
    default_binder_pct = 1.60
    default_salt_pct = 0.01
    target_protein_min = 12.0
    target_protein_max = 13.5
    gluten_behavior = "High Starch Gelatinization & High Elasticity. Matrix must actively bind massive egg moisture volumes, expanding violently into a hollow, self-supporting structural shell via steam inflation."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Requires a neutral background to allow rich egg-custard components to dominate."
    tannin_sensitive = True
    production_profile = {
        "thermodynamic_focus": "hydration_binding_shock",
        "mechanical_energy_threshold": "moderate_shearing",
        "permissible_action_types": ["knead", "cream"],
        "environmental_rest_strategy": "gluten_relaxation",
    }
    secondary_ingredients = {
        "lipids": {
            "default": "unsalted_butter",
            "options": ["unsalted_butter", "salted_butter", "coconut_oil", "avocado_oil"],
            "math_modifiers": {
                "salted_butter": { "target_target": "salt", "subtract_percentage": 0.015 }
            }
        },
        "liquids": {
            "default": "pure_water",
            "options": ["pure_water", "whole_milk", "heavy_cream", "buttermilk"],
            "math_modifiers": {
                "buttermilk": { "trigger_chemical_leavening_acid_flag": True }
            }
        },
        "binders": {
            "default": "whole_eggs",
            "options": ["none", "whole_eggs", "egg_whites", "aquafaba_vegan"]
        }
    }

    permissible_form_factors = {
        "extrusion-piping-sheet": {
            "name": "Extrusion Piping Sheet / Silpat",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 45.0,
            "base_count": 12,
            "step_increment": 12,
            "unit_label": "portion",
            "unit_label_plural": "portions",
            "bake_temp_f": 425,
            "bake_time_min": 20,
            "steam_required": True,
            "is_enriched_profile": True,
        }
    }

    presets = [
        "Chocolate Éclairs", "Cream Puffs (Profiteroles)", "Savory Cheese Gougères",
        "French Crullers", "Traditional Churros", "Paris-Brest Pastries"
    ]

    archetypes = {
        "piped_shell": {
            "label": "Piped Shell",
            "icon": "🍫",
            "description": "Linear or round hollow vectors like Éclairs and Profiteroles.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "9.5% - 11.5%"
            },
            "culinary_nuance_directive": (
                "Focus on pre-gelatinized starch panade formation and moderate gluten extensibility. The flour must bind "
                "massive egg moisture volumes during the secondary paste integration, providing a flexible protein web "
                "that stretches cleanly under explosive internal steam expansion without rupturing the shell walls."
            )
        },
        "extrusion_fried": {
            "label": "Extrusion Fried Paste",
            "icon": "🌀",
            "description": "Star-die extrusion profiles built for rapid oil expansion like Churros.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "9.0% - 11.0%"
            },
            "culinary_nuance_directive": (
                "Focus on structural moisture containment and rapid surface setting under direct hot fat conduction. The paste "
                "network must minimize horizontal flow while maintaining deep star-die definition, allowing water-vapor to flash "
                "immediately into a light interior puff while sealing out oil absorption."
            )
        },
        "savory_emulsion": {
            "label": "Savory Emulsion",
            "icon": "🧀",
            "description": "High-lipid, cheese-bound panade drops like Gougères.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "9.5% - 11.5%"
            },
            "culinary_nuance_directive": (
                "Focus on high lipid encapsulation alongside moderate protein elasticity. The matrix must support heavy grated "
                "cheese weights and fat loads, maintaining stable structural drops that puff cleanly in the oven without "
                "collapsing into oily pools."
            )
        },
    }


    def get_diagnostic_insight(self, item_id: str) -> dict:
        from .insights_fallbacks import SWEET_FALLBACKS
        insight = SWEET_FALLBACKS.get(item_id)
        if not insight and item_id.startswith('grain_'):
            for k, val in SWEET_FALLBACKS.items():
                if k.startswith('grain_') and (k in item_id or item_id in k):
                    insight = val
                    break
        return insight or {
            'labor_roi': 'Low Priority / Minor Textural Return',
            'last_10_percent_analysis': 'An objective workspace configuration parameter. No significant performance anomalies or hidden labor opportunities detected.'
        }

    def get_flavor_bases(self, creativity_level: int) -> list:
        if creativity_level <= 3:
            return ['Vanilla Bean & Brown Butter', 'Double Chocolate', 'Lemon Zest & Buttermilk']
        else:
            return ['Matcha & White Chocolate', 'Earl Grey & Lavender', 'Miso Caramel & Pecan']

    def get_ai_flavor_directive(self) -> str:
        return "Do not call them 'Spelt Cookie' or 'Rye Cake'. Use creative but clear culinary names."

    def get_ai_structural_directive(self) -> str:
        return "For example, tender confections generally do not need a 'proofing_environment' or 'shaping_surface'."

    def get_sensory_benchmark(self, grain_type: str, flour_maturity: str, effective_hydration: float, category_slug: str = None, preset_slug: str = None) -> str:
        grain_name = grain_type.replace('_', ' ').title()
        desc = f'For fresh-milled {grain_name} confections: '
        if category_slug == 'cookies-shortbread':
            desc += 'Expect a thick, soft paste or firm chilled dough. The fat should be fully creamed with flour particles evenly coated to control spread. '
        elif category_slug == 'cakes-batters':
            desc += 'Expect a highly aerated, smooth fluid batter. It should hold micro-air bubbles from egg/fat whipping with zero large pockets. '
        else:
            desc += 'The batter/dough should be delicate and soft. Mixing should be kept to an absolute minimum to ensure a tender crumb. '
            
        if flour_maturity == 'just_milled':
            desc += 'As this flour was milled today, its enzymes will promote fast browning. Keep mixing short to avoid any accidental gluten development.'
        elif flour_maturity == 'dead_zone':
            desc += 'Caution: Flour is in the 1-2 week dead zone. The structural proteins are slightly unstable. Bake promptly after mixing to ensure the rise sets correctly.'
        else:
            desc += 'Flour is fully matured. It will provide a highly stable, predictable structure and excellent tender mouthfeel.'
        return desc

    def apply_sub_class_constraints(self, hydration: float, fat: float, sugar: float, leaven: float, salt: float, leaven_type: str = 'yeast') -> tuple[float, float, float, float, float]:
        hyd = max(0.0, min(1.50, hydration))
        f = max(0.0, min(1.00, fat))
        s = max(0.0, min(0.30, sugar))
        if leaven_type == 'sourdough':
            leaven = max(0.0, min(0.60, leaven))
        elif leaven_type == 'chemical':
            leaven = max(0.0, min(0.10, leaven))
        else:
            leaven = max(0.0, min(0.015, leaven))
        salt = max(0.0, min(0.10, salt))
        return hyd, f, s, leaven, salt

    def get_ai_culinary_directive(self) -> str:
        return "Choux paste relies heavily on a high ratio of eggs for leavening puff. Ensure you include a substantial amount of whole eggs, and zero yeast. This is choux pastry. NEVER include leaveners (it relies on steam). Requires high hydration, high lipids (butter), and high binders (eggs)."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives (like cheese), use true baker's percentages (flour = 100%). For choux doughs, these typically range from 10.0 to 25.0. CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile."

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        boil_min = 3
        cook_min = 4
        cool_min = 5
        egg_min = 8
        
        # Split bake time into high expansion puffing and drying phases
        puff_min = 15
        dry_min = max(10, bake_time_min - puff_min)

        return [
            {
                "key": "boil",
                "name": "Boil Liquid & Fat",
                "duration_sec": boil_min * 60,
                "desc": "Heat water, milk, butter, and salt in a saucepan until boiling and fat is fully melted."
            },
            {
                "key": "cook",
                "name": "Pan Gelatinization Cook",
                "duration_sec": cook_min * 60,
                "desc": "Add all flour at once. Cook over medium-high heat, stirring vigorously, until the mixture pulls away from the pan sides and forms a film on the bottom (pre-gelatinizes starch).",
                "is_mix": True
            },
            {
                "key": "cool",
                "name": "Cooling Rest",
                "duration_sec": cool_min * 60,
                "desc": "Transfer dough ball to a mixing bowl. Let rest to cool below 140°F so eggs do not scramble when added."
            },
            {
                "key": "eggs",
                "name": "Egg Integration & V-Stage",
                "duration_sec": egg_min * 60,
                "desc": "Add eggs incrementally, mixing thoroughly after each. Evaluate the paste structure: stop adding eggs when it achieves a glossy, smooth 'V-stage' ribbon droop from the spatula.",
                "is_knead": True
            },
            {
                "key": "puff_bake",
                "name": "Oven Expansion Bake",
                "duration_sec": puff_min * 60,
                "desc": "Bake at high heat (425°F). Moisture steam-flashes inside the paste, expanding shells to triple their volume. Do NOT open the oven door during this phase!",
                "is_bake": True
            },
            {
                "key": "dry_bake",
                "name": "Dry Setting Bake",
                "duration_sec": dry_min * 60,
                "desc": "Reduce heat to 375°F. Pierce shell walls to vent trapped steam and dry until golden, crisp, and hollow.",
                "is_bake": True
            },
            {
                "key": "cool",
                "name": "Wire Rack Cooling",
                "duration_sec": 30 * 60,
                "desc": "Transfer to a wire rack to cool completely before filling. Filling warm shells will melt pastry cream and make them soggy."
            }
        ]
