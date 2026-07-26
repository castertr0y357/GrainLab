from django.shortcuts import render, redirect
from django.views import View
from apps.core.services.calculator_session import get_calculator_state, get_engines_archetypes_json, get_engines_ff_json

class FinalRecipeView(View):
    def get(self, request, category, archetype):
        state = get_calculator_state(request)
        
        if not state.get('active_berries') and category != 'pizza': # Add robust fallback logic later if necessary
            pass
            
        if state.get('selected_master') != category or state.get('preset_slug') != archetype:
            from apps.core.services.calculator_session import update_calculator_state
            update_calculator_state(request, {
                'selected_master': category, 
                'preset_slug': archetype,
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
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"MATH ERROR: {e}")
            context["recipe_compiled"] = False
            context["math_error"] = str(e)
            
        return render(request, 'calculator/final_recipe.html', context)

    def post(self, request, category, archetype):
        action = request.POST.get('action')
        
        if action == 'reset':
            from apps.core.services.calculator_session import clear_calculator_state
            clear_calculator_state(request)
            return redirect('calculator_phase1')
            
        return redirect('calculator_final_recipe', category=category, archetype=archetype)
