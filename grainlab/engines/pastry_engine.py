from grainlab.engines.base_engine import BaseEngine

class PastryEngine(BaseEngine):
    name = "Pastry & Lamination Engine"
    slug = "pastry"
    default_binder_pct = 0.10
    default_leaven_pct = 0.0
    target_protein_min = 11.0
    target_protein_max = 12.5
    gluten_behavior = "Exceptional Extensibility. Dough sheets must roll out into paper-thin layers wrapping alternating cold solid butter blocks without tearing or puncturing."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Requires an ultra-clean, sweet backdrop to highlight intense layered butter fat distribution."
    tannin_sensitive = True
    supported_tweaks = ["hydration", "leavening", "enrichment"]
    production_profile = {
        "thermodynamic_focus": "crystalline_fat_preservation",
        "mechanical_energy_threshold": "minimal_folding",
        "permissible_action_types": ["cut_in", "sheet"],
        "environmental_rest_strategy": "fat_solidification",
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
            "default": "none",
            "options": ["none", "whole_eggs", "egg_whites", "aquafaba_vegan"]
        }
    }

    permissible_form_factors = {
        "perforated-sheet-air-mat": {
            "name": "Perforated Sheet + Air Mat",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 90.0,
            "base_count": 6,
            "step_increment": 6,
            "unit_label": "pastry",
            "unit_label_plural": "pastries",
            "bake_temp_f": 400,
            "bake_time_min": 20,
            "steam_required": False,
            "is_enriched_profile": True,
        },
        "fluted-ring-tart-pan": {
            "name": "Fluted Ring Tart Pan",
            "tier": "recommended",
            "is_portioned": False,
            "unit_weight": 400.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "tart",
            "unit_label_plural": "tarts",
            "bake_temp_f": 375,
            "bake_time_min": 25,
            "steam_required": False,
            "is_enriched_profile": True,
        }
    }

    presets = [
        "Classic Croissants", "Pain au Chocolat", "All-Butter Puff Pastry",
        "Danish Pastry Dough", "Flaky Pie Crust (Pâte Brisée)",
        "Sweet Tart Dough (Pâte Sucrée)", "Palmiers", "Vol-au-vents"
    ]

    archetypes = {
        "layered_viennoiserie": {
            "label": "Layered Viennoiserie",
            "icon": "🥐",
            "description": "Yeast-leavened laminated structures like Croissants and Danishes.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "11.0% - 13.0%"
            }
        },
        "inverted_puff": {
            "label": "Inverted Puff Pastry",
            "icon": "🍥",
            "description": "Unleavened laminated doughs driven entirely by water-vapor lift.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "11.0% - 13.0%"
            }
        },
        "shortcrust_tart": {
            "label": "Shortcrust Tart Casing",
            "icon": "🥧",
            "description": "High-fat friable crumb shells designed to remain completely impermeable to wet fillings.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.5%"
            }
        },
        "paper_thin_phyllo": {
            "label": "Paper-Thin Phyllo / Strudel",
            "icon": "🫓",
            "description": "Stretched, transparent gluten films stacked with liquid fat layers.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "11.5% - 13.5%"
            }
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
        hyd = max(0.0, min(0.60, hydration))
        f = max(0.0, min(1.20, fat))
        s = max(0.0, min(0.50, sugar))
        if leaven_type == 'sourdough':
            leaven = max(0.0, min(0.60, leaven))
        elif leaven_type == 'chemical':
            leaven = max(0.0, min(0.10, leaven))
        else:
            leaven = max(0.0, min(0.015, leaven))
        salt = max(0.0, min(0.10, salt))
        return hyd, f, s, leaven, salt

    def get_ai_culinary_directive(self) -> str:
        return "Specify the exact butter block weight required for lamination (around 28% of total dough mass), and detail the lamination fold style (e.g., book folds vs letter folds) and zero yeast if it is a shortcrust pastry. This is laminated or pie pastry (croissants, puff, pie crust). Requires extreme lipids (butter blocks). NEVER include chemical leaveners for puff/pie crust (croissants may use yeast). Cold temperatures are strictly required."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives (like fruit fillings or almond paste), use true baker's percentages (flour = 100%). For pastries, these typically range from 10.0 to 50.0. CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile."

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        preset_slug = kwargs.get("preset_slug") or ""
        
        if "puff" in preset_slug.lower() or "danish" in preset_slug.lower():
            fold_desc = "Roll dough to a rectangle. Fold both outer edges to meet in the middle, then fold in half like a book (4 layers generated)."
        elif "croissant" in preset_slug.lower() or "chocolat" in preset_slug.lower():
            fold_desc = "Roll dough to a rectangle. Fold one-third over the center, then the opposite third over that like a letter (3 layers generated)."
        else:
            fold_desc = "Rub cold butter chunks into flour until pea-sized. Keep cool; do not laminate."

        if "tart" in preset_slug.lower() or "pie" in preset_slug.lower() or "shortcrust" in preset_slug.lower():
            steps = [
                {
                    "key": "mix",
                    "name": "Shortcrust Base Mix",
                    "duration_sec": 10 * 60,
                    "desc": "Cut cold butter into flour until pea-sized, add cold liquid until it just holds together. Do not overwork.",
                    "is_mix": True
                },
                {
                    "key": "chill_lock_one",
                    "name": "Chill Lock",
                    "duration_sec": 30 * 60,
                    "desc": "Mandatory chill step in fridge to solidify butter before rolling out."
                },
                {
                    "key": "bake",
                    "name": "Crust Bake",
                    "duration_sec": bake_time_min * 60,
                    "desc": "Blind bake or bake with filling until crust is deeply golden.",
                    "is_bake": True
                }
            ]
        elif "phyllo" in preset_slug.lower() or "strudel" in preset_slug.lower():
            steps = [
                {
                    "key": "mix",
                    "name": "Phyllo Base Mix",
                    "duration_sec": 10 * 60,
                    "desc": "Mix flour, water, and a touch of oil/vinegar into a smooth, highly extensible dough.",
                    "is_mix": True
                },
                {
                    "key": "chill_lock_one",
                    "name": "Relaxation Rest",
                    "duration_sec": 60 * 60,
                    "desc": "Rest dough at room temperature for at least 1 hour to fully relax gluten for extreme stretching."
                },
                {
                    "key": "stretch",
                    "name": "Paper-Thin Stretch & Stack",
                    "duration_sec": 30 * 60,
                    "desc": "Stretch dough paper-thin until translucent, stack layers while brushing generously with melted fat/oil."
                },
                {
                    "key": "bake",
                    "name": "Crisp Laminate Bake",
                    "duration_sec": bake_time_min * 60,
                    "desc": "Bake until golden and shatteringly crisp.",
                    "is_bake": True
                }
            ]
        else:
            steps = [
                {
                    "key": "mix",
                    "name": "Détrempe Base Mix",
                    "duration_sec": 6 * 60,
                    "desc": "Mix base dough (détrempe) until combined. Do not over-knead to prevent excess gluten toughness.",
                    "is_mix": True
                },
                {
                    "key": "butter_encase",
                    "name": "Butter Block Encasement",
                    "duration_sec": 10 * 60,
                    "desc": f"Roll the détrempe out. Place the cold butter block ({recipe_data.get('butter_block_weight', 0.0)}g) in the center. Fold the corners of the dough over to fully seal the butter block."
                },
                {
                    "key": "fold_one",
                    "name": "First Fold Set",
                    "duration_sec": 10 * 60,
                    "desc": f"Perform the first fold set: {fold_desc} Work quickly so butter remains cold."
                },
                {
                    "key": "chill_lock_one",
                    "name": "Low-Temp Chill Lock 1",
                    "duration_sec": 30 * 60,
                    "desc": "Mandatory low-temperature environmental chill-rest step. Chill in freezer/fridge to solidify butter and relax gluten sheets."
                },
                {
                    "key": "fold_two",
                    "name": "Second Fold Set",
                    "duration_sec": 10 * 60,
                    "desc": f"Roll dough out and perform the second fold set: {fold_desc}"
                },
                {
                    "key": "chill_lock_two",
                    "name": "Low-Temp Chill Lock 2",
                    "duration_sec": 30 * 60,
                    "desc": "Second mandatory chill lock. Keeps laminated butter solid so layers do not bleed together."
                }
            ]
            
            if "croissant" in preset_slug.lower() or "danish" in preset_slug.lower() or "chocolat" in preset_slug.lower() or "viennoiserie" in preset_slug.lower():
                steps.extend([
                    {
                        "key": "shape",
                        "name": "Final Shaping",
                        "duration_sec": 15 * 60,
                        "desc": "Roll out the chilled dough and shape into final forms."
                    },
                    {
                        "key": "proof",
                        "name": "Final Proof",
                        "duration_sec": estimated_proof_minutes * 60,
                        "desc": "Proof at a warm room temperature (around 78°F, do not exceed 80°F or butter will melt). Must double in size and jiggle when shaken.",
                        "is_proof": True
                    }
                ])
                
            steps.append({
                "key": "bake",
                "name": "Laminated Steam Rise Bake",
                "duration_sec": bake_time_min * 60,
                "desc": "Bake in hot oven. Water in butter boils instantly, creating steam which puffs the pastry layers apart while fat setting locks the crumb.",
                "is_bake": True
            })
        
        steps.append({
            "key": "cool",
            "name": "Wire Rack Cooling",
            "duration_sec": 30 * 60,
            "desc": "Transfer to a wire rack. Allow the pastries to cool completely to room temperature so the butter sets back up, restoring the crisp flaky texture."
        })
        
        return steps
