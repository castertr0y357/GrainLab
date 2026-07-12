from grainlab.engines.base_engine import BaseEngine
from grainlab.engines.hearth_engine import HearthEngine
from grainlab.engines.pan_engine import PanEngine
from grainlab.engines.bath_engine import BathEngine
from grainlab.engines.flat_engine import FlatEngine
from grainlab.engines.quick_engine import QuickEngine
from grainlab.engines.batter_engine import BatterEngine
from grainlab.engines.pastry_engine import PastryEngine
from grainlab.engines.choux_engine import ChouxEngine
from grainlab.engines.cookie_engine import CookieEngine
from grainlab.engines.fry_engine import FryEngine
from grainlab.engines.pasta_engine import PastaEngine

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
