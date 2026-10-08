from django.core.management.base import BaseCommand
from apps.core.engines.router import ENGINES
from apps.core.management.commands.run_qa_recipes import evaluate_recipe
from apps.core.services.ai.recipe_service import process_recipe_details
import json

class Command(BaseCommand):
    def handle(self, *args, **options):
        def test_engine(engine_id, archetype_id, profile):
            engine = ENGINES.get(engine_id)
            if not engine:
                print(f"Engine {engine_id} not found")
                return
            recipe_name = f"{archetype_id} Test"
            recipe_slug = "test-slug"
            try:
                final_recipe_obj = process_recipe_details({
                    "recipe_slug": recipe_slug,
                    "engine_id": engine_id,
                    "recipe_name": recipe_name,
                    "inferred_flavor_profile": profile,
                    "active_archetype_id": archetype_id,
                    "selected_grains": '[{"id": "grain1", "name": "Hard Red Winter Wheat"}]',
                    "active_variation_id": None,
                    "category_slug": "savory",
                    "stream": False
                })
                print(f"Generated for {engine_id} ({archetype_id}):")
                
                timeline = engine.get_live_timeline_steps(
                    recipe_data=final_recipe_obj.get("recipe", {}),
                    estimated_bulk_minutes=120,
                    estimated_proof_minutes=60,
                    bake_time_min=30,
                    preset_slug=archetype_id,
                )
                
                evals = evaluate_recipe(
                    recipe=final_recipe_obj,
                    profile_type=profile,
                    engine_id=engine_id,
                    timeline=timeline,
                    final_recipe=final_recipe_obj,
                    process_details={"tweaks_applied": []},
                    archetype_id=archetype_id,
                )
                fails = [e for e in evals if not e.get('passed')]
                if fails:
                    print(f"  [FAILS] {json.dumps(fails, indent=2)}")
                else:
                    print("  [SUCCESS] All checks passed.")
            except Exception as e:
                import traceback
                traceback.print_exc()

        test_engine("choux", "classic_eclair", "savory")
        test_engine("pasta", "alkaline_noodles", "savory")
