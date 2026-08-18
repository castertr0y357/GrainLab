from grainlab.engines.base_engine import BaseEngine

class BatterEngine(BaseEngine):
    name = "Cakes & Batters Engine"
    slug = "batter"
    default_binder_pct = 0.45
    default_leaven_pct = 0.03
    target_protein_min = 7.5
    target_protein_max = 9.5
    gluten_behavior = "Complete Absence of Gluten. High-ratio sugar and liquid dispersion requires structure built purely on starch gelatinization and egg protein coagulation."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Demands a completely neutral grain baseline to host delicate vanilla, citrus, or fruit fats."
    tannin_sensitive = True
    supported_tweaks = ["enrichment"]
    tweak_labels = {
        "enrichment": ["Dense / Fudgy", "Light / Spongy"]
    }
    production_profile = {
        "thermodynamic_focus": "lipid_emulsification",
        "mechanical_energy_threshold": "low_emulsifying",
        "permissible_action_types": ["cream", "fold"],
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
            "default": "none",
            "options": ["none", "whole_eggs", "egg_whites", "aquafaba_vegan"]
        }
    }

    permissible_form_factors = {
        "straight-sided-round-tin": {
            "name": "Straight-Sided Round Tin",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 500.0,
            "base_count": 2,
            "step_increment": 2,
            "unit_label": "layer",
            "unit_label_plural": "layers",
            "bake_temp_f": 350,
            "bake_time_min": 30,
            "steam_required": False,
            "is_enriched_profile": True,
        },
        "high-border-sheet-pan": {
            "name": "High-Border Sheet Cake Pan",
            "tier": "recommended",
            "is_portioned": False,
            "unit_weight": 1000.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "pan",
            "unit_label_plural": "pans",
            "bake_temp_f": 350,
            "bake_time_min": 25,
            "steam_required": False,
            "is_enriched_profile": True,
        },
        "cupcake-liner-matrix": {
            "name": "Cupcake Liner Matrix",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 41.67,
            "base_count": 24,
            "step_increment": 24,
            "unit_label": "cupcake",
            "unit_label_plural": "cupcakes",
            "bake_temp_f": 350,
            "bake_time_min": 20,
            "steam_required": False,
            "is_enriched_profile": True,
        }
    }

    presets = [
        "Yellow Layer Cake", "Fudgy Chocolate Cake", "Victoria Sponge",
        "Chiffon Cake", "Angel Food Cake", "Traditional Pound Cake",
        "Madeleines", "Vanilla Cupcakes", "Buttermilk Pancakes",
        "Belgian Waffles"
    ]

    archetypes = {
        "sponge_cake": {
            "label": "Foam / Sponge Cake",
            "icon": "🍰",
            "description": "Fat-free or low-fat aeration systems like Genoise or Chiffon.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "8.0% - 9.5%"
            },
            "culinary_nuance_directive": (
                "Focus entirely on egg-protein foam stabilization and complete gluten suppression. Grains must have minimal "
                "protein content to prevent structural toughness, allowing delicate egg-cell walls to expand unhindered "
                "while relying purely on gentle liquid starch gelatinization to set a feather-light, aerated crumb."
            )
        },
        "creamed_cake": {
            "label": "Creamed Layer Cake",
            "icon": "🎂",
            "description": "Emulsified lipid-sugar crystal structures for standard layers.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "8.0% - 10.0%"
            },
            "culinary_nuance_directive": (
                "Focus on lipid-sugar crystal aeration and uniform emulsion stability. Low-protein grains are mandatory to "
                "prevent unwanted gluten strands during liquid integration. Flour starches must absorb moisture smoothly "
                "to encapsulate fat phases uniformly, preventing batter separation and ensuring a velvety, tender layered structure."
            )
        },
        "pound_cake": {
            "label": "High-Ratio Pound Cake",
            "icon": "🍫",
            "description": "Dense, uniform crumb carrying massive sugar and fat weights.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.5%"
            },
            "culinary_nuance_directive": (
                "Focus on managing high-ratio sugar and lipid loads within a dense, uniform crumb matrix. Grains must maximize "
                "tender starch swelling without developing elastic protein networks, allowing the batter to hold massive "
                "butter and sugar weights without collapsing or leaving greasy pockets."
            )
        },
        "griddle_batter": {
            "label": "Fluid Griddle Batter",
            "icon": "🥞",
            "description": "High-moisture pourable structures like Pancakes, Waffles, and Crepes.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "high_spread",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "8.5% - 10.5%"
            },
            "culinary_nuance_directive": (
                "Focus on pourable hydration mechanics and rapid surface heat transfer. Grains must allow instant liquid "
                "dispersion and minimal viscosity development. Texture relies on swift starch gelatinization upon hot "
                "iron contact, forming crisp outer grids while keeping the interior soft and aerated."
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

    def apply_sub_class_constraints(self, hydration: float, fat: float, sugar: float, texture_score: int, crumb_score: int) -> tuple[float, float, float]:
        hyd = max(0.0, min(1.50, hydration))
        f = max(0.0, min(1.20, fat))
        s = max(0.0, min(2.00, sugar))
        return hyd, f, s

    def get_ai_culinary_directive(self) -> str:
        return "This is a batter. Recommend a specific emulsification style (e.g. whipped egg foam, creamed butter) to aerate the dough, and ensure zero yeast is used. This is a liquid batter (pancakes, waffles, cakes). Requires chemical leaveners, high hydration (milk/buttermilk), and binders (eggs)."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives (like berries or chips), use true baker's percentages (flour = 100%). For liquid batters, these typically range from 20.0 to 80.0."

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        preset_slug = kwargs.get("preset_slug") or ""
        
        # Branch for griddle batters (Pancakes, Waffles, Crepes)
        if "griddle" in preset_slug.lower() or "pancake" in preset_slug.lower() or "waffle" in preset_slug.lower() or "crepe" in preset_slug.lower():
            return [
                {
                    "key": "dry_whisk",
                    "name": "Dry Sift & Whisk",
                    "duration_sec": 3 * 60,
                    "desc": "Whisk together the flour, sugar, leavening agents, and salt in a large bowl. Creating a uniform dry mix prevents clumps later."
                },
                {
                    "key": "wet_mix",
                    "name": "Wet Ingredient Emulsification",
                    "duration_sec": 4 * 60,
                    "desc": "In a separate bowl, whisk together the eggs, milk/buttermilk, and melted fat (butter or oil) until smooth."
                },
                {
                    "key": "fold",
                    "name": "Wet-into-Dry Fold",
                    "duration_sec": 3 * 60,
                    "desc": "Pour the wet ingredients into the dry ingredients. Gently fold with a spatula just until combined. Lumps are acceptable and desired; over-mixing develops gluten and makes the batter tough.",
                    "is_mix": True
                },
                {
                    "key": "bake",
                    "name": "Griddle / Iron Cooking",
                    "duration_sec": bake_time_min * 60,
                    "desc": "Cook portions of the batter on a preheated, greased griddle or waffle iron until golden brown and cooked through. For pancakes, flip when bubbles form and pop on the surface.",
                    "is_bake": True
                }
            ]

        # Standard Cake/Batter Branch
        if "chiffon" in preset_slug.lower() or "angel" in preset_slug.lower():
            steps = [
                {
                    "key": "mix",
                    "name": "Egg Foam Emulsification",
                    "duration_sec": 6 * 60,
                    "desc": "Whip egg whites/yolks with sugar to soft peaks. Creates the micro-bubbles needed for rise without chemical leavening.",
                    "is_mix": True
                },
                {
                    "key": "fold",
                    "name": "Dry Sift & Fold",
                    "duration_sec": 4 * 60,
                    "desc": "Gently fold in sifted flour and dry ingredients to avoid deflating the egg foam."
                },
                {
                    "key": "bake",
                    "name": "Cake Stencil Bake",
                    "duration_sec": bake_time_min * 60,
                    "desc": "Bake in prepared pans. Air bubbles expand and starches gelatinize to form a tender crumb structure.",
                    "is_bake": True
                }
            ]
        elif "cupcake" in preset_slug.lower() or "paste" in preset_slug.lower():
            steps = [
                {
                    "key": "mix",
                    "name": "Dry & Fat Mix (Reverse Creaming)",
                    "duration_sec": 6 * 60,
                    "desc": "Mix flour, sugar, leavening, and softened butter together until it resembles wet sand. Prevents excess gluten structure.",
                    "is_mix": True
                },
                {
                    "key": "liquid_stream",
                    "name": "Liquid Addition",
                    "duration_sec": 3 * 60,
                    "desc": "Stream in eggs and liquids in two batches, mixing well after each to build structure and aerate."
                },
                {
                    "key": "bake",
                    "name": "Cake Stencil Bake",
                    "duration_sec": bake_time_min * 60,
                    "desc": "Bake in prepared pans. Starches gelatinize to form a tender crumb structure.",
                    "is_bake": True
                }
            ]
        else:
            steps = [
                {
                    "key": "mix",
                    "name": "Fat Emulsification Phase",
                    "duration_sec": 6 * 60,
                    "desc": "Cream softened butter and sugar at medium-high speed for 5-6 minutes until pale and fluffy. Traps air bubbles inside the fat crystals.",
                    "is_mix": True
                },
                {
                    "key": "egg_stream",
                    "name": "Egg Emulsion",
                    "duration_sec": 3 * 60,
                    "desc": "Add eggs one at a time, mixing well after each addition to maintain a stable emulsion."
                },
                {
                    "key": "fold",
                    "name": "Alternate Dry & Wet Fold",
                    "duration_sec": 4 * 60,
                    "desc": "Fold in sifted flour and remaining wet ingredients (like milk) alternately in batches, beginning and ending with dry. Avoid over-mixing.",
                    "is_mix": True
                },
                {
                    "key": "bake",
                    "name": "Cake Stencil Bake",
                    "duration_sec": bake_time_min * 60,
                    "desc": "Bake in prepared pans. Air bubbles expand and starches gelatinize to form a tender crumb structure.",
                    "is_bake": True
                }
            ]
        
        steps.append({
            "key": "cool",
            "name": "Pan & Wire Rack Cooling",
            "duration_sec": 30 * 60,
            "desc": "Allow the cake to cool in its pan for 10-15 minutes before carefully inverting onto a wire rack to cool completely. Frosting a warm cake will cause it to melt."
        })
        
        return steps
