from apps.core.engines.base_engine import BaseEngine
from apps.core.engines.bath_engine import BathEngine
from apps.core.engines.batter_engine import BatterEngine
from apps.core.engines.choux_engine import ChouxEngine
from apps.core.engines.cookie_engine import CookieEngine
from apps.core.engines.flat_engine import FlatEngine
from apps.core.engines.fry_engine import FryEngine
from apps.core.engines.hearth_engine import HearthEngine
from apps.core.engines.pan_engine import PanEngine
from apps.core.engines.pasta_engine import PastaEngine
from apps.core.engines.pastry_engine import PastryEngine
from apps.core.engines.quick_engine import QuickEngine

# Instantiate singletons to prevent multiple instances of Base Engines
ENGINES = {
    "hearth": HearthEngine(),
    "pan": PanEngine(),
    "bath": BathEngine(),
    "flat": FlatEngine(),
    "quick": QuickEngine(),
    "batter": BatterEngine(),
    "pastry": PastryEngine(),
    "choux": ChouxEngine(),
    "cookie": CookieEngine(),
    "fry": FryEngine(),
    "pasta": PastaEngine(),
}

CATEGORY_MAPPINGS = {
    "lean-crusty": "hearth",
    "lean_crusty": "hearth",
    "hearths": "hearth",
    "enriched-soft": "pan",
    "enriched_soft": "pan",
    "pans": "pan",
    "alkaline-bath": "bath",
    "alkaline_bath": "bath",
    "baths": "bath",
    "flatbreads-griddles": "flat",
    "flatbreads_griddles": "flat",
    "flats": "flat",
    "non-leavened-crisp": "flat",
    "quick-breads-scones": "quick",
    "quick_breads_scones": "quick",
    "quick-breads": "quick",
    "quick_breads": "quick",
    "quicks": "quick",
    "chemically-leavened": "quick",
    "cakes-batters": "batter",
    "cakes_batters": "batter",
    "batters": "batter",
    "batter-based": "batter",
    "pastry-lamination": "pastry",
    "pastry_lamination": "pastry",
    "pastries-laminated": "pastry",
    "pastries_laminated": "pastry",
    "pastries": "pastry",
    "choux-paste": "choux",
    "choux_paste": "choux",
    "cookies-shortbread": "cookie",
    "cookies_shortbread": "cookie",
    "cookies": "cookie",
    "fried-doughs": "fry",
    "fried_doughs": "fry",
    "frys": "fry",
    "fresh-pasta-noodles": "pasta",
    "fresh_pasta_noodles": "pasta",
    "pastas": "pasta",
}

_SUBCLASS_CACHE = {}


def get_engine_for_preset(preset_slug: str, category_slug: str = None) -> BaseEngine:
    if preset_slug:
        preset_slug_lower = preset_slug.lower()

        # Dynamic Discovery: Ask every base engine if it or its subclasses own this preset
        for base_name, base_engine_inst in ENGINES.items():
            archetypes = base_engine_inst.archetypes
            for arch_slug, arch_data in archetypes.items():
                matchers = arch_data.get("preset_matchers", [])
                if any(m in preset_slug_lower for m in matchers):
                    # Found a match! Return the exact subclass instance.
                    if arch_slug not in _SUBCLASS_CACHE:
                        for subclass in base_engine_inst.__class__.__subclasses__():
                            sub_slug = getattr(
                                subclass, "archetype_slug", getattr(subclass, "id", getattr(subclass, "slug", None))
                            )
                            if sub_slug == arch_slug:
                                _SUBCLASS_CACHE[arch_slug] = subclass()
                                break
                    if arch_slug in _SUBCLASS_CACHE:
                        return _SUBCLASS_CACHE[arch_slug]

    if category_slug:
        category_slug_lower = category_slug.lower()

        # Direct Match
        if category_slug_lower in ENGINES:
            return ENGINES[category_slug_lower]

        # Mapped Match
        if category_slug_lower in CATEGORY_MAPPINGS:
            mapped_name = CATEGORY_MAPPINGS[category_slug_lower]
            return ENGINES[mapped_name]

        # Fuzzy Match
        if "hearth" in category_slug_lower or "lean" in category_slug_lower:
            return ENGINES["hearth"]
        if "pan" in category_slug_lower or "enriched" in category_slug_lower:
            return ENGINES["pan"]
        if "bath" in category_slug_lower or "alkaline" in category_slug_lower:
            return ENGINES["bath"]
        if "flat" in category_slug_lower:
            return ENGINES["flat"]
        if "quick" in category_slug_lower or "chemically" in category_slug_lower:
            return ENGINES["quick"]
        if "batter" in category_slug_lower:
            return ENGINES["batter"]
        if "pastry" in category_slug_lower:
            return ENGINES["pastry"]
        if "choux" in category_slug_lower:
            return ENGINES["choux"]
        if "cookie" in category_slug_lower:
            return ENGINES["cookie"]
        if "fry" in category_slug_lower:
            return ENGINES["fry"]
        if "pasta" in category_slug_lower:
            return ENGINES["pasta"]

    return ENGINES["hearth"]
