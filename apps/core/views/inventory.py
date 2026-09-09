import logging
import uuid

from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View

from apps.core.forms.inventory import EquipmentForm, WheatBerryForm
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
        wheat_berries = WheatBerry.objects.filter(Q(user=request.user) | Q(user__isnull=True)).order_by("name")
        equipment = Equipment.objects.filter(Q(user=request.user) | Q(user__isnull=True)).order_by("name")
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
        form = WheatBerryForm(request.POST)
        if form.is_valid():
            wb = form.save(commit=False)
            wb.user = request.user
            wb.save()
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse("inventory_page")
            return response
        return HttpResponse(f"<div class='error-box' style='color:red;'>{form.errors.as_text()}</div>", status=400)


class ToggleWheatBerryActiveView(View):
    def get(self, request: HttpRequest, id: uuid.UUID):
        """
        Toggles the active state of a wheat berry.
        """
        wb = get_object_or_404(WheatBerry, id=id)
        if wb.user and wb.user != request.user:
            return HttpResponse("Unauthorized", status=403)
        wb.is_active = not wb.is_active
        wb.save()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("inventory_page")
        return response


class DeleteWheatBerryView(View):
    def post(self, request: HttpRequest, id: uuid.UUID):
        """
        Deletes a wheat berry from inventory.
        """
        wb = get_object_or_404(WheatBerry, id=id)
        if wb.user and wb.user != request.user:
            return HttpResponse("Unauthorized", status=403)
        wb.delete()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("inventory_page")
        return response


class AddEquipmentView(View):
    def post(self, request: HttpRequest):
        """
        Creates a new equipment record in the inventory.
        """
        form = EquipmentForm(request.POST)
        if form.is_valid():
            eq = form.save(commit=False)
            eq.user = request.user
            eq.save()
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse("inventory_page")
            return response
        return HttpResponse(f"<div class='error-box' style='color:red;'>{form.errors.as_text()}</div>", status=400)


class DeleteEquipmentView(View):
    def post(self, request: HttpRequest, id: uuid.UUID):
        """
        Deletes equipment from inventory.
        """
        eq = get_object_or_404(Equipment, id=id)
        if eq.user and eq.user != request.user:
            return HttpResponse("Unauthorized", status=403)
        eq.delete()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("inventory_page")
        return response


class EditWheatBerryView(View):
    def post(self, request):
        wb_id = request.POST.get("id")
        wb = get_object_or_404(WheatBerry, id=wb_id)
        if wb.user and wb.user != request.user:
            return HttpResponse("Unauthorized", status=403)

        form = WheatBerryForm(request.POST, instance=wb)
        if form.is_valid():
            form.save()
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse("inventory_page")
            return response
        return HttpResponse(f"<div class='error-box' style='color:red;'>{form.errors.as_text()}</div>", status=400)


class EditEquipmentView(View):
    def post(self, request):
        eq_id = request.POST.get("id")
        eq = get_object_or_404(Equipment, id=eq_id)
        if eq.user and eq.user != request.user:
            return HttpResponse("Unauthorized", status=403)

        form = EquipmentForm(request.POST, instance=eq)
        if form.is_valid():
            form.save()
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse("inventory_page")
            return response
        return HttpResponse(f"<div class='error-box' style='color:red;'>{form.errors.as_text()}</div>", status=400)
