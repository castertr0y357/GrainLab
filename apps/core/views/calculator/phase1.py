from django.shortcuts import render, redirect
from django.views import View
from apps.core.models import DoughCategory, FormFactor, BreadPreset
from apps.core.services.calculator.session import get_calculator_state, update_calculator_state
from apps.core.engines.router import get_engine_for_preset
import json

class Phase1View(View):
    def get(self, request):
        state = get_calculator_state(request)
        context = {
            'categories': DoughCategory.objects.all(),
            'form_factors': FormFactor.objects.all(),
            'presets': BreadPreset.objects.all(),
            'state': state,
        }
        return render(request, 'calculator/phase1.html', context)

    def post(self, request):
        # Process the form submission to transition to Phase 2
        from apps.core.services.calculator.session import get_calculator_state, clear_calculator_state, update_calculator_state
        state = get_calculator_state(request)
        global_ai_enabled = state.get('global_ai_enabled', True)
        
        # Clear out old state that might be lingering
        clear_calculator_state(request)
        
        selected_master = request.POST.get('selected_master')
        preset_slug = request.POST.get('preset_slug', '')
        preset_name = request.POST.get('preset_name', '')
        
        updates = {
            'current_phase': 2,
            'selected_master': selected_master,
            'preset_slug': preset_slug,
            'preset_name': preset_name,
            'global_ai_enabled': global_ai_enabled,
        }
        
        # If there's an active engine selected (preset + category), save it
        if selected_master:
            try:
                engine = get_engine_for_preset(preset_slug, selected_master)
                if hasattr(engine, 'archetypes'):
                    updates['engines_archetypes'] = {k: v for k, v in engine.archetypes.items()}
                
                if preset_slug:
                    preset = BreadPreset.objects.filter(slug=preset_slug).first()
                    if preset:
                        updates['selected_recipe_id'] = preset.id
            except Exception as e:
                pass
                
        if not selected_master:
            return redirect('calculator_phase1')
            
        update_calculator_state(request, updates)
        
        return redirect('calculator_phase2', category=selected_master)
