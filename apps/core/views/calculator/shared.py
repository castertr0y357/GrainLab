from django.shortcuts import get_object_or_404, redirect, render

from apps.core.models import SavedRecipe
from apps.core.services.calculator.calculation import calculate_final_recipe
from apps.core.services.calculator.session import (
    get_calculator_state,
    get_engines_archetypes_json,
    get_engines_ff_json,
)


def save_recipe(request):
    if request.method == "POST":
        state = get_calculator_state(request)

        if not state.get("active_berries"):
            return redirect("calculator_phase1")

        try:
            recipe_context = calculate_final_recipe(state)

            # Serialize all Django models for JSONField compatibility
            from django.db.models import Model
            from django.forms.models import model_to_dict

            for key, value in list(recipe_context.items()):
                if isinstance(value, Model):
                    recipe_context[key] = model_to_dict(value)

        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Error calculating final recipe: {e}")
            recipe_context = {}

        category_slug = state.get("selected_master", "unknown")
        archetype_slug = state.get("preset_slug", "unknown")

        cat_data = recipe_context.get("cat", {})
        ff_data = recipe_context.get("ff", {})

        c_name = (
            cat_data.get("name")
            if isinstance(cat_data, dict)
            else category_slug.replace("-", " ").replace("_", " ").title()
        )
        f_name = (
            ff_data.get("name")
            if isinstance(ff_data, dict)
            else archetype_slug.replace("-", " ").replace("_", " ").title()
        )

        fallback_name = f"{f_name} - {c_name}".strip(" -")
        recipe_name = state.get("recipe_name", "").strip()
        final_name = recipe_name if recipe_name else fallback_name

        formula = SavedRecipe.objects.create(
            name=final_name,
            category_slug=category_slug,
            archetype_slug=archetype_slug,
            configuration_state=state,
            compiled_data=recipe_context,
        )

        return redirect("shared_recipe", recipe_id=formula.id)
    return redirect("calculator_phase1")


def shared_recipe(request, recipe_id):
    formula = get_object_or_404(SavedRecipe, id=recipe_id)

    import json

    process_recs = formula.configuration_state.get("process_recommendations", {})

    context = {
        "formula": formula,
        "state": formula.configuration_state,
        "recipe_compiled": True if formula.compiled_data else False,
        "engines_archetypes_json": get_engines_archetypes_json(),
        "engines_ff_json": get_engines_ff_json(),
        "process_recommendations_json": json.dumps(process_recs),
    }

    context.update(formula.compiled_data)

    recipe = formula.compiled_data.get("recipe", {})
    ingredient_weights = {}
    if recipe.get("added_flour", 0) > 0:
        ingredient_weights["Flour Base"] = float(recipe.get("added_flour", 0))
    if recipe.get("wheat_berry_mix"):
        for b, w in recipe["wheat_berry_mix"].items():
            ingredient_weights[b] = float(w)
    for item in recipe.get("liquid_items", []):
        ingredient_weights[item.get("name", "Liquid")] = float(item.get("weight", 0))
    if not recipe.get("liquid_items") and recipe.get("added_water", 0) > 0:
        ingredient_weights["Water"] = float(recipe.get("added_water", 0))
    for item in recipe.get("lipid_items", []) + recipe.get("fat_items", []):
        ingredient_weights[item.get("name", "Fat")] = float(item.get("weight", 0))
    if not recipe.get("lipid_items") and not recipe.get("fat_items") and recipe.get("fat_weight", 0) > 0:
        ingredient_weights[recipe.get("fat_substitute_label", "Unsalted Butter")] = float(recipe.get("fat_weight", 0))
    for item in recipe.get("sweetener_items", []) + recipe.get("sugar_items", []):
        ingredient_weights[item.get("name", "Sugar")] = float(item.get("weight", 0))
    if not recipe.get("sweetener_items") and not recipe.get("sugar_items") and recipe.get("sugar_weight", 0) > 0:
        ingredient_weights[recipe.get("sugar_label", "Granulated Sugar")] = float(recipe.get("sugar_weight", 0))
    for item in recipe.get("binder_items", []):
        ingredient_weights[item.get("name", "Binder")] = float(item.get("weight", 0))
    if not recipe.get("binder_items") and recipe.get("binder_weight", 0) > 0:
        ingredient_weights[recipe.get("binder_label", "Whole Eggs")] = float(recipe.get("binder_weight", 0))
    if recipe.get("salt_item"):
        ingredient_weights[recipe["salt_item"].get("name", "Salt")] = float(recipe["salt_item"].get("weight", 0))
    elif recipe.get("salt", 0) > 0:
        ingredient_weights["Salt"] = float(recipe.get("salt", 0))
        ingredient_weights["Fine Sea Salt"] = float(recipe.get("salt", 0))  # Alias
    if recipe.get("commercial_yeast_item"):
        ingredient_weights[recipe["commercial_yeast_item"].get("name", "Yeast")] = float(
            recipe["commercial_yeast_item"].get("weight", 0)
        )
    elif recipe.get("yeast_weight", 0) > 0:
        ingredient_weights[recipe.get("yeast_label", "Commercial Yeast")] = float(recipe.get("yeast_weight", 0))
    if recipe.get("starter_levain_item"):
        ingredient_weights[recipe["starter_levain_item"].get("name", "Sourdough Starter")] = float(
            recipe["starter_levain_item"].get("weight", 0)
        )
    elif recipe.get("starter_weight", 0) > 0:
        ingredient_weights["Sourdough Starter"] = float(recipe.get("starter_weight", 0))
    for item in recipe.get("flavor_inclusions", []) + recipe.get("additive_items", []):
        if isinstance(item, dict):
            ingredient_weights[item.get("name", "Inclusion")] = float(item.get("weight", 0))
        elif isinstance(item, str):
            ingredient_weights[item] = 0.0

    context["ingredient_weights_json"] = json.dumps(ingredient_weights)

    return render(request, "calculator/shared_recipe.html", context)
