from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from apps.core.models import SavedRecipe
from apps.core.services.calculator.session import get_calculator_state, update_calculator_state, get_engines_archetypes_json, get_engines_ff_json
from apps.core.services.calculator.calculation import calculate_final_recipe

def save_recipe(request):
    if request.method == "POST":
        state = get_calculator_state(request)
        
        if not state.get('active_berries'):
            return redirect('calculator_phase1')
            
        try:
            recipe_context = calculate_final_recipe(state)
            
            # Serialize all Django models for JSONField compatibility
            from django.forms.models import model_to_dict
            from django.db.models import Model
            for key, value in list(recipe_context.items()):
                if isinstance(value, Model):
                    recipe_context[key] = model_to_dict(value)
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error calculating final recipe: {e}")
            recipe_context = {}
            
        category_slug = state.get('selected_master', 'unknown')
        archetype_slug = state.get('preset_slug', 'unknown')
        
        cat_data = recipe_context.get('cat', {})
        ff_data = recipe_context.get('ff', {})
        
        c_name = cat_data.get('name') if isinstance(cat_data, dict) else category_slug.replace('-', ' ').replace('_', ' ').title()
        f_name = ff_data.get('name') if isinstance(ff_data, dict) else archetype_slug.replace('-', ' ').replace('_', ' ').title()
        
        fallback_name = f"{f_name} - {c_name}".strip(' -')
        recipe_name = state.get('recipe_name', '').strip()
        final_name = recipe_name if recipe_name else fallback_name
        
        formula = SavedRecipe.objects.create(
            name=final_name,
            category_slug=category_slug,
            archetype_slug=archetype_slug,
            configuration_state=state,
            compiled_data=recipe_context
        )
        
        return redirect('shared_recipe', recipe_id=formula.id)
    return redirect('calculator_phase1')

def shared_recipe(request, recipe_id):
    formula = get_object_or_404(SavedRecipe, id=recipe_id)
    
    import json
    process_recs = formula.configuration_state.get('process_recommendations', {})
    
    context = {
        'formula': formula,
        'state': formula.configuration_state,
        'recipe_compiled': True if formula.compiled_data else False,
        'engines_archetypes_json': get_engines_archetypes_json(),
        'engines_ff_json': get_engines_ff_json(),
        'process_recommendations_json': json.dumps(process_recs)
    }

    context.update(formula.compiled_data)
    
    return render(request, 'calculator/shared_recipe.html', context)
