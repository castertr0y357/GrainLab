import logging
import math
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views import View

from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting, WheatBerry, Equipment, BackgroundTask
from apps.core import bakers_math
from apps.core import gemma
from apps.core.views.tasks import run_async_task, ai_analyze_wheat_berry_task, ai_analyze_equipment_task, bulk_ai_analyze_task, redo_ai_analysis_task

logger = logging.getLogger("grainlab.views")
executor = ThreadPoolExecutor(max_workers=2)


class AiRecipeDetailsView(View):
    def get(self, request):
        """
        Returns AI-generated detailed science profile and elevate recipe tips for a selected recipe.
        Accepts: GET ?recipe_slug=<slug>&engine_id=<slug>&active_archetype_id=<slug>&selected_grains=<comma-separated>&category_slug=<slug>
        Returns: JSON { sidebar_science_profile: "...", elevate_recipe: [...] }
        """
        from django.http import JsonResponse
        from apps.core import gemma

        recipe_slug = request.GET.get("recipe_slug", "").strip()
        recipe_name = request.GET.get("recipe_name", "").strip()
        engine_id = request.GET.get("engine_id", "").strip()
        active_archetype_id = request.GET.get("active_archetype_id", "").strip()
        selected_grains = request.GET.get("selected_grains", "").strip()
        category_slug = request.GET.get("category_slug", "").strip()
        mill_type = request.GET.get("mill_type", "").strip()
        is_sifted = request.GET.get("is_sifted", "false").strip().lower() == "true"

        if not recipe_slug:
            return JsonResponse({"error": "recipe_slug is required."}, status=400)

        # Convert grain IDs to actual human-readable names for the LLM
        selected_grains_names = ""
        if selected_grains:
            grain_ids = [g.strip() for g in selected_grains.split(",") if g.strip()]
            parsed_uuids = []
            raw_names = []
            for gid in grain_ids:
                try:
                    parsed_uuids.append(uuid.UUID(gid))
                except ValueError:
                    raw_names.append(gid)
        
            db_grains = WheatBerry.objects.filter(id__in=parsed_uuids)
            db_names = [b.name for b in db_grains]
            all_names = db_names + raw_names
            selected_grains_names = ", ".join(all_names)

        # Sanitize archetype ID if it contains suffixes
        if active_archetype_id:
            for suffix in ["_level", "_l1", "_l2", "_l3", "_v1", "_v2", "_v3", "_alt"]:
                if suffix in active_archetype_id:
                    active_archetype_id = active_archetype_id.split(suffix)[0]

        is_stream = request.GET.get("stream", "false").strip().lower() == "true"
        target = request.GET.get("target", "all").strip().lower()
        if is_stream:
            from django.http import StreamingHttpResponse
            
            def event_stream():
                try:
                    generator = gemma.stream_recipe_details(
                        engine_id=engine_id,
                        active_archetype_id=active_archetype_id,
                        recipe_slug=recipe_slug,
                        recipe_name=recipe_name,
                        selected_grains=selected_grains_names,
                        category_slug=category_slug,
                        mill_type=mill_type,
                        is_sifted=is_sifted,
                        target=target
                    )
                    for item in generator:
                        yield f"data: {json.dumps(item)}\n\n"
                except Exception as e:
                    logger.error(f"[AI] - Recipe Details Stream Error: {e}")
                    yield f"data: {json.dumps({'error': 'Failed streaming recipe details'})}\n\n"
                yield "data: [DONE]\n\n"
                
            return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

        result = gemma.generate_recipe_details(
            engine_id=engine_id,
            active_archetype_id=active_archetype_id,
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            selected_grains=selected_grains_names,
            category_slug=category_slug,
            mill_type=mill_type,
            is_sifted=is_sifted
        )

        if result is None:
            from apps.core.models import SystemSetting
            if SystemSetting.get_val('ai_enabled', 'False') == 'True':
                return JsonResponse({'error': 'Failed generating recipe details'}, status=503)
            result = gemma.get_local_recipe_details(
                recipe_slug=recipe_slug,
                recipe_name=recipe_name,
                engine_id=engine_id,
                active_archetype_id=active_archetype_id,
                selected_grains=selected_grains_names,
                mill_type=mill_type,
                is_sifted=is_sifted
            )
            return JsonResponse(result, status=200)

        return JsonResponse(result, status=200)


class AiRecipePercentagesView(View):
    def post(self, request):
        from django.http import JsonResponse
        from apps.core import gemma
        import json

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        recipe_slug = data.get("recipe_slug", "").strip()
        recipe_name = data.get("recipe_name", "").strip()
        engine_id = data.get("engine_id", "").strip()
        active_archetype_id = data.get("active_archetype_id", "").strip()
        secondary_ingredients = data.get("secondary_ingredients", [])

        if not recipe_slug and not recipe_name:
            return JsonResponse({"error": "recipe_slug or recipe_name is required."}, status=400)

        result = gemma.generate_recipe_percentages(
            engine_id=engine_id,
            active_archetype_id=active_archetype_id,
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            secondary_ingredients=secondary_ingredients
        )

        if result is None:
            return JsonResponse({'error': 'Failed generating recipe percentages'}, status=503)

        return JsonResponse(result, status=200)


class AiGenerateSubstitutesView(View):
    def post(self, request):
        """
        Returns AI-generated substitutes for a specific category.
        Accepts: POST JSON payload with engine_id, active_archetype_id, recipe_slug, recipe_name, selected_grains, target_category, original_recommendation
        Returns: JSON { substitutes: [...] }
        """
        from django.http import JsonResponse
        from apps.core import gemma
        import json

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        recipe_slug = data.get("recipe_slug", "").strip()
        recipe_name = data.get("recipe_name", "").strip()
        engine_id = data.get("engine_id", "").strip()
        active_archetype_id = data.get("active_archetype_id", "").strip()
        selected_grains = data.get("selected_grains", "").strip()
        target_category = data.get("target_category", "").strip()
        original_recommendation = data.get("original_recommendation", {})

        exclude_names = data.get("exclude_names", [])

        if not recipe_slug or not target_category:
            return JsonResponse({"error": "recipe_slug and target_category are required."}, status=400)

        is_stream = request.GET.get("stream", "false").strip().lower() == "true"
        if is_stream:
            from django.http import StreamingHttpResponse
            
            def event_stream():
                try:
                    generator = gemma.stream_generate_substitutes(
                        engine_id=engine_id,
                        active_archetype_id=active_archetype_id,
                        recipe_slug=recipe_slug,
                        recipe_name=recipe_name,
                        selected_grains=selected_grains,
                        target_category=target_category,
                        original_recommendation=original_recommendation,
                        exclude_names=exclude_names
                    )
                    for item in generator:
                        yield f"data: {json.dumps(item)}\n\n"
                except Exception as e:
                    logger.error(f"[AI] - Substitute Stream Error: {e}")
                    yield f"data: {json.dumps({'error': 'Failed streaming substitutes'})}\n\n"
                yield "data: [DONE]\n\n"
                
            return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

        result = gemma.generate_substitutes(
            engine_id=engine_id,
            active_archetype_id=active_archetype_id,
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            selected_grains=selected_grains,
            target_category=target_category,
            original_recommendation=original_recommendation,
            exclude_names=exclude_names
        )

        if result is None:
            return JsonResponse({'error': 'Failed generating substitutes'}, status=503)

        return JsonResponse(result, status=200)

class AiProcessAlternativesView(View):
    def post(self, request):
        from django.http import JsonResponse
        from apps.core import gemma
        import json

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        recipe_slug = data.get("recipe_slug", "").strip()
        recipe_name = data.get("recipe_name", "").strip()
        engine_id = data.get("engine_id", "").strip()
        active_archetype_id = data.get("active_archetype_id", "").strip()
        target_category = data.get("target_category", "").strip()
        original_recommendation = data.get("original_recommendation", {})
        exclude_names = data.get("exclude_names", [])

        if not recipe_slug or not target_category:
            return JsonResponse({"error": "recipe_slug and target_category are required."}, status=400)

        is_stream = request.GET.get("stream", "false").strip().lower() == "true"
        if is_stream:
            from django.http import StreamingHttpResponse
            import logging
            logger = logging.getLogger("grainlab.gemma")
            
            def event_stream():
                try:
                    generator = gemma.stream_process_alternatives(
                        engine_id=engine_id,
                        active_archetype_id=active_archetype_id,
                        recipe_slug=recipe_slug,
                        recipe_name=recipe_name,
                        target_category=target_category,
                        original_recommendation=original_recommendation,
                        exclude_names=exclude_names
                    )
                    for chunk in generator:
                        yield f"data: {json.dumps(chunk)}\n\n"
                except Exception as e:
                    logger.error(f"[AI] - Process Alternatives Stream Error: {e}")
                    yield f"data: {json.dumps({'error': 'Failed streaming process alternatives'})}\n\n"
                yield "data: [DONE]\n\n"
                
            return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

        result = gemma.generate_process_alternatives(
            engine_id=engine_id,
            active_archetype_id=active_archetype_id,
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            target_category=target_category,
            original_recommendation=original_recommendation,
            exclude_names=exclude_names
        )

        if result is None:
            return JsonResponse({'error': 'Failed generating process alternatives'}, status=503)

        return JsonResponse(result, status=200)

class AiProcessDetailsView(View):
    def get(self, request):
        from django.http import JsonResponse
        from apps.core import gemma

        recipe_slug = request.GET.get("recipe_slug", "").strip()
        recipe_name = request.GET.get("recipe_name", "").strip()
        engine_id = request.GET.get("engine_id", "").strip()
        active_archetype_id = request.GET.get("active_archetype_id", "").strip()

        if not recipe_slug:
            return JsonResponse({"error": "recipe_slug is required."}, status=400)

        is_stream = request.GET.get("stream", "false").strip().lower() == "true"
        target = request.GET.get("target", "all").strip().lower()
        if is_stream:
            from django.http import StreamingHttpResponse
            import json
            import logging
            logger = logging.getLogger("grainlab.gemma")
            
            def event_stream():
                try:
                    from apps.core.services.calculator_session import get_calculator_state
                    state = get_calculator_state(request)
                    flavor_inclusions = state.get('flavor_inclusions', [])
                    additives = state.get('secondary_ingredients', {}).get('additives', [])
                    combined_inclusions = list(flavor_inclusions) + list(additives)
                    generator = gemma.stream_process_details(
                        engine_id=engine_id,
                        active_archetype_id=active_archetype_id,
                        recipe_slug=recipe_slug,
                        recipe_name=recipe_name,
                        flavor_inclusions=combined_inclusions,
                        target=target
                    )
                    for item in generator:
                        yield f"data: {json.dumps(item)}\n\n"
                except Exception as e:
                    logger.error(f"[AI] - Process Details Stream Error: {e}")
                    yield f"data: {json.dumps({'error': 'Failed streaming process details'})}\n\n"
                yield "data: [DONE]\n\n"
                
            return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

        from apps.core.services.calculator_session import get_calculator_state
        state = get_calculator_state(request)
        flavor_inclusions = state.get('flavor_inclusions', [])
        additives = state.get('secondary_ingredients', {}).get('additives', [])
        combined_inclusions = list(flavor_inclusions) + list(additives)
        
        result = gemma.generate_process_details(
            engine_id=engine_id,
            active_archetype_id=active_archetype_id,
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            flavor_inclusions=combined_inclusions
        )

        if result is None:
            return JsonResponse({'error': 'Failed generating process details'}, status=503)

        return JsonResponse(result, status=200)

class AiRecipeTweaksView(View):
    def post(self, request):
        """
        Receives current ingredients and returns creative AI tweaks.
        Accepts: POST JSON payload with engine_id, active_archetype_id, recipe_name, current_ingredients, applied_tweaks_history
        Returns: JSON matching the tweak schema
        """
        try:
            data = json.loads(request.body)
            engine_id = data.get("engine_id", "").strip()
            active_archetype_id = data.get("active_archetype_id", "").strip()
            recipe_name = data.get("recipe_name", "").strip()
            current_ingredients = data.get("current_ingredients", [])
            applied_tweaks_history = data.get("applied_tweaks_history", [])

            if not engine_id or not current_ingredients:
                return JsonResponse({"error": "engine_id and current_ingredients are required."}, status=400)

            is_stream = request.GET.get("stream", "false").strip().lower() == "true"
            if is_stream:
                from django.http import StreamingHttpResponse
                from apps.core.gemma.phase4_client import stream_recipe_tweaks
                
                generator = stream_recipe_tweaks(
                    engine_id=engine_id,
                    active_archetype_id=active_archetype_id,
                    recipe_name=recipe_name,
                    current_ingredients=current_ingredients,
                    applied_tweaks_history=applied_tweaks_history
                )
                
                def event_stream():
                    if generator:
                        for chunk in generator:
                            if chunk:
                                yield f"data: {json.dumps({'text': chunk})}\n\n"
                    yield "data: [DONE]\n\n"
                                
                return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

            from apps.core.gemma.phase4_client import generate_recipe_tweaks
            result = generate_recipe_tweaks(
                engine_id=engine_id,
                active_archetype_id=active_archetype_id,
                recipe_name=recipe_name,
                current_ingredients=current_ingredients,
                applied_tweaks_history=applied_tweaks_history
            )

            if result is None:
                return JsonResponse({'error': 'Failed generating recipe tweaks'}, status=503)

            return JsonResponse(result, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"[AI] - Tweak View Error: {e}")
            return JsonResponse({"error": "Internal server error"}, status=500)

class AiApplyTweakView(View):
    def post(self, request):
        """
        Receives a flat list of AI-generated tweak ingredients, categorizes them, 
        calculates percentages, and updates the calculator session state.
        Accepts: POST { "recipe_slug": "...", "engine_id": "...", "active_archetype_id": "...", "recipe_name": "...", "new_ingredients": ["..."] }
        Returns: JSON { "status": "success" }
        """
        import json
        from apps.core.services.calculator_session import get_calculator_state, update_calculator_state
        from apps.core.gemma.phase4_client import generate_tweak_application_state

        try:
            body = json.loads(request.body)
            recipe_slug = body.get("recipe_slug", "").strip()
            engine_id = body.get("engine_id", "").strip()
            active_archetype_id = body.get("active_archetype_id", "").strip()
            recipe_name = body.get("recipe_name", "").strip()
            proposed_modifications = body.get("proposed_modifications", [])
            tweak_title = body.get("tweak_title", "").strip()

            if not proposed_modifications:
                return JsonResponse({"error": "proposed_modifications is required."}, status=400)

            # Get the current state before generating tweak application state
            state = get_calculator_state(request)

            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[AiApplyTweakView] - Info - Proposed modifications for tweak '{tweak_title}': {proposed_modifications}")

            result = generate_tweak_application_state(
                engine_id=engine_id,
                active_archetype_id=active_archetype_id,
                recipe_slug=recipe_slug,
                recipe_name=recipe_name,
                proposed_modifications=proposed_modifications,
                current_state=state
            )

            if not result:
                return JsonResponse({"error": "Failed generating tweak application state"}, status=503)
                
            logger.info(f"[AiApplyTweakView] - Info - Generated tweak state: {result}")
            
            existing_sec = state.get("secondary_ingredients", {})
            new_sec = result.get("secondary_ingredients", {})
            
            for cat_key, items in new_sec.items():
                if cat_key not in existing_sec:
                    existing_sec[cat_key] = []
                # Append items avoiding exact name duplicates
                existing_names = {item.get("name", "") for item in existing_sec[cat_key]}
                for item in items:
                    if item.get("name", "") not in existing_names:
                        existing_sec[cat_key].append(item)
            
            state["secondary_ingredients"] = existing_sec
            
            existing_pct = state.get("applied_tweak_percentages", {})
            new_pct = result.get("percentages", {})
            existing_pct.update(new_pct)
            state["applied_tweak_percentages"] = existing_pct
            
            # Inject bakers_percentage into the ingredients themselves, which is 
            # especially required for 'additives' / 'flavor_inclusions'
            percentages_map = state["applied_tweak_percentages"]
            for cat_key, items in state["secondary_ingredients"].items():
                for item in items:
                    name = item.get("name", "")
                    if name in percentages_map:
                        item["bakers_percentage"] = percentages_map[name]
                        
            # Sync flavor inclusions from additives
            additives = state["secondary_ingredients"].get("additives", [])
            existing_flavor = state.get("flavor_inclusions", [])
            existing_flavor_names = {item.get("name", "") for item in existing_flavor}
            for additive in additives:
                if additive.get("name", "") not in existing_flavor_names:
                    existing_flavor.append(additive)
            state["flavor_inclusions"] = existing_flavor
            
            # Update base parameters if provided
            if "target_fat_pct" in result:
                state["fat_pct"] = result["target_fat_pct"]
            if "target_sugar_pct" in result:
                state["sugar_pct"] = result["target_sugar_pct"]
            if "target_hydration_pct" in result:
                state["hydration_pct"] = result["target_hydration_pct"]
            if "target_leaven_pct" in result:
                state["leaven_pct"] = result["target_leaven_pct"]
            if "target_salt_pct" in result:
                state["salt_pct"] = result["target_salt_pct"]
            if "target_binder_pct" in result:
                state["binder_pct"] = result["target_binder_pct"]
            if "target_mixing_method" in result:
                state["mixing_method"] = result["target_mixing_method"]
            if "target_flour_blend" in result and isinstance(result["target_flour_blend"], dict):
                state["flour_blend"] = result["target_flour_blend"]

            # Save the applied tweak to history so it doesn't get suggested again
            if tweak_title:
                history = state.get("applied_tweaks_history", [])
                applied_title = f"Applied: {tweak_title}"
                if applied_title not in history:
                    history.append(applied_title)
                state["applied_tweaks_history"] = history
            
            update_calculator_state(request, state)

            return JsonResponse({"status": "success"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"[AI] - Apply Tweak Error: {e}")
            return JsonResponse({"error": "Internal server error"}, status=500)
