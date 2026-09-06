GRAIN_THIRST_MODIFIERS = {
    "all_purpose": 0.0,
    "whole_wheat": 0.03,
    "spelt": 0.05,
    "kamut": 0.06,
    "einkorn": 0.04,
}

MATURITY_HYDRATION_MODIFIERS = {
    "just_milled": 0.0,
    "dead_zone": -0.02,
    "matured": 0.0,
}

FRICTION_FACTORS = {
    "hand_knead": 2.0,
    "stand_mixer": 10.0,
    "bread_machine": 15.0,
}


def _get_val(obj, key, default=None):
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


from .ai_prompts import AIPromptBuilder


class BaseEngine(AIPromptBuilder):
    name = "Base Engine"
    slug = "base"
    target_protein_min = 11.0
    target_protein_max = 13.0
    gluten_behavior = "Standard gluten development"
    flavor_affinity = "Standard flour profile"
    tannin_sensitive = False
    supported_tweaks = ["hydration", "leavening"]
    tweak_labels = {"enrichment": ["Lean", "Brioche"], "hydration": ["Tight", "Open"], "leavening": ["Yeast", "40%"]}
    production_profile = {
        "thermodynamic_focus": "biological_yeast_activity",
        "mechanical_energy_threshold": "high_kneading",
        "permissible_action_types": ["knead"],
        "environmental_rest_strategy": "gas_proofing",
    }
    secondary_ingredients = {}

    def culinary_nuance_directive(self, active_archetype_id: str = None, active_variation_id: str = None) -> str:
        """
        Dynamically construct a highly specific culinary nuance directive
        based on the engine's unique parametric attributes and optional active archetype.
        """
        tannin_text = (
            "Preferred: Tannin Sensitive (Sweet/Neutral). You may recommend whole grains with tannins if you provide notes on how to balance their bitterness/astringency."
            if self.tannin_sensitive
            else "This engine is tannin tolerant. It welcomes rustic, savory caramelization, lactic/acetic sourness, "
            "and deep whole grain bran expressions."
        )
        actions = ", ".join(self.production_profile.get("permissible_action_types", []))

        global_criteria = (
            f"Focus on the unique target chemistry of the {self.name}:\n"
            f"* Gluten & Structural Behavior: {self.gluten_behavior}\n"
            f"* Flavor Affinity & Botanical Compatibility: {self.flavor_affinity} ({tannin_text})\n"
            f"* Preferred Protein Window: {self.target_protein_min}% to {self.target_protein_max}%\n"
            f"* Production Parameters: Thermodynamic focus is {self.production_profile.get('thermodynamic_focus')}, "
            f"rest strategy is {self.production_profile.get('environmental_rest_strategy')}, and permissible actions include [{actions}]."
        )

        if not active_archetype_id:
            return global_criteria

        archetypes = getattr(self, "archetypes", {})
        archetype = archetypes.get(active_archetype_id)
        if not archetype:
            return global_criteria

        # Create a copy so we don't permanently modify the class definition
        mechanics = dict(archetype.get("target_archetype_mechanics", {}))
        arch_directive = archetype.get("culinary_nuance_directive", "")
        variation_directive = ""

        if active_variation_id and hasattr(self, "variations"):
            variation = self.variations.get(active_variation_id, {})
            overrides = variation.get("mechanics_overrides", {})
            mechanics.update(overrides)
            variation_directive = variation.get("culinary_nuance_directive_append", "")

        gluten = mechanics.get("required_gluten_elasticity", "N/A")
        flow = mechanics.get("desired_horizontal_flow", "N/A")
        lipids = mechanics.get("moisture_lipid_ratio", "N/A")
        protein_window = mechanics.get("optimal_protein_window", "N/A")
        affinity = archetype.get("grain_affinity", "N/A")

        stacked_text = (
            f"{global_criteria}\n\n"
            f"[TARGET ARCHETYPE: {archetype.get('label', active_archetype_id)} MOLECULAR PHYSICS OBJECTIVES]\n"
            f"* Gluten Behavior Objective: {gluten}\n"
            f"* Flow Objective: {flow}\n"
            f"* Lipid & Moisture Objective: {lipids}\n\n"
            f"[BOTANICAL COMPATIBILITY BOUNDARIES]\n"
            f"* Optimal Protein Window: {protein_window}\n"
            f"* Grain Affinity: {affinity}"
        )

        if arch_directive:
            stacked_text += f"\n\n[SPECIFIC CULINARY NUANCE DIRECTIVE]\n{arch_directive}"

        if variation_directive:
            stacked_text += f"\n\n[VARIATION DIRECTIVE]\n{variation_directive}"

        return stacked_text

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
        }
    }

    def calculate_wheat_berry_shares(
        self,
        active_berries: list,
        texture_score: int,
        crumb_score: int,
        preset_slug: str = None,
        preset_name: str = None,
        flour_blend: dict = None,
    ) -> tuple[dict[str, float], float, str | None]:
        if not active_berries:
            return {"House Blend": 1.0}, 1.0, None

        total_berries = len(active_berries)
        shares = {}
        if flour_blend:
            for b in active_berries:
                name = _get_val(b, "name")
                slug = name.lower().replace(" ", "_").replace("-", "_")

                pct = flour_blend.get(slug)
                if pct is None:
                    slug_clean = "".join(c for c in slug if c.isalnum() or c == "_")
                    pct = flour_blend.get(slug_clean)

                if pct is None:
                    for k, v in flour_blend.items():
                        if k in slug or slug in k:
                            pct = v
                            break

                shares[name] = float(pct or 0.0)

            total_share = sum(shares.values())
            if total_share > 0:
                shares = {k: v / total_share for k, v in shares.items()}
            else:
                shares = {_get_val(b, "name"): 1.0 / total_berries for b in active_berries}
        else:
            shares = {_get_val(b, "name"): 1.0 / total_berries for b in active_berries}

        weighted_absorption = sum(_get_val(b, "moisture_absorption_coef", 1.0) for b in active_berries) / total_berries
        return shares, weighted_absorption, None

    def get_flavor_bases(self, creativity_level: int) -> list:
        return ["Flour, water, and salt", "Toasted grains and seeds", "Malted barley syrup or molasses"]

    def get_contextual_pitfalls(self, effective_hydration: float, grain_type: str, preset_slug: str = None) -> list:
        pitfalls = []
        if effective_hydration >= 0.78:
            pitfalls.append(
                {
                    "title": "High Hydration Handling",
                    "message": "With a hydration of over 78%, this dough is wet. Do not add raw flour to the workspace; instead, perform 'stretch-and-folds' with wet hands to build gluten structure.",
                }
            )
        if grain_type in ["spelt", "kamut", "einkorn"]:
            pitfalls.append(
                {
                    "title": "Ancient Grain Fragility",
                    "message": f"{grain_type.title()} has weaker gluten networks. Avoid intensive machine mixing. Prefer short hand mixing followed by gentle folds to keep the structure from collapsing.",
                }
            )
        if not pitfalls:
            pitfalls.append(
                {
                    "title": "Standard Proofing Check",
                    "message": "Keep dough covered at a stable temp of 75-78°F. The poke test is your best guide: if a gentle indent springs back slowly, it is ready to bake.",
                }
            )
        return pitfalls

    def get_sensory_benchmark(
        self,
        grain_type: str,
        flour_maturity: str,
        effective_hydration: float,
        category_slug: str = None,
        preset_slug: str = None,
    ) -> str:
        if grain_type is None:
            grain_type = "all_purpose"
        grain_name = grain_type.replace("_", " ").title()
        desc = f"For fresh-milled {grain_name} dough: "
        if effective_hydration >= 0.75:
            desc += "The dough will be wet and sticky. Look for a glossy surface and a clean, dome-like rise. "
        elif effective_hydration >= 0.65:
            desc += (
                "Expect a supple, holding structure. The dough should feel alive, resilient, and elastic when touched. "
            )
        else:
            desc += "Dough is firm and tight. It will not double dramatically; monitor for a rounded dome and a smooth outer skin. "

        if flour_maturity == "just_milled":
            desc += "As this flour was milled today, gluten activity is highly active but lacks extensibility. Expect rapid enzyme fermentation; handle gently to avoid tearing."
        elif flour_maturity == "dead_zone":
            desc += "Caution: Flour is in the 1-2 week enzyme dead zone. Gluten structure is relaxed and vulnerable. The dough will feel sticky and might lack holding power; do not over-proof."
        else:
            desc += "Flour is fully matured. Gluten bonds are stable and predictable. The rise will be steady with solid gas retention."
        return desc

    def calculate_recipe(
        self,
        base_hydration: float,
        base_fat: float,
        base_sugar: float,
        target_mass: float,
        grain_type: str = "all_purpose",
        flour_maturity: str = "matured",
        leaven_type: str = "yeast",
        leaven_pct: float = 0.015,
        salt_pct: float = 0.02,
        room_temp_f: float = 72.0,
        flour_temp_f: float = 70.0,
        mixing_method: str = "stand_mixer",
        substitution: dict[str, str] = None,
        active_berries: list = None,
        texture_score: int = 50,
        crumb_score: int = 50,
        friction_override: float = None,
        preset_slug: str = None,
        preset_name: str = None,
        **kwargs,
    ) -> dict:
        # 1. Apply Simple Hydration Modifiers
        flour_blend = kwargs.get("flour_blend", {})
        if active_berries:
            berry_shares, weighted_absorption, structural_warning = self.calculate_wheat_berry_shares(
                active_berries,
                texture_score,
                crumb_score,
                preset_slug=preset_slug,
                preset_name=preset_name,
                flour_blend=flour_blend,
            )
            thirst_mod = weighted_absorption - 1.0
        else:
            berry_shares = {}
            thirst_mod = GRAIN_THIRST_MODIFIERS.get(grain_type, 0.0)

        maturity_mod = MATURITY_HYDRATION_MODIFIERS.get(flour_maturity, 0.0)
        effective_hydration = base_hydration + thirst_mod + maturity_mod
        effective_fat = base_fat
        effective_sugar = base_sugar

        # 2. Map Secondary Ingredients & Substitutions
        fat_substitute_label = None
        sec_lipids = kwargs.get("secondary_lipids") or []
        sec_liquids = kwargs.get("secondary_liquids") or []
        sec_binders = kwargs.get("secondary_binders") or []
        sec_sweeteners = kwargs.get("secondary_sweeteners") or []
        sec_leaveners = kwargs.get("secondary_leaveners") or []
        sec_additives = kwargs.get("secondary_additives") or []

        # Apply legacy substitution mapping
        if substitution and substitution.get("original") == "water":
            sub_sub = substitution.get("substitute")
            if sub_sub in ["whole_milk", "almond_milk"]:
                sec_liquids = [{"name": sub_sub.replace("_", " ").title(), "ratio": 1.0}]

        if substitution and substitution.get("original") == "fat":
            sub_sub = substitution.get("substitute")
            if sub_sub in ["butter", "salted_butter", "unsalted_butter", "olive_oil", "canola_oil", "vegetable_oil"]:
                sec_lipids = [{"name": sub_sub.replace("_", " ").title(), "ratio": 1.0}]

        binder_pct = getattr(self, "default_binder_pct", 0.10) if len(sec_binders) > 0 else 0.0

        # Perform subclass-specific constraints (ceilings / floors)
        try:
            flavor_profile = kwargs.get("inferred_flavor_profile", "neutral")
            effective_hydration, effective_fat, effective_sugar, leaven_pct, salt_pct = (
                self.apply_sub_class_constraints(
                    effective_hydration,
                    effective_fat,
                    effective_sugar,
                    leaven_pct,
                    salt_pct,
                    leaven_type,
                    flavor_profile=flavor_profile,
                    sec_liquids=sec_liquids,
                    sec_binders=sec_binders,
                )
            )
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                effective_hydration, effective_fat, effective_sugar, leaven_pct, salt_pct = (
                    self.apply_sub_class_constraints(
                        effective_hydration, effective_fat, effective_sugar, leaven_pct, salt_pct, leaven_type
                    )
                )
            else:
                raise

        # 3. Calculate Baker's Math Scaling
        flavor_inclusions = kwargs.get("flavor_inclusions", [])
        inclusion_pct = 0.0
        for inc in flavor_inclusions + sec_additives:
            if isinstance(inc, dict) and "bakers_percentage" in inc:
                name = inc.get("name", "")
                try:
                    pct = float(inc["bakers_percentage"]) / 100.0
                    if "salt" in name.lower() and pct <= 0.04:
                        continue
                    inclusion_pct += pct
                except (ValueError, TypeError):
                    pass

        total_ratios = (
            1.0
            + effective_hydration
            + effective_fat
            + effective_sugar
            + salt_pct
            + leaven_pct
            + binder_pct
            + inclusion_pct
        )
        flour_weight = target_mass / total_ratios
        water_weight = flour_weight * effective_hydration
        fat_weight = flour_weight * effective_fat
        sugar_weight = flour_weight * effective_sugar
        salt_weight = flour_weight * salt_pct
        leaven_weight = flour_weight * leaven_pct

        added_flour = flour_weight
        added_water = water_weight
        starter_weight = 0.0
        yeast_weight = 0.0

        if leaven_type == "sourdough":
            starter_weight = leaven_weight
            added_flour = flour_weight - (starter_weight / 2.0)
            added_water = water_weight - (starter_weight / 2.0)
        else:
            yeast_weight = leaven_weight

        STANDARD_UNIT_WEIGHTS = {
            "egg": {"weight": 50, "singular": "large egg", "plural": "large eggs"},
            "yolk": {"weight": 18, "singular": "large yolk", "plural": "large yolks"},
            "egg white": {"weight": 30, "singular": "large white", "plural": "large whites"},
            "lemon juice": {"weight": 45, "singular": "lemon, juiced", "plural": "lemons, juiced"},
            "lemon zest": {"weight": 6, "singular": "lemon, zested", "plural": "lemons, zested"},
            "lime juice": {"weight": 30, "singular": "lime, juiced", "plural": "limes, juiced"},
            "lime zest": {"weight": 4, "singular": "lime, zested", "plural": "limes, zested"},
            "garlic": {"weight": 5, "singular": "clove", "plural": "cloves"},
            "vanilla bean": {"weight": 3, "singular": "whole bean", "plural": "whole beans"},
            "active dry yeast": {"weight": 7, "singular": "packet", "plural": "packets"},
            "instant yeast": {"weight": 7, "singular": "packet", "plural": "packets"},
            "banana": {"weight": 115, "singular": "medium banana", "plural": "medium bananas"},
            "butter": {"weight": 113, "singular": "stick", "plural": "sticks"},
        }
        LIQUID_TERMS = [
            "water",
            "milk",
            "buttermilk",
            "cream",
            "juice",
            "oil",
            "extract",
            "vanilla",
            "vinegar",
            "coffee",
            "tea",
            "broth",
            "stock",
            "liquor",
            "bourbon",
            "rum",
            "vodka",
        ]

        def annotate_unit_weight(name: str, weight: float) -> str:
            name_lower = name.lower()
            for key, data in STANDARD_UNIT_WEIGHTS.items():
                if key in name_lower:
                    if key == "egg" and ("white" in name_lower or "yolk" in name_lower):
                        continue
                    if key == "butter" and "buttermilk" in name_lower:
                        continue
                    unit_weight = data["weight"]
                    units = weight / unit_weight
                    rounded_units = round(units * 2) / 2
                    if rounded_units > 0:
                        unit_str = f"{int(rounded_units)}" if rounded_units.is_integer() else f"{rounded_units}"
                        plural = data["plural"] if rounded_units > 1 else data["singular"]
                        return f"{name} (~{unit_str} {plural})"

            if any(term in name_lower for term in LIQUID_TERMS):
                if weight >= 120:
                    fl_oz = round(weight / 30)
                    return f"{name} (~{fl_oz} fl oz)"
                elif weight >= 15:
                    tbsp = round(weight / 15)
                    return f"{name} (~{tbsp} Tbsp)"
                elif weight > 0:
                    tsp = round((weight / 5) * 2) / 2
                    tsp_str = f"{int(tsp)}" if tsp.is_integer() else f"{tsp}"
                    return f"{name} (~{tsp_str} tsp)"
            return name

        def allocate_weights(items, total_weight, default_name):
            if not items:
                if total_weight > 0:
                    annotated_default = annotate_unit_weight(default_name, int(round(total_weight)))
                    return [{"name": annotated_default, "weight": int(round(total_weight))}]
                return []

            # Legacy robust: if items is a dict instead of list of dicts, make it a list
            if isinstance(items, dict):
                items = [items]

            total_ratio = sum(float(item.get("ratio", 1.0)) for item in items if isinstance(item, dict))
            if total_ratio == 0:
                total_ratio = 1.0

            results = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                ratio = float(item.get("ratio", 1.0))
                weight = int(round(total_weight * (ratio / total_ratio)))
                if weight > 0:
                    raw_name = item.get("name")
                    if raw_name is None:
                        raw_name = default_name
                    clean_name = raw_name.replace("_", " ").title()
                    annotated_name = annotate_unit_weight(clean_name, weight)
                    results.append({"name": annotated_name, "weight": weight})
            return results

        # Re-compute weights dynamically pulling defaults from child engine
        def get_default(cat, fallback):
            raw_val = self.secondary_ingredients.get(cat, {}).get("default", fallback)
            if raw_val is None:
                raw_val = fallback
            val = raw_val.replace("_", " ").title()
            return val if val.lower() != "none" else fallback

        liquid_items = allocate_weights(sec_liquids, added_water, get_default("liquids", "Water"))
        lipid_items = allocate_weights(sec_lipids, fat_weight, get_default("lipids", "Unsalted Butter"))
        binder_weight = flour_weight * binder_pct
        binder_items = allocate_weights(sec_binders, binder_weight, get_default("binders", "Whole Eggs"))
        sweetener_items = allocate_weights(sec_sweeteners, sugar_weight, get_default("sweeteners", "Granulated Sugar"))

        leaven_default = "Sourdough Starter" if leaven_type == "sourdough" else get_default("leaveners", "Baking Soda")
        leavener_items = allocate_weights(sec_leaveners, leaven_weight, leaven_default)

        # 5. Desired Dough Temperature (DDT)
        ddt_target_f = 78.0
        friction = friction_override if friction_override is not None else FRICTION_FACTORS.get(mixing_method, 10.0)
        required_water_temp_f = (3.0 * ddt_target_f) - room_temp_f - flour_temp_f - friction

        processed_inclusions = []
        for inc in flavor_inclusions:
            if isinstance(inc, dict) and "name" in inc:
                name = inc["name"]
                vol = inc.get("volume_description", "")
                pct = 0.0
                try:
                    pct = float(inc.get("bakers_percentage", 0)) / 100.0
                except (ValueError, TypeError):
                    pass

                if "salt" in name.lower() and pct <= 0.04:
                    continue

                weight = int(round(flour_weight * pct)) if pct > 0 else 0
                if weight > 0:
                    processed_inclusions.append(
                        {"name": name, "weight": weight, "volume_description": vol, "percentage": round(pct * 100, 1)}
                    )

        # Handle secondary additives similarly since they act as inclusions but have their percentages driven by phase 4
        processed_additives = []
        for inc in sec_additives:
            if isinstance(inc, dict) and "name" in inc:
                name = inc["name"]
                vol = inc.get("volume_description", "")
                pct = 0.0
                try:
                    pct = float(inc.get("ratio", inc.get("bakers_percentage", 0))) / 100.0
                except (ValueError, TypeError):
                    pass

                if "salt" in name.lower() and pct <= 0.04:
                    continue

                weight = int(round(flour_weight * pct)) if pct > 0 else 0
                if weight > 0:
                    processed_additives.append(
                        {"name": name, "weight": weight, "volume_description": vol, "percentage": round(pct * 100, 1)}
                    )

        return {
            "target_mass": int(round(target_mass)),
            "flour_weight": int(round(flour_weight)),
            "flavor_inclusions": processed_inclusions,
            "water_weight": int(round(water_weight)),
            "effective_hydration_pct": round(effective_hydration * 100, 1),
            "effective_fat_pct": round(effective_fat * 100, 1),
            "effective_sugar_pct": round(effective_sugar * 100, 1),
            "added_flour": int(round(added_flour)),
            "added_water": int(round(added_water)),
            "liquid_items": liquid_items,
            "yeast_weight": int(round(yeast_weight)),
            "leavener_items": leavener_items,
            "fat_weight": int(round(fat_weight)),
            "lipid_items": lipid_items,
            "sugar_weight": int(round(sugar_weight)),
            "sweetener_items": sweetener_items,
            "salt_weight": int(round(salt_weight)),
            "starter_weight": int(round(starter_weight)),
            "binder_weight": int(round(binder_weight)),
            "binder_items": binder_items,
            "inclusions": processed_inclusions,
            "additive_items": processed_additives,
            "secondary_lipids": sec_lipids,
            "secondary_liquids": sec_liquids,
            "secondary_binders": sec_binders,
            "thirst_modifier_applied": thirst_mod,
            "maturity_modifier_applied": maturity_mod,
            "required_water_temp_f": round(required_water_temp_f, 1),
            "required_water_temp_c": round((required_water_temp_f - 32) * 5 / 9, 1),
            "substitution_notes": ["Simplified Baker's Math formulation."],
            "wheat_berry_mix": {
                name: int(round(flour_weight * share)) for name, share in berry_shares.items() if share > 0.0
            }
            if active_berries
            else None,
            "structural_warning": None,
            "fat_substitute_label": fat_substitute_label,
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
        """Sub-classes override this to inject custom mathematical validations.
        Base limits to prevent completely broken AI formulas."""
        hyd = max(0.0, min(1.50, hydration))
        f = max(0.0, min(1.20, fat))
        s = max(0.0, min(2.00, sugar))
        if leaven_type == "sourdough":
            l = max(0.0, min(0.60, leaven))
        elif leaven_type == "chemical":
            l = max(0.0, min(0.10, leaven))
        else:
            l = max(0.0, min(0.015, leaven))
        st = max(0.0, min(0.10, salt))
        return hyd, f, s, l, st

    def get_live_timeline_steps(
        self,
        recipe_data: dict,
        estimated_bulk_minutes: int,
        estimated_proof_minutes: int,
        bake_time_min: int,
        mixing_method: str = "stand_mixer",
        **kwargs,
    ) -> list[dict]:
        return [
            {
                "key": "mix",
                "name": "Mix",
                "duration_sec": 300,
                "desc": "Combine ingredients into a cohesive shaggy mass.",
                "is_mix": True,
            },
            {
                "key": "knead",
                "name": "Knead",
                "duration_sec": 600,
                "desc": "Work the dough to develop structural gluten alignment.",
                "is_knead": True,
            },
            {
                "key": "bulk",
                "name": "Bulk Ferment",
                "duration_sec": estimated_bulk_minutes * 60,
                "desc": "Primary fermentation: allow yeast/sourdough to aerate the dough.",
            },
            {
                "key": "proof",
                "name": "Proof",
                "duration_sec": estimated_proof_minutes * 60,
                "desc": "Final proofing: shape and rise in baking pan/mat.",
                "is_proof": True,
            },
            {
                "key": "bake",
                "name": "Bake",
                "duration_sec": bake_time_min * 60,
                "desc": "Oven bake: target internal temp and crisp crust development.",
                "is_bake": True,
            },
        ]
