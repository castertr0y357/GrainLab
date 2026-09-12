SESSION_KEY = "grainlab_calculator_state"


def get_calculator_state(request):
    """Retrieve the current calculator state from the session."""
    state = request.session.get(SESSION_KEY, {})
    if not isinstance(state, dict):
        state = {}
    return state


def save_calculator_state(request, state):
    """Save the updated state back to the session."""
    request.session[SESSION_KEY] = state
    request.session.modified = True


def clear_calculator_state(request):
    """Clear the calculator state from the session."""
    if SESSION_KEY in request.session:
        del request.session[SESSION_KEY]
        request.session.modified = True


def update_calculator_state(request, updates):
    """Update specific keys in the calculator state."""
    state = get_calculator_state(request)
    state.update(updates)
    save_calculator_state(request, state)


def get_active_grains(request):
    """Return the list of actively selected grains from phase 2."""
    state = get_calculator_state(request)
    return state.get("active_grains", [])


def get_engines_ff_json() -> str:
    import json

    from apps.core.engines.router import ENGINES
    from apps.core.gemma import CATEGORY_TO_ENGINE

    engines_ff_data = {}
    for cat_slug, eng_name in CATEGORY_TO_ENGINE.items():
        engine = ENGINES[eng_name]
        engines_ff_data[cat_slug] = {
            "default_yield_unit": getattr(engine, "default_yield_unit", "pieces"),
            "permissible_form_factors": getattr(engine, "permissible_form_factors", {}),
            "production_profile": getattr(engine, "production_profile", {}),
            "secondary_ingredients": getattr(engine, "secondary_ingredients", {}),
            "supported_tweaks": getattr(engine, "supported_tweaks", ["hydration", "leavening"]),
            "tweak_labels": getattr(engine, "tweak_labels", {}),
            "variations": getattr(engine, "variations", {}),
        }
    return json.dumps(engines_ff_data)


def get_engines_archetypes_json() -> str:
    import json

    from apps.core.engines.router import ENGINES
    from apps.core.gemma import CATEGORY_TO_ENGINE

    archetypes_data = {}
    for cat_slug, eng_name in CATEGORY_TO_ENGINE.items():
        engine = ENGINES[eng_name]
        archetypes_data[cat_slug] = getattr(engine, "archetypes", {})
    return json.dumps(archetypes_data)
