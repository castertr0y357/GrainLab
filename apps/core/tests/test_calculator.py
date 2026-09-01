import logging
from django.test import TestCase, Client
from django.urls import get_resolver, reverse
from unittest.mock import patch
from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting, WheatBerry, Equipment, BackgroundTask
from apps.core.utils import math as bakers_math
from apps.core.services.calculator.calculation import calculate_final_recipe

logger = logging.getLogger("grainlab.tests")

class RecipeRestructuringAndBakingTests(TestCase):
    """
    Tests the restructured progressive wizard features:
    - Mass-based bake time/temp scaling.
    - Sourdough bulk/proof countdown timer calculations.
    """
    @classmethod
    def setUpTestData(cls):
        cls.category = DoughCategory.objects.create(
            name="Lean & Crusty",
            slug="lean-crusty",
            base_hydration=0.68,
            base_fat=0.0,
            base_sugar=0.0
        )
        cls.form_factor = FormFactor.objects.create(
            name="Standard 9x5 Loaf Pan",
            slug="loaf-pan",
            target_weight=900.0,
            unit_weight=900.0,
            default_count=1,
            bake_temp_f=375,
            bake_time_min=45,
            is_enriched_profile=False
        )

    def test_bake_profile_scaling(self):
        client = Client()
        
        # Test standard weight (900g) -> time should be close to 45 mins, temp 375F
        context = calculate_final_recipe( {
            "dough_category": self.category.slug,
            "form_factor": self.form_factor.slug,
            "texture_score": 50,
            "crumb_score": 50,
            "target_weight": 900.0
        })
        self.assertEqual(context["bake_temp_f"], 375)
        self.assertEqual(context["bake_time_min"], 45)

        # Test scaled up weight (1500g) -> time should be increased, temp should decrease (by 10F)
        context_large = calculate_final_recipe( {
            "dough_category": self.category.slug,
            "form_factor": self.form_factor.slug,
            "texture_score": 50,
            "crumb_score": 50,
            "target_weight": 1500.0
        })
        self.assertLess(context_large["bake_temp_f"], 375)
        self.assertGreater(context_large["bake_time_min"], 45)

    def test_dynamic_fermentation_timers(self):
        client = Client()
        
        # Test yeast leaven (default bulk = 90 mins, proof = 60 mins at ambient)
        context = calculate_final_recipe( {
            "dough_category": self.category.slug,
            "form_factor": self.form_factor.slug,
            "texture_score": 50,
            "crumb_score": 50,
            "leaven_type": "yeast",
            "proofing_environment": "ambient"
        })
        self.assertEqual(context["estimated_bulk_minutes"], 90)
        self.assertEqual(context["estimated_proof_minutes"], 60)

        # Test proofing environment (mat -> 10% faster proofing = 54 mins)
        context_mat = calculate_final_recipe( {
            "dough_category": self.category.slug,
            "form_factor": self.form_factor.slug,
            "texture_score": 50,
            "crumb_score": 50,
            "leaven_type": "yeast",
            "proofing_environment": "mat"
        })
        self.assertEqual(context_mat["estimated_proof_minutes"], 54)

    def test_advanced_substitutions_oils_and_butters(self):
        # 1. Olive Oil (direct 1:1, no hydration offset)
        recipe_olive_oil = bakers_math.calculate_recipe(
            base_hydration=0.68,
            base_fat=0.10,
            base_sugar=0.0,
            target_mass=1000.0,
            substitution={"original": "fat", "substitute": "olive_oil"}
        )
        self.assertEqual(recipe_olive_oil["effective_hydration_pct"], 68.0)
        self.assertEqual(recipe_olive_oil["effective_fat_pct"], 10.0)
        self.assertTrue(recipe_olive_oil["lipid_items"][0]["name"].startswith("Olive Oil"))
        self.assertAlmostEqual(recipe_olive_oil["lipid_items"][0]["weight"], recipe_olive_oil["flour_weight"] * 0.10, delta=1)
        pass

        # 2. Salted Butter (no hydration offset in simplified)
        recipe_salted_butter = bakers_math.calculate_recipe(
            base_hydration=0.68,
            base_fat=0.10,
            base_sugar=0.0,
            target_mass=1000.0,
            substitution={"original": "fat", "substitute": "salted_butter"}
        )
        self.assertEqual(recipe_salted_butter["effective_hydration_pct"], 68.0)
        self.assertTrue(recipe_salted_butter["lipid_items"][0]["name"].startswith("Salted Butter"))
        self.assertAlmostEqual(recipe_salted_butter["lipid_items"][0]["weight"], recipe_salted_butter["flour_weight"] * 0.10, delta=1)
        pass

        # 3. Unsalted Butter (no hydration offset in simplified)
        recipe_unsalted_butter = bakers_math.calculate_recipe(
            base_hydration=0.68,
            base_fat=0.10,
            base_sugar=0.0,
            target_mass=1000.0,
            substitution={"original": "fat", "substitute": "unsalted_butter"}
        )
        self.assertEqual(recipe_unsalted_butter["effective_hydration_pct"], 68.0)
        self.assertTrue(recipe_unsalted_butter["lipid_items"][0]["name"].startswith("Unsalted Butter"))
        self.assertAlmostEqual(recipe_unsalted_butter["lipid_items"][0]["weight"], recipe_unsalted_butter["flour_weight"] * 0.10, delta=1)
        pass

    def test_ajax_calculate_with_advanced_substitution(self):
        client = Client()
        context = calculate_final_recipe( {
            "dough_category": self.category.slug,
            "form_factor": self.form_factor.slug,
            "texture_score": 50,
            "crumb_score": 50,
            "sub_original": "fat",
            "sub_substitute": "olive_oil",
            "editor_mode": "advanced"
        })
        self.assertIn("fat_substitute_label", context["recipe"])
        self.assertTrue(context["recipe"]["lipid_items"][0]["name"].startswith("Olive Oil"))

    def test_countertop_metadata_attributes_output(self):
        client = Client()
        context = calculate_final_recipe( {
            "dough_category": self.category.slug,
            "form_factor": self.form_factor.slug,
            "texture_score": 50,
            "crumb_score": 50,
            "target_weight": 900.0,
            "room_temp": 72,
            "flour_temp": 70
        })
        html = context.get("countertop_steps_json", "")
        self.assertIn('countertop_steps_json', context)
        self.assertIn('bake_temp_f', context)
        self.assertIn('steam_required', context)
        self.assertIn('doneness_temp_f', context)
        self.assertIn('required_water_temp_f', context['recipe'])

    def test_calculate_final_recipe_none_secondary_ingredients(self) -> None:
        """Verifies calculate_final_recipe handles secondary_ingredients with None category values without crashing."""
        context = calculate_final_recipe({
            "dough_category": self.category.slug,
            "form_factor": self.form_factor.slug,
            "texture_score": 50,
            "crumb_score": 50,
            "secondary_ingredients": {
                "lipids": None,
                "liquids": [{"name": "Whole Milk", "category_name": "Liquid Medium"}],
                "binders": None,
                "sweeteners": None,
                "leaveners": None,
            },
            "flavor_inclusions": None,
            "flour_blend": None,
        }, run_ai=False)
        self.assertIn("recipe", context)
        self.assertIsNotNone(context["recipe"])





