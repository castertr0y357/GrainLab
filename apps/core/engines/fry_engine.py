from apps.core.engines.base_engine import BaseEngine


class FryEngine(BaseEngine):
    name = "Fried Doughs Engine"
    slug = "fry"
    default_yield_unit = "donuts"
    target_protein_min = 11.5
    target_protein_max = 13.0
    gluten_behavior = "Rapid Gas Expansion & Fat Resistance. Surface must expand immediately and seal against rapid convection liquid heat to lock out excess frying oil absorption."
    flavor_affinity = "Tannin Sensitive (Sweet/Neutral). Demands a warm, clean, light baseline suitable for immediate sugar/glaze applications."
    tannin_sensitive = True
    production_profile = {
        "thermodynamic_focus": "biological_yeast_activity",
        "mechanical_energy_threshold": "high_kneading",
        "permissible_action_types": ["mix", "fry"],
        "environmental_rest_strategy": "gas_proofing",
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
        "binders": {"default": "none", "options": ["none", "whole_eggs", "egg_whites", "aquafaba_vegan"]},
    }

    permissible_form_factors = {
        "high-volume-oil-vat": {
            "name": "High-Volume Cast Iron Oil Vat",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 65.0,
            "base_count": 12,
            "step_increment": 12,
            "unit_label": "donut",
            "unit_label_plural": "donuts",
            "bake_temp_f": 375,
            "bake_time_min": 5,
            "steam_required": False,
            "is_enriched_profile": True,
        }
    }

    presets = [
        "Yeast-Raised Donuts",
        "Fluffy New Orleans Beignets",
        "Puffed Sopapillas",
        "Traditional Native Frybread",
        "Cake Donuts",
        "Apple Fritters",
        "Crullers (Fried Execution)",
    ]

    archetypes = {
        "yeast_raised_donut": {
            "default_form_factor": "high-volume-oil-vat",
            "default_salt_pct": 0.01,
            "label": "Yeast-Raised Donut",
            "icon": "🍩",
            "description": "Highly aerated, light, floating dough rings.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "default_form_factor": "high-volume-oil-vat",
                "default_salt_pct": 0.01,
                "default_form_factor": "high-volume-oil-vat",
                "default_salt_pct": 0.01,
                "default_form_factor": "high-volume-oil-vat",
                "default_salt_pct": 0.01,
                "default_form_factor": "high-volume-oil-vat",
                "default_salt_pct": 0.01,
                "required_gluten_elasticity": "high_retention",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "11.0% - 13.0%",
            },
            "culinary_nuance_directive": (
                "Focus on high gas retention and maximum structural lightness. The dough demands an elastic, highly resilient "
                "long-chain protein web capable of capturing yeast respiration during proofing, enabling the ring to float "
                "high in hot fat while building an oil-impermeable outer crust."
            ),
        },
        "cake_donut": {
            "default_form_factor": "deep-fry-vat",
            "default_salt_pct": 0.01,
            "label": "Cake / Chemical Donut",
            "icon": "🍩",
            "description": "Tender, friable, batter-based rings dropping directly into fat.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "low_moisture_high_fat",
                "optimal_protein_window": "8.5% - 10.5%",
            },
            "culinary_nuance_directive": (
                "Focus on complete gluten suppression and controlled chemical gas expansion. Grains must maximize tender starch "
                "swelling with zero elastic snapback, allowing the thick batter to release cleanly from extrusion dies and "
                "fry into a soft, cakey ring with a short crumb."
            ),
        },
        "fritter_beignet": {
            "default_form_factor": "high-volume-oil-vat",
            "default_salt_pct": 0.01,
            "label": "Batter Fritter / Beignet",
            "yield_unit": "beignets",
            "icon": "☁️",
            "description": "Irregular high-hydration moisture puffs expanding violently in oil.",
            "grain_affinity": "low_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "minimal_to_none",
                "desired_horizontal_flow": "high_spread",
                "moisture_lipid_ratio": "high_hydration_lean",
                "optimal_protein_window": "9.0% - 11.0%",
            },
            "culinary_nuance_directive": (
                "Focus on high-hydration steam puffs and explosive internal vapor expansion. Grains must allow irregular, wet "
                "dough masses to hold their shape loosely upon dropping into fat, flash-frying into hollow, airy pillows "
                "without absorbing excess grease."
            ),
        },
        "fried_laminate": {
            "default_form_factor": "high-volume-oil-vat",
            "default_salt_pct": 0.01,
            "label": "Fried Laminated",
            "yield_unit": "pastries",
            "icon": "🫓",
            "description": "Alternating layers flashing open instantly in convection fat.",
            "grain_affinity": "medium_protein",
            "target_archetype_mechanics": {
                "required_gluten_elasticity": "moderate_extensible",
                "desired_horizontal_flow": "controlled_expansion",
                "moisture_lipid_ratio": "balanced_emulsion",
                "optimal_protein_window": "10.0% - 12.0%",
            },
            "culinary_nuance_directive": (
                "Focus on thin alternating layer definition under sudden convective thermal shock. The flour must provide excellent "
                "extensibility to hold crisp rolled structural sheets separate from fat boundaries, allowing the layers to separate "
                "cleanly into flaky shards upon frying."
            ),
        },
    }

    def apply_sub_class_constraints(
        self,
        hydration: float,
        fat: float,
        sugar: float,
        leaven: float,
        salt: float,
        leaven_type: str = "yeast",
        flavor_profile: str = "neutral",
        **kwargs,
    ) -> tuple[float, float, float, float, float]:
        hyd = max(0.0, min(0.80, hydration))
        f = max(0.0, min(0.40, fat))
        s = max(0.0, min(0.40, sugar))

        # Prevent "soup" by capping hydration if fat is very high
        if f > 0.30 and hyd > 0.85:
            hyd = 0.85

        if leaven_type == "sourdough":
            leaven = max(0.0, min(0.60, leaven))
        elif leaven_type == "chemical":
            leaven = max(0.0, min(0.10, leaven))
        else:
            leaven = max(0.0, min(0.015, leaven))
        salt = max(0.0, min(0.10, salt))
        return hyd, f, s, leaven, salt

    def get_ai_culinary_directive(self) -> str:
        return "Provide the target frying oil pre-heat temperature (typically around 375°F to allow a drop to 365°F during frying). This is a fried dough (donuts, beignets). Enriched dough requiring lipids and leaveners. Use sweeteners and eggs for sweet donuts, but omit sweeteners for savory fried doughs (like savory fritters)."

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives (like spices or glaze bases), use true baker's percentages (flour = 100%). For fried doughs, these typically range from 10.0 to 30.0. CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile. CRITICAL: For commercial yeast (active/instant), strictly limit to 0.5 to 1.5. For sourdough starter, strictly limit to 10.0 to 25.0."

    def get_live_timeline_steps(
        self,
        recipe_data: dict,
        estimated_bulk_minutes: int,
        estimated_proof_minutes: int,
        bake_time_min: int,
        mixing_method: str = "stand_mixer",
        **kwargs,
    ) -> list[dict]:
        mix_min = 8
        proof_min = estimated_proof_minutes or 45

        # Side A & B frying steps (measured in seconds!)
        side_a_sec = 120
        flip_sec = 10
        side_b_sec = 120
        preset_slug = kwargs.get("preset_slug") or ""

        is_batter = False
        if "cake" in preset_slug.lower() or "fritter" in preset_slug.lower() or "batter" in preset_slug.lower():
            is_batter = True

        if is_batter:
            steps = [
                {
                    "key": "mix",
                    "name": "Batter Mix",
                    "duration_sec": mix_min * 60,
                    "desc": "Whisk wet and dry ingredients into a thick, uniform batter. Do not over-mix.",
                    "is_mix": True,
                }
            ]
        else:
            steps = [
                {
                    "key": "mix",
                    "name": "Dough Mix & Knead",
                    "duration_sec": mix_min * 60,
                    "desc": "Mix ingredients to form a soft, supple leavened dough. Knead until smooth.",
                    "is_mix": True,
                },
                {
                    "key": "proof",
                    "name": "Portion & Proof",
                    "duration_sec": proof_min * 60,
                    "desc": "Roll out and cut into shapes. Proof on parchment squares until airy and delicate.",
                    "is_proof": True,
                },
            ]

        steps.append(
            {
                "key": "preheat",
                "name": "Oil Preheat & Recovery Check",
                "duration_sec": 10 * 60,
                "desc": "Heat neutral fry oil to 375°F. Confirm your drainage racks, spider tools, and coatings are ready.",
            }
        )

        if is_batter:
            steps.append(
                {
                    "key": "fry_a",
                    "name": "Drop & Fry Side A",
                    "duration_sec": side_a_sec,
                    "desc": "Drop, pipe, or extrude the batter directly into the hot oil. Fry Side A.",
                    "is_bake": True,
                }
            )
        else:
            steps.append(
                {
                    "key": "fry_a",
                    "name": "Fry Side A",
                    "duration_sec": side_a_sec,
                    "desc": "Gently drop proofed dough into hot oil. Fry Side A. Watch for rapid expansion and bubble formation.",
                    "is_bake": True,
                }
            )

        steps.extend(
            [
                {
                    "key": "flip",
                    "name": "Flip",
                    "duration_sec": flip_sec,
                    "desc": "Use tongs or chopsticks to quickly flip the pieces. Maintain oil temperature.",
                },
                {
                    "key": "fry_b",
                    "name": "Fry Side B",
                    "duration_sec": side_b_sec,
                    "desc": "Fry Side B until deeply golden and cooked through.",
                    "is_bake": True,
                },
                {
                    "key": "cool",
                    "name": "Drain & Cool",
                    "duration_sec": 10 * 60,
                    "desc": "Remove from oil onto a wire rack to drain. If coating with sugar/cinnamon, do so while hot. If glazing, wait until slightly cooled.",
                },
            ]
        )
        return steps
