from django.http import JsonResponse
from django.views import View

from apps.core.forms.ai.insights_forms import SidebarInsightForm, BatchInsightsForm
from apps.core.services.ai.insights_service import get_sidebar_insight, get_batch_insights

class AiSidebarInsightView(View):
    def get(self, request):
        """
        Returns dynamic labor ROI and critique analysis for the hovered element.
        """
        form = SidebarInsightForm(request.GET)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)
            
        insight = get_sidebar_insight(form.cleaned_data)
        return JsonResponse(insight)

class AiBatchInsightsView(View):
    def get(self, request):
        """
        Returns dynamic labor ROI and critique analysis for multiple elements.
        """
        form = BatchInsightsForm(request.GET)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)
            
        results = get_batch_insights(form.cleaned_data)
        return JsonResponse({"batch_insights": results})
