from django.shortcuts import render, redirect
from django.views import View
from apps.core.models import WheatBerry
from apps.core.services.calculator_session import get_calculator_state, update_calculator_state
from apps.core.services.calculator_session import get_engines_archetypes_json, get_engines_ff_json

class Phase2View(View):
    def get(self, request, category):
        state = get_calculator_state(request)
        if state.get('selected_master') != category:
            update_calculator_state(request, {'selected_master': category, 'current_phase': 2})
            state = get_calculator_state(request)
            
        berries = WheatBerry.objects.filter(is_active=True)
        import json
        berries_data = []
        for b in berries:
            berries_data.append({
                'id': str(b.id),
                'name': b.name,
                'hardness': b.hardness,
                'protein': float(b.protein_content),
                'absorption': float(b.moisture_absorption_coef),
                'selected': False
            })
            
        from apps.core.models import Equipment
        context = {
            'berries': berries,
            'berries_json': json.dumps(berries_data),
            'mills': Equipment.objects.filter(equipment_type='mill'),
            'state': state,
            'engines_archetypes_json': get_engines_archetypes_json(),
            'engines_ff_json': get_engines_ff_json(),
        }
        return render(request, 'calculator/phase2.html', context)

    def post(self, request, category):
        # Process the grain selections from Phase 2 to transition to Phase 3
        # Since this data is complex (list of objects), it will likely be submitted as JSON
        import json
        
        archetype = request.POST.get('active_archetype_id')
        if not archetype:
            return redirect('calculator_phase2', category=category)
        
        try:
            active_berries = json.loads(request.POST.get('active_berries', '[]'))
        except json.JSONDecodeError:
            active_berries = []
            
        updates = {
            'current_phase': 3,
            'active_berries': active_berries,
            'global_ai_enabled': request.POST.get('global_ai_enabled', 'true') == 'true',
            'recipe_name': request.POST.get('recipe_name', ''),
            'secondary_ingredients': request.POST.get('secondary_ingredients', '{}'),
        }
        
        update_calculator_state(request, updates)
        
        return redirect('calculator_phase3', category=category, archetype=archetype)
