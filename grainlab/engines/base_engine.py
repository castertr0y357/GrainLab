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

    def calculate_wheat_berry_shares(self, active_berries: list, texture_score: int, crumb_score: int, preset_slug: str = None, preset_name: str = None) -> tuple[dict[str, float], float, str | None]:
        if not active_berries:
            return {"House Blend": 1.0}, 1.0, None

        # Check if AI is active and query Gemma for optimized blend
        from apps.core.models import SystemSetting
        from django.conf import settings
        
        db_enabled = SystemSetting.get_val("ai_enabled", "False").lower() in ("true", "1", "t")
        env_mock = getattr(settings, "MOCK_MODE", True)
        ai_active = db_enabled and not env_mock

        if ai_active:
            from apps.core import gemma_client
            ai_res = gemma_client.optimize_grain_blend(preset_slug, preset_name, active_berries)
            if ai_res:
                shares, structural_warning = ai_res
                weighted_absorption = 0.0
                for b in active_berries:
                    name = _get_val(b, 'name')
                    share = shares.get(name, 0.0)
                    coef = _get_val(b, 'moisture_absorption_coef', 1.0)
                    weighted_absorption += share * coef
                if weighted_absorption == 0.0:
                    weighted_absorption = 1.0
                return shares, weighted_absorption, structural_warning

        # 1. Classify berries
        ancient_berries = []
        hard_berries = []
        soft_berries = []

        for b in active_berries:
            hardness = _get_val(b, 'hardness', 'hard')
            protein = _get_val(b, 'protein_content', 12.0)
            
            if hardness == 'ancient':
                ancient_berries.append(b)
            elif hardness == 'soft' or (protein < 12.0 and hardness != 'durum' and hardness != 'hard'):
                soft_berries.append(b)
            else:
                hard_berries.append(b)

        # 2. Determine target protein content based on Texture (Softness) and Crumb (Openness)
        target_protein = 11.5 - (texture_score / 100.0 * 2.5) + (crumb_score / 100.0 * 1.5) + 0.5
        target_protein = max(9.0, min(15.0, target_protein))

        # 3. Calculate blend shares
        shares = {}
        
        has_hard = len(hard_berries) > 0
        has_soft = len(soft_berries) > 0
        has_ancient = len(ancient_berries) > 0

        ancient_share = 0.15 if has_ancient else 0.0
        if has_ancient:
            share_per_ancient = ancient_share / len(ancient_berries)
            for b in ancient_berries:
                name = _get_val(b, 'name')
                shares[name] = share_per_ancient

        remaining_share = 1.0 - ancient_share

        if has_hard and has_soft:
            avg_p_hard = sum(_get_val(b, 'protein_content', 12.0) for b in hard_berries) / len(hard_berries)
            avg_p_soft = sum(_get_val(b, 'protein_content', 12.0) for b in soft_berries) / len(soft_berries)
            
            if avg_p_hard != avg_p_soft:
                x = (target_protein - avg_p_soft) / (avg_p_hard - avg_p_soft)
                x = max(0.0, min(1.0, x))
            else:
                x = 0.5
                
            hard_share = x * remaining_share
            soft_share = (1.0 - x) * remaining_share
            
            for b in hard_berries:
                name = _get_val(b, 'name')
                shares[name] = hard_share / len(hard_berries)
            for b in soft_berries:
                name = _get_val(b, 'name')
                shares[name] = soft_share / len(soft_berries)
                
        elif has_hard:
            for b in hard_berries:
                name = _get_val(b, 'name')
                shares[name] = remaining_share / len(hard_berries)
                
        elif has_soft:
            for b in soft_berries:
                name = _get_val(b, 'name')
                shares[name] = remaining_share / len(soft_berries)
                
        elif has_ancient:
            for b in ancient_berries:
                name = _get_val(b, 'name')
                shares[name] = 1.0 / len(ancient_berries)
                
        else:
            return {"House Blend": 1.0}, 1.0, None

        # 4. Enforce structural safety for high-rise presets
        is_high_rise = self.is_high_rise_preset(preset_slug, preset_name)

        structural_warning = None
        if is_high_rise:
            current_hard_share = sum(shares.get(_get_val(b, 'name'), 0.0) for b in hard_berries)
            if current_hard_share < 0.70:
                preset_label = preset_name or "High-Rise Bread"
                structural_warning_grain = "Hard Red Wheat"
                
                if not has_hard:
                    from apps.core.models import WheatBerry
                    strongest_db = WheatBerry.objects.filter(hardness='hard').order_by('-protein_content').first()
                    if strongest_db:
                        injected_grain = strongest_db
                        structural_warning_grain = strongest_db.name
                    else:
                        class MockBerry:
                            name = "Hard Red Winter Wheat"
                            protein_content = 13.0
                            hardness = "hard"
                            moisture_absorption_coef = 1.0
                        injected_grain = MockBerry()
                        structural_warning_grain = injected_grain.name
                    hard_berries.append(injected_grain)
                    if injected_grain not in active_berries:
                        active_berries = list(active_berries) + [injected_grain]
                else:
                    strongest_selected = max(hard_berries, key=lambda b: _get_val(b, 'protein_content', 12.0))
                    structural_warning_grain = _get_val(strongest_selected, 'name')

                structural_warning = f"❌ Structural Hazard: Selected grain blend lacks the gluten strength required for a {preset_label}. Adjusting blend to include 70% {structural_warning_grain} for safety."
                
                shares = {}
                share_per_hard = 0.70 / len(hard_berries)
                for b in hard_berries:
                    name = _get_val(b, 'name')
                    shares[name] = share_per_hard
                
                weak_berries = soft_berries + ancient_berries
                if weak_berries:
                    share_per_weak = 0.30 / len(weak_berries)
                    for b in weak_berries:
                        name = _get_val(b, 'name')
                        shares[name] = share_per_weak
                else:
                    for b in hard_berries:
                        name = _get_val(b, 'name')
                        shares[name] = 1.0 / len(hard_berries)

        # 5. Calculate weighted absorption coefficient
        weighted_absorption = 0.0
        for b in active_berries:
            name = _get_val(b, 'name')
            share = shares.get(name, 0.0)
            coef = _get_val(b, 'moisture_absorption_coef', 1.0)
            weighted_absorption += share * coef

        if weighted_absorption == 0.0:
            weighted_absorption = 1.0

        return shares, weighted_absorption, structural_warning

    def is_high_rise_preset(self, preset_slug: str, preset_name: str) -> bool:
        if preset_slug:
            preset_slug_lower = preset_slug.lower()
            return 'bagel' in preset_slug_lower or 'boule' in preset_slug_lower or 'artisan' in preset_slug_lower
        if preset_name:
            preset_name_lower = preset_name.lower()
            return 'bagel' in preset_name_lower or 'boule' in preset_name_lower or 'artisan' in preset_name_lower
        return False

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
        # 1. Apply Fail-Safe Hydration Modifiers
        structural_warning = None
        if active_berries:
            berry_shares, weighted_absorption, structural_warning = self.calculate_wheat_berry_shares(
                active_berries, texture_score, crumb_score, preset_slug=preset_slug, preset_name=preset_name
            )
            thirst_mod = weighted_absorption - 1.0
        else:
            berry_shares = {}
            thirst_mod = GRAIN_THIRST_MODIFIERS.get(grain_type, 0.0)

        maturity_mod = MATURITY_HYDRATION_MODIFIERS.get(flour_maturity, 0.0)
        
        effective_hydration = base_hydration + thirst_mod + maturity_mod
        effective_fat = base_fat
        effective_sugar = base_sugar

        # 2. Deconstruct and Balance Substitutions
        sub_notes = []
        sub_offsets = {"water": 0.0, "fat": 0.0, "sugar": 0.0}
        
        if substitution:
            original = substitution.get("original")
            substitute = substitution.get("substitute")
            
            if original == "water" and substitute == "whole_milk":
                sub_notes.append("Using Whole Milk instead of Water. Water and fat ratios adjusted to maintain equilibrium.")
                milk_ratio = effective_hydration / 0.87
                fat_excess = milk_ratio * 0.04
                sugar_excess = milk_ratio * 0.05
                effective_fat = max(0.0, effective_fat - fat_excess)
                effective_sugar = max(0.0, effective_sugar - sugar_excess)
                sub_offsets["milk_required"] = milk_ratio

            elif original == "water" and substitute == "almond_milk":
                sub_notes.append("Using Almond Milk instead of Water. Slightly adjusted liquid ratio (+3%) to compensate for milk solids.")
                almond_ratio = effective_hydration / 0.97
                fat_excess = almond_ratio * 0.01
                effective_fat = max(0.0, effective_fat - fat_excess)
                sub_offsets["almond_milk_required"] = almond_ratio

            elif original == "fat" and substitute in ["butter", "salted_butter", "unsalted_butter"]:
                sub_label = "Butter" if substitute == "butter" else ("Salted Butter" if substitute == "salted_butter" else "Unsalted Butter")
                sub_notes.append(f"Using {sub_label} instead of pure Oil. Butter is 80% fat; increased butter weight by 25% and reduced added liquid.")
                butter_ratio = effective_fat / 0.80
                water_excess = butter_ratio * 0.18
                effective_hydration = max(0.40, effective_hydration - water_excess)
                sub_offsets["butter_required"] = butter_ratio

            elif original == "fat" and substitute in ["olive_oil", "canola_oil", "vegetable_oil"]:
                sub_label = "Olive Oil" if substitute == "olive_oil" else ("Canola Oil" if substitute == "canola_oil" else "Vegetable Oil")
                sub_notes.append(f"Using {sub_label} instead of pure Oil. Direct 1:1 fat replacement applied.")
                sub_offsets["oil_required"] = effective_fat

        # Perform sub-class specific math hooks here if needed
        effective_hydration, effective_fat, effective_sugar = self.apply_sub_class_constraints(
            effective_hydration, effective_fat, effective_sugar, texture_score, crumb_score
        )

        # 3. Calculate Baker's Math Scaling
        total_ratios = 1.0 + effective_hydration + effective_fat + effective_sugar + salt_pct + leaven_pct
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

        liquid_label = "Water"
        liquid_weight = added_water
        added_butter = 0.0
        added_oil = fat_weight
        fat_substitute_label = None

        if substitution:
            substitute = substitution.get("substitute")
            if substitute == "whole_milk":
                liquid_label = "Whole Milk"
                liquid_weight = flour_weight * sub_offsets["milk_required"]
                if leaven_type == "sourdough":
                    liquid_weight -= (starter_weight / 2.0)
            elif substitute == "almond_milk":
                liquid_label = "Almond Milk"
                liquid_weight = flour_weight * sub_offsets["almond_milk_required"]
                if leaven_type == "sourdough":
                    liquid_weight -= (starter_weight / 2.0)
            elif substitute in ["butter", "salted_butter", "unsalted_butter"]:
                added_butter = flour_weight * sub_offsets["butter_required"]
                added_oil = 0.0
                fat_substitute_label = "Butter" if substitute == "butter" else ("Salted Butter" if substitute == "salted_butter" else "Unsalted Butter")
            elif substitute in ["olive_oil", "canola_oil", "vegetable_oil"]:
                added_oil = flour_weight * sub_offsets["oil_required"]
                added_butter = 0.0
                fat_substitute_label = "Olive Oil" if substitute == "olive_oil" else ("Canola Oil" if substitute == "canola_oil" else "Vegetable Oil")

        # 5. Desired Dough Temperature (DDT)
        ddt_target_f = 78.0
        if friction_override is not None:
            friction = friction_override
        else:
            friction = FRICTION_FACTORS.get(mixing_method, 10.0)
        required_water_temp_f = (3.0 * ddt_target_f) - room_temp_f - flour_temp_f - friction

        return {
            "target_mass": round(target_mass, 1),
            "flour_weight": round(flour_weight, 1),
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
            "thirst_modifier_applied": thirst_mod,
            "maturity_modifier_applied": maturity_mod,
            "required_water_temp_f": round(required_water_temp_f, 1),
            "required_water_temp_c": round((required_water_temp_f - 32) * 5 / 9, 1),
            "substitution_notes": sub_notes,
            "wheat_berry_mix": {name: round(flour_weight * share, 1) for name, share in berry_shares.items() if share > 0.0} if active_berries else None,
            "structural_warning": structural_warning,
            "fat_substitute_label": fat_substitute_label,
        }

    def apply_sub_class_constraints(self, hydration: float, fat: float, sugar: float, texture_score: int, crumb_score: int) -> tuple[float, float, float]:
        """Sub-classes override this to inject custom mathematical validations."""
        return hydration, fat, sugar

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        """Sub-classes override this to export their unique sequential step arrays."""
        # Generic fallback step array
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
                "key": "autolyse",
                "name": "Rest/Autolyse",
                "duration_sec": 1800,
                "desc": "Let the dough rest to relax gluten and absorb moisture."
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
