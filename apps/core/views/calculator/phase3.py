from django.shortcuts import render, redirect
from django.views import View
from apps.core.services.calculator.session import get_calculator_state, update_calculator_state
from apps.core.services.calculator.session import get_engines_archetypes_json, get_engines_ff_json
from apps.core.models import Equipment, WheatBerry
import json

class Phase3View(View):
    def get(self, request, category, archetype):
        state = get_calculator_state(request)
        
        # Fallback for empty session: if no active_berries, redirect back to Phase 2 to pick grains
        if not state.get('active_berries'):
            return redirect('calculator_phase2', category=category)
            
        if state.get('selected_master') != category or state.get('preset_slug') != archetype:
            update_calculator_state(request, {
                'selected_master': category, 
                'preset_slug': archetype,
                'current_phase': 3
            })
            state = get_calculator_state(request)
            
        context = {
            'berries': WheatBerry.objects.filter(is_active=True), # In case we need it, but the state has active_berries
            'active_berries_json': json.dumps(state.get('active_berries', [])),
            'state': state,
            'secondary_ingredients_json': json.dumps(state.get('secondary_ingredients', {})),
            'flavor_inclusions_json': json.dumps(state.get('flavor_inclusions', [])),
            'engines_archetypes_json': get_engines_archetypes_json(),
            'engines_ff_json': get_engines_ff_json(),
            'mixers': Equipment.objects.filter(equipment_type='mixer').order_by('name'),
            'mills': Equipment.objects.filter(equipment_type='mill').order_by('name'),
        }
        return render(request, 'calculator/phase3.html', context)

    def post(self, request, category, archetype):
        # Process slider states and configuration to transition to phase 4
        
        # Parse JSON fields safely
        try:
            secondary_ingredients = json.loads(request.POST.get('secondary_ingredients', '{}'))
        except json.JSONDecodeError:
            secondary_ingredients = {}
            
        try:
            flavor_inclusions = json.loads(request.POST.get('flavor_inclusions', '[]'))
        except json.JSONDecodeError:
            flavor_inclusions = []
            
        try:
            flour_blend = json.loads(request.POST.get('flour_blend', '{}'))
        except json.JSONDecodeError:
            flour_blend = {}
            
        updates = {
            'current_phase': 4,
            # We would capture the full finalized recipe data here, e.g. hydration, fat, sugar, salt
            'crumb_score': request.POST.get('crumb_score', 50),
            'texture_score': request.POST.get('texture_score', 50),
            'hydration_pct': request.POST.get('hydration_pct', 70),
            'leaven_pct': request.POST.get('leaven_pct', 20),
            'fat_pct': request.POST.get('fat_pct', 0),
            'sugar_pct': request.POST.get('sugar_pct', 0),
            'target_weight': request.POST.get('target_weight', 1000),
            'secondary_ingredients': secondary_ingredients,
            'flavor_inclusions': flavor_inclusions,
            'flour_blend': flour_blend,
            'default_yield_amount': request.POST.get('default_yield_amount', 1),
            'yield_unit': request.POST.get('yield_unit', 'loaf'),
            'is_portionable': request.POST.get('is_portionable', 'false') == 'true',
        }
        
        # Additional processing if any before phase 4 calculations
        
        update_calculator_state(request, updates)
        
        return redirect('calculator_phase4', category=category, archetype=archetype)
