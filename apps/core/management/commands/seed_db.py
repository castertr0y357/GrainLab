from django.core.management.base import BaseCommand
from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting

class Command(BaseCommand):
    help = "Seeds initial dough categories, form factors, presets, and default system settings."

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        # 1. Dough Categories
        categories_data = [
            {
                "name": "Lean & Crusty",
                "slug": "lean-crusty",
                "base_hydration": 0.68,
                "base_fat": 0.0,
                "base_sugar": 0.0,
                "base_salt": 0.02,
                "base_yeast": 0.015,
                "base_starter": 0.0,
                "description": "Crispy crust and airy interior. Standard sourdough or country bread style.",
            },
            {
                "name": "Enriched & Soft",
                "slug": "enriched-soft",
                "base_hydration": 0.62,
                "base_fat": 0.08,
                "base_sugar": 0.08,
                "base_salt": 0.02,
                "base_yeast": 0.015,
                "base_starter": 0.0,
                "description": "Soft crumb enriched with butter, oil, eggs, or milk. Sandwich bread, buns, or brioche style.",
            },
            {
                "name": "Chemically Leavened",
                "slug": "chemically-leavened",
                "base_hydration": 0.60,
                "base_fat": 0.10,
                "base_sugar": 0.15,
                "base_salt": 0.015,
                "base_yeast": 0.0,
                "base_starter": 0.0,
                "description": "Leavened with baking powder or baking soda. Quick breads, biscuits, and scones.",
            },
            {
                "name": "Batter-Based",
                "slug": "batter-based",
                "base_hydration": 0.85,
                "base_fat": 0.15,
                "base_sugar": 0.20,
                "base_salt": 0.01,
                "base_yeast": 0.0,
                "base_starter": 0.0,
                "description": "High moisture content forming pourable batters. Pancakes, waffles, or muffins.",
            },
            {
                "name": "Non-Leavened / Crisp",
                "slug": "non-leavened-crisp",
                "base_hydration": 0.45,
                "base_fat": 0.05,
                "base_sugar": 0.0,
                "base_salt": 0.02,
                "base_yeast": 0.0,
                "base_starter": 0.0,
                "description": "Dense unleavened doughs designed for thin, crispy, or flat results. Tortillas, crackers, or flatbreads.",
            },
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = DoughCategory.objects.update_or_create(
                slug=cat_data["slug"], defaults=cat_data
            )
            categories[cat.slug] = cat
            if created:
                self.stdout.write(f"  Created dough category: {cat.name}")

        # 2. Form Factors
        form_factors_data = [
            {
                "name": "Standard 9x5 Loaf Pan",
                "slug": "loaf-pan",
                "is_portioned": False,
                "target_weight": 900.0,
                "unit_weight": 900.0,
                "default_count": 1,
                "bake_temp_f": 375,
                "bake_time_min": 45,
                "steam_required": False,
                "is_enriched_profile": False,
            },
            {
                "name": "Portioned Buns / Dinner Rolls",
                "slug": "buns",
                "is_portioned": True,
                "target_weight": 960.0,
                "unit_weight": 80.0,
                "default_count": 12,
                "bake_temp_f": 375,
                "bake_time_min": 20,
                "steam_required": False,
                "is_enriched_profile": True,
            },
            {
                "name": "Bagel Units",
                "slug": "bagel-form",
                "is_portioned": True,
                "target_weight": 880.0,
                "unit_weight": 110.0,
                "default_count": 8,
                "bake_temp_f": 425,
                "bake_time_min": 22,
                "steam_required": True,
                "is_enriched_profile": False,
            },
            {
                "name": "Pretzel Units",
                "slug": "pretzel-form",
                "is_portioned": True,
                "target_weight": 800.0,
                "unit_weight": 100.0,
                "default_count": 8,
                "bake_temp_f": 425,
                "bake_time_min": 16,
                "steam_required": False,
                "is_enriched_profile": False,
            },
            {
                "name": "Naan Flatbreads",
                "slug": "naan-form",
                "is_portioned": True,
                "target_weight": 540.0,
                "unit_weight": 90.0,
                "default_count": 6,
                "bake_temp_f": 500,
                "bake_time_min": 5,
                "steam_required": False,
                "is_enriched_profile": False,
            },
            {
                "name": "Focaccia Sheet Pan",
                "slug": "focaccia-sheet",
                "is_portioned": False,
                "target_weight": 800.0,
                "unit_weight": 800.0,
                "default_count": 1,
                "bake_temp_f": 425,
                "bake_time_min": 25,
                "steam_required": False,
                "is_enriched_profile": False,
            },
        ]

        form_factors = {}
        for ff_data in form_factors_data:
            ff, created = FormFactor.objects.update_or_create(
                slug=ff_data["slug"], defaults=ff_data
            )
            form_factors[ff.slug] = ff
            if created:
                self.stdout.write(f"  Created form factor: {ff.name}")

        # 3. Bread Presets
        presets_data = [
            {
                "name": "Pretzel",
                "slug": "pretzel",
                "dough_category": categories["enriched-soft"],
                "form_factor": form_factors["pretzel-form"],
                "hydration_override": 0.55,
                "fat_override": 0.04,
                "sugar_override": 0.02,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
            },
            {
                "name": "Naan",
                "slug": "naan",
                "dough_category": categories["enriched-soft"],
                "form_factor": form_factors["naan-form"],
                "hydration_override": 0.60,
                "fat_override": 0.05,
                "sugar_override": 0.02,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
            },
            {
                "name": "Focaccia",
                "slug": "focaccia",
                "dough_category": categories["lean-crusty"],
                "form_factor": form_factors["focaccia-sheet"],
                "hydration_override": 0.80,
                "fat_override": 0.06,
                "sugar_override": 0.0,
                "starter_override": 0.0,
                "flour_type_default": "whole_wheat",
                "flour_maturity_default": "matured",
            },
            {
                "name": "Bagel",
                "slug": "bagel",
                "dough_category": categories["lean-crusty"],
                "form_factor": form_factors["bagel-form"],
                "hydration_override": 0.55,
                "fat_override": 0.0,
                "sugar_override": 0.02,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
            },
        ]

        for p_data in presets_data:
            p, created = BreadPreset.objects.update_or_create(
                slug=p_data["slug"], defaults=p_data
            )
            if created:
                self.stdout.write(f"  Created bread preset: {p.name}")

        # 4. System Settings
        settings_defaults = [
            ("ai_enabled", "False"),
            ("ai_api_url", "http://host.docker.internal:11434/v1"),
            ("ai_model_name", "gemma:12b"),
            ("ai_thinking_enabled", "True"),
            ("ai_thinking_effort", "medium"),
        ]

        for key, val in settings_defaults:
            setting, created = SystemSetting.objects.get_or_create(key=key, defaults={"value": val})
            if created:
                self.stdout.write(f"  Created setting: {key} = {val}")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
