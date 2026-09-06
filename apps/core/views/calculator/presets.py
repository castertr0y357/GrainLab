import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.core.models import (
    BreadPreset,
)

logger = logging.getLogger("grainlab.views")


class SearchPresetsView(View):
    def get(self, request):
        """
        Handles debounced preset search queries, returning HTMX results.
        """
        q = request.GET.get("q", "").strip()
        if len(q) < 2:
            return HttpResponse("")

        presets = BreadPreset.objects.filter(name__icontains=q)[:5]
        return render(request, "partials/search_results.html", {"presets": presets})


class LoadPresetView(View):
    def get(self, request, preset_id):
        """
        Loads a selected preset, replacing the parameters panel and trigger recalculation.
        """
        preset = get_object_or_404(BreadPreset, id=preset_id)

        # Update session with preset data
        request.session["calculator_state"] = {
            "selected_master": preset.dough_category.slug,
            "preset_slug": preset.slug,
            "form_factor": preset.form_factor.slug,
            "texture_score": preset.classifier_texture,
            "crumb_score": preset.classifier_crumb,
            "grain_type": preset.flour_type_default,
            "flour_maturity": preset.flour_maturity_default,
        }

        return redirect("calculator_phase2", category=preset.dough_category.slug)
