import logging

from django.test import Client, TestCase
from django.urls import reverse

from apps.core.models import (
    BackgroundTask,
    Equipment,
    WheatBerry,
)

logger = logging.getLogger("grainlab.tests")


class AuditSecurityQualityTests(TestCase):
    """
    Validates newly added security, reliability, and code quality features
    such as Soft Deletes, Correlation IDs, and Background Task State polling.
    """

    def test_soft_deletes_wheat_berry(self):
        """
        Verify that WheatBerry model utilizes soft deletes.
        """
        wb = WheatBerry.objects.create(name="Soft Delete test Berry", protein_content=13.0, hardness="hard")
        self.assertIsNone(wb.deleted_at)

        # Count should be 1
        self.assertTrue(WheatBerry.objects.filter(id=wb.id).exists())

        # Soft delete
        wb.delete()
        wb = WheatBerry.all_objects.get(id=wb.id)
        self.assertIsNotNone(wb.deleted_at)

        # Default objects manager must filter it out
        self.assertFalse(WheatBerry.objects.filter(id=wb.id).exists())
        # all_objects manager must still find it
        self.assertTrue(WheatBerry.all_objects.filter(id=wb.id).exists())

        # Check dead queryset
        self.assertIn(wb, WheatBerry.all_objects.all().dead())

    def test_soft_deletes_equipment(self):
        """
        Verify that Equipment model utilizes soft deletes.
        """
        eq = Equipment.objects.create(name="Soft Delete test Mixer", equipment_type="mixer", friction_heat_factor=8.0)
        self.assertIsNone(eq.deleted_at)

        # Count should be 1
        self.assertTrue(Equipment.objects.filter(id=eq.id).exists())

        # Soft delete
        eq.delete()
        eq = Equipment.all_objects.get(id=eq.id)
        self.assertIsNotNone(eq.deleted_at)

        # Default objects manager must filter it out
        self.assertFalse(Equipment.objects.filter(id=eq.id).exists())
        # all_objects manager must still find it
        self.assertTrue(Equipment.all_objects.filter(id=eq.id).exists())

    def test_correlation_id_middleware(self):
        """
        Verify that every request generates a unique correlation ID in the header response.
        """
        client = Client()
        response = client.get(reverse("calculator_phase1"))
        self.assertTrue(response.has_header("X-Correlation-ID"))
        correlation_id = response.headers.get("X-Correlation-ID")
        self.assertTrue(len(correlation_id) > 0)

    def test_background_task_creation_and_status(self):
        """
        Verify task status polling view works and outputs appropriate polling HTML templates.
        """
        client = Client()
        task = BackgroundTask.objects.create(status="RUNNING", progress=45)

        # Check polling task status (individual)
        url = reverse("task_status", args=[task.id])
        response = client.get(url)
        self.assertIn("AI Running (45%)", response.content.decode("utf-8"))

        # Check bulk task status
        response_bulk = client.get(url + "?bulk=true")
        self.assertIn("Bulk Analyzing...", response_bulk.content.decode("utf-8"))
        self.assertIn("width: 45%", response_bulk.content.decode("utf-8"))

        # Check completed status (redirects to inventory)
        task.status = "SUCCESS"
        task.save()
        response_completed = client.get(url)
        self.assertEqual(response_completed.headers.get("HX-Redirect"), reverse("inventory_page"))
