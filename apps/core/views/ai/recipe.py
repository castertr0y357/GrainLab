import logging
import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View

from apps.core.forms.ai.recipe_forms import (
    RecipeDetailsForm, RecipePercentagesForm, GenerateSubstitutesForm,
    ProcessAlternativesForm, ProcessDetailsForm, RecipeTweaksForm, ApplyTweakForm
)
from apps.core.services.ai.recipe_service import (
    process_recipe_details, process_recipe_percentages, process_generate_substitutes,
    process_alternatives, process_details, process_recipe_tweaks, apply_tweak
)

logger = logging.getLogger("grainlab.views")

class AiRecipeDetailsView(View):
    def get(self, request):
        form = RecipeDetailsForm(request.GET)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)
            
        result = process_recipe_details(form.cleaned_data)
        
        if form.cleaned_data.get('stream'):
            return StreamingHttpResponse(result(), content_type='text/event-stream')
            
        if result is None:
            return JsonResponse({'error': 'Failed generating recipe details'}, status=503)
            
        return JsonResponse(result, status=200)

class AiRecipePercentagesView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
            
        form = RecipePercentagesForm(data)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)
            
        result = process_recipe_percentages(form.cleaned_data)
        if result is None:
            return JsonResponse({"error": "Failed to generate percentages"}, status=500)
        return JsonResponse(result, status=200)

class AiGenerateSubstitutesView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
            
        # Incorporate stream from query params
        data['stream'] = request.GET.get("stream", "false").strip().lower() == "true"
            
        form = GenerateSubstitutesForm(data)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)
            
        result = process_generate_substitutes(form.cleaned_data)
        
        if form.cleaned_data.get('stream'):
            return StreamingHttpResponse(result(), content_type='text/event-stream')
            
        if result is None:
            return JsonResponse({'error': 'Failed generating substitutes'}, status=503)
            
        return JsonResponse(result, status=200)

class AiProcessAlternativesView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
            
        data['stream'] = request.GET.get("stream", "false").strip().lower() == "true"
        
        form = ProcessAlternativesForm(data)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)
            
        result = process_alternatives(form.cleaned_data)
        
        if form.cleaned_data.get('stream'):
            return StreamingHttpResponse(result(), content_type='text/event-stream')
            
        if result is None:
            return JsonResponse({'error': 'Failed generating process alternatives'}, status=503)
            
        return JsonResponse(result, status=200)

class AiProcessDetailsView(View):
    def get(self, request):
        form = ProcessDetailsForm(request.GET)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)
            
        result = process_details(form.cleaned_data, request)
        
        if form.cleaned_data.get('stream'):
            return StreamingHttpResponse(result(), content_type='text/event-stream')
            
        if result is None:
            return JsonResponse({'error': 'Failed generating process details'}, status=503)
            
        return JsonResponse(result, status=200)

class AiRecipeTweaksView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
            
        data['stream'] = request.GET.get("stream", "false").strip().lower() == "true"
        
        form = RecipeTweaksForm(data)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)
            
        try:
            result = process_recipe_tweaks(form.cleaned_data)
            
            if form.cleaned_data.get('stream'):
                return StreamingHttpResponse(result(), content_type='text/event-stream')
                
            if result is None:
                return JsonResponse({'error': 'Failed generating recipe tweaks'}, status=503)
                
            return JsonResponse(result, status=200)
        except Exception as e:
            logger.error(f"[AI] - Tweak View Error: {e}")
            return JsonResponse({"error": "Internal server error"}, status=500)

class AiApplyTweakView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
            
        form = ApplyTweakForm(data)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)
            
        try:
            success = apply_tweak(form.cleaned_data, request)
            if not success:
                return JsonResponse({"error": "Failed generating tweak application state"}, status=503)
            return JsonResponse({"status": "success"}, status=200)
        except Exception as e:
            logger.error(f"[AI] - Apply Tweak Error: {e}")
            return JsonResponse({"error": "Internal server error"}, status=500)
