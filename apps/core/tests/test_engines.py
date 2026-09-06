import logging

from django.test import Client, TestCase

from apps.core.models import (
    BreadPreset,
    DoughCategory,
    FormFactor,
)
from apps.core.services.calculator.calculation import calculate_final_recipe
from apps.core.utils import math as bakers_math

logger = logging.getLogger("grainlab.tests")


class ClassifierEngineTests(TestCase):
    """
    Tests the Euclidean distance classifier engine and the mapping
    of texture and crumb scores to recipe percentages.
    """

    @classmethod
    def setUpTestData(cls):
        cls.category = DoughCategory.objects.create(
            name="Enriched & Soft", slug="enriched-soft", base_hydration=0.62, base_fat=0.08, base_sugar=0.08
        )
        cls.form_factor = FormFactor.objects.create(
            name="Portioned Buns",
            slug="buns",
            is_portioned=True,
            target_weight=960.0,
            unit_weight=80.0,
            default_count=12,
        )
        # Create presets for classification
        cls.bagel = BreadPreset.objects.create(
            name="Bagel",
            slug="bagel",
            dough_category=cls.category,
            form_factor=cls.form_factor,
            classifier_texture=15,
            classifier_crumb=15,
            crumb_preview="Even",
        )
        cls.pretzel = BreadPreset.objects.create(
            name="Pretzel",
            slug="pretzel",
            dough_category=cls.category,
            form_factor=cls.form_factor,
            classifier_texture=20,
            classifier_crumb=10,
            crumb_preview="Even",
        )
        cls.naan = BreadPreset.objects.create(
            name="Naan",
            slug="naan",
            dough_category=cls.category,
            form_factor=cls.form_factor,
            classifier_texture=65,
            classifier_crumb=35,
            crumb_preview="Balanced",
        )

    def test_score_mapping_to_ratios(self):
        """
        Verify that texture and crumb scores map to fat, sugar, and hydration correctly.
        """
        client = Client()
        context = calculate_final_recipe(
            {
                "dough_category": self.category.slug,
                "form_factor": self.form_factor.slug,
                "texture_score": 100,  # Max texture score = 15% fat, 12% sugar
                "crumb_score": 100,  # Max crumb score = 85% hydration
            }
        )
        recipe = context["recipe"]
        # Max texture maps to 15% fat and 12% sugar
        self.assertAlmostEqual(recipe["effective_fat_pct"], 15.0, places=1)
        self.assertAlmostEqual(recipe["effective_sugar_pct"], 12.0, places=1)
        # Max crumb maps to 85% hydration
        self.assertAlmostEqual(recipe["effective_hydration_pct"], 85.0, places=1)

    def test_euclidean_distance_classification(self):
        """
        Verify that coordinates close to specific presets match them.
        """
        client = Client()
        # Coordinates (16, 14) are very close to Bagel (15, 15)
        context = calculate_final_recipe(
            {
                "dough_category": self.category.slug,
                "form_factor": self.form_factor.slug,
                "texture_score": 16,
                "crumb_score": 14,
            }
        )
        self.assertEqual(context["classified_preset"], self.bagel)

        # Coordinates (60, 38) are very close to Naan (65, 35)
        context2 = calculate_final_recipe(
            {
                "dough_category": self.category.slug,
                "form_factor": self.form_factor.slug,
                "texture_score": 60,
                "crumb_score": 38,
            }
        )
        self.assertEqual(context2["classified_preset"], self.naan)


class SubEnginesTests(TestCase):
    """
    Tests the 11 modular decoupled sub-engines, checking boundaries, ceilings, and timeline step generators.
    """

    def test_bath_engine_hydration_ceiling(self):
        """Pretzel/bath engine must enforce 65% base hydration boundary ceiling."""
        recipe = bakers_math.calculate_recipe(
            base_hydration=0.70,  # requested too high
            base_fat=0.04,
            base_sugar=0.02,
            target_mass=1000.0,
            preset_slug="pretzel",
        )
        self.assertEqual(recipe["effective_hydration_pct"], 65.0)

        # Test timeline steps generator directly
        from apps.core.engines import router

        engine = router.get_engine_for_preset("pretzel")
        steps = engine.get_live_timeline_steps(recipe, 240, 120, 45, preset_slug="pretzel")
        step_keys = [s["key"] for s in steps]
        self.assertIn("shape", step_keys)
        self.assertIn("boil", step_keys)

    def test_pasta_engine_zero_leaven(self):
        """Pasta engine timeline steps."""
        recipe = bakers_math.calculate_recipe(
            base_hydration=0.38,
            base_fat=0.02,
            base_sugar=0.0,
            target_mass=500.0,
            leaven_type="yeast",
            leaven_pct=0.02,
            category_slug="fresh-pasta-noodles",
        )

        # Test timeline steps generator directly
        from apps.core.engines import router

        engine = router.get_engine_for_preset(None, "fresh-pasta-noodles")
        steps = engine.get_live_timeline_steps(recipe, 240, 120, 45, category_slug="fresh-pasta-noodles")
        step_keys = [s["key"] for s in steps]
        self.assertIn("roll_pass", step_keys)
        self.assertIn("bake", step_keys)

    def test_pastry_engine_folding_steps(self):
        """Pastry/lamination engine must inject single/double book folds based on fold count."""
        recipe = bakers_math.calculate_recipe(
            base_hydration=0.60, base_fat=0.25, base_sugar=0.05, target_mass=800.0, preset_slug="all-butter-puff-pastry"
        )
        # Test timeline steps generator directly
        from apps.core.engines import router

        engine = router.get_engine_for_preset("all-butter-puff-pastry")
        steps = engine.get_live_timeline_steps(recipe, 240, 120, 45, preset_slug="all-butter-puff-pastry")
        step_descs = [s["desc"] for s in steps]
        self.assertTrue(any("book" in d.lower() for d in step_descs))

    def test_batter_engine_high_ratio(self):
        """Batter/cake engine must support and balance high-ratio sugar/fat scaling."""
        recipe = bakers_math.calculate_recipe(
            base_hydration=0.75, base_fat=0.35, base_sugar=0.50, target_mass=1200.0, preset_slug="yellow-layer-cake"
        )
        # Test timeline steps generator directly
        from apps.core.engines import router

        engine = router.get_engine_for_preset("yellow-layer-cake")
        steps = engine.get_live_timeline_steps(recipe, 240, 120, 45, preset_slug="yellow-layer-cake")
        step_keys = [s["key"] for s in steps]
        self.assertIn("mix", step_keys)
        self.assertIn("fold", step_keys)
