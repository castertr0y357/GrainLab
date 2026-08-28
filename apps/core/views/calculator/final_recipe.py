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
        import json
        try:
            recipe_context = calculate_final_recipe(state)
            context.update(recipe_context)
            context["recipe_compiled"] = True
            
            # Build ingredients list for AI tweaks
            ingredients_list = []
            recipe = recipe_context.get("recipe", {})
            if recipe.get("wheat_berry_mix"):
                ingredients_list.extend(recipe["wheat_berry_mix"].keys())
            else:
                gt = recipe.get("grain_type")
                if gt == "whole_wheat": ingredients_list.append("Whole Wheat Flour")
                elif gt == "spelt": ingredients_list.append("Spelt Flour")
                elif gt == "kamut": ingredients_list.append("Kamut Flour")
                elif gt == "einkorn": ingredients_list.append("Einkorn Flour")
                else: ingredients_list.append("Flour Base")
                
            for item in recipe.get("liquid_items", []): ingredients_list.append(item.get("name", "Liquid"))
            if not recipe.get("liquid_items") and recipe.get("added_water", 0) > 0: ingredients_list.append("Water")
            for item in recipe.get("fat_items", []): ingredients_list.append(item.get("name", "Fat"))
            for item in recipe.get("sugar_items", []): ingredients_list.append(item.get("name", "Sugar"))
            for item in recipe.get("binder_items", []): ingredients_list.append(item.get("name", "Binder"))
            
            if recipe.get("salt_item"): ingredients_list.append(recipe["salt_item"].get("name", "Salt"))
            elif recipe.get("salt", 0) > 0: ingredients_list.append("Fine Sea Salt")
            
            if recipe.get("commercial_yeast_item"): ingredients_list.append(recipe["commercial_yeast_item"].get("name", "Yeast"))
            if recipe.get("starter_levain_item"): ingredients_list.append(recipe["starter_levain_item"].get("name", "Sourdough Starter"))
            
            for item in recipe.get("flavor_inclusions", []):
                if isinstance(item, dict):
                    ingredients_list.append(item.get("name", "Inclusion"))
                elif isinstance(item, str):
                    ingredients_list.append(item)
                    
            context["ingredients_json"] = json.dumps([{"name": ing} for ing in list(dict.fromkeys(ingredients_list))])
            context["applied_tweaks_history_json"] = json.dumps(state.get("applied_tweaks_history", []))
            
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

from django.http import JsonResponse

class FinalRecipeAIView(View):
    def get(self, request, category, archetype):
        from apps.core.services.calculator_session import get_calculator_state
        from apps.core.services.calculation import calculate_final_recipe
        state = get_calculator_state(request)
        if not state:
            state = {
                "selected_master": category,
                "preset_slug": archetype,
                "global_ai_enabled": True
            }
        is_stream = request.GET.get("stream", "false").strip().lower() == "true"
        if is_stream:
            from django.http import StreamingHttpResponse
            import json
            from apps.core.gemma.core_client import stream_final_insights
            
            
            recipe_context = calculate_final_recipe(state, run_ai=False)
            
            generator = stream_final_insights(
                state=state,
                recipe_data=recipe_context.get("recipe", {}),
                countertop_steps_json=recipe_context.get("countertop_steps_json", "[]"),
                bake_temp_f=recipe_context.get("bake_temp_f"),
                bake_time_min=recipe_context.get("bake_time_min"),
                steam_required=recipe_context.get("steam_required")
            )
            
            def event_stream():
                if generator:
                    for chunk in generator:
                        if chunk:
                            yield f"data: {json.dumps(chunk)}\n\n"
                        
            return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

        try:
            recipe_context = calculate_final_recipe(state, run_ai=True)
            response_data = {
                'recipe': recipe_context.get('recipe', {}),
                'sensory_description': recipe_context.get('sensory_description'),
                'pitfalls': recipe_context.get('pitfalls'),
                'bake_temp_f': recipe_context.get('bake_temp_f'),
                'bake_time_min': recipe_context.get('bake_time_min'),
                'estimated_bulk_minutes': recipe_context.get('estimated_bulk_minutes'),
                'estimated_proof_minutes': recipe_context.get('estimated_proof_minutes'),
                'countertop_steps_json': recipe_context.get('countertop_steps_json'),
                'steam_required': recipe_context.get('steam_required'),
                'geometry_evaluation': recipe_context.get('geometry_evaluation'),
            }
            return JsonResponse({'status': 'success', 'data': response_data})
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"AI FETCH ERROR: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
