import logging
import uuid

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View

from apps.core.models import (
    Equipment,
    WheatBerry,
)

logger = logging.getLogger("grainlab.views")


class InventoryPageView(View):
    def get(self, request):
        """
        Renders inventory page listing wheat berries and equipment.
        """
        wheat_berries = WheatBerry.objects.all().order_by("name")
        equipment = Equipment.objects.all().order_by("name")
        context = {
            "wheat_berries": wheat_berries,
            "equipment": equipment,
        }
        return render(request, "inventory.html", context)


class AddWheatBerryView(View):
    def post(self, request):
        """
        Creates a new wheat berry record in the inventory.
        """
        name = request.POST.get("name", "").strip()
        protein = float(request.POST.get("protein_content", 12.0) or 12.0)
        hardness = request.POST.get("hardness", "hard")
        absorption = float(request.POST.get("moisture_absorption_coef", 1.0) or 1.0)
        notes = request.POST.get("notes", "").strip()
        is_active = request.POST.get("is_active") in ("on", "true", "True")

        if name:
            WheatBerry.objects.create(
                name=name,
                protein_content=protein,
                hardness=hardness,
                moisture_absorption_coef=absorption,
                notes=notes,
                is_active=is_active,
            )

        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("inventory_page")
        return response


class ToggleWheatBerryActiveView(View):
    def get(self, request: HttpRequest, id: uuid.UUID):
        """
        Toggles the active state of a wheat berry.
        """
        wb = get_object_or_404(WheatBerry, id=id)
        wb.is_active = not wb.is_active
        wb.save()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("inventory_page")
        return response


class DeleteWheatBerryView(View):
    def get(self, request: HttpRequest, id: uuid.UUID):
        """
        Deletes a wheat berry from inventory.
        """
        wb = get_object_or_404(WheatBerry, id=id)
        wb.delete()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("inventory_page")
        return response


class AddEquipmentView(View):
    def post(self, request: HttpRequest):
        """
        Creates a new equipment record in the inventory.
        """
        name = request.POST.get("name", "").strip()
        eq_type = request.POST.get("equipment_type", "other")
        friction = float(request.POST.get("friction_heat_factor", 0.0) or 0.0)
        notes = request.POST.get("notes", "").strip()

        if name:
            Equipment.objects.create(name=name, equipment_type=eq_type, friction_heat_factor=friction, notes=notes)

        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("inventory_page")
        return response


class DeleteEquipmentView(View):
    def get(self, request: HttpRequest, id: uuid.UUID):
        """
        Deletes equipment from inventory.
        """
        eq = get_object_or_404(Equipment, id=id)
        eq.delete()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("inventory_page")
        return response


class EditWheatBerryView(View):
    def post(self, request, id):
        wb = get_object_or_404(WheatBerry, id=id)
        name = request.POST.get("name", "").strip()
        if name:
            wb.name = name
            wb.protein_content = float(request.POST.get("protein_content", 12.0) or 12.0)
            wb.hardness = request.POST.get("hardness", "hard")
            wb.moisture_absorption_coef = float(request.POST.get("moisture_absorption_coef", 1.0) or 1.0)
            wb.notes = request.POST.get("notes", "").strip()
            wb.is_active = request.POST.get("is_active") in ("on", "true", "True")
            wb.save()

        # We can just redirect back to the page since this will be submitted via standard form or htmx
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("inventory_page")
        return response


class EditEquipmentView(View):
    def post(self, request, id):
        eq = get_object_or_404(Equipment, id=id)
        name = request.POST.get("name", "").strip()
        if name:
            eq.name = name
            eq.equipment_type = request.POST.get("equipment_type", "other")
            eq.friction_heat_factor = float(request.POST.get("friction_heat_factor", 0.0) or 0.0)
            eq.notes = request.POST.get("notes", "").strip()
            eq.save()

        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("inventory_page")
        return response
