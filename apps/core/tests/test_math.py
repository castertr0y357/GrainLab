import logging
from django.test import TestCase, Client
from django.urls import get_resolver, reverse
from unittest.mock import patch
from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting, WheatBerry, Equipment, BackgroundTask
from apps.core.utils import math as bakers_math
from apps.core.services.calculator.calculation import calculate_final_recipe

logger = logging.getLogger("grainlab.tests")

class BakersMathTests(TestCase):
    """
    Tests mathematical precision of the Baker's Math scaling engine
    and the fail-safe grain/maturity modifiers.
    """
    
    def test_bakers_math_scaling_sums_to_target(self):
        """
        Verify that total calculated weight matches target mass exactly.
        """
        recipe = bakers_math.calculate_recipe(
            base_hydration=0.68,
            base_fat=0.04,
            base_sugar=0.02,
            target_mass=1000.0,
            grain_type="all_purpose",
            flour_maturity="matured"
        )
        # Sum individual ingredients
        total_sum = (
            recipe["added_flour"] +
            recipe["added_water"] +
            recipe["salt_weight"] +
            recipe["yeast_weight"] +
            (recipe["lipid_items"][0]["weight"] if recipe["lipid_items"] else 0) +
            recipe["sugar_weight"]
        )
        self.assertAlmostEqual(total_sum, 1000.0, delta=2)

    def test_thirst_modifier_spelt(self):
        """
        Ancient grains like Spelt must inject +0.05 hydration coefficient.
        """
        recipe = bakers_math.calculate_recipe(
            base_hydration=0.60,
            base_fat=0.0,
            base_sugar=0.0,
            target_mass=900.0,
            grain_type="spelt"
        )
        self.assertEqual(recipe["thirst_modifier_applied"], 0.05)
        self.assertEqual(recipe["effective_hydration_pct"], 65.0)

    def test_maturity_dead_zone(self):
        """
        Flour in 1-2 weeks dead zone must apply -0.02 hydration reduction.
        """
        recipe = bakers_math.calculate_recipe(
            base_hydration=0.68,
            base_fat=0.0,
            base_sugar=0.0,
            target_mass=900.0,
            flour_maturity="dead_zone"
        )
        self.assertEqual(recipe["maturity_modifier_applied"], -0.02)
        self.assertEqual(recipe["effective_hydration_pct"], 66.0)

    def test_sourdough_flour_water_balancing(self):
        """
        Verify that starter leavening deconstructs the starter weight
        and subtracts it from primary flour and water.
        """
        recipe = bakers_math.calculate_recipe(
            base_hydration=0.70,
            base_fat=0.0,
            base_sugar=0.0,
            target_mass=1000.0,
            leaven_type="sourdough",
            leaven_pct=0.20
        )
        # Starter is 20% of flour weight. Total ratio = 1 + 0.70 + 0.02 (salt) + 0.20 (starter) = 1.92.
        # Flour weight = 1000 / 1.92 = 520.83.
        # Starter weight = 520.83 * 0.20 = 104.16.
        # Added flour = 520.83 - 52.08 = 468.75.
        # Added water = (520.83 * 0.70) - 52.08 = 364.58 - 52.08 = 312.5.
        self.assertAlmostEqual(recipe["starter_weight"], 104, delta=1)
        self.assertAlmostEqual(recipe["added_flour"], 469, delta=1)
        self.assertAlmostEqual(recipe["added_water"], 313, delta=1)

    def test_whole_milk_chemistry_rebalancing(self):
        """
        Verify that whole milk swap updates liquid label.
        """
        recipe = bakers_math.calculate_recipe(
            base_hydration=0.62,
            base_fat=0.08,
            base_sugar=0.08,
            target_mass=1000.0,
            substitution={"original": "water", "substitute": "whole_milk"}
        )
        self.assertEqual(recipe["effective_fat_pct"], 8.0)
        self.assertEqual(recipe["effective_sugar_pct"], 8.0)
        self.assertTrue(recipe["liquid_items"][0]["name"].startswith("Whole Milk"))

    def test_secondary_ingredients_math(self):
        """
        Verify that secondary ingredients scale correctly under simplified math.
        Note: preset_slug uses a bread engine so cookie-specific fat/hydration
        clamping constraints do not interfere with these assertions.
        """
        recipe_salted = bakers_math.calculate_recipe(
            base_hydration=0.50,
            base_fat=0.20,
            base_sugar=0.10,
            target_mass=1000.0,
            secondary_lipids=[{"name": "Salted Butter", "ratio": 1.0}],
            preset_slug="sandwich_bread"
        )
        self.assertAlmostEqual(recipe_salted["lipid_items"][0]["weight"], 109.0, places=1)

        recipe_buttermilk_egg = bakers_math.calculate_recipe(
            base_hydration=0.60,
            base_fat=0.10,
            base_sugar=0.05,
            target_mass=1000.0,
            secondary_liquids=[{"name": "Buttermilk", "ratio": 1.0}],
            secondary_binders=[{"name": "Whole Eggs", "ratio": 1.0}],
            preset_slug="sandwich_bread"
        )
        self.assertTrue(recipe_buttermilk_egg["binder_items"][0]["weight"] > 0)
        self.assertTrue(recipe_buttermilk_egg["liquid_items"][0]["name"].startswith("Buttermilk"))




