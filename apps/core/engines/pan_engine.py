from apps.core.engines.base_engine import BaseEngine

class PanEngine(BaseEngine):
    name = "Enriched & Soft Engine"
    slug = "pan"
    target_protein_min = 11.5
    target_protein_max = 13.0
    gluten_behavior = "High Shreddability. Must possess enough structural lift to support heavy lipid loads (butter, sugar, milk, egg yolks) without collapsing."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Demands a clean, sweet, milky baseline; whole-grain bitterness is an active defect."
    tannin_sensitive = True
    supported_tweaks = ["hydration", "leavening", "enrichment"]
    production_profile = {
        "thermodynamic_focus": "biological_yeast_activity",
        "mechanical_energy_threshold": "high_kneading",
        "permissible_action_types": ["knead"],
        "environmental_rest_strategy": "gas_proofing",
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
        "standard-9x5-pan": {
            "name": "Standard 9x5 Loaf Pan",
            "tier": "recommended",
            "is_portioned": False,
            "unit_weight": 900.0,
            "base_count": 1,
            "step_increment": 1,
            "unit_label": "loaf",
            "unit_label_plural": "loaves",
            "bake_temp_f": 375,
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
            "bake_temp_f": 375,
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
            "bake_temp_f": 375,
            "bake_time_min": 20,
            "steam_required": False,
            "is_enriched_profile": True,
        }
    }

    presets = [
        "Everyday White Sandwich Loaf", "Rich Brioche", "Traditional Challah",
        "Hokkaido Milk Bread", "Soft Burger Buns", "Dinner Rolls",
        "Cinnamon Rolls", "Chocolate Babka", "Monkey Bread"
    ]

    archetypes = {
        "sandwich_pan": {
            "default_form_factor": "standard-9x5-pan",
            "label": "Sandwich Pan Loaf",
            "icon": "🍞",
            "description": "Straight sidewall containment maximizing volume and thin slicing.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
            "default_form_factor": "standard-9x5-pan",
            "default_form_factor": "standard-9x5-pan",
            "default_form_factor": "standard-9x5-pan",
            "default_form_factor": "standard-9x5-pan",
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "11.0% - 13.0%"
            },
            "culinary_nuance_directive": (
                "Focus on maximizing vertical volume and achieving a uniform, tight cell structure. Grains must provide high protein "
                "retention to support thin sidewall pans, ensuring a soft, elastic crumb that slices cleanly without crumbling."
            )
        },
        "freeform_braided": {
            "default_form_factor": "standard-9x5-pan",
            "label": "Freeform Braided Loaf",
            "icon": "🥯",
            "description": "High-tensile strands capable of holding shape without pan walls like Challah or Brioche.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "zero_spread_stable",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "11.5% - 13.5%"
            },
            "culinary_nuance_directive": (
                "Focus on high structural retention and zero horizontal flow without pan walls. Grains must yield an elastic, highly "
                "cohesive protein backbone capable of holding intricate braided definition under heavy lipid and sugar enrichment "
                "weights without collapsing or slumping."
            )
        },
        "soft_dinner_roll": {
            "default_form_factor": "standard-9x5-pan",
            "label": "Soft Dinner Roll",
            "icon": "🫓",
            "description": "Small batch pull-apart clusters prioritizing maximum steam-trapped softness.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "11.0% - 12.5%"
            },
            "culinary_nuance_directive": (
                "Focus on steam-trapped softness and excellent cluster lift. The protein web must remain extensible and resilient, "
                "allowing small batch dough clusters to crowd together and climb vertically, trapping internal moisture for a classic "
                "feather-light, pull-apart tear texture."
            )
        },
        "filled_sweet_roll": {
            "default_form_factor": "standard-9x5-pan",
            "label": "Filled Sweet Roll",
            "icon": "🌀",
            "description": "Laminated or sheeted scroll structures built to contain heavy interior fillings.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "11.5% - 13.0%"
            },
            "culinary_nuance_directive": (
                "Focus on uniform dough-sheet stretch and high filling containment. The flour must provide an elastic, robust backbone "
                "capable of being rolled thin, scroll-shaped, and baked without rupturing or allowing heavy sweet fillings to cause "
                "structural collapse."
            )
        },
    }
    def apply_sub_class_constraints(self, hydration: float, fat: float, sugar: float, leaven: float, salt: float, leaven_type: str = 'yeast', flavor_profile: str = 'neutral', **kwargs) -> tuple[float, float, float, float, float]:
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
            "title": "Fermentation Retardation",
            "message": "Fats and sugars slow down yeast fermentation. Allow for a longer bulk proof or create a warm, moist proofing box to encourage active rising."
        })
        return pitfalls

    def get_ai_culinary_directive(self) -> str:
        return "Warn the user if the dough mass will overflow or underfill the selected form factor (e.g. 9x5 loaf pan, pullman pan, or individual rolls). This is an enriched pan bread (e.g. brioche, sandwich loaf). For sweet profiles, use sugar, butter, and eggs. For savory profiles (like garlic herb), STRICTLY OMIT sweeteners and eggs (never use eggs as binders for savory pan breads), and ensure total lipid fat is precisely between 5.0% and 10.0%. Always include a liquid medium and yeast leavener."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives (like seeds), use true baker's percentages (flour = 100%). For sandwich breads, these typically range from 5.0 to 15.0. CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile. CRITICAL: For commercial yeast (active/instant), strictly limit to 0.5 to 1.5. For sourdough starter, limit to 10.0 to 25.0. If total lipid fat exceeds 30.0%, total liquid MUST NOT exceed 85.0% to prevent emulsification failure."

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        mix_min = 6
        knead_min = 12 if mixing_method == "stand_mixer" else 18
        
        # Warm rise: enriched doughs rise slower, warm bulk rise is helpful
        bulk_min = estimated_bulk_minutes
        proof_min = estimated_proof_minutes
        preset_slug = kwargs.get("preset_slug") or ""

        steps = [
            {
                "key": "mix",
                "name": "Lipid Mix Phase",
                "duration_sec": mix_min * 60,
                "desc": "Combine flour, liquids, yeast, sugar, and egg yolks. Mix on low speed to establish the gluten base. Keep butter/fat separate for now to avoid premature coating of gluten proteins.",
                "is_mix": True
            },
            {
                "key": "knead",
                "name": "Intensive Dough Hook Knead",
                "duration_sec": knead_min * 60,
                "desc": "Slowly incorporate softened butter/fat in pieces while running the stand mixer. Knead intensively until the dough is silky, elastic, and clears the sides of the bowl.",
                "is_knead": True
            },
            {
                "key": "bulk",
                "name": "Enriched Bulk Ferment",
                "duration_sec": bulk_min * 60,
                "desc": "Enriched doughs ferment slower due to fat and sugar retardants. Keep in a warm, draft-free place."
            }
        ]

        if "braid" in preset_slug.lower() or "challah" in preset_slug.lower() or "babka" in preset_slug.lower():
            shape_name = "Strand Division & Braiding"
            shape_desc = "Divide dough into equal strands. Roll out and braid tightly. Transfer to a parchment-lined sheet pan."
            proof_name = "Freeform Final Proof"
            proof_desc = "Proof freeform on the baking sheet until nearly doubled in size. Brush with egg wash before baking."
        elif "roll" in preset_slug.lower() and "cinnamon" not in preset_slug.lower() and "sweet" not in preset_slug.lower():
            shape_name = "Roll Portioning"
            shape_desc = "Divide dough into small uniform portions (e.g., 50g-70g). Roll into tight balls and cluster together in a buttered pan."
            proof_name = "Clustered Final Proof"
            proof_desc = "Proof in the pan until the rolls expand, touch each other, and reach the pan rim."
        elif "cinnamon" in preset_slug.lower() or "sweet_roll" in preset_slug.lower():
            shape_name = "Lamination & Filling"
            shape_desc = "Roll dough into a large rectangle. Spread filling evenly, roll into a tight cylinder, and slice into rounds. Place in a prepared pan."
            proof_name = "Filled Pan Proof"
            proof_desc = "Proof the sliced rounds in the pan until puffy and pressing against one another."
        else:
            shape_name = "Loaf Sizing & Portioning"
            shape_desc = "Divide the dough into uniform portions for multi-loaf scaling. Shape into tight rounds or logs for baking."
            proof_name = "Loaf Pan Final Proof"
            proof_desc = "Transfer dough pieces into the greased baking pan. Proof until the dough reaches 1 inch above the pan rim."

        steps.extend([
            {
                "key": "divide_portion",
                "name": shape_name,
                "duration_sec": 10 * 60,
                "desc": shape_desc
            },
            {
                "key": "proof",
                "name": proof_name,
                "duration_sec": proof_min * 60,
                "desc": proof_desc,
                "is_proof": True
            },
            {
                "key": "bake",
                "name": "Soft Crumb Bake",
                "duration_sec": bake_time_min * 60,
                "desc": "Bake at moderate heat (350-375°F). Rich sugars caramelize rapidly; shield loaf/rolls with foil if top browns too early.",
                "is_bake": True
            }
        ])
        
        preset_slug = kwargs.get("preset_slug", "")
        if "roll" in preset_slug.lower() or "bun" in preset_slug.lower():
            cooling_desc = "Allow the rolls/buns to cool in the pan for 5-10 minutes. They can be served warm, or transferred to a wire rack to cool completely."
            cooling_duration = 15
        else:
            cooling_desc = "Allow the bread to cool in the pan for 10 minutes to stabilize, then carefully turn out onto a wire rack to cool completely. Slicing warm bread will crush the crumb."
            cooling_duration = 60
            
        steps.append({
            "key": "cool",
            "name": "Pan & Wire Rack Cooling",
            "duration_sec": cooling_duration * 60,
            "desc": cooling_desc
        })
        
        return steps
