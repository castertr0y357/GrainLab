from django.core.management.base import BaseCommand
import json
import logging
import os
from pathlib import Path
import logging
import shutil
import time
import shutil
from apps.core.gemma.core_client import CATEGORY_TO_ENGINE
from apps.core.gemma.phase3_client import generate_recipe_details, generate_recipe_percentages
from apps.core.gemma.phase4_client import generate_process_details
from apps.core.services.calculation import calculate_final_recipe
from grainlab.engines.router import ENGINES

logger = logging.getLogger('grainlab.gemma')

def evaluate_recipe(recipe, profile_type, engine_id, timeline, final_recipe=None, process_details=None):
    checks = []
    
    if not recipe:
        return [{"rule": "Valid Output", "passed": False, "reason": "No recipe returned"}]

    ingredients = recipe.get("secondary_ingredients", {})
    
    # Check 1: Leavener scaling logic (Yeast vs Chemical vs Starter)
    leaveners = ingredients.get("leaveners", [])
    for l in leaveners:
        name_lower = l.get("name", "").lower()
        if "starter" in name_lower or "levain" in name_lower:
            max_leaven = 25.0
        elif "powder" in name_lower or "soda" in name_lower or "chemical" in name_lower:
            max_leaven = 5.0
        else:
            max_leaven = 1.5

        if l.get("bakers_percentage", 0) > max_leaven:
            checks.append({"rule": "Leaven Limit", "passed": False, "reason": f"Leavener {l.get('name')} exceeds {max_leaven}% max ({l.get('bakers_percentage')}%)"})
        else:
            checks.append({"rule": "Leaven Limit", "passed": True, "reason": f"Leavener {l.get('name')} within limits."})

    # Check 2: Aromatics herbs/spices <= 2.0%
    aromatics = ingredients.get("aromatics", [])
    for a in aromatics:
        name_lower = a.get("name", "").lower()
        if any(spice in name_lower for spice in ["garlic", "oregano", "cinnamon", "pepper", "herb", "spice"]):
            if a.get("bakers_percentage", 0) > 2.0:
                checks.append({"rule": "Spice Limit", "passed": False, "reason": f"Spice {a.get('name')} exceeds 2.0% max ({a.get('bakers_percentage')}%)"})
            else:
                checks.append({"rule": "Spice Limit", "passed": True, "reason": f"Spice {a.get('name')} within limits."})

    # Check 3: Savory profile checks (Pan Engine specifically)
    if profile_type == "savory" and engine_id == "pan":
        # Check no eggs
        binders = ingredients.get("binders", [])
        has_egg = any("egg" in b.get("name", "").lower() for b in binders)
        if has_egg:
            checks.append({"rule": "Savory Pan - No Eggs", "passed": False, "reason": "Found eggs in a savory pan recipe."})
        else:
            checks.append({"rule": "Savory Pan - No Eggs", "passed": True, "reason": "No eggs found."})

        # Check total fat 5-10%
        # Check total fat 5-10%
        lipids = ingredients.get("lipids", [])
        total_fat = sum(l.get("bakers_percentage", 0) for l in lipids)
        if 5.0 <= total_fat <= 10.0:
            checks.append({"rule": "Savory Pan - Fat %", "passed": True, "reason": f"Fat is {total_fat}%, within 5-10%."})
        else:
            checks.append({"rule": "Savory Pan - Fat %", "passed": False, "reason": f"Fat is {total_fat}%, outside 5-10% bound."})

    # Check 4: Chronological Logic Check
    bake_idx = -1
    mix_idx = -1
    for i, step in enumerate(timeline):
        key = step.get("key", "").lower()
        if key == "bake": bake_idx = i
        if key in ["mix", "knead"]: mix_idx = i
    
    if bake_idx != -1 and mix_idx != -1 and bake_idx < mix_idx:
        checks.append({"rule": "Chronological Logic", "passed": False, "reason": "Bake step occurs before mix/knead."})
    else:
        checks.append({"rule": "Chronological Logic", "passed": True, "reason": "Steps are chronologically sound."})

    # Check 5: Time Bounds Auditing
    total_duration_sec = sum(step.get("duration_sec", 0) for step in timeline)
    if total_duration_sec <= 0:
        checks.append({"rule": "Time Bounds Audit", "passed": False, "reason": "Total duration is zero or negative."})
    elif total_duration_sec > 72 * 3600:
        checks.append({"rule": "Time Bounds Audit", "passed": False, "reason": f"Total duration is too long ({total_duration_sec}s)."})
    else:
        checks.append({"rule": "Time Bounds Audit", "passed": True, "reason": f"Total duration ({total_duration_sec}s) is within reasonable bounds."})

    # Check 6: Required Action Verification
    actions = recipe.get("required_actions", [])
    missing_actions = []
    timeline_text = " ".join([f"{s.get('key','')} {s.get('name','')} {s.get('desc','')}" for s in timeline]).lower()
    for act in actions:
        normalized_act = act.lower().replace("-", "_")
        words = normalized_act.split("_")
        found = False
        for w in words:
            if w in ["and", "or", "the", "a", "of", "in", "with"]: continue
            if w in timeline_text:
                found = True
                break
        if not found:
            missing_actions.append(act)
    
    if missing_actions:
        checks.append({"rule": "Required Actions Audit", "passed": False, "reason": f"Missing required actions in timeline: {', '.join(missing_actions)}"})
    else:
        checks.append({"rule": "Required Actions Audit", "passed": True, "reason": "All required actions are represented in the timeline."})

    # Check 7: Hydration vs Lipid Balancing
    liquids = ingredients.get("liquids", [])
    total_liquid = sum(l.get("bakers_percentage", 0) for l in liquids) if liquids else 0.0
    lipids = ingredients.get("lipids", [])
    total_lipid = sum(l.get("bakers_percentage", 0) for l in lipids) if lipids else 0.0
    
    if engine_id != "choux" and total_lipid > 30.0 and total_liquid > 85.0:
        checks.append({"rule": "Hydration Balance", "passed": False, "reason": f"High lipid ({total_lipid}%) paired with excessive hydration ({total_liquid}%) creates structural failure (soup)."})
    else:
        checks.append({"rule": "Hydration Balance", "passed": True, "reason": "Hydration to lipid ratio is physically viable."})

    # Check 8: Yield & Portion Realism
    ff = final_recipe.get("ff") if final_recipe else None
    if ff and getattr(ff, 'is_portioned', False):
        default_yield = getattr(ff, 'default_count', 1)
    else:
        default_yield = recipe.get("default_yield_amount", 1)
        if isinstance(default_yield, str) and default_yield.isdigit():
            default_yield = int(default_yield)
        elif not isinstance(default_yield, (int, float)):
            default_yield = 1
    
    total_bp = 100.0  # base flour
    for cat, items in ingredients.items():
        if items:
            total_bp += sum(i.get("bakers_percentage", 0) for i in items)
            
    total_mass_g = 1000.0 * (total_bp / 100.0) # Assume 1000g of flour base
    portion_size_g = total_mass_g / default_yield if default_yield > 0 else total_mass_g
    
    if portion_size_g < 5.0:
        checks.append({"rule": "Yield Realism", "passed": False, "reason": f"Portion size too small ({portion_size_g:.1f}g) for yield of {default_yield}."})
    else:
        checks.append({"rule": "Yield Realism", "passed": True, "reason": f"Portion size ({portion_size_g:.1f}g) is realistic."})

    # Check 9: Form Factor Match
    if process_details and "process_recommendations" in process_details:
        baking_vessel_ai = process_details["process_recommendations"].get("baking_vessel", {}).get("name", "")
        if ff and baking_vessel_ai:
            checks.append({"rule": "AI Form Factor Match", "passed": True, "reason": f"AI recommended: {baking_vessel_ai}. System mapped to: {getattr(ff, 'name', '')}"})

    # Check 10: Archetype Salt Limit Verification
    if final_recipe and "recipe" in final_recipe:
        recipe_math = final_recipe["recipe"]
        flour_w = recipe_math.get("flour_weight", 0)
        salt_w = recipe_math.get("salt_weight", 0)
        actual_salt_pct = (salt_w / flour_w) if flour_w > 0 else 0
        
        if engine_id in ['quick', 'cookie', 'batter', 'choux', 'pasta']:
            if actual_salt_pct > 0.0101:
                checks.append({"rule": "Salt Limit", "passed": False, "reason": f"Salt is too high ({actual_salt_pct*100:.2f}%) for {engine_id} engine."})
            else:
                checks.append({"rule": "Salt Limit", "passed": True, "reason": f"Salt ({actual_salt_pct*100:.2f}%) is within bounds for {engine_id}."})
        else:
            checks.append({"rule": "Salt Limit", "passed": True, "reason": f"Salt ({actual_salt_pct*100:.2f}%) is within bounds for {engine_id}."})

            
    if not checks:
        checks.append({"rule": "Basic Sanity", "passed": True, "reason": "Payload parsed but no specific rules evaluated."})

    return checks

class Command(BaseCommand):
    help = 'Runs automated QA test on the Gemma recipe generation engines.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Run a single recipe generation to test the script.',
        )

    def handle(self, *args, **options):
        test_mode = options['test']
        
        # Clear out the QA_recipes folder
        qa_dir = os.path.join(os.getcwd(), 'QA_recipes')
        if os.path.exists(qa_dir):
            shutil.rmtree(qa_dir, ignore_errors=True)
        
        # Ensure the model is set to the correct local Ollama tag
        from apps.core.models import SystemSetting
        SystemSetting.set_val("ai_model_name", "gemma4:e4b")
        
        # Generic grains payload
        dummy_grains = json.dumps([
            {
                "id": "12345678-1234-5678-1234-567812345678",
                "name": "Hard Red Winter Wheat",
                "crude_protein_percentage": "12.5%",
                "bran_tannin_profile": "high",
                "pentosan_concentration": "standard"
            }
        ])

        results = []

        self.stdout.write("Starting QA Test Suite for Gemma Recipe Generation")

        # We want to run across all engines and all archetypes, but only 1 recipe per archetype
        categories_to_run = list(CATEGORY_TO_ENGINE.items())
        if test_mode:
            categories_to_run = [(k, v) for k, v in categories_to_run if v == "cookie"]

        for category_slug, engine_id in categories_to_run:
            engine_instance = ENGINES.get(engine_id)
            if not engine_instance:
                self.stderr.write(f"Could not load engine: {engine_id}")
                continue

            archetypes_dict = getattr(engine_instance, "archetypes", {})
            archetype_ids = list(archetypes_dict.keys())

            for archetype_id in archetype_ids:
                if archetype_id != "drop_cookie":
                    continue
                    
                tests_to_run = [{"name": f"Classic Chocolate Chip Cookie (Run {i})", "type": f"sweet_run_{i}"} for i in range(1, 3)]

                for test in tests_to_run:
                    self.stdout.write(f"Running engine '{engine_id}', archetype '{archetype_id}', profile: '{test['name']}'...")
                    
                    try:
                        current_grains = [] if 'flourless' in test['type'] else dummy_grains
                        run_name = f"{test['name']} (Run {int(time.time())})"
                        recipe_data = generate_recipe_details(
                            engine_id=engine_id,
                            active_archetype_id=archetype_id,
                            recipe_slug=f"qa-test-{engine_id}",
                            recipe_name=run_name,
                            selected_grains=json.dumps(current_grains) if isinstance(current_grains, list) else current_grains,
                            category_slug=category_slug
                        )

                        flat_secondary = []
                        for cat_key, items in recipe_data.get("secondary_ingredients", {}).items():
                            if isinstance(items, list):
                                flat_secondary.extend([i.get("name") for i in items])
                            else:
                                flat_secondary.append(items.get("name"))
                                
                        if "flavor_inclusions" in recipe_data:
                            flat_secondary.extend([i.get("name") for i in recipe_data["flavor_inclusions"]])
                            
                        flat_secondary = [name for name in flat_secondary if name]
                        
                        if flat_secondary:
                            percentages_data = generate_recipe_percentages(
                                engine_id=engine_id,
                                active_archetype_id=archetype_id,
                                recipe_slug=f"qa-test-{engine_id}",
                                recipe_name=run_name,
                                secondary_ingredients=flat_secondary
                            )
                            if percentages_data and "percentages" in percentages_data:
                                for cat_key, items in recipe_data.get("secondary_ingredients", {}).items():
                                    if isinstance(items, list):
                                        for item in items:
                                            if item.get("name") in percentages_data["percentages"]:
                                                item["bakers_percentage"] = percentages_data["percentages"][item.get("name")]
                                    else:
                                        if items.get("name") in percentages_data["percentages"]:
                                            items["bakers_percentage"] = percentages_data["percentages"][items.get("name")]
                                            
                                if "flavor_inclusions" in recipe_data:
                                    for item in recipe_data["flavor_inclusions"]:
                                        if item.get("name") in percentages_data["percentages"]:
                                            item["bakers_percentage"] = percentages_data["percentages"][item.get("name")]
                                            
                                for target_key in ["target_fat_pct", "target_sugar_pct", "target_hydration_pct", "target_binder_pct", "target_leaven_pct", "target_salt_pct"]:
                                    if target_key in percentages_data:
                                        recipe_data[target_key] = percentages_data[target_key]


                        active_arch = engine_instance.archetypes.get(archetype_id, {})
                        ff_slug = active_arch.get("default_form_factor")
                        if not ff_slug:
                            ff_dict = getattr(engine_instance, "permissible_form_factors", {})
                            ff_slug = next(iter(ff_dict.keys())) if ff_dict else None
                        try:
                            # Mock the state from Phase 1/2/3 to pass to Phase 4
                            mock_state = {
                                "selected_master": category_slug,
                                "preset_slug": archetype_id,

                                "global_ai_enabled": True,
                                "recipe_name": run_name,
                                "active_berries": current_grains if isinstance(current_grains, list) else json.loads(current_grains),
                                "secondary_ingredients": json.dumps(recipe_data.get('secondary_ingredients', {})),
                                "dynamic_directions": json.dumps(recipe_data.get('dynamic_directions', {}))
                            }
                            
                            # Phase 4
                            final_recipe = calculate_final_recipe(mock_state, run_ai=True)
                            bake_temp = final_recipe.get("bake_temp_f", 400)
                            bake_time = final_recipe.get("bake_time_min", 30)
                            
                            # Generate timeline (just for the evaluation checks)
                            bake_time_int = int(bake_time) if str(bake_time).isdigit() else 30
                            timeline = engine_instance.get_live_timeline_steps(
                                recipe_data=recipe_data,
                                estimated_bulk_minutes=120,
                                estimated_proof_minutes=60,
                                bake_time_min=bake_time_int,
                                mixing_method="stand_mixer",
                                preset_slug=archetype_id
                            )
                        except Exception as e:
                            timeline = []
                            self.stderr.write(f"  [WARNING] Failed to generate phase 4 or timeline for {engine_id}: {e}")
                            bake_temp = 0
                            bake_time = 0

                        # Call generate_process_details for the "how are we making it" metadata
                        try:
                            process_details = generate_process_details(
                                engine_id=engine_id,
                                active_archetype_id=archetype_id,
                                recipe_slug=f"qa-test-{engine_id}",
                                recipe_name=test['name']
                            )
                        except Exception as e:
                            self.stderr.write(f"  [WARNING] Failed to generate process details: {e}")
                            process_details = {}

                        evaluations = evaluate_recipe(recipe_data, test['type'], engine_id, timeline, final_recipe=final_recipe, process_details=process_details)
                        
                        # Add Phase 4 evaluation checks
                        is_pasta = engine_id == 'pasta'
                        
                        if is_pasta:
                            if bake_temp not in [0, 212]:
                                evaluations.append({"rule": "Phase 4 - Temp Limit", "passed": False, "reason": f"Bake temp {bake_temp}F invalid for pasta (should be 0 or 212)"})
                            else:
                                evaluations.append({"rule": "Phase 4 - Temp Limit", "passed": True, "reason": f"Bake temp {bake_temp}F is realistic for pasta."})
                        else:
                            if bake_temp < 300 or bake_temp > 550:
                                evaluations.append({"rule": "Phase 4 - Temp Limit", "passed": False, "reason": f"Bake temp {bake_temp}F outside bounds (300-550)"})
                            else:
                                evaluations.append({"rule": "Phase 4 - Temp Limit", "passed": True, "reason": f"Bake temp {bake_temp}F is realistic."})
                            
                        if bake_time < 1 or bake_time > 120:
                            evaluations.append({"rule": "Phase 4 - Time Limit", "passed": False, "reason": f"Bake time {bake_time}m outside bounds (1-120)"})
                        else:
                            evaluations.append({"rule": "Phase 4 - Time Limit", "passed": True, "reason": f"Bake time {bake_time}m is realistic."})
                            
                        all_passed = all(check['passed'] for check in evaluations)

                        results.append({
                            "engine": engine_id,
                            "archetype": archetype_id,
                            "profile": test['type'],
                            "all_passed": all_passed,
                            "evaluations": evaluations,
                            "recipe": recipe_data
                        })
                        
                        # Generate Output MD
                        qa_dir = Path("QA_recipes")
                        qa_dir.mkdir(exist_ok=True)
                        md_path = qa_dir / f"{category_slug}_{archetype_id}_{test['type']}.md"
                        
                        ff = final_recipe.get("ff") if final_recipe else None
                        bake_temp = final_recipe.get("bake_temp_f", "N/A") if final_recipe else "N/A"
                        bake_time = final_recipe.get("bake_time_min", "N/A") if final_recipe else "N/A"
                        steam = final_recipe.get("steam_required", False) if final_recipe else False
                        
                        process_md = ""
                        if process_details and "process_recommendations" in process_details:
                            process_md += "## How Are We Making It (AI Recommendations)\n"
                            for key, val in process_details["process_recommendations"].items():
                                process_md += f"- **{key.title().replace('_', ' ')}**: {val.get('name', '')} - {val.get('explanation', '')}\n"

                        ingredients_md = ""
                        for cat_key, items in recipe_data.get("secondary_ingredients", {}).items():
                            if items:
                                ingredients_md += f"\n### {cat_key.capitalize()}\n"
                                for item in items:
                                    ingredients_md += f"- **{item.get('name')}**: {item.get('bakers_percentage')}% ({item.get('temperature', '')})\n"

                        actions = recipe_data.get("required_actions", [])
                        
                        timeline_md = ""
                        for step in timeline:
                            mins = int(step.get('duration_sec', 0) / 60)
                            timeline_md += f"**{step.get('key', 'step').title()}. {step.get('name', '')}** ({mins} min)\n{step.get('desc', '')}\n\n"
                        
                        md_content = f"""# {test['name']}
**Category:** {category_slug}  
**Archetype:** {archetype_id}  
**QA Status:** {'PASS' if all_passed else 'FAIL'}

## Ingredients (AI Generated)
{ingredients_md}

## Final Compiled Formula (Scaled)
```text\nSalt: {((final_recipe.get('recipe', {}).get('salt_weight', 0) / final_recipe.get('recipe', {}).get('flour_weight', 1)) if final_recipe.get('recipe', {}).get('flour_weight', 0) > 0 else 0) * 100:.2f}%\nTotal Mass: {final_recipe.get('recipe', {}).get('target_mass', 0):.1f}g\nYield Count: {getattr(ff, 'default_count', 1) if not isinstance(ff, type(None)) else 1}\n```\n
## Required Actions
{chr(10).join(f"- {a}" for a in actions)}


## Directions
{timeline_md}
{process_md}
## Baking Profile
- **Baking Vessel (System Mapped):** {getattr(ff, 'name', 'Unknown') if ff else 'Unknown'}
- **Temperature:** {bake_temp}°F
- **Time:** {bake_time} minutes
- **Steam Mode:** {'Yes' if steam else 'No'}

## QA Rule Audit
"""
                        for check in evaluations:
                            md_content += f"- **{check['rule']}**: {'PASS' if check['passed'] else 'FAIL'} - {check['reason']}\n"

                        with open(md_path, 'w', encoding='utf-8') as f:
                            f.write(md_content)

                        if all_passed:
                            self.stdout.write(self.style.SUCCESS(f"  [SUCCESS] All checks passed. Output: {md_path}"))
                        else:
                            self.stderr.write(f"  [FAIL] Violations found. Output: {md_path}")
                            for check in evaluations:
                                if not check['passed']:
                                    self.stderr.write(f"    - {check['reason']}")
                                    
                        from apps.core.gemma.phase4_client import generate_recipe_tweaks
                        
                        # TWEAK LOOP TESTING
                        applied_tweaks_history = []
                        current_ingredients = flat_secondary
                        
                        for tweak_round in range(2):
                            self.stdout.write(f"    -> Running Tweak Round {tweak_round+1}...")
                            tweak_data = generate_recipe_tweaks(
                                engine_id=engine_id,
                                active_archetype_id=archetype_id,
                                recipe_name=run_name,
                                current_ingredients=current_ingredients,
                                applied_tweaks_history=applied_tweaks_history
                            )
                            if tweak_data.get("is_max_optimized"):
                                self.stdout.write(f"      -> AI declared recipe is MAX OPTIMIZED: {tweak_data.get('optimization_message')}")
                                md_content += f"\n## Tweak Round {tweak_round+1}\n**OPTIMIZED**: {tweak_data.get('optimization_message')}\n"
                                break
                            
                            tweaks = tweak_data.get("tweaks", [])
                            if not tweaks:
                                self.stdout.write("      -> No tweaks generated.")
                                break
                                
                            chosen_tweak = tweaks[0]
                            self.stdout.write(f"      -> Chose tweak: {chosen_tweak.get('title')}")
                            applied_tweaks_history.append(chosen_tweak.get('title'))
                            
                            md_content += f"\n## Tweak Round {tweak_round+1}\n"
                            md_content += f"**Chosen**: {chosen_tweak.get('title')}\n"
                            md_content += f"**Description**: {chosen_tweak.get('description')}\n"
                            md_content += f"**New Ingredients**: {', '.join(chosen_tweak.get('new_ingredients', []))}\n"
                            
                            current_ingredients = chosen_tweak.get('new_ingredients', current_ingredients)
                            
                        # Resave the markdown file to include tweaks
                        with open(md_path, 'w', encoding='utf-8') as f:
                            f.write(md_content)
                        
                        
                    except Exception as e:
                        self.stderr.write(f"  [FAILED] {str(e)}")
                        results.append({
                            "engine": engine_id,
                            "archetype": archetype_id,
                            "profile": test['type'],
                            "error": str(e)
                        })

        # Process and output report
        with open('qa_report.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)
        
        self.stdout.write(self.style.SUCCESS("\nQA Run complete. Report saved to qa_report.json."))
