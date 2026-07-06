from grainlab.engines.base_engine import BaseEngine

class FlatEngine(BaseEngine):
    name = "Flatbreads & Griddles Engine"
    slug = "flat"
    target_protein_min = 10.5
    target_protein_max = 12.0
    gluten_behavior = "High Extensibility, Low Elasticity. Dough must roll to millimeter thickness without tearing or snapping back violently."
    flavor_affinity = "Tannin Tolerant (Rustic/Savory). Enhances toasted, nutty conduction-heat surface blistering."
    tannin_sensitive = False
    production_profile = {
        "thermodynamic_focus": "hydration_binding_shock",
        "mechanical_energy_threshold": "moderate_shearing",
        "permissible_action_types": ["knead", "sheet"],
        "environmental_rest_strategy": "gluten_relaxation",
    }

    permissible_form_factors = {
        "heavy-cast-iron-skillet": {
            "name": "Heavy Cast-Iron Skillet / Griddle",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 80.0,
            "base_count": 8,
            "step_increment": 4,
            "unit_label": "disk",
            "unit_label_plural": "disks",
            "bake_temp_f": 500,
            "bake_time_min": 2,
            "steam_required": False,
            "is_enriched_profile": False,
        },
        "high-heat-oven-stone": {
            "name": "High-Heat Oven Baking Stone",
            "tier": "recommended",
            "is_portioned": True,
            "unit_weight": 80.0,
            "base_count": 8,
            "step_increment": 4,
            "unit_label": "disk",
            "unit_label_plural": "disks",
            "bake_temp_f": 500,
            "bake_time_min": 3,
            "steam_required": False,
            "is_enriched_profile": False,
        }
    }

    presets = [
        "Flour Tortillas", "Hand-Slapped Naan", "Pocked Pocket Pita",
        "Roti / Chapati", "Layered Paratha", "Flaky Scallion Pancakes",
        "Lavash Crisp", "Matzo", "Artisan Seed Crackers"
    ]

    def calculate_recipe(self, **kwargs) -> dict:
        recipe = super().calculate_recipe(**kwargs)
        
        # Determine mechanical rolling thickness targets
        preset_slug = kwargs.get("preset_slug", "")
        if "tortilla" in preset_slug.lower() or "roti" in preset_slug.lower() or "chapati" in preset_slug.lower():
            thickness_mm = 1.0
        elif "naan" in preset_slug.lower() or "pita" in preset_slug.lower():
            thickness_mm = 3.0
        elif "cracker" in preset_slug.lower() or "lavash" in preset_slug.lower() or "matzo" in preset_slug.lower():
            thickness_mm = 0.8
        else:
            thickness_mm = 1.5
            
        recipe["mechanical_thickness_mm"] = thickness_mm
        recipe["substitution_notes"] = recipe.get("substitution_notes", []) + [
            f"Mechanical thickness target: Roll dough out to exactly {thickness_mm} mm for proper crisp/puff balance.",
            "High-velocity conduction: Pre-heat griddle/cast-iron skillet to 500°F before loading dough."
        ]
        return recipe

    def get_live_timeline_steps(self, recipe_data: dict, estimated_bulk_minutes: int, estimated_proof_minutes: int, bake_time_min: int, mixing_method: str = "stand_mixer", **kwargs) -> list[dict]:
        mix_min = 4
        # Gluten network relaxation rest window timer to prevent snap-back:
        relax_min = 20
        # Rolling phase:
        roll_min = 10
        # High-velocity conduction flash-bake (120 seconds):
        flash_sec = 120

        return [
            {
                "key": "mix",
                "name": "Flatbread Mix",
                "duration_sec": mix_min * 60,
                "desc": "Combine flour, water, salt, and fat. Mix until a soft, uniform dough ball is achieved.",
                "is_mix": True
            },
            {
                "key": "relax",
                "name": "Gluten Relaxation Rest",
                "duration_sec": relax_min * 60,
                "desc": "Essential relaxation window! Let the dough rest covered. This relaxes the gluten network to prevent dough snap-back during rolling."
            },
            {
                "key": "divide",
                "name": "Portion & Pre-shape",
                "duration_sec": 10 * 60,
                "desc": "Divide the dough into equal portions and roll into smooth balls. Rest balls covered for 10 minutes to relax gluten once more."
            },
            {
                "key": "roll",
                "name": "Mechanical Rolling",
                "duration_sec": roll_min * 60,
                "desc": f"Use a rolling pin to flatten dough portions. Target thickness is {recipe_data.get('mechanical_thickness_mm', 1.5)} mm. Keep rolled doughs covered to prevent skinning."
            },
            {
                "key": "bake",  # Key must match 'bake' so that is_bake properties are flagged or trigger correctly
                "name": "Flash Skillet Sear",
                "duration_sec": flash_sec,  # 120 seconds!
                "desc": "Place dough onto a screaming hot, dry cast-iron skillet/griddle. Flash-sear. Look for ballooning bubbles and dark leopard char spots.",
                "is_bake": True
            },
            {
                "key": "cool",
                "name": "Stack & Steam-Soften",
                "duration_sec": 5 * 60,
                "desc": "Stack cooked flatbreads wrapped in a clean kitchen towel. Residual steam will soften the structure, keeping them pliable."
            }
        ]
