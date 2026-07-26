from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from apps.core.models import SavedRecipe
from apps.core.services.calculator_session import get_calculator_state, update_calculator_state
from apps.core.services.calculation import calculate_final_recipe

def save_recipe(request):
    if request.method == "POST":
        state = get_calculator_state(request)
        
        if not state.get('active_berries'):
            return redirect('calculator_phase1')
            
        try:
            recipe_context = calculate_final_recipe(state)
        except Exception:
            recipe_context = {}
            
        category_slug = state.get('selected_master', 'unknown')
        archetype_slug = state.get('preset_slug', 'unknown')
        
        name_prefix = category_slug.replace('-', ' ').title()
        archetype_prefix = archetype_slug.replace('-', ' ').title()
        
        formula = SavedRecipe.objects.create(
            name=f"{archetype_prefix} {name_prefix}",
            category_slug=category_slug,
            archetype_slug=archetype_slug,
            configuration_state=state,
            compiled_data=recipe_context
        )
        
        return redirect('shared_recipe', recipe_id=formula.id)
    return redirect('calculator_phase1')

def shared_recipe(request, recipe_id):
    formula = get_object_or_404(SavedRecipe, id=recipe_id)
    
    context = {
        'formula': formula,
        'state': formula.configuration_state,
        'recipe_compiled': True if formula.compiled_data else False
    }
    context.update(formula.compiled_data)
    
    return render(request, 'calculator/shared_recipe.html', context)

def tweak_recipe(request, recipe_id):
    if request.method == "POST":
        formula = get_object_or_404(SavedRecipe, id=recipe_id)
        
        # Copy the configuration state to the user's current session
        update_calculator_state(request, formula.configuration_state)
        
        # Add a flag to indicate we are tweaking
        # This will be used to hide the "Back" button in Phase 3
        update_calculator_state(request, {'is_tweaking': True})
        
        return redirect('calculator_phase3', category=formula.category_slug, archetype=formula.archetype_slug)
    
    return redirect('shared_recipe', recipe_id=recipe_id)
