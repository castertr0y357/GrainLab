import os
from django.core.management.base import BaseCommand
from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting, WheatBerry, Equipment

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
                "classifier_texture": 20,
                "classifier_crumb": 10,
                "accessibility_definition": "Requires shaping and a brief boiling alkaline bath before baking to develop its characteristic dark, shiny skin.",
                "cultural_anchor": "Traditional Bavarian soft bread, heavily associated with German beer halls and seasonal festivals.",
                "crumb_preview": "Even",
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
                "classifier_texture": 65,
                "classifier_crumb": 35,
                "accessibility_definition": "Fast hot-pan skillet bake. Best cooked in a screaming hot cast-iron skillet to mimic a tandoor oven.",
                "cultural_anchor": "Classic South Asian flatbread, traditionally brushed with ghee and served alongside curries.",
                "crumb_preview": "Balanced",
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
                "classifier_texture": 25,
                "classifier_crumb": 85,
                "accessibility_definition": "No-knead sheet pan bake. Relies on dimpling the dough and drizzling generously with olive oil and coarse sea salt.",
                "cultural_anchor": "Traditional Ligurian flatbread from Northern Italy, seasoned with fresh rosemary and sea salt.",
                "crumb_preview": "Open",
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
                "classifier_texture": 15,
                "classifier_crumb": 15,
                "accessibility_definition": "Requires boiling in a malt-barley water bath before baking to lock in structure and crust shine.",
                "cultural_anchor": "Traditional Jewish bakery bread, famously boiled and baked, originating in Poland.",
                "crumb_preview": "Even",
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

        # 4b. Default Wheat Berries
        self.stdout.write("Seeding default wheat berries...")
        wheat_berries_data = [
            {
                "name": "Hard Red Winter Wheat",
                "protein_content": 13.0,
                "hardness": "hard",
                "moisture_absorption_coef": 1.0,
                "is_active": True,
                "ai_analyzed": True,
                "notes": "Good baseline hard wheat with solid gluten development suitable for general crusty breads."
            },
            {
                "name": "Hard Red Spring Wheat",
                "protein_content": 14.5,
                "hardness": "hard",
                "moisture_absorption_coef": 1.02,
                "is_active": True,
                "ai_analyzed": True,
                "notes": "High protein content, excellent gluten strength, perfect for open crumb and sourdoughs."
            },
            {
                "name": "Soft White Wheat",
                "protein_content": 9.5,
                "hardness": "soft",
                "moisture_absorption_coef": 0.97,
                "is_active": True,
                "ai_analyzed": True,
                "notes": "Low protein, tender gluten. Great for cakes, pastries, biscuits, or softening hard wheat blends."
            },
            {
                "name": "Spelt Wheat (Ancient)",
                "protein_content": 11.5,
                "hardness": "ancient",
                "moisture_absorption_coef": 1.05,
                "is_active": True,
                "ai_analyzed": True,
                "notes": "Highly soluble gluten, ancient variety. Provides a nutty, sweet flavor and a slightly relaxed crumb."
            },
            {
                "name": "Einkorn (Ancient)",
                "protein_content": 12.5,
                "hardness": "ancient",
                "moisture_absorption_coef": 1.04,
                "is_active": False,
                "ai_analyzed": True,
                "notes": "The most ancient cultivated wheat. Weaker gluten structure, high carotenoid pigments (yellow color)."
            }
        ]

        for wb_data in wheat_berries_data:
            wb, created = WheatBerry.objects.update_or_create(
                name=wb_data["name"], defaults=wb_data
            )
            if created:
                self.stdout.write(f"  Created wheat berry: {wb.name}")

        # 4c. Default Equipment
        self.stdout.write("Seeding default equipment...")
        equipment_data = [
            {
                "name": "KitchenAid Professional 600",
                "equipment_type": "mixer",
                "friction_heat_factor": 10.0,
                "ai_analyzed": True,
                "notes": "Planetary stand mixer. High speed mixing can introduce significant heat to dough.",
                "details": {"capacity_grams": 1000, "recommended_speed": "Speed 2"}
            },
            {
                "name": "Ankarsrum Assistant Mixer",
                "equipment_type": "mixer",
                "friction_heat_factor": 6.0,
                "ai_analyzed": True,
                "notes": "Rotating bowl spiral mixer. Low friction design, preserves dough temperature well.",
                "details": {"capacity_grams": 2500, "recommended_speed": "Medium low"}
            },
            {
                "name": "Mockmill 200 Grain Mill",
                "equipment_type": "mill",
                "friction_heat_factor": 0.0,
                "ai_analyzed": True,
                "notes": "Stoneburr grain mill, 200W motor. Fast throughput with minimum heat transfer.",
                "details": {"capacity_grams": 500, "extraction_rate_pct": 100}
            },
            {
                "name": "Hand Kneading (Manual)",
                "equipment_type": "mixer",
                "friction_heat_factor": 2.0,
                "ai_analyzed": True,
                "notes": "Human-powered mixing. Low friction, relies on hand stretches to build structure.",
                "details": {"capacity_grams": 5000}
            }
        ]

        for eq_data in equipment_data:
            eq, created = Equipment.objects.update_or_create(
                name=eq_data["name"], defaults=eq_data
            )
            if created:
                self.stdout.write(f"  Created equipment: {eq.name}")

        # 5. Create default superuser if it doesn't exist
        superuser_username = os.getenv("SUPERUSER_USERNAME")
        superuser_email = os.getenv("SUPERUSER_EMAIL")
        superuser_password = os.getenv("SUPERUSER_PASSWORD")

        if superuser_username and superuser_password:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if not User.objects.filter(username=superuser_username).exists():
                self.stdout.write("Creating default superuser...")
                User.objects.create_superuser(
                    username=superuser_username,
                    email=superuser_email or "",
                    password=superuser_password
                )
                self.stdout.write(f"  Created superuser: {superuser_username}")
            else:
                self.stdout.write(f"  Superuser '{superuser_username}' already exists.")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
