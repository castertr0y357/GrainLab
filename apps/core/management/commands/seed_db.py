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
                "name": "Alkaline Bath",
                "slug": "alkaline-bath",
                "base_hydration": 0.53,
                "base_fat": 0.02,
                "base_sugar": 0.02,
                "base_salt": 0.02,
                "base_yeast": 0.015,
                "base_starter": 0.0,
                "description": "Doughs boiled in an alkaline bath (e.g. baking soda/lye) to develop character skin shine and texture.",
            },
            {
                "name": "Flatbreads & Griddles",
                "slug": "flatbreads-griddles",
                "base_hydration": 0.58,
                "base_fat": 0.05,
                "base_sugar": 0.0,
                "base_salt": 0.02,
                "base_yeast": 0.0,
                "base_starter": 0.0,
                "description": "Flat griddled or quick-baked flatbreads.",
            },
            {
                "name": "Quick Breads & Scones",
                "slug": "quick-breads-scones",
                "base_hydration": 0.60,
                "base_fat": 0.10,
                "base_sugar": 0.15,
                "base_salt": 0.015,
                "base_yeast": 0.0,
                "base_starter": 0.0,
                "description": "Leavened with baking powder or baking soda. Quick breads, biscuits, and scones.",
            },
            {
                "name": "Cakes & Batters",
                "slug": "cakes-batters",
                "base_hydration": 0.90,
                "base_fat": 0.30,
                "base_sugar": 0.40,
                "base_salt": 0.005,
                "base_yeast": 0.0,
                "base_starter": 0.0,
                "description": "High moisture content forming pourable batters or foam-emulsified structures.",
            },
            {
                "name": "Pastry & Lamination",
                "slug": "pastry-lamination",
                "base_hydration": 0.55,
                "base_fat": 0.10,
                "base_sugar": 0.05,
                "base_salt": 0.015,
                "base_yeast": 0.01,
                "base_starter": 0.0,
                "description": "Laminated butter sheets or short pastries (croissants, puff pastry, tart doughs).",
            },
            {
                "name": "Choux Paste",
                "slug": "choux-paste",
                "base_hydration": 0.80,
                "base_fat": 0.40,
                "base_sugar": 0.0,
                "base_salt": 0.01,
                "base_yeast": 0.0,
                "base_starter": 0.0,
                "description": "Cooked flour paste emulsified with eggs for hollow baked pastry shells.",
            },
            {
                "name": "Cookies & Shortbread",
                "slug": "cookies-shortbread",
                "base_hydration": 0.15,
                "base_fat": 0.50,
                "base_sugar": 0.50,
                "base_salt": 0.005,
                "base_yeast": 0.0,
                "base_starter": 0.0,
                "description": "Low-moisture baking with high spread factor and tender chew/snap crumb.",
            },
            {
                "name": "Fried Doughs",
                "slug": "fried-doughs",
                "base_hydration": 0.58,
                "base_fat": 0.05,
                "base_sugar": 0.05,
                "base_salt": 0.015,
                "base_yeast": 0.015,
                "base_starter": 0.0,
                "description": "Yeasted or chemically leavened doughs fried in hot oil.",
            },
            {
                "name": "Fresh Pasta & Noodles",
                "slug": "fresh-pasta-noodles",
                "base_hydration": 0.38,
                "base_fat": 0.0,
                "base_sugar": 0.0,
                "base_salt": 0.0,
                "base_yeast": 0.0,
                "base_starter": 0.0,
                "description": "Dense, compacted, unleavened semolina or wheat noodle dough.",
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

        # Remove old unused categories if present to clean up
        DoughCategory.objects.filter(slug__in=["chemically-leavened", "non-leavened-crisp", "batter-based"]).delete()

        # 2. Form Factors
        form_factors_data = [
            {
                "name": "Standard 9x5 Loaf Pan",
                "slug": "standard-9x5-pan",
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
                "name": "Free-form / Shaped Loaf (Boule)",
                "slug": "freeform-loaf",
                "is_portioned": False,
                "target_weight": 750.0,
                "unit_weight": 750.0,
                "default_count": 1,
                "bake_temp_f": 425,
                "bake_time_min": 35,
                "steam_required": True,
                "is_enriched_profile": False,
            },
            {
                "name": "Portioned Sheet Pan (Buns/Rolls)",
                "slug": "portioned-buns-rolls",
                "is_portioned": True,
                "target_weight": 1080.0,
                "unit_weight": 90.0,
                "default_count": 12,
                "bake_temp_f": 375,
                "bake_time_min": 20,
                "steam_required": False,
                "is_enriched_profile": True,
            },
            {
                "name": "Baguette / Long Loaf",
                "slug": "baguette-long-loaf",
                "is_portioned": True,
                "target_weight": 900.0,
                "unit_weight": 300.0,
                "default_count": 3,
                "bake_temp_f": 450,
                "bake_time_min": 25,
                "steam_required": True,
                "is_enriched_profile": False,
            },
            {
                "name": "Sheet Pan",
                "slug": "sheet-pan",
                "is_portioned": False,
                "target_weight": 800.0,
                "unit_weight": 800.0,
                "default_count": 1,
                "bake_temp_f": 420,
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
            # Lean & Crusty Presets
            {
                "name": "Sourdough Boule",
                "slug": "sourdough-boule",
                "dough_category": categories["lean-crusty"],
                "form_factor": form_factors["freeform-loaf"],
                "hydration_override": 0.72,
                "fat_override": 0.0,
                "sugar_override": 0.0,
                "starter_override": 0.20,
                "flour_type_default": "whole_wheat",
                "flour_maturity_default": "matured",
                "classifier_texture": 10,
                "classifier_crumb": 75,
                "accessibility_definition": "Leavened entirely with wild yeast. Features a crisp, dark blistered crust and open, Custardy interior.",
                "cultural_anchor": "The hallmark of artisanal baking, rooted in traditional French sourdough methods.",
                "crumb_preview": "Open",
            },
            {
                "name": "Baguette",
                "slug": "baguette",
                "dough_category": categories["lean-crusty"],
                "form_factor": form_factors["baguette-long-loaf"],
                "hydration_override": 0.68,
                "fat_override": 0.0,
                "sugar_override": 0.0,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 15,
                "classifier_crumb": 60,
                "accessibility_definition": "Long, thin crusty loaf, scored deeply to expand and form sharp, golden ears.",
                "cultural_anchor": "An iconic symbol of French culinary heritage, legally protected under national baking guidelines.",
                "crumb_preview": "Balanced",
            },
            {
                "name": "Ciabatta",
                "slug": "ciabatta",
                "dough_category": categories["lean-crusty"],
                "form_factor": form_factors["freeform-loaf"],
                "hydration_override": 0.82,
                "fat_override": 0.02,
                "sugar_override": 0.0,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 10,
                "classifier_crumb": 90,
                "accessibility_definition": "Extremely high hydration dough yielding a flat, irregular shape resembling a slipper with giant pockets of air.",
                "cultural_anchor": "Developed in 1982 by a baker in Adria, Italy, to compete with the popularity of French baguettes.",
                "crumb_preview": "Open",
            },
            {
                "name": "French Loaf",
                "slug": "french-loaf",
                "dough_category": categories["lean-crusty"],
                "form_factor": form_factors["standard-9x5-pan"],
                "hydration_override": 0.65,
                "fat_override": 0.02,
                "sugar_override": 0.02,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 35,
                "classifier_crumb": 40,
                "accessibility_definition": "Softer, everyday style crusty white bread baked in a standard pan to optimize slice sizing.",
                "cultural_anchor": "A kitchen staple developed for uniform slicing, combining artisan flavor with sandwich utility.",
                "crumb_preview": "Balanced",
            },
            {
                "name": "Artisan Pizza",
                "slug": "artisan-pizza",
                "dough_category": categories["lean-crusty"],
                "form_factor": form_factors["freeform-loaf"],
                "hydration_override": 0.70,
                "fat_override": 0.03,
                "sugar_override": 0.0,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 20,
                "classifier_crumb": 70,
                "accessibility_definition": "Fermented slow and hot, stretched thin by hand to achieve a charred, puffy Neapolitan-style cornicione.",
                "cultural_anchor": "Deeply tied to Naples, Italy, where the art of pizza making is recognized as UNESCO intangible heritage.",
                "crumb_preview": "Open",
            },
            
            # Enriched & Soft Presets
            {
                "name": "Everyday Sandwich",
                "slug": "everyday-sandwich",
                "dough_category": categories["enriched-soft"],
                "form_factor": form_factors["standard-9x5-pan"],
                "hydration_override": 0.62,
                "fat_override": 0.06,
                "sugar_override": 0.06,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 70,
                "classifier_crumb": 20,
                "accessibility_definition": "Soft, uniform sandwich crumb with low crumbly scatter, structured with mild butter/oil fats and sweet sugar accents.",
                "cultural_anchor": "Standard modern American pan bread, the baseline of household pantry boxes.",
                "crumb_preview": "Even",
            },
            {
                "name": "Brioche",
                "slug": "brioche",
                "dough_category": categories["enriched-soft"],
                "form_factor": form_factors["standard-9x5-pan"],
                "hydration_override": 0.52,
                "fat_override": 0.25,
                "sugar_override": 0.12,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 95,
                "classifier_crumb": 15,
                "accessibility_definition": "Ultra-rich pastry bread loaded with butter and eggs, yielding a tender, paper-thin golden crumb.",
                "cultural_anchor": "Born in Normandy, France, representing the pinnacle of classic French enrichment techniques.",
                "crumb_preview": "Even",
            },
            {
                "name": "Challah",
                "slug": "challah",
                "dough_category": categories["enriched-soft"],
                "form_factor": form_factors["freeform-loaf"],
                "hydration_override": 0.50,
                "fat_override": 0.08,
                "sugar_override": 0.08,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 80,
                "classifier_crumb": 15,
                "accessibility_definition": "Egg-enriched braided loaf, egg-washed to achieve a dark, burnished chestnut shine.",
                "cultural_anchor": "A traditional Jewish bread baked for the Sabbath and holidays, rich with symbolism.",
                "crumb_preview": "Even",
            },
            {
                "name": "Cinnamon Rolls",
                "slug": "cinnamon-rolls",
                "dough_category": categories["enriched-soft"],
                "form_factor": form_factors["sheet-pan"],
                "hydration_override": 0.60,
                "fat_override": 0.12,
                "sugar_override": 0.15,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 90,
                "classifier_crumb": 10,
                "accessibility_definition": "Rolled scroll shapes enclosing butter-cinnamon-sugar layers, glazed warm with cream cheese frosting.",
                "cultural_anchor": "Svenska kanelbullar variants, customized across modern cafes globally.",
                "crumb_preview": "Even",
            },
            {
                "name": "Burger Buns",
                "slug": "burger-buns",
                "dough_category": categories["enriched-soft"],
                "form_factor": form_factors["portioned-buns-rolls"],
                "hydration_override": 0.60,
                "fat_override": 0.08,
                "sugar_override": 0.06,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 85,
                "classifier_crumb": 20,
                "accessibility_definition": "Portioned soft rounds, topped with sesame, engineered to hold up under hot burger juices without breaking.",
                "cultural_anchor": "The ultimate partner to the classic American smash burger.",
                "crumb_preview": "Even",
            },
            
            # Alkaline Bath Presets
            {
                "name": "Pretzel",
                "slug": "pretzel",
                "dough_category": categories["alkaline-bath"],
                "form_factor": form_factors["portioned-buns-rolls"],
                "hydration_override": 0.52,
                "fat_override": 0.03,
                "sugar_override": 0.02,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 20,
                "classifier_crumb": 10,
                "accessibility_definition": "Twisted loop shapes or rolls, dipped in a warm lye/baking-soda bath before baking to develop a signature crusty sheen.",
                "cultural_anchor": "Traditional Bavarian soft bread, heavily associated with German beer halls and seasonal festivals.",
                "crumb_preview": "Even",
            },
            {
                "name": "Bagel",
                "slug": "bagel",
                "dough_category": categories["alkaline-bath"],
                "form_factor": form_factors["portioned-buns-rolls"],
                "hydration_override": 0.55,
                "fat_override": 0.0,
                "sugar_override": 0.02,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 15,
                "classifier_crumb": 15,
                "accessibility_definition": "Boiled in a hot alkaline bath before baking to gelatinize surface starches, locking in crust crunch and chewiness.",
                "cultural_anchor": "Traditional Jewish bakery bread, famously boiled and baked, originating in Poland.",
                "crumb_preview": "Even",
            },
            
            # Flatbreads & Griddles Presets
            {
                "name": "Naan",
                "slug": "naan",
                "dough_category": categories["flatbreads-griddles"],
                "form_factor": form_factors["sheet-pan"],
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
            
            # Quick Breads Presets
            {
                "name": "Southern Buttermilk Biscuits",
                "slug": "biscuits",
                "dough_category": categories["quick-breads-scones"],
                "form_factor": form_factors["portioned-buns-rolls"],
                "hydration_override": 0.60,
                "fat_override": 0.12,
                "sugar_override": 0.0,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 55,
                "classifier_crumb": 30,
                "accessibility_definition": "Tender layered biscuits, leavened chemically, baked hot for high flake growth.",
                "cultural_anchor": "The soul of Southern breakfast cooking.",
                "crumb_preview": "Balanced",
            },

            # Cakes & Batters Presets
            {
                "name": "Yellow Layer Cake",
                "slug": "yellow-cake",
                "dough_category": categories["cakes-batters"],
                "form_factor": form_factors["sheet-pan"],
                "hydration_override": 0.85,
                "fat_override": 0.25,
                "sugar_override": 0.35,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 90,
                "classifier_crumb": 10,
                "accessibility_definition": "Emulsified butter batter baking, soft structure setting rapidly in oven.",
                "cultural_anchor": "Traditional birthday slice standard.",
                "crumb_preview": "Even",
            },

            # Pastry & Lamination Presets
            {
                "name": "Classic Croissants",
                "slug": "croissants",
                "dough_category": categories["pastry-lamination"],
                "form_factor": form_factors["portioned-buns-rolls"],
                "hydration_override": 0.55,
                "fat_override": 0.10,
                "sugar_override": 0.05,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 50,
                "classifier_crumb": 80,
                "accessibility_definition": "Laminated croissant dough sheets with single folds, high steam puffing rise.",
                "cultural_anchor": "The pride of Parisian viennoiserie.",
                "crumb_preview": "Open",
            },

            # Choux Paste Presets
            {
                "name": "Chocolate Éclairs",
                "slug": "eclairs",
                "dough_category": categories["choux-paste"],
                "form_factor": form_factors["portioned-buns-rolls"],
                "hydration_override": 0.80,
                "fat_override": 0.40,
                "sugar_override": 0.0,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 30,
                "classifier_crumb": 90,
                "accessibility_definition": "Pre-gelatinized starch paste, egg-integrated V-stage, hot steam puffing.",
                "cultural_anchor": "High-end French patisserie log shells.",
                "crumb_preview": "Open",
            },

            # Cookies & Shortbread Presets
            {
                "name": "Chewy Chocolate Chip Cookies",
                "slug": "cookies",
                "dough_category": categories["cookies-shortbread"],
                "form_factor": form_factors["portioned-buns-rolls"],
                "hydration_override": 0.15,
                "fat_override": 0.45,
                "sugar_override": 0.50,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 80,
                "classifier_crumb": 5,
                "accessibility_definition": "Low moisture baking with high spread coefficient, chewy center, crisp edges.",
                "cultural_anchor": "The ultimate home-baked classic cookie.",
                "crumb_preview": "Even",
            },

            # Fried Doughs Presets
            {
                "name": "Yeast-Raised Donuts",
                "slug": "donuts",
                "dough_category": categories["fried-doughs"],
                "form_factor": form_factors["portioned-buns-rolls"],
                "hydration_override": 0.58,
                "fat_override": 0.06,
                "sugar_override": 0.06,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 75,
                "classifier_crumb": 25,
                "accessibility_definition": "Yeasted dough fried in hot oil, flipping at intervals to rise light.",
                "cultural_anchor": "The corner donut shop benchmark.",
                "crumb_preview": "Even",
            },

            # Fresh Pasta & Noodles Presets
            {
                "name": "Fresh Egg Tagliatelle",
                "slug": "tagliatelle",
                "dough_category": categories["fresh-pasta-noodles"],
                "form_factor": form_factors["sheet-pan"],
                "hydration_override": 0.38,
                "fat_override": 0.0,
                "sugar_override": 0.0,
                "starter_override": 0.0,
                "flour_type_default": "all_purpose",
                "flour_maturity_default": "matured",
                "classifier_texture": 5,
                "classifier_crumb": 5,
                "accessibility_definition": "Stiff unleavened semolina compacted dough, run through mechanical roller setting passes.",
                "cultural_anchor": "Emilian traditional egg pasta.",
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
                "name": "Hard White Wheat",
                "protein_content": 12.5,
                "hardness": "hard",
                "moisture_absorption_coef": 1.0,
                "is_active": True,
                "ai_analyzed": True,
                "notes": "Mild flavor and light color. Combines the gluten strength of hard red with a sweeter taste profile."
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
                "name": "Kamut (Ancient)",
                "protein_content": 13.5,
                "hardness": "ancient",
                "moisture_absorption_coef": 1.06,
                "is_active": True,
                "ai_analyzed": True,
                "notes": "Rich, buttery flavored ancient khorasan grain. High protein but extensible gluten structures."
            },
            {
                "name": "Einkorn (Ancient)",
                "protein_content": 12.5,
                "hardness": "ancient",
                "moisture_absorption_coef": 1.04,
                "is_active": False,
                "ai_analyzed": True,
                "notes": "The most ancient cultivated wheat. Weaker gluten structure, high carotenoid pigments (yellow color)."
            },
            {
                "name": "Rye (Ancient)",
                "protein_content": 10.0,
                "hardness": "ancient",
                "moisture_absorption_coef": 1.08,
                "is_active": True,
                "ai_analyzed": True,
                "notes": "Distinct earthy flavor with high soluble dietary fiber (pentosans). Very weak gluten strength."
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

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
