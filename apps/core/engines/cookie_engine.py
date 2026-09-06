from apps.core.engines.base_engine import BaseEngine

class CookieEngine(BaseEngine):
    name = "Cookies & Shortbread Engine"
    slug = "cookie"
    default_binder_pct = 0.35
    default_salt_pct = 0.008
    target_protein_min = 8.5
    target_protein_max = 10.5
    gluten_behavior = "Minimal Gluten Interaction. Flour must allow melting fats and sugars to spread horizontally before the crumb structure sets in the oven."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Designed for toasted brown sugars and confections; whole-grain bitterness clashes aggressively."
    tannin_sensitive = True
    supported_tweaks = ["enrichment"]
    tweak_labels = {
        "enrichment": ["Crispy / Chewy", "Soft / Cakey"]
    }
    variations = {
        "thin_crispy": {
            "label": "Thin & Crispy",
            "mechanics_overrides": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "high_spread",
                "optimal_protein_window": "8.0% - 9.5%"
            },
            "culinary_nuance_directive_append": (
                "CRITICAL: The user selected THIN & CRISPY. Maximize spread by using high proportions of white sugar "
                "and melted or liquid fats. Favor low-protein soft wheats (e.g., Pastry Flour, Soft White Wheat) "
                "to completely inhibit gluten formation and ensure a delicate, brittle snap. Increase bake time slightly."
            )
        },
        "soft_chewy": {
            "label": "Soft & Chewy",
            "mechanics_overrides": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "minimal_spread",
                "optimal_protein_window": "10.0% - 12.0%"
            },
            "culinary_nuance_directive_append": (
                "CRITICAL: The user selected SOFT & CHEWY. Prevent excessive spread by using creamed cold fats "
                "and higher proportions of brown sugar/molasses. Favor higher-protein hard wheats (e.g., Hard White Wheat, "
                "Bread Flour) to build enough gluten structure to maintain thickness and deliver a chewy bite. "
                "Reduce bake time to keep the center doughy."
            )
        }
    }
    production_profile = {
        "thermodynamic_focus": "lipid_emulsification",
        "mechanical_energy_threshold": "low_emulsifying",
        "permissible_action_types": ["cream", "fold"],
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
        "heavy-aluminum-sheet": {
            "name": "Heavy Aluminum Cookie Sheet",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 40.0,
            "base_count": 24,
            "step_increment": 12,
            "unit_label": "cookie",
            "unit_label_plural": "cookies",
            "bake_temp_f": 350,
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
            "bake_temp_f": 350,
            "bake_time_min": 25,
            "steam_required": False,
            "is_enriched_profile": True,
        }
    }

    presets = [
        "Chewy Chocolate Chip Cookies", "Oatmeal Raisin Bakes", "Buttery Shortbread Wedges",
        "Italian Almond Biscotti", "Gingerbread People", "French Almond Macarons",
        "Snickerdoodles", "Classic Sugar Cookies"
    ]

    archetypes = {
        "drop_cookie": {
            "default_form_factor": "half-sheet-pan",
            "default_salt_pct": 0.0075,
            "label": "Drop Cookie",
            "icon": "🍪",
            "description": "Irregular mounds designed to flow into tender discs.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
            "default_form_factor": "heavy-aluminum-sheet",
            "default_salt_pct": 0.0075,
            "default_form_factor": "heavy-aluminum-sheet",
            "default_salt_pct": 0.0075,
            "default_form_factor": "heavy-aluminum-sheet",
            "default_salt_pct": 0.0075,
            "default_form_factor": "heavy-aluminum-sheet",
            "default_salt_pct": 0.0075,
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "high_spread",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.5%"
            },
            "culinary_nuance_directive": (
                "For drop cookies, the balance of gluten development and moisture retention determines the final texture. "
                "CRITICAL PHYSICS: High pentosan concentrations (found in grains like Rye) can aggressively absorb water, "
                "starving wheat proteins of hydration. This can be used to inhibit gluten for tender textures, or to trap moisture for a gooey chew. "
                "FLAVOR COMPATIBILITY: Strictly sensitive to high-astringent red wheat tannins, which create bitter notes. "
                "Tannin-free Hard White Wheats, Soft White Wheats, or low-malty ancient profiles (like Spelt or Kamut) are excellent choices "
                "that introduce desirable culinary depth without clashing with confections."
            )
        },
        "bar_cookie": {
            "default_form_factor": "heavy-aluminum-sheet",
            "default_salt_pct": 0.0075,
            "label": "Bar / Slab",
            "icon": "🍫",
            "description": "Continuous uniform block baking, minimizing perimeter crisping.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.5%"
            },
            "culinary_nuance_directive": (
                "Focus on perimeter stability and controlled horizontal expansion. Grains must preserve a tender, short crumb "
                "that slices cleanly without shattering, while providing enough uniform starch walls to hold heavy inclusion "
                "weights across a continuous slab pan without center sinking."
            )
        },
        "slice_bake": {
            "default_form_factor": "heavy-aluminum-sheet",
            "default_salt_pct": 0.0075,
            "label": "Slice & Bake",
            "icon": "🔪",
            "description": "Log configuration, highly compressed fat crystals for crisp rings.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.0%"
            },
            "culinary_nuance_directive": (
                "Focus on high compression crystal arrays and clean circular margins. Dough demands maximum fat-crystal packing "
                "with minimal protein resilience, allowing chilled logs to be sheeted or sliced cleanly without dragging crumbs, "
                "baking into uniform, crisp rings."
            )
        },
        "rolled_cutout": {
            "default_form_factor": "half-sheet-pan",
            "default_salt_pct": 0.0075,
            "label": "Rolled Cutout",
            "icon": "📐",
            "description": "Zero-spread formulation maintaining clean geometric edges post-bake.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "9.0% - 11.0%"
            },
            "culinary_nuance_directive": (
                "Focus on moderate structural extensibility and zero thermal flow. Grains must allow the dough to accept "
                "sharp die-cutting and release cleanly from rolling mats, holding precise geometric definitions and sharp "
                "borders under immediate oven heat."
            )
        }
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

    def apply_sub_class_constraints(self, hydration: float, fat: float, sugar: float, leaven: float, salt: float, leaven_type: str = 'yeast', **kwargs) -> tuple[float, float, float, float, float]:
        # Cookies have zero added water (hydration comes entirely from eggs and butter).
        # We allow a small amount (5%) if an explicit flavor liquid (like lemon juice) is requested.
        sec_liquids = kwargs.get("sec_liquids", [])
        has_liquid = False
        for liq in sec_liquids:
            name = str(liq.get("name", "")).lower()
            if name and name not in ["none", "pure water", "water"]:
                has_liquid = True
                break
        
        cookie_hyd = 0.05 if has_liquid else 0.0
        # Wider guardrails to allow AI flavor chemistry to dictate final cookie richness.
        # Max 1.20 for fat (e.g. shortbreads), max 2.00 for sugar (e.g. extremely chewy brittle cookies)
        cookie_fat = max(0.20, min(1.20, fat))
        cookie_sugar = max(0.40, min(2.00, sugar))
        if leaven_type == 'sourdough':
            leaven = max(0.0, min(0.60, leaven))
        elif leaven_type == 'chemical':
            leaven = max(0.0, min(0.10, leaven))
        else:
            leaven = max(0.0, min(0.015, leaven))
        salt = max(0.0, min(0.10, salt))
        return cookie_hyd, cookie_fat, cookie_sugar, leaven, salt

    def get_ai_culinary_directive(self) -> str:
        return "Cookies require a careful balance of chemical leavening and zero yeast. Focus on proper sugar/fat creaming to control the final spread coefficient. This is a cookie archetype. You MUST include a chemical leavener (baking soda/powder). It requires heavy lipids. For sweet cookies, use heavy sugars. For savory shortbreads/crackers, omit sugar and use savory fats (cheese, butter). Liquids are rarely needed unless specified."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives (like chocolate chips or nuts), use true baker's percentages (flour = 100%). For cookies, these MUST be scaled heavily, typically ranging from 50.0 to 150.0. CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile. CRITICAL: For chemical leaveners (baking powder, baking soda), strictly limit to 1.0 to 5.0 to avoid chemical taste. If total lipid fat exceeds 30.0%, total liquid MUST NOT exceed 85.0%."

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        cream_min = 5
        fold_min = 3
        chill_min = 60
        bake_min = bake_time_min
        preset_slug = kwargs.get("preset_slug") or ""

        steps = [
            {
                "key": "mix",
                "name": "Cream Fat & Sugar",
                "duration_sec": cream_min * 60,
                "desc": "Beat butter and sugar together until light and fluffy. Dissolving sugar partially in fat helps manage the final oven spread coefficient.",
                "is_mix": True
            },
            {
                "key": "fold",
                "name": "Fold Dry & Inclusions",
                "duration_sec": fold_min * 60,
                "desc": "Fold in flour, salt, and inclusions (chocolate chips, oats) just until combined. Do not over-work to keep the crumb tender."
            }
        ]

        if "slice" in preset_slug.lower() or "biscotti" in preset_slug.lower():
            steps.append({
                "key": "shape_log",
                "name": "Form Dough Cylinder",
                "duration_sec": 10 * 60,
                "desc": "Form dough into a tight cylinder or log on parchment paper before chilling."
            })

        steps.append({
            "key": "chill",
            "name": "Fridge Chilling Rest",
            "duration_sec": chill_min * 60,
            "desc": "Mandatory refrigeration rest for at least 1 hour (up to 24-48 hours for optimal flavor). Chilling solidifies butter fat (slowing spread) and hydrates flour completely for a chewier center."
        })

        if "bar" in preset_slug.lower() or "slab" in preset_slug.lower() or "continuous" in preset_slug.lower():
            bake_name = "Continuous Slab Bake"
            bake_desc = "Press dough evenly into a prepared continuous pan. Bake until edges are set and golden. Center will set soft."
        elif "slice" in preset_slug.lower() or "biscotti" in preset_slug.lower():
            bake_name = "Sliced Disc Bake"
            bake_desc = "Slice chilled log into uniform discs and arrange on a baking sheet. Bake until crisp and golden."
        elif "cutout" in preset_slug.lower() or "gingerbread" in preset_slug.lower() or "sugar" in preset_slug.lower():
            bake_name = "Geometric Rolled Bake"
            bake_desc = "Roll out chilled dough on a floured surface, cut with geometric dies/cutters, and place on sheet pan. Bake until edges are set."
        else:
            bake_name = "Horizontal Spread Bake"
            bake_desc = "Scoop dough balls onto sheet pan. Bake until edges are set and golden, watching horizontal expansion spread. Center will set soft."

        steps.extend([
            {
                "key": "bake",
                "name": bake_name,
                "duration_sec": bake_min * 60,
                "desc": bake_desc,
                "is_bake": True
            },
            {
                "key": "cool",
                "name": "Pan & Wire Rack Cooling",
                "duration_sec": 15 * 60,
                "desc": "Allow the cookies to cool on the hot baking/pan for 5 minutes before transferring to a wire rack to cool completely. This carryover cooking sets the soft centers."
            }
        ])
        return steps

