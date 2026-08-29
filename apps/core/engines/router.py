from apps.core.engines.base_engine import BaseEngine
from apps.core.engines.hearth_engine import HearthEngine
from apps.core.engines.pan_engine import PanEngine
from apps.core.engines.bath_engine import BathEngine
from apps.core.engines.flat_engine import FlatEngine
from apps.core.engines.quick_engine import QuickEngine
from apps.core.engines.batter_engine import BatterEngine
from apps.core.engines.pastry_engine import PastryEngine
from apps.core.engines.choux_engine import ChouxEngine
from apps.core.engines.cookie_engine import CookieEngine
from apps.core.engines.fry_engine import FryEngine
from apps.core.engines.pasta_engine import PastaEngine

# Instantiate singletons to prevent multiple instances
hearth_engine = HearthEngine()
pan_engine = PanEngine()
bath_engine = BathEngine()
flat_engine = FlatEngine()
quick_engine = QuickEngine()
batter_engine = BatterEngine()
pastry_engine = PastryEngine()
choux_engine = ChouxEngine()
cookie_engine = CookieEngine()
fry_engine = FryEngine()
pasta_engine = PastaEngine()

ENGINES = {
    # Original singular keys
    "hearth": hearth_engine,
    "pan": pan_engine,
    "bath": bath_engine,
    "flat": flat_engine,
    "quick": quick_engine,
    "batter": batter_engine,
    "pastry": pastry_engine,
    "choux": choux_engine,
    "cookie": cookie_engine,
    "fry": fry_engine,
    "pasta": pasta_engine,

    # Plural fallback keys
    "hearths": hearth_engine,
    "pans": pan_engine,
    "baths": bath_engine,
    "flats": flat_engine,
    "quicks": quick_engine,
    "batters": batter_engine,
    "pastries": pastry_engine,
    "cookies": cookie_engine,
    "frys": fry_engine,
    "pastas": pasta_engine,

    # Duplicate semantic & category slug aliases
    "lean-crusty": hearth_engine,
    "lean_crusty": hearth_engine,
    "enriched-soft": pan_engine,
    "enriched_soft": pan_engine,
    "alkaline-bath": bath_engine,
    "alkaline_bath": bath_engine,
    "flatbreads-griddles": flat_engine,
    "flatbreads_griddles": flat_engine,
    "quick-breads-scones": quick_engine,
    "quick_breads_scones": quick_engine,
    "quick-breads": quick_engine,
    "quick_breads": quick_engine,
    "cakes-batters": batter_engine,
    "cakes_batters": batter_engine,
    "pastry-lamination": pastry_engine,
    "pastry_lamination": pastry_engine,
    "pastries-laminated": pastry_engine,
    "pastries_laminated": pastry_engine,
    "choux-paste": choux_engine,
    "choux_paste": choux_engine,
    "cookies-shortbread": cookie_engine,
    "cookies_shortbread": cookie_engine,
    "fried-doughs": fry_engine,
    "fried_doughs": fry_engine,
    "fresh-pasta-noodles": pasta_engine,
    "fresh_pasta_noodles": pasta_engine,
}

def get_engine_for_preset(preset_slug: str, category_slug: str = None) -> BaseEngine:
    if preset_slug:
        preset_slug_lower = preset_slug.lower()
        
        # Check Hearth
        if any(x in preset_slug_lower for x in ["boule", "baguette", "ciabatta", "french-loaf", "pizza", "calzone", "focaccia", "altamura", "campagne"]):
            return ENGINES["hearth"]
            
        # Check Pan
        if any(x in preset_slug_lower for x in ["sandwich", "brioche", "challah", "milk-bread", "burger-buns", "dinner-rolls", "cinnamon-rolls", "babka", "monkey-bread"]):
            return ENGINES["pan"]
            
        # Check Bath
        if any(x in preset_slug_lower for x in ["pretzel", "bagel", "simit"]):
            return ENGINES["bath"]
            
        # Check Flat
        if any(x in preset_slug_lower for x in ["tortilla", "naan", "pita", "roti", "chapati", "paratha", "scallion", "lavash", "matzo", "cracker"]):
            return ENGINES["flat"]
            
        # Check Quick
        if any(x in preset_slug_lower for x in ["biscuit", "scone", "soda-bread", "banana-bread", "pumpkin", "cornbread", "muffin", "zucchini"]):
            return ENGINES["quick"]
            
        # Check Batter
        if any(x in preset_slug_lower for x in ["cake", "sponge", "chiffon", "angel-food", "madeleine", "cupcake", "pancake", "waffle"]):
            return ENGINES["batter"]
            
        # Check Pastry
        if any(x in preset_slug_lower for x in ["croissant", "pain-au-chocolat", "puff-pastry", "danish", "pie-crust", "tart", "palmier", "vol-au-vent"]):
            return ENGINES["pastry"]
            
        # Check Choux
        if any(x in preset_slug_lower for x in ["eclair", "profiterole", "gougere", "cruller", "churro", "paris-breast"]):
            if "fried" in preset_slug_lower:
                return ENGINES["fry"]
            return ENGINES["choux"]
            
        # Check Cookie
        if any(x in preset_slug_lower for x in ["cookie", "raisin-bake", "shortbread", "biscotti", "gingerbread", "macaron", "snickerdoodle"]):
            return ENGINES["cookie"]
            
        # Check Fry
        if any(x in preset_slug_lower for x in ["donut", "beignet", "sopapilla", "frybread", "fritter"]):
            return ENGINES["fry"]
            
        # Check Pasta
        if any(x in preset_slug_lower for x in ["tagliatelle", "fettuccine", "ravioli", "rigatoni", "udon", "ramen", "gyoza", "dumpling"]):
            return ENGINES["pasta"]

    if category_slug:
        category_slug_lower = category_slug.lower()
        if category_slug_lower in ENGINES:
            return ENGINES[category_slug_lower]
            
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
            
        # Fallback mappings for old category slugs
        if category_slug_lower == "non-leavened-crisp":
            return ENGINES["flat"]
        if category_slug_lower == "batter-based":
            return ENGINES["batter"]

    return ENGINES["hearth"]
