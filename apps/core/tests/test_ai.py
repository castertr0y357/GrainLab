import logging
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from apps.core.models import (
    DoughCategory,
    WheatBerry,
)

logger = logging.getLogger("grainlab.tests")


class GeometryEvaluationTests(TestCase):
    """
    Tests the engine permissible form factors, geometry advisory client,
    and dynamic target mass calculations.
    """

    def test_hearth_engine_permissible_factors(self):
        from apps.core.engines.hearth_engine import HearthEngine

        engine = HearthEngine()
        pffs = getattr(engine, "permissible_form_factors", {})
        self.assertIn("cast-iron-dutch-oven", pffs)
        self.assertIn("standard-9x5-pan", pffs)

    def test_gemma_client_fallback_advisory(self):
        from apps.core.gemma import get_geometry_advisory

        # Call with dry category 'lean-crusty' and form factor 'standard-9x5-pan'
        res = get_geometry_advisory("custom", "Custom Sourdough", "lean-crusty", "standard-9x5-pan")
        self.assertIn("geometry_evaluation", res)
        ge = res["geometry_evaluation"]
        self.assertEqual(ge["status"], "recommended")
        self.assertEqual(ge["profile_adjustments"]["oven_temp_offset_f"], 0)
        self.assertEqual(ge["profile_adjustments"]["bake_time_offset_m"], 0)


class SidebarInsightTests(TestCase):
    """
    Tests the new Split-Pane Contextual Sidebar Insight view and client logic.
    """

    def test_sidebar_insight_empty_element(self):
        response = self.client.get(reverse("ai_sidebar_insight"))
        data = response.json()
        self.assertIn("labor_roi", data)
        self.assertIn("last_10_percent_analysis", data)
        self.assertEqual(data["labor_roi"], "Low Priority / Minor Textural Return")

    def test_sidebar_insight_valid_element(self):
        response = self.client.get(reverse("ai_sidebar_insight") + "?element=stand_mixer")
        data = response.json()
        self.assertIn("labor_roi", data)
        self.assertIn("last_10_percent_analysis", data)
        self.assertEqual(data["labor_roi"], "Low Priority / Minor Textural Return")
        self.assertIn("planetary friction heat", data["last_10_percent_analysis"].lower())

    def test_sidebar_insight_unknown_element(self):
        response = self.client.get(reverse("ai_sidebar_insight") + "?element=nonexistent_widget")
        data = response.json()
        self.assertIn("labor_roi", data)
        self.assertIn("last_10_percent_analysis", data)
        self.assertEqual(data["labor_roi"], "Low Priority / Minor Textural Return")
        self.assertIn("an objective workspace configuration parameter", data["last_10_percent_analysis"].lower())

    def test_sidebar_insight_fuzzy_grain_matching(self):
        response = self.client.get(
            reverse("ai_sidebar_insight") + "?element=grain_soft_white_wheat&category_slug=lean-crusty"
        )
        data = response.json()
        self.assertEqual(data["labor_roi"], "Low Priority / Dangerous Structural Choice")
        self.assertIn("soft white wheat lacks", data["last_10_percent_analysis"].lower())

    def test_sidebar_insight_out_of_stock_grain_suggestion(self):
        from apps.core.models import WheatBerry

        # Create categories and grains
        category, _ = DoughCategory.objects.get_or_create(
            slug="cookies-shortbread",
            defaults={"name": "Cookies & Shortbread", "base_hydration": 0.20, "base_fat": 0.35, "base_sugar": 0.40},
        )
        soft_white = WheatBerry.objects.create(
            name="Soft White Wheat", protein_content=9.5, hardness="soft", is_active=False
        )
        try:
            response = self.client.get(
                reverse("ai_sidebar_insight") + "?element=stand_mixer&category_slug=cookies-shortbread"
            )
            data = response.json()
            self.assertEqual(data["recommendation_tier"], "recommended")
            self.assertIn("soft white wheat is currently out of stock", data["last_10_percent_analysis"].lower())
        finally:
            soft_white.delete()

    @patch("apps.core.gemma.phase2_client.call_gemma_api")
    def test_sidebar_insight_culinary_sovereignty_override(self, mock_call_gemma):
        import json

        from apps.core.gemma import get_sidebar_insight_ai
        from apps.core.models import WheatBerry

        # Setup fake return for call_gemma_api
        mock_call_gemma.return_value = {
            "recommendation_tier": "sub-optimal",
            "labor_roi_rating": "High Priority",
            "last_10_percent_analysis": "Rye has high pentosans which block gluten.",
            "elevate_recipe": "Blend with 10% rye for gooey cookies.",
        }

        # Create a test wheat berry in db
        rye = WheatBerry.objects.create(name="Rye Wheat Berry", protein_content=8.0, hardness="ancient", is_active=True)

        try:
            res = get_sidebar_insight_ai("grain_rye_wheat_berry", "lean-crusty", "sourdough-boule")

            # Assert call_gemma_api was called
            self.assertTrue(mock_call_gemma.called)
            system_prompt = mock_call_gemma.call_args[0][0]
            user_prompt = json.loads(mock_call_gemma.call_args[0][1])

            # Verify system prompt has the sovereignty override rule
            self.assertIn("[CRITICAL RULE: CULINARY SOVEREIGNTY]", system_prompt)

            # Verify user prompt does NOT contain parametric and factual science profiles
            self.assertNotIn("parametric_profile", user_prompt)
            self.assertNotIn("factual_science_profile", user_prompt)

            self.assertEqual(res["elevate_recipe"], "Blend with 10% rye for gooey cookies.")

        finally:
            rye.delete()


class GenerateVariantsTests(TestCase):
    """
    Tests the polymorphic generate_variants view and its data contract.
    Verifies both valid requests (returns structured generated_variants JSON)
    and invalid requests (400 with error message).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from unittest.mock import patch

        cls.patcher1 = patch("apps.core.gemma.phase3_client.stream_gemma_api")
        cls.patcher2 = patch("apps.core.gemma.phase3_client.call_gemma_api")
        cls.mock_stream = cls.patcher1.start()
        cls.mock_call = cls.patcher2.start()

        # Mock responses
        cls.mock_stream.return_value = [
            {"variant_id": "test_1", "variant_name": "Test 1", "description": "desc"},
            {"variant_id": "test_2", "variant_name": "Test 2", "description": "desc"},
            {"variant_id": "test_3", "variant_name": "Test 3", "description": "desc"},
            {"variant_id": "test_4", "variant_name": "Test 4", "description": "desc"},
            {"variant_id": "test_5", "variant_name": "Test 5", "description": "desc"},
        ]

    @classmethod
    def tearDownClass(cls):
        cls.patcher1.stop()
        cls.patcher2.stop()
        super().tearDownClass()

    def setUp(self) -> None:
        self.client = Client()
        self.wb1 = WheatBerry.objects.create(
            name="Hard Red Spring",
            protein_content=14.5,
            hardness="hard",
            is_active=True,
            moisture_absorption_coef=1.08,
        )
        self.wb2 = WheatBerry.objects.create(
            name="Soft White",
            protein_content=10.0,
            hardness="soft",
            is_active=True,
            moisture_absorption_coef=1.02,
        )

    def tearDown(self) -> None:
        WheatBerry.objects.filter(name__in=["Hard Red Spring", "Soft White"]).delete()

    def test_generate_variants_missing_params_returns_400(self) -> None:
        """Missing engine_id and active_archetype_id must return 400."""
        response = self.client.get("/generate-variants/")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_generate_variants_missing_archetype_returns_400(self) -> None:
        """Missing active_archetype_id alone must return 400."""
        response = self.client.get("/generate-variants/?engine_id=lean-crusty")
        self.assertEqual(response.status_code, 400)

    def test_generate_variants_valid_request_returns_200(self) -> None:
        """Valid request returns 200 with generated_variants list."""
        self.mock_stream.return_value = [
            {"variant_id": f"test_{i}", "variant_name": f"Test {i}", "description": "desc"} for i in range(5)
        ]
        url = (
            f"/generate-variants/"
            f"?engine_id=lean-crusty"
            f"&active_archetype_id=classic_sourdough"
            f"&inventory_ids={self.wb1.id},{self.wb2.id}"
        )
        response = self.client.get(url)
        content = "".join([chunk.decode("utf-8") for chunk in response.streaming_content])
        self.assertIn("data:", content)
        # Parse first data event
        import json

        for line in content.split("\n"):
            if line.startswith("data:") and len(line) > 5 and line[6:].strip() != "{}":
                data = json.loads(line[6:].strip())
                self.assertIn("variant_id", data)
                break

    def test_generate_variants_data_contract(self) -> None:
        """Each variant must include required polymorphic schema keys without details."""
        self.mock_stream.return_value = [
            {"variant_id": f"test_{i}", "variant_name": f"Test {i}", "description": "desc"} for i in range(5)
        ]
        url = "/generate-variants/" "?engine_id=lean-crusty" "&active_archetype_id=classic_sourdough"
        response = self.client.get(url)
        content = "".join([chunk.decode("utf-8") for chunk in response.streaming_content])

        import json

        variants_parsed = 0
        for line in content.split("\n"):
            if line.startswith("data:") and len(line) > 5 and line[6:].strip() != "{}":
                variant = json.loads(line[6:].strip())
                self.assertIn("variant_id", variant, "Missing variant_id key")
                self.assertIn("variant_name", variant, "Missing variant_name key")
                self.assertNotIn("sidebar_science_profile", variant)
                self.assertNotIn("sidebar_ai_insight", variant)
                variants_parsed += 1

        self.assertGreater(variants_parsed, 0, "Must return at least 1 variant")

    def test_generate_variants_cookie_engine(self) -> None:
        """Cookie engine archetypes must produce valid variants."""
        self.mock_stream.return_value = [
            {"variant_id": f"test_{i}", "variant_name": f"Test {i}", "description": "desc"} for i in range(5)
        ]
        url = "/generate-variants/" "?engine_id=cookies-pastries" "&active_archetype_id=drop_cookie"
        response = self.client.get(url)
        content = "".join([chunk.decode("utf-8") for chunk in response.streaming_content])
        self.assertIn("data:", content)

    def test_generate_variants_with_creativity_level(self) -> None:
        """Verifies generate_variants handles creativity_level parameters and returns correct alt variants."""
        self.mock_stream.return_value = [
            {"variant_id": f"test_{i}", "variant_name": f"Test {i}", "description": "desc"} for i in range(5)
        ]
        url = "/generate-variants/?engine_id=lean-crusty&active_archetype_id=hearth_level1_concept&creativity_level=1"
        response = self.client.get(url)
        content = "".join([chunk.decode("utf-8") for chunk in response.streaming_content])
        import json

        variants = []
        for line in content.split("\n"):
            if line.startswith("data:") and len(line) > 5 and line[6:].strip() != "{}":
                variants.append(json.loads(line[6:].strip()))
        self.assertEqual(len(variants), 5)

    def test_ai_recipe_details_valid(self) -> None:
        """Verifies ai_recipe_details endpoint returns flavor description and technical science profile."""
        url = "/ai-recipe-details/?recipe_slug=hearth_level1_1&engine_id=lean-crusty&active_archetype_id=classic_sourdough&selected_grains=hard_red_spring_wheat"
        response = self.client.get(url)
        data = response.json()
        self.assertIn("menu_description", data)
        self.assertIn("secondary_ingredients", data)
        self.assertIn("recommended_grain_ids", data)
        self.assertIsInstance(data["recommended_grain_ids"], list)

    def test_ai_recipe_details_missing_params(self) -> None:
        """Verifies ai_recipe_details returns 400 Bad Request if recipe_slug is not provided."""
        url = "/ai-recipe-details/?engine_id=lean-crusty"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_culinary_nuance_directive_method(self) -> None:
        """Verifies converting culinary_nuance_directive from property to a method with archetype stacked directives."""
        from apps.core.engines.cookie_engine import CookieEngine

        engine = CookieEngine()

        # Test default/macro-level return
        macro_text = engine.culinary_nuance_directive()
        self.assertIn("Focus on the unique target chemistry of the Cookies & Shortbread Engine", macro_text)
        self.assertNotIn("[TARGET ARCHETYPE:", macro_text)

        # Test specific archetype stack
        archetype_text = engine.culinary_nuance_directive("drop_cookie")
        self.assertIn("[TARGET ARCHETYPE: Drop Cookie MOLECULAR PHYSICS OBJECTIVES]", archetype_text)
        self.assertIn("[BOTANICAL COMPATIBILITY BOUNDARIES]", archetype_text)

    def test_engines_router_aliases(self) -> None:
        """Verifies plural, singular, and category-slug dictionary lookups in ENGINES."""
        from apps.core.engines import router

        # Singular
        self.assertEqual(router.get_engine_for_preset(None, "cookie").slug, "cookie")
        # Plural
        self.assertEqual(router.get_engine_for_preset(None, "cookies").slug, "cookie")
        # Category slug
        self.assertEqual(router.get_engine_for_preset(None, "cookies-shortbread").slug, "cookie")

    def test_json_healing_resilience(self) -> None:
        """Verifies formatting/delimiting corrections on raw truncated JSON text."""
        import json

        from apps.core.gemma import heal_json_string

        # Truncated trailing commas
        raw1 = '{"shares": {"rye": 10}, "structural_warning": "Too much hydration",}'
        self.assertEqual(
            json.loads(heal_json_string(raw1)), {"shares": {"rye": 10}, "structural_warning": "Too much hydration"}
        )

        # Truncated missing braces
        raw2 = '{"shares": {"rye": 10, "spelt": 5'
        self.assertEqual(json.loads(heal_json_string(raw2)), {"shares": {"rye": 10, "spelt": 5}})


class PromptOptimizationTests(TestCase):
    @patch("apps.core.gemma.phase2_client.call_gemma_api")
    def test_sidebar_insight_temperature_conversion(self, mock_call_gemma):
        from apps.core.gemma.phase2_client import get_sidebar_insight_ai

        mock_call_gemma.return_value = {
            "recommendation_tier": "recommended",
            "labor_roi_rating": "High Priority",
            "last_10_percent_analysis": "Bake it at 350F for 30 minutes. Then increase to 400°F.",
            "elevate_recipe": "Use cold butter at 40F.",
        }

        result = get_sidebar_insight_ai("cookie", "choc", "Soft Wheat")

        self.assertIn("350°F (177°C)", result["last_10_percent_analysis"])
        self.assertIn("400°F (204°C)", result["last_10_percent_analysis"])
        self.assertIn("40°F (4°C)", result["elevate_recipe"])

    @patch("apps.core.gemma.core_client.call_gemma_api")
    def test_generate_tweak_flour_normalization(self, mock_call_gemma):
        from apps.core.gemma.phase4_client import generate_tweak_application_state

        mock_call_gemma.return_value = {
            "secondary_ingredients": {},
            "percentages": {},
            "target_flour_blend": {"soft_white": 3, "spelt": 1},
        }

        result = generate_tweak_application_state("engine", "arch", "slug", "name", [], {})

        blend = result["target_flour_blend"]
        self.assertEqual(blend["soft_white"], 75.0)
        self.assertEqual(blend["spelt"], 25.0)
