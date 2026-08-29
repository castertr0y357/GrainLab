from django.shortcuts import render, redirect
from django.views import View
import json
from apps.core.models import WheatBerry, DoughCategory
from apps.core.services.calculator.session import get_calculator_state, get_engines_archetypes_json, get_engines_ff_json, update_calculator_state, clear_calculator_state
from apps.core.forms.calculator.phase4_forms import Phase4Form

class Phase4View(View):
    def get(self, request, category, archetype):
        state = get_calculator_state(request)
        
        # Fallback for empty session: if no active_berries, redirect back to Phase 2 to pick grains
        if not state.get('active_berries'):
            return redirect('calculator_phase2', category=category)
            
        if state.get('selected_master') != category or state.get('preset_slug') != archetype:
            update_calculator_state(request, {
                'selected_master': category, 
                'preset_slug': archetype,
                'current_phase': 4
            })
            state = get_calculator_state(request)
            
        # Safeguard if state has strings instead of parsed objects
        sec_ing = state.get('secondary_ingredients', {})
        if isinstance(sec_ing, str):
            try: sec_ing = json.loads(sec_ing)
            except: sec_ing = {}
            
        flav_inc = state.get('flavor_inclusions', [])
        if isinstance(flav_inc, str):
            try: flav_inc = json.loads(flav_inc)
            except: flav_inc = []

        context = {
            'berries': WheatBerry.objects.filter(is_active=True), # In case we need it, but the state has active_berries
            'active_berries_json': json.dumps(state.get('active_berries', [])),
            'state': state,
            'secondary_ingredients_json': json.dumps(sec_ing),
            'flavor_inclusions_json': json.dumps(flav_inc),
            'engines_archetypes_json': get_engines_archetypes_json(),
            'engines_ff_json': get_engines_ff_json(),
            'category_name': DoughCategory.objects.get(slug=category).name,
            'process_recommendations_json': json.dumps(state.get('process_recommendations', {})),
        }
        
        # Calculate final recipe and inject into context
        from apps.core.services.calculator.calculation import calculate_final_recipe
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
        form = Phase4Form(request.POST)
        
        if form.is_valid():
            action = form.cleaned_data.get('action')
            
            if action == 'reset':
                clear_calculator_state(request)
                return redirect('calculator_phase1')

            update_calculator_state(request, {
                'texture': form.cleaned_data.get('texture'),
                'crumb': form.cleaned_data.get('crumb'),
                'starter': form.cleaned_data.get('starter'),
                'mixing_method': form.cleaned_data.get('mixing_method'),
                'active_action': form.cleaned_data.get('active_action'),
                'process_recommendations': form.cleaned_data.get('process_recommendations'),
                'flavor_inclusions': form.cleaned_data.get('flavor_inclusions'),
                'secondary_ingredients': form.cleaned_data.get('secondary_ingredients'),
            })
            
        return redirect('calculator_final_recipe', category=category, archetype=archetype)
