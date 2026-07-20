import math
from grainlab.core.shared_math import calculate_yield_mass

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


class BaseEngine:
    name = "Base Engine"
    slug = "base"
    target_protein_min = 11.0
    target_protein_max = 13.0
    gluten_behavior = "Standard gluten development"
    flavor_affinity = "Standard flour profile"
    tannin_sensitive = False
    production_profile = {
        "thermodynamic_focus": "biological_yeast_activity",
        "mechanical_energy_threshold": "high_kneading",
        "permissible_action_types": ["knead"],
        "environmental_rest_strategy": "gas_proofing",
    }
    secondary_ingredients = {}

    def culinary_nuance_directive(self, active_archetype_id: str = None) -> str:
        """
        Dynamically construct a highly specific culinary nuance directive 
        based on the engine's unique parametric attributes and optional active archetype.
        """
        tannin_text = (
            "This engine is extremely tannin sensitive. Bitterness or astringency from whole grain bran "
            "(such as red wheat tannins) will clash aggressively with the sweet, neutral flavors required."
            if self.tannin_sensitive else
            "This engine is tannin tolerant. It welcomes rustic, savory caramelization, lactic/acetic sourness, "
            "and deep whole grain bran expressions."
        )
        actions = ", ".join(self.production_profile.get("permissible_action_types", []))
        
        global_criteria = (
            f"Focus on the unique target chemistry of the {self.name}:\n"
            f"* Gluten & Structural Behavior: {self.gluten_behavior}\n"
            f"* Flavor Affinity & Botanical Compatibility: {self.flavor_affinity} ({tannin_text})\n"
            f"* Required Protein Window: {self.target_protein_min}% to {self.target_protein_max}%\n"
            f"* Production Parameters: Thermodynamic focus is {self.production_profile.get('thermodynamic_focus')}, "
            f"rest strategy is {self.production_profile.get('environmental_rest_strategy')}, and permissible actions include [{actions}]."
        )
        
        if not active_archetype_id:
            return global_criteria

        archetypes = getattr(self, "archetypes", {})
        archetype = archetypes.get(active_archetype_id)
        if not archetype:
            return global_criteria
            
        mechanics = archetype.get("target_archetype_mechanics", {})
        arch_directive = archetype.get("culinary_nuance_directive", "")
        
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

    def calculate_wheat_berry_shares(self, active_berries: list, texture_score: int, crumb_score: int, preset_slug: str = None, preset_name: str = None, flour_blend: dict = None) -> tuple[dict[str, float], float, str | None]:
        if not active_berries:
            return {"House Blend": 1.0}, 1.0, None

        total_berries = len(active_berries)
        shares = {}
        if flour_blend:
            for b in active_berries:
                name = _get_val(b, 'name')
                slug = name.lower().replace(" ", "_").replace("-", "_")
                pct = flour_blend.get(slug, 0.0)
                shares[name] = float(pct) / 100.0
        else:
            shares = {_get_val(b, 'name'): 1.0 / total_berries for b in active_berries}
        
        weighted_absorption = sum(_get_val(b, 'moisture_absorption_coef', 1.0) for b in active_berries) / total_berries
        return shares, weighted_absorption, None

    def get_ai_culinary_directive(self) -> str:
        return ""

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
        **kwargs
    ) -> dict:
        # 1. Apply Simple Hydration Modifiers
        flour_blend = kwargs.get('flour_blend', {})
        if active_berries:
            berry_shares, weighted_absorption, structural_warning = self.calculate_wheat_berry_shares(
                active_berries, texture_score, crumb_score, preset_slug=preset_slug, preset_name=preset_name, flour_blend=flour_blend
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
        sec_lipid = kwargs.get("secondary_lipid") or "none"
        sec_liquid = kwargs.get("secondary_liquid") or "pure_water"
        sec_binder = kwargs.get("secondary_binder") or "none"

        # Apply legacy substitution mapping
        if substitution and substitution.get("original") == "water":
            sub_sub = substitution.get("substitute")
            if sub_sub in ["whole_milk", "almond_milk"]:
                sec_liquid = sub_sub

        if substitution and substitution.get("original") == "fat":
            sub_sub = substitution.get("substitute")
            if sub_sub in ["butter", "salted_butter", "unsalted_butter", "olive_oil", "canola_oil", "vegetable_oil"]:
                sec_lipid = sub_sub
                if sec_lipid == "butter":
                    sec_lipid = "unsalted_butter"

        binder_pct = 0.10 if sec_binder != "none" else 0.0

        # Perform subclass-specific constraints (ceilings / floors)
        effective_hydration, effective_fat, effective_sugar = self.apply_sub_class_constraints(
            effective_hydration, effective_fat, effective_sugar, texture_score, crumb_score
        )

        # 3. Calculate Baker's Math Scaling
        flavor_inclusions = kwargs.get("flavor_inclusions", [])
        inclusion_pct = 0.0
        for inc in flavor_inclusions:
            if isinstance(inc, dict) and "bakers_percentage" in inc:
                try:
                    inclusion_pct += float(inc["bakers_percentage"]) / 100.0
                except (ValueError, TypeError):
                    pass
        
        total_ratios = 1.0 + effective_hydration + effective_fat + effective_sugar + salt_pct + leaven_pct + binder_pct + inclusion_pct
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

        # Re-compute liquid weight based on selection
        liquid_weight = added_water
        liquid_label = "Water"
        if sec_liquid == "whole_milk":
            liquid_label = "Whole Milk"
        elif sec_liquid == "heavy_cream":
            liquid_label = "Heavy Cream"
        elif sec_liquid == "buttermilk":
            liquid_label = "Buttermilk"
        elif sec_liquid == "almond_milk":
            liquid_label = "Almond Milk"

        # Re-compute lipids weight
        added_butter = fat_weight if sec_lipid in ["unsalted_butter", "salted_butter"] else 0.0
        added_oil = fat_weight if sec_lipid not in ["unsalted_butter", "salted_butter"] else 0.0
        fat_substitute_label = sec_lipid.replace("_", " ").title() if sec_lipid != "none" else None

        # Re-compute binders weight
        added_eggs = flour_weight * binder_pct if sec_binder == "whole_eggs" else 0.0
        added_egg_whites = flour_weight * binder_pct if sec_binder == "egg_whites" else 0.0
        added_aquafaba = flour_weight * binder_pct if sec_binder == "aquafaba_vegan" else 0.0

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
                weight = round(flour_weight * pct, 1) if pct > 0 else 0.0
                processed_inclusions.append({
                    "name": name,
                    "weight": weight,
                    "volume_description": vol,
                    "percentage": round(pct * 100, 1)
                })

        return {
            "target_mass": round(target_mass, 1),
            "flour_weight": round(flour_weight, 1),
            "flavor_inclusions": processed_inclusions,
            "water_weight": round(water_weight, 1),
            "effective_hydration_pct": round(effective_hydration * 100, 1),
            "effective_fat_pct": round(effective_fat * 100, 1),
            "effective_sugar_pct": round(effective_sugar * 100, 1),
            "added_flour": round(added_flour, 1),
            "added_water": round(added_water, 1),
            "liquid_label": liquid_label,
            "liquid_weight": round(liquid_weight, 1),
            "sugar_weight": round(sugar_weight, 1),
            "salt_weight": round(salt_weight, 1),
            "yeast_weight": round(yeast_weight, 1),
            "starter_weight": round(starter_weight, 1),
            "added_butter": round(added_butter, 1),
            "added_oil": round(added_oil, 1),
            "added_eggs": round(added_eggs, 1),
            "added_egg_whites": round(added_egg_whites, 1),
            "added_aquafaba": round(added_aquafaba, 1),
            "secondary_lipid": sec_lipid,
            "secondary_liquid": sec_liquid,
            "secondary_binder": sec_binder,
            "thirst_modifier_applied": thirst_mod,
            "maturity_modifier_applied": maturity_mod,
            "required_water_temp_f": round(required_water_temp_f, 1),
            "required_water_temp_c": round((required_water_temp_f - 32) * 5 / 9, 1),
            "substitution_notes": ["Simplified Baker's Math formulation."],
            "wheat_berry_mix": {name: round(flour_weight * share, 1) for name, share in berry_shares.items() if share > 0.0} if active_berries else None,
            "structural_warning": None,
            "fat_substitute_label": fat_substitute_label,
        }

    def apply_sub_class_constraints(self, hydration: float, fat: float, sugar: float, texture_score: int, crumb_score: int) -> tuple[float, float, float]:
        """Sub-classes override this to inject custom mathematical validations."""
        return hydration, fat, sugar

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        return [
            {
                "key": "mix",
                "name": "Mix",
                "duration_sec": 300,
                "desc": "Combine ingredients into a cohesive shaggy mass.",
                "is_mix": True
            },
            {
                "key": "knead",
                "name": "Knead",
                "duration_sec": 600,
                "desc": "Work the dough to develop structural gluten alignment.",
                "is_knead": True
            },
            {
                "key": "bulk",
                "name": "Bulk Ferment",
                "duration_sec": estimated_bulk_minutes * 60,
                "desc": "Primary fermentation: allow yeast/sourdough to aerate the dough."
            },
            {
                "key": "proof",
                "name": "Proof",
                "duration_sec": estimated_proof_minutes * 60,
                "desc": "Final proofing: shape and rise in baking pan/mat.",
                "is_proof": True
            },
            {
                "key": "bake",
                "name": "Bake",
                "duration_sec": bake_time_min * 60,
                "desc": "Oven bake: target internal temp and crisp crust development.",
                "is_bake": True
            }
        ]
