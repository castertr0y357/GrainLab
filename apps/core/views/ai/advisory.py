from django.http import JsonResponse, StreamingHttpResponse
from django.views import View

from apps.core.forms.ai.advisory_forms import GrainAdvisoryForm
from apps.core.services.ai.advisory_service import process_grain_advisory, get_inactive_grain_recommendations

class AiGrainAdvisoryView(View):
    def get(self, request):
        """
        Returns dynamic recommendation and warning details for the requested preset or category.
        """
        # Parse query params, handling multiple alias params
        data = request.GET.dict()
        data["lipid"] = request.GET.get("lipid", "") or request.GET.get("secondary_lipid", "")
        data["liquid"] = request.GET.get("liquid", "") or request.GET.get("secondary_liquid", "")
        data["binder"] = request.GET.get("binder", "") or request.GET.get("secondary_binder", "")
        
        form = GrainAdvisoryForm(data)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)
            
        is_stream, result = process_grain_advisory(form.cleaned_data)
        
        if is_stream:
            return StreamingHttpResponse(result(), content_type="text/event-stream")
            
        if "error" in result:
            return JsonResponse(result, status=503)
            
        return JsonResponse(result, status=200)

# Export the helper for other parts of the system if needed
__all__ = ['AiGrainAdvisoryView', 'get_inactive_grain_recommendations']
