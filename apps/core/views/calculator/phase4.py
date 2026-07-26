from django.shortcuts import render, redirect
from django.views import View
from apps.core.services.calculator_session import get_calculator_state, get_engines_archetypes_json, get_engines_ff_json
class Phase4View(View):
    def get(self, request, category, archetype):
        state = get_calculator_state(request)
        
        # Fallback for empty session: if no active_berries, redirect back to Phase 2 to pick grains
        if not state.get('active_berries'):
            return redirect('calculator_phase2', category=category)
            
        if state.get('selected_master') != category or state.get('preset_slug') != archetype:
            from apps.core.services.calculator_session import update_calculator_state
            update_calculator_state(request, {
                'selected_master': category, 
                'preset_slug': archetype,
                'current_phase': 4
            })
            state = get_calculator_state(request)
            
        context = {
            'state': state,
            'engines_archetypes_json': get_engines_archetypes_json(),
            'engines_ff_json': get_engines_ff_json(),
        }
        
        # Calculate final recipe and inject into context
        from apps.core.services.calculation import calculate_final_recipe
        try:
            recipe_context = calculate_final_recipe(state)
            context.update(recipe_context)
            context["recipe_compiled"] = True
        except Exception as e:
            # If math fails or data is missing, we can still render but show error
            print(f"MATH ERROR: {e}")
            context["recipe_compiled"] = False
            context["math_error"] = str(e)
            
        return render(request, 'calculator/phase4.html', context)

    def post(self, request, category, archetype):
        # Handle form submissions on phase 4, such as saving the finalized recipe,
        # printing, or resetting to start over.
        action = request.POST.get('action')
        
        if action == 'reset':
            from apps.core.services.calculator_session import clear_calculator_state
            clear_calculator_state(request)
            return redirect('calculator_phase1')
            
        from apps.core.services.calculator_session import update_calculator_state
        update_calculator_state(request, {
            'texture': request.POST.get('texture'),
            'crumb': request.POST.get('crumb'),
            'starter': request.POST.get('starter'),
            'mixing_method': request.POST.get('mixing_method'),
            'active_action': request.POST.get('active_action'),
        })
            
        # Redirect to final recipe view
        return redirect('calculator_final_recipe', category=category, archetype=archetype)
