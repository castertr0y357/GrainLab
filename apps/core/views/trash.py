from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView

from apps.core.models.inventory import Equipment, WheatBerry
from apps.core.models.recipe import SavedRecipe

TRASH_MODELS = {
    "recipe": SavedRecipe,
    "wheatberry": WheatBerry,
    "equipment": Equipment,
}


class TrashListView(LoginRequiredMixin, TemplateView):
    template_name = "partials/trash_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trash_items = []

        for key, model in TRASH_MODELS.items():
            dead_items = model.all_objects.dead()
            for item in dead_items:
                trash_items.append({"id": item.pk, "type": key, "name": str(item), "deleted_at": item.deleted_at})

        # Sort by most recently deleted first
        trash_items.sort(key=lambda x: x["deleted_at"], reverse=True)
        context["trash_items"] = trash_items
        return context


class TrashRestoreView(LoginRequiredMixin, View):
    def post(self, request, item_type, item_id, *args, **kwargs):
        if item_type not in TRASH_MODELS:
            raise Http404("Invalid model type")

        model = TRASH_MODELS[item_type]
        item = get_object_or_404(model.all_objects, pk=item_id)

        item.deleted_at = None
        item.save()

        response = HttpResponse(status=204)
        response["HX-Trigger"] = "refreshTrash"
        return response


class TrashHardDeleteView(LoginRequiredMixin, View):
    def post(self, request, item_type, item_id, *args, **kwargs):
        if item_type not in TRASH_MODELS:
            raise Http404("Invalid model type")

        model = TRASH_MODELS[item_type]
        # Get from all_objects to include dead items
        item = get_object_or_404(model.all_objects, pk=item_id)

        # Hard delete directly
        item.delete()  # Wait, model.delete() might set deleted_at again.
        # So we should use model.all_objects.filter(pk=item_id).hard_delete()
        model.all_objects.filter(pk=item_id).hard_delete()

        response = HttpResponse(status=204)
        response["HX-Trigger"] = "refreshTrash"
        return response
