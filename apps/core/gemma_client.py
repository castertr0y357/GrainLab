import json
import logging
import requests
from django.conf import settings
from django.core.cache import cache
from apps.core.models import SystemSetting
from apps.core.bakers_math import (
    get_local_sensory_benchmark,
    get_local_contextual_pitfalls,
)

FACTUAL_DICTIONARY = {
    'refined': 'Store refined commercial flour. High shelf stability and consistent protein levels, but stripped of bran and germ.',
    'milled': 'Freshly milled whole grain. Retains 100% of germ and bran oils. High enzyme activity and complex rustic flavor profile.',
    'grain_hard_red_spring': 'High-protein hard wheat. Strong, elastic gluten structure.',
    'grain_hard_red_winter': 'Moderate-high protein wheat. Balanced gluten elasticity and extensibility.',
    'grain_soft_white': 'Low-protein soft wheat. Weak, tender gluten structure.',
    'grain_hard_white': 'Mild, light-colored hard wheat. Structural strength without bitter red wheat tannins.',
    'grain_spelt': 'Ancient hulled wheat species. Extensible but weak gluten strength; water-absorbent.',
    'grain_kamut': 'Ancient Khorasan wheat. High protein, lower elasticity; absorbs water slowly.',
    'grain_rye': 'Ancient rye grass grain. High pentosan concentration and weak gluten strength.',
    'stand_mixer': 'Planetary stand mixer. Delivers intensive mechanical shearing, building fast gluten structures but adding heat.',
    'bread_machine': 'Automated high-torque chamber mixer. Fully enclosed, creating high friction heat and rapid development.',
    'food_processor': 'High-velocity steel blade shearing. Forces hydration and gluten alignment rapidly but risks blade damage.',
    'hand_beaters': 'Light whipping beaters. Aerates liquid and fat emulsions without building strong gluten networks.',
    'whisk': 'Manual aerating whisk. Incorporates gas bubbles into fluid batters to support leavening lift.',
    'spatula_bowl': 'Zero-friction manual mixing. Minimal mechanical energy transfer to prevent any accidental gluten formation.',
    'knead': 'Mechanical folding and stretching of dough to align glutenin and gliadin proteins into a structural matrix.',
    'cream': 'Aeration of solid fat and sugar. Traps micro-bubbles to form the foundation of crumb leavening.',
    'fold': 'Gentle folding layers the dough and develops structure without degassing. Crucial for retaining large, irregular open crumb cells.',
    'cut_in': 'Distribution of cold fat pieces into dry flour. Forms flat fat pockets for flaky pastry lamination.',
    'sheet': 'Compressing dough through rollers to achieve a uniform thin sheet, aligning starch and gluten strands.',
    'extrude': 'Forcing dense dough through a shaped die to form structured shapes under high compaction pressure.',
    'ambient': 'Countertop proofing. Relies on local ambient room temperature (70-75°F (21-24°C)) for steady biological activity.',
    'mat': 'Open heated proofing mat. Warms the bottom of the vessel to accelerate yeast and lactic acid production.',
    'box': 'Warm, humid enclosed proofing chamber. Maximizes biological activity while preventing surface skin drying.',
    'refrigerator': 'Cold retardation (34-40°F (1-4°C)). Solidifies fats and slows yeast while enzymes continue developing complex sugars.',
    'bench_rest': 'Relaxation rest under a damp cloth. Releases elastic tension in the gluten matrix to allow final shaping.',
    'cast-iron-dutch-oven': 'Heavy cast iron pot. Retains heat and traps steam released from the dough. Ensures optimal starch gelatinization and maximum oven spring.',
    'open-baking-stone-steel': 'High-conduction hearth surface. Transports heat immediately into the base of the loaf for maximum oven spring.',
    'standard-9x5-pan': 'Metal loaf pan. Restricts lateral movement, forcing the rising dough vertically into a uniform sandwich shape.',
    'perforated-baking-sheet': 'Airflow baking tray. Promotes dry skin dehydration on all sides, crucial for crispy pretzels or bagels.',
    'butter': 'Emulsified fat containing 80% fat, 18% water, and milk solids. Adds rich dairy flavor and tender crumb structures.',
    'unsalted_butter': 'Pure unsalted cream butter. Allows precise salt control while introducing emulsified dairy fats.',
    'salted_butter': 'Salted cream butter. Contributes dairy fats and adds a baseline salinity to the dough mixture.',
    'olive_oil': '100% monounsaturated plant fat. Highly fluid liquid state, coats gluten strands for a moist, extensible crumb.',
    'canola_oil': 'Neutral plant seed oil. Provides 100% pure fat coating to tenderize structures without clashing flavors.',
    'vegetable_oil': 'Clean liquid plant fat. Retains moisture in baked goods by keeping fat phase fluid at room temperature.',
    'whole_milk': 'Milky liquid containing 87% water, fat, sugar, and proteins. Enhances caramelization and softens crumb structures.',
    'almond_milk': 'Nut-based dairy substitute. Adds water and micro-solids, requiring slight liquid adjustments due to lack of animal fats.',
    'coconut_oil': 'Plant-based solid lipid. Solidifies at cooler room temperatures, imparting a faint tropical aroma and a melt-in-the-mouth crumb.',
    'avocado_oil': 'Neutral liquid lipid that remains fluid at room temperature. Coats gluten strands completely for a soft and long-lasting crumb.',
    'pure_water': 'Clean, zero-interference hydration. The absolute optimal choice for lean hearth loaves to keep the crumb airy and the crust crispy.',
    'heavy_cream': 'Immense dairy fat richness (37% fat) and milk sugars. Tenderizes the crumb dramatically, yielding an ultra-soft slice.',
    'buttermilk': 'Acidic dairy medium. Tenderizes gluten chemically and reacts with chemical leaveners for a flaky, tender structure.',
    'none': 'No binder. Relies purely on the gluten network and hydration matrix to establish structural integrity.',
    'whole_eggs': 'Rich binder contributing fat, moisture, and lecithin. Promotes rich browning and a soft, custard-like crumb.',
    'egg_whites': 'Pure albumin protein and hydration. Dries and solidifies during baking to create a taller, lighter, and crisper crust.',
    'aquafaba_vegan': 'Vegan binder made from legume starch liquid. Mimics the foam stability of egg whites but lacks animal protein fats.'
}

logger = logging.getLogger("grainlab.gemma")

ENGINE_FLAVORS = {
    "alkaline-bath": {
        1: [
            {"name": "Classic Salted Pretzel/Bagel", "desc": "A baseline standard profile featuring traditional crust browning and coarse sea salt finish."},
            {"name": "Cinnamon Raisin Swirl", "desc": "A sweet-spiced profile with sweet raisin inclusions throughout a dense, chewy crumb."},
            {"name": "Sesame Seed Crunch", "desc": "A nutty, toasted sesame seed coated crust pairing with a soft, low-hydration crumb."},
            {"name": "Garlic Parmesan Glaze", "desc": "A savory garlic infused dough with a crispy, parmesan-crusted outer shell."},
            {"name": "Honey Whole Wheat", "desc": "A mellow honey-sweetened bagel/pretzel base with high chewiness."}
        ],
        2: [
            {"name": "Jalapeno White Cheddar", "desc": "An advanced variation with spicy jalapeno slices and pockets of melted aged white cheddar."},
            {"name": "Malted Caramel Onion", "desc": "A modern savory profile featuring slow-caramelized sweet onion folding and malt glaze."},
            {"name": "Everything Bagel Herb", "desc": "An aromatic toasted garlic, onion, poppy seed, and herb crusted variation."},
            {"name": "Asiago Rosemary Crust", "desc": "An advanced formulation utilizing fresh rosemary infusion and baked asiago topping."},
            {"name": "Sweet Maple Pecan Glaze", "desc": "A sweet, dessert-inspired bagel/pretzel with maple syrup infusion and toasted pecans."}
        ]
    },
    "cakes-batters": {
        1: [
            {"name": "Vanilla Bean Sponge Cake", "desc": "A classic vanilla bean sponge with a light, airy crumb structure and high moisture retention."},
            {"name": "Double Chocolate Chip Muffins", "desc": "A rich dark chocolate batter loaded with chocolate chunks for rich meltability."},
            {"name": "Blueberry Lemon Zest Muffins", "desc": "A bright lemon-perfumed muffin base bursting with sweet whole blueberries."},
            {"name": "Spiced Carrot Walnut Cake", "desc": "A traditional spiced batter containing grated carrots and toasted walnuts for texture."},
            {"name": "Classic Golden Butter Cake", "desc": "A rich, tender butter cake with fine crumb and excellent structure."}
        ],
        2: [
            {"name": "Toasted Coconut Lime Cream Cake", "desc": "An advanced cake featuring fresh lime zest and coconut cream emulsions."},
            {"name": "Salted Caramel Banana Muffin", "desc": "A modern profile with caramelized banana paste and salted toffee swirl inserts."},
            {"name": "Red Velvet Espresso Infusion", "desc": "A sophisticated cocoa-red velvet cake elevated by espresso micro-crystals."},
            {"name": "Cardamom Pistachio Sponge", "desc": "An advanced delicate cake scented with ground cardamom and layered with toasted pistachios."},
            {"name": "Lavender Honey Poppyseed Cake", "desc": "A modern floral cake sweetened with lavender-infused honey and poppyseeds."}
        ]
    },
    "choux-paste": {
        1: [
            {"name": "Vanilla Bean Cream Puffs", "desc": "A traditional hollow choux shell filled with rich vanilla bean pastry cream."},
            {"name": "Classic Chocolate Glazed Eclairs", "desc": "Standard elongated choux shells topped with a glossy dark chocolate ganache."},
            {"name": "Salted Caramel Profiteroles", "desc": "Bite-sized choux puffs drizzled with warm, salty caramel glaze."},
            {"name": "Espresso Mocha Cream Puffs", "desc": "Standard puffs filled with mocha coffee-infused light custard cream."},
            {"name": "Lemon Curd Choux Puffs", "desc": "Traditional crisp choux filled with a tart, vibrant lemon curd."}
        ],
        2: [
            {"name": "Pistachio Praline Eclairs", "desc": "Advanced choux pastry filled with toasted pistachio praline paste and pastry cream."},
            {"name": "Hazelnut Gianduja Cream Puffs", "desc": "A modern variant filled with hazelnut-chocolate gianduja mousse."},
            {"name": "Raspberry Rose Chantilly Puff", "desc": "An advanced floral choux containing fresh raspberry compote and rosewater cream."},
            {"name": "Spiced Cardamom Pear Choux", "desc": "A modern choux pastry featuring poached pear cubes and cardamom cream."},
            {"name": "Dark Chocolate Grand Marnier Eclair", "desc": "Advanced orange-liqueur infused pastry cream in a dark chocolate shell."}
        ]
    },
    "cookies-shortbread": {
        1: [
            {"name": "Classic Chocolate Chip Cookie", "desc": "A baseline standard cookie prioritizing chocolate chips, balanced horizontal spread, and brown sugar chew."},
            {"name": "Golden Sugar Cookie", "desc": "Standard soft-baked cookie with a balanced white sugar ratio for crisp edges and chewy centers."},
            {"name": "Traditional Oatmeal Raisin", "desc": "Reliable rolled oats base bound by butter and eggs, generating a chewy, fibrous structure."},
            {"name": "Spiced Ginger Snaps", "desc": "Standard molasses-sweetened cookie with high crispness and regular surface cracks."},
            {"name": "Old-Fashioned Peanut Butter", "desc": "A dense, rich drop cookie using peanut paste fats to shorten gluten strands."}
        ],
        2: [
            {"name": "Triple-Valrhona Malted Cookie", "desc": "Advanced recipe utilizing malted milk powder and three chocolate chunk inclusions."},
            {"name": "Lactic-Fermented Buttermilk Cookie", "desc": "Modern profile incorporating buttermilk powder for a faint lactic tang and tender center."},
            {"name": "Espresso-Infused Brown Butter", "desc": "Advanced cookie with espresso micro-crystals dispersed throughout browned butter fat."},
            {"name": "Salted Toffee Pecan drop cookie", "desc": "Advanced cookie containing homemade toasted pecan brittle and butter toffee shards."},
            {"name": "Chilled Honey-Lavender Cookie", "desc": "Modern floral cookie sweetened with wildflower honey and infused lavender."}
        ]
    },
    "enriched-soft": {
        1: [
            {"name": "Classic Buttery Brioche", "desc": "A rich, egg-and-butter enriched dough yielding an ultra-soft, pillowy feather crumb."},
            {"name": "Cinnamon Sugar Swirl Buns", "desc": "Standard sweet rolls filled with dark brown sugar and aromatic cinnamon paste."},
            {"name": "Cardamom Spiced Sweet Bread", "desc": "A traditional Scandinavian recipe scented with freshly ground cardamom seed."},
            {"name": "Honey Glazed Soft Dinner Rolls", "desc": "Baseline dinner rolls with a shiny honey glaze and exceptionally soft interior."},
            {"name": "Orange Zest Morning Buns", "desc": "Sweet morning buns infused with refreshing orange zest sugar."}
        ],
        2: [
            {"name": "Chocolate Hazelnut Babka", "desc": "Advanced twisted loaf layered with dark chocolate ganache and hazelnut spread."},
            {"name": "Pecan Sticky Buns", "desc": "Advanced morning pastry baked in a pool of caramelized butter, honey, and pecans."},
            {"name": "Vanilla Bean Glazed Yeasted Donuts", "desc": "Modern light yeasted dough, fried and dipped in a real vanilla bean glaze."},
            {"name": "Maple Pecan Braided Crown", "desc": "An advanced braided crown dough filled with pure maple butter and chopped pecans."},
            {"name": "Sourdough Enriched Swirl Loaf", "desc": "Modern sourdough brioche base utilizing wild yeast acidity to balance butter richness."}
        ]
    },
    "flatbreads-griddles": {
        1: [
            {"name": "Garlic Herb Naan", "desc": "A classic flatbread brushed with garlic-infused ghee and fresh cilantro leaves."},
            {"name": "Rosemary Sea Salt Focaccia", "desc": "Traditional dimpled olive oil flatbread topped with sea salt flakes and rosemary."},
            {"name": "Toasted Sesame Pita Bread", "desc": "A baseline pocket pita coated with nutty toasted sesame seeds."},
            {"name": "Scallion Green Onion Flatbread", "desc": "Standard griddle flatbread layered with green scallions and sesame oil."},
            {"name": "Spicy Chili Flakes Roti", "desc": "Traditional thin unleavened flatbread seasoned with red chili flakes."}
        ],
        2: [
            {"name": "Honey Butter English Crumpets", "desc": "Advanced high-hydration griddle bread with characteristic honeycomb internal holes."},
            {"name": "Cumin Spiced Garlic Pita", "desc": "A modern pocket bread seasoned with roasted cumin and garlic paste."},
            {"name": "Smoked Paprika Olive Flatbread", "desc": "Advanced flatbread topped with kalamata olives and smoked Spanish paprika."},
            {"name": "Blue Cheese Fig Focaccia", "desc": "A modern flavor profile featuring sweet fig jam and aged blue cheese crumbs."},
            {"name": "Caramelized Shallot Herb Flatbread", "desc": "Advanced griddle flatbread topped with slow-cooked sweet shallots."}
        ]
    },
    "fresh-pasta-noodles": {
        1: [
            {"name": "Classic Egg Semolina Fettuccine", "desc": "Traditional rich golden pasta utilizing whole egg yolks and durum semolina flour."},
            {"name": "Spinach Herb Green Tagliatelle", "desc": "A vibrant green spinach-puree infused dough with fresh garden herbs."},
            {"name": "Roasted Garlic Ravioli Dough", "desc": "Standard pasta sheet seasoned with sweet roasted garlic paste."},
            {"name": "Cracked Black Pepper Pappardelle", "desc": "Egg pasta dough studded with coarse cracked black pepper grains."},
            {"name": "Vibrant Tomato Basil Penne", "desc": "A red-hued tomato paste and fresh basil infused pasta dough."}
        ],
        2: [
            {"name": "Beet Root Pink Lasagna Sheets", "desc": "Advanced pasta sheets colored with concentrated sweet beet juice."},
            {"name": "Squid Ink Black Linguine", "desc": "A modern savory seafood pasta colored and flavored with natural squid ink."},
            {"name": "Porcini Mushroom Fettuccine", "desc": "Advanced pasta dough incorporating dehydrated wild porcini mushroom powder."},
            {"name": "Golden Saffron Capellini", "desc": "A premium pasta dough infused with luxury saffron threads and white wine."},
            {"name": "Herb-Laminated Silk Handkerchiefs", "desc": "Advanced pasta with whole parsley leaves pressed between translucent sheets."}
        ]
    },
    "fried-doughs": {
        1: [
            {"name": "Glazed Vanilla Ring Donut", "desc": "A baseline standard donut with a light, airy crumb and vanilla sugar glaze."},
            {"name": "Cinnamon Sugar Churros", "desc": "Crispy ridged fried dough coated in sweet cinnamon sugar."},
            {"name": "Raspberry Jelly Filled Beignets", "desc": "Traditional square puffed donuts filled with seedless raspberry jam."},
            {"name": "Chocolate Frosted Sprinkles Donut", "desc": "A rich yeasted donut topped with dark chocolate icing."},
            {"name": "Powdered Sugar Funnel Cake", "desc": "Classic crispy fried batter ribbons dusted with powdered sugar."}
        ],
        2: [
            {"name": "Maple Bacon Glazed Fritter", "desc": "An advanced yeast donut topped with maple glaze and crispy smoked bacon bits."},
            {"name": "Apple Cider Spiced Donut", "desc": "A modern cake donut flavored with boiled apple cider reduction and fall spices."},
            {"name": "Blueberry Glazed Cruller", "desc": "Advanced choux-based fried ring donut with a sweet blueberry glaze."},
            {"name": "Meyer Lemon Filled Berliner", "desc": "A modern Berliner donut filled with tart Meyer lemon curd."},
            {"name": "Cardamom Spiced Beignets", "desc": "Advanced beignets flavored with ground cardamom and orange blossom honey."}
        ]
    },
    "lean-crusty": {
        1: [
            {"name": "Classic Sourdough Boule", "desc": "A traditional country sourdough boule with an open, airy crumb and blistered crust."},
            {"name": "Roasted Garlic Herb Batard", "desc": "A baseline lean batard filled with roasted sweet garlic cloves and fresh herbs."},
            {"name": "Rosemary Sea Salt French Loaf", "desc": "A fragrant, long loaf topped with fresh rosemary and sea salt flakes."},
            {"name": "Black Olive Oregano Batard", "desc": "Standard Mediterranean loaf filled with sliced kalamata olives and oregano."},
            {"name": "Simple Hearth Sourdough Batard", "desc": "A traditional, highly reliable sourdough batard prioritizing pure grain expression."}
        ],
        2: [
            {"name": "Fig & Walnut Sourdough Boule", "desc": "Advanced modern boule combining sweet dried black mission figs and toasted walnuts."},
            {"name": "Cranberry Pecan Hearth Loaf", "desc": "A modern flavor profile featuring tart dried cranberries and toasted pecans."},
            {"name": "Toasted Sesame Crust Sourdough", "desc": "An advanced sourdough loaf coated completely in toasted sesame seeds for a nutty crunch."},
            {"name": "Beer Batter Sourdough Rye", "desc": "A modern dark rye bread utilizing craft stout beer instead of water for hydration."},
            {"name": "Multigrain Honey Seeded Loaf", "desc": "Advanced lean bread packed with pre-soaked flax, sunflower, and pumpkin seeds."}
        ]
    },
    "pastry-lamination": {
        1: [
            {"name": "Classic Butter Croissant", "desc": "Traditional laminated pastry featuring hundreds of paper-thin buttery layers."},
            {"name": "Pain au Chocolat", "desc": "A baseline standard laminated roll filled with sweet dark chocolate bars."},
            {"name": "Cinnamon Swirl Danish", "desc": "Standard laminated danish dough swirled with sweet cinnamon butter fill."},
            {"name": "Almond Frangipane Turnover", "desc": "Traditional turnover filled with sweet almond frangipane paste."},
            {"name": "Raspberry Jam Laminated Twist", "desc": "A simple laminated twist filled with red raspberry jam."}
        ],
        2: [
            {"name": "Meyer Lemon Cheese Danish", "desc": "Advanced laminated danish topped with sweet cream cheese and tart lemon curd."},
            {"name": "Cardamom Twist Laminated Danish", "desc": "A modern danish flavored with Swedish cardamom sugar and orange glaze."},
            {"name": "Maple Pecan Plait Danish", "desc": "Advanced braided danish pastry filled with maple syrup butter and toasted pecans."},
            {"name": "Vanilla Custard Fruit Danish", "desc": "Advanced danish filled with vanilla pastry cream and seasonal fruits."},
            {"name": "Apple Chausson Laminated Turnover", "desc": "A modern flaky turnover filled with caramelized apple compote."}
        ]
    },
    "quick-breads-scones": {
        1: [
            {"name": "Banana Walnut Quick Bread", "desc": "A traditional sweet quick bread loaded with ripe mashed bananas and walnuts."},
            {"name": "Blueberry Lemon Scones", "desc": "Classic flaky scones bursting with blueberries and glazed with fresh lemon juice."},
            {"name": "Cranberry Sweet Orange Bread", "desc": "Standard quick bread featuring tart dried cranberries and sweet orange zest."},
            {"name": "Spiced Pumpkin Scones", "desc": "A baseline pumpkin scone flavored with ginger, nutmeg, and cinnamon spices."},
            {"name": "Classic Cheddar Chive Scones", "desc": "Standard savory scones layered with sharp cheddar cheese and fresh chives."}
        ],
        2: [
            {"name": "Zucchini Chocolate Chip Quick Bread", "desc": "Advanced quick bread with shredded zucchini for moisture and dark chocolate chips."},
            {"name": "Maple Pecan Scones", "desc": "Modern scones sweetened with maple syrup and packed with toasted pecans."},
            {"name": "Cinnamon Apple Streusel Bread", "desc": "Advanced quick bread topped with apple slices and a brown sugar streusel."},
            {"name": "Lemon Glazed Poppyseed Bread", "desc": "A modern quick bread with blue poppyseeds and a tart lemon icing glaze."},
            {"name": "Ginger Molasses Scones", "desc": "Advanced spiced scones flavored with dark molasses and candied ginger."}
        ]
    }
}

def generate_dynamic_flavors(cat_slug: str, level: int, count: int = 8, exclude_names: list = None) -> list:
    if exclude_names is None:
        exclude_names = []
    exclude_set = {n.strip().lower() for n in exclude_names}
    
    bases = {
        "alkaline-bath": [
            "Poppy Seed Crusted", "Toasted Onion & Chive", "Sweet Molasses", "Black Pepper Asiago", 
            "Sundried Tomato Basil", "Smoked Paprika Glazed", "Sourdough Rye Twist", "Maple Brown Sugar",
            "Cheddar Herb Butter", "Spiced Pumpkin Seed", "Garlic Herb Infusion", "Sweet Honey Oat"
        ],
        "cakes-batters": [
            "Lemon Raspberry Drizzle", "Spiced Apple Streusel", "Rich Fudge Marble", "Banana Chocolate Chunk",
            "Toasted Almond Peach", "Orange Cranberry Spice", "Classic Red Velvet", "Vanilla Cream Swirl",
            "Coconut Pineapple Delight", "Gingerbread Molasses", "Maple Pecan Muffin", "Strawberry Buttermilk"
        ],
        "choux-paste": [
            "Pecan Maple Cream", "White Chocolate Raspberry", "Dark Chocolate Orange", "Salted Caramel Pecan",
            "Vanilla Custard Glaze", "Double Chocolate Mousse", "Coffee Espresso Swirl", "Lemon Meringue Puff",
            "Spiced Apple Cinnamon", "Toasted Almond Praline", "Blueberry Cream Custard", "Sweet Coconut Cream"
        ],
        "cookies-shortbread": [
            "Snickerdoodle Cinnamon", "Triple Chocolate Chunk", "White Chocolate Macadamia", "Chewy Oatmeal Raisin",
            "Lemon Zest Butter", "Spiced Ginger Molasses", "Classic Sugar Sparkle", "Toasted Pecan Shortbread",
            "Double Fudge Brownie Drop", "Maple Walnut Cookie", "Cranberry Orange Drop", "Almond Butter Sandies"
        ],
        "enriched-soft": [
            "Chocolate Fudge Babka", "Cinnamon Streusel Swirl", "Sweet Maple Braid", "Orange Blossom Honey Rolls",
            "Cardamom Almond Crown", "Buttermilk Parker House", "Spiced Pumpkin Brioche", "Vanilla Custard Roll",
            "Toasted Coconut Buns", "Raspberry Jam Twists", "Apple Cinnamon Morning Buns", "Golden Egg Dinner Rolls"
        ],
        "flatbreads-griddles": [
            "Everything Bagel Focaccia", "Garlic Butter Naan", "Spinach Feta Piadina", "Pesto Mozzarella Flatbread",
            "Caramelized Onion Roti", "Toasted Sesame Pita", "Chili Flake Olive Flatbread", "Rosemary Parmesan Focaccia",
            "Sweet Honey Butter Crumpet", "Roasted Garlic Herb Pita", "Smoked Paprika Flatbread", "Za'atar Olive Flatbread"
        ],
        "fresh-pasta-noodles": [
            "Saffron Egg Tagliatelle", "Spinach Ricotta Ravioli", "Beet Root Pink Lasagna", "Squid Ink Black Linguine",
            "Porcini Mushroom Fettuccine", "Roasted Garlic Pappardelle", "Black Pepper Semolina Pasta", "Basil Pesto Penne",
            "Tomato Paste Fettuccine", "Lemon Herb Tagliolini", "Spiced Red Pepper Pappardelle", "Whole Grain Durum Noodle"
        ],
        "fried-doughs": [
            "Apple Cider Fritter", "Maple Glazed Bacon Donut", "Meyer Lemon Curd Berliner", "Chocolate Frosted Glaze",
            "Cinnamon Sugar Beignet", "Cardamom Spiced Churro", "Raspberry Jam Jelly Donut", "Powdered Sugar Funnel Cake",
            "Vanilla Bean Glazed Cruller", "Spiced Pumpkin Donut", "Toasted Coconut Fry Bread", "Blueberry Glazed Donut"
        ],
        "lean-crusty": [
            "Fig & Walnut Sourdough", "Cranberry Pecan Batard", "Toasted Sesame Boule", "Olive Oregano Sourdough",
            "Roasted Garlic Hearth Batard", "Rosemary French Baguette", "Multigrain Honey Seeded Boule", "Dark Beer Stout Rye",
            "Classic Country Sourdough", "Sun-Dried Tomato Batard", "Spiced Pumpkin Seed Hearth", "Ancient Grain Emmer Boule"
        ],
        "pastry-lamination": [
            "Meyer Lemon Cream Danish", "Almond Frangipane Turnover", "Raspberry Jam Pinwheel", "Cinnamon Sugar Palmier",
            "Vanilla Custard Fruit Plait", "Maple Butter Laminated Knot", "Chocolate Hazelnut Croissant", "Orange Glazed Cruffin",
            "Cardamom Spiced Morning Roll", "Toasted Pecan Laminated Twist", "Apple Compote Turnover", "Savory Ham Cheese Croissant"
        ],
        "quick-breads-scones": [
            "Zucchini Walnut Quick Bread", "Blueberry Lemon Glazed Scone", "Maple Pecan Oatmeal Scone", "Cranberry Orange Loaf",
            "Chocolate Chip Banana Bread", "Sharp Cheddar Herb Scone", "Spiced Pumpkin Ginger Bread", "Honey Butter Cornbread",
            "Vanilla Bean Blackberry Scone", "Apple Streusel Quick Loaf", "Savory Bacon Green Onion Scone", "Toasted Almond Poppyseed"
        ]
    }
    
    category_bases = bases.get(cat_slug, bases["cookies-shortbread"])
    
    variants = []
    descriptions = [
        "A beautiful, aromatic variant optimized to accentuate whole grain notes.",
        "A texture-focused twist featuring hydration adjustments for a softer bite.",
        "A premium profile featuring rich inclusion blending and deep flavor depth.",
        "An artisanal variation using custom preferment ratios for complex aromatics.",
        "A delightful variation balancing sweet/savory flavor tones and fine crumb.",
        "A rustic formula prioritizing crumb tenderness and high oven spring.",
        "A mouthwatering twist designed for uniform heat distribution and crispy edges.",
        "A sophisticated variation adding subtle spices to contrast the grain profile.",
        "A modern take with adjusted baking parameters to produce a stunning crust.",
        "A highly reliable recipe modification designed for consistent, delicious results."
    ]
    
    gen_idx = 0
    tweak_count = 0
    while len(variants) < count and gen_idx < len(category_bases) * 2:
        name = category_bases[gen_idx % len(category_bases)]
        if name.lower() not in exclude_set:
            variants.append({
                "name": name,
                "desc": f"{descriptions[tweak_count % len(descriptions)]} Perfect for pairing with active milled grains.",
                "menu_desc": f"{name} crafted to highlight the unique nuances of freshly milled flour."
            })
            tweak_count += 1
        gen_idx += 1
        
    return variants


def get_fallback_creativity_recipes(engine_id: str, active_archetype_id: str, pref_slugs: list) -> dict:
    cat_slug = engine_id
    if cat_slug not in ENGINE_FLAVORS:
        for k, v in CATEGORY_TO_ENGINE.items():
            if v == engine_id:
                cat_slug = k
                break
                
    flavors_data = ENGINE_FLAVORS.get(cat_slug)
    if not flavors_data:
        flavors_data = ENGINE_FLAVORS["cookies-shortbread"]
        
    recipes = []
    for lvl in [1, 2]:
        for idx, item in enumerate(flavors_data[lvl]):
            recipes.append({
                "recipe_id": f"{active_archetype_id}_level{lvl}_{idx+1}",
                "recipe_name": item["name"],
                "creativity_level": lvl,
                "description": item["desc"],
                "menu_description": f"A delightful artisanal version of {item['name']}, baked fresh with heritage grains."
            })
    return {"recipes": recipes}


def get_fallback_variants(engine_id: str, active_archetype_id: str, creativity_level: int, pref_slugs: list, exclude_names: list = None) -> dict:
    cat_slug = engine_id
    if cat_slug not in ENGINE_FLAVORS:
        for k, v in CATEGORY_TO_ENGINE.items():
            if v == engine_id:
                cat_slug = k
                break
                
    dynamic_items = generate_dynamic_flavors(cat_slug, creativity_level, count=5, exclude_names=exclude_names)
    
    variants = []
    for idx, item in enumerate(dynamic_items):
        variants.append({
            "variant_id": f"{active_archetype_id}_v{creativity_level}_alt{idx+1}",
            "variant_name": item["name"],
            "description": item["desc"],
            "menu_description": item.get("menu_desc", f"A delicious, elevated take on {item['name']}.")
        })
    return {"generated_variants": variants}

def _get_val(obj, key, default=None):
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def _is_ai_enabled() -> bool:
    """Checks if AI integration is active."""
    # Check database settings to see if AI is active
    return SystemSetting.get_val("ai_enabled", "False").lower() in ("true", "1", "t")


def _get_api_config() -> tuple[str, str]:
    """Retrieves API details from SystemSettings."""
    url = SystemSetting.get_val("ai_api_url", "http://host.docker.internal:11434/v1")
    model = SystemSetting.get_val("ai_model_name", "gemma:12b")
    # Clean completions URL if it doesn't end with chat/completions
    if not url.endswith("/chat/completions"):
        url = url.rstrip("/") + "/chat/completions"
    return url, model


def load_grain_registry():
    import os
    import json
    path = os.path.join(os.path.dirname(__file__), "grain_registry.json")
    with open(path, "r") as f:
        return json.load(f)


def get_grain_registry_profile(grain_name: str) -> dict:
    import re
    slug = re.sub(r'[^a-z0-9]', '_', grain_name.lower()).strip('_')
    slug = re.sub(r'_+', '_', slug)
    try:
        registry = load_grain_registry()
        grains = registry.get("grains", {})
        if slug in grains:
            return grains[slug]["intrinsic_chemical_profile"]
        for k, val in grains.items():
            if k in slug or slug in k:
                return val["intrinsic_chemical_profile"]
    except Exception:
        pass
    return {
        "crude_protein_percentage": "12.0%",
        "gluten_binding_capacity": "high",
        "pentosan_concentration": "low_standard",
        "bran_tannin_profile": "none_neutral"
    }


def get_archetype_mechanics(engine, active_archetype_id=None, preset_slug=None) -> tuple[str, dict]:
    archetypes = getattr(engine, "archetypes", {})
    archetype_data = None
    archetype_display = "Default Archetype"
    
    if active_archetype_id and active_archetype_id in archetypes:
        archetype_data = archetypes[active_archetype_id]
        archetype_display = archetype_data.get("label", active_archetype_id)
    elif preset_slug:
        slug_lower = preset_slug.lower()
        for k, v in archetypes.items():
            k_clean = k.replace("_", "-")
            label_clean = v.get("label", "").lower()
            if k_clean in slug_lower or slug_lower in k_clean or label_clean in slug_lower:
                archetype_data = v
                active_archetype_id = k
                archetype_display = v.get("label", k)
                break
                
    if archetype_data is None and archetypes:
        first_key = list(archetypes.keys())[0]
        archetype_data = archetypes[first_key]
        active_archetype_id = first_key
        archetype_display = archetype_data.get("label", first_key)

    if archetype_data:
        return archetype_display, archetype_data.get("target_archetype_mechanics", {
            "required_gluten_elasticity": "high_retention",
            "desired_horizontal_flow": "controlled_expansion",
            "moisture_lipid_ratio": "balanced_emulsion",
            "optimal_protein_window": "11.0% - 13.0%"
        })
    
    return "Default Archetype", {
        "required_gluten_elasticity": "high_retention",
        "desired_horizontal_flow": "controlled_expansion",
        "moisture_lipid_ratio": "balanced_emulsion",
        "optimal_protein_window": "11.0% - 13.0%"
    }


def calculate_local_compatibility_from_specs(wb, engine, preset_slug=None, active_archetype_id=None) -> dict:
    grain_profile = get_grain_registry_profile(wb.name)
    archetype_display, mechanics = get_archetype_mechanics(engine, active_archetype_id, preset_slug)
    
    try:
        gp = float(grain_profile["crude_protein_percentage"].replace("%", ""))
    except Exception:
        gp = getattr(wb, "protein_content", 12.0) or 12.0

    window_str = mechanics.get("optimal_protein_window", "11.0% - 13.0%")
    try:
        parts = window_str.replace("%", "").split("-")
        p_min = float(parts[0].strip())
        p_max = float(parts[1].strip())
    except Exception:
        p_min, p_max = 11.0, 13.0

    elasticity = mechanics.get("required_gluten_elasticity", "high_retention")
    binding = grain_profile.get("gluten_binding_capacity", "high")
    
    if p_min <= gp <= p_max:
        tier = "recommended"
    elif (p_min - 1.5) <= gp <= (p_max + 1.5):
        tier = "sub-optimal"
    else:
        tier = "not-recommended"

    if elasticity == "minimal_to_none" and binding in ["negligible", "moderate"]:
        tier = "recommended"
    elif elasticity == "extreme_tensile" and binding == "negligible":
        tier = "not-recommended"
    elif elasticity == "minimal_to_none" and binding == "extreme":
        tier = "not-recommended"

    justification = (
        f"At crude protein of {gp}%, the raw material aligns with the target window of {window_str}. "
        f"Gluten binding capacity of {binding} provides the necessary structural behaviour for {elasticity} elasticity requirements."
    )
    
    return {
        "tier": tier,
        "reasoning": justification
    }


def get_mock_gemma_response(system_prompt: str, user_prompt: str, expected_keys: list = None) -> dict | None:
    """
    Generates realistic, schema-compliant mock responses for offline testing/development.
    """
    import json
    try:
        user_data = json.loads(user_prompt)
    except Exception:
        user_data = {}

    if expected_keys and "evaluation_result" in expected_keys:
        grain_name = user_data.get("grain_name", "")
        from apps.core.models import WheatBerry
        wb = WheatBerry.objects.filter(name=grain_name).first()
        if not wb:
            grain_id = user_data.get("grain_id", "")
            wb = WheatBerry.objects.filter(id=grain_id).first()
        
        from grainlab.engines import router
        engine_id = user_data.get("engine_id", "hearth")
        active_archetype_id = user_data.get("active_archetype_id")
        
        engine = None
        try:
            engine = router.get_engine_by_id(engine_id)
        except Exception:
            pass
        if not engine:
            try:
                engine = router.get_engine_for_preset("", engine_id)
            except Exception:
                pass
            
        res = calculate_local_compatibility_from_specs(wb, engine, active_archetype_id=active_archetype_id)
        return {
            "evaluation_result": {
                "compatibility_tier": res["tier"].upper().replace("-", "_"),
                "technical_justification": res["reasoning"]
            }
        }

    if expected_keys and "shares" in expected_keys:
        berries = user_data.get("active_berries", [])
        shares = {}
        warning = None
        if not berries:
            return {"shares": {}, "structural_warning": None}
            
        if len(berries) == 2:
            shares[berries[0]["name"]] = 0.70
            shares[berries[1]["name"]] = 0.30
            warning = "This split is optimized to balance the strong gluten of the first grain with the extensibility or flavor profile of the second."
        else:
            equal_share = round(1.0 / len(berries), 2)
            for b in berries:
                shares[b["name"]] = equal_share
            shares[berries[-1]["name"]] += round(1.0 - sum(shares.values()), 2)
        return {"shares": shares, "structural_warning": warning}

    elif expected_keys and ("grain_evaluations" in expected_keys or "elevate_recipe" in expected_keys):
        preset_slug = user_data.get("preset_slug", "")
        category_slug = user_data.get("category_slug", "")
        preset_name = user_data.get("preset_name", "")
        inventory = user_data.get("inventory", [])
        
        from grainlab.engines import router
        engine = router.get_engine_for_preset(preset_slug, category_slug)
        
        evaluations = []
        for b in inventory:
            class MockBerry:
                def __init__(self, name, protein, hardness):
                    self.name = name
                    self.protein_content = protein
                    self.hardness = hardness
            wb = MockBerry(b.get("name"), b.get("protein", 12.0), b.get("hardness", "hard"))
            res = calculate_local_compatibility_from_specs(wb, engine, preset_slug)
            evaluations.append({
                "grain_id": b.get("id"),
                "tier": res["tier"],
                "reasoning": res["reasoning"]
            })
            
        elevate_recipe = [
            "Adjust initial water temperature to regulate yeast/enzymatic activity under current ambient conditions.",
            "Incorporate a 30-minute autolyse stage to fully hydrate raw bran and soften the structural network.",
            "Utilize gradual, gentle folding rather than intensive mechanical mixing to control gluten elasticity."
        ]
        
        return {
            "grain_evaluations": evaluations,
            "elevate_recipe": elevate_recipe,
            "mill_recommendation": {
                "mill_id": "mock-mill",
                "reasoning": "[MOCK] A stone mill is ideal to retain volatile aromatics for this category."
            },
            "sifted_recommendation": {
                "should_sift": False,
                "reasoning": "[MOCK] Whole grain bran provides essential structure and flavor depth."
            }
        }

    elif expected_keys and "recipes" in expected_keys:
        engine_id = user_data.get("engine_id", "hearth")
        active_archetype_id = user_data.get("active_archetype_id", "classic_sourdough")
        inventory = user_data.get("inventory", [])
        
        def grain_slug(g):
            return g.get("name", "").lower().replace(" ", "_").replace("/", "").replace("-", "_")

        hard_grains = [b for b in inventory if "hard" in b.get("hardness", "").lower()]
        soft_grains = [b for b in inventory if "soft" in b.get("hardness", "").lower() or b.get("hardness") == "ancient"]
        hard_slugs = [grain_slug(g) for g in hard_grains[:2]] or ["hard_red_spring_wheat"]
        soft_slugs = [grain_slug(g) for g in soft_grains[:2]] or ["soft_white_wheat"]
        pref_slugs = hard_slugs if engine_id in ["hearth", "pan", "bath", "pasta", "lean-crusty", "alkaline-bath", "fresh-pasta-noodles", "enriched-soft"] else soft_slugs

        return get_fallback_creativity_recipes(engine_id, active_archetype_id, pref_slugs)

    elif expected_keys and "generated_variants" in expected_keys:
        engine_id = user_data.get("engine_id", "hearth")
        active_archetype_id = user_data.get("active_archetype_id", "")
        creativity_level = user_data.get("creativity_level")
        exclude_names = user_data.get("exclude_names", [])

        inventory = user_data.get("inventory", [])
        hard_grains = [b for b in inventory if "hard" in b.get("hardness", "").lower()]
        soft_grains = [b for b in inventory if "soft" in b.get("hardness", "").lower() or b.get("hardness") == "ancient"]

        def grain_slug(g):
            return g.get("name", "").lower().replace(" ", "_").replace("/", "").replace("-", "_")

        hard_slugs = [grain_slug(g) for g in hard_grains[:2]] or ["hard_red_spring_wheat"]
        soft_slugs = [grain_slug(g) for g in soft_grains[:2]] or ["soft_white_wheat"]
        pref_slugs = hard_slugs if engine_id in ["hearth", "pan", "bath", "pasta", "lean-crusty", "alkaline-bath", "fresh-pasta-noodles", "enriched-soft"] else soft_slugs

        c_lvl = int(creativity_level) if creativity_level is not None else 1
        return get_fallback_variants(engine_id, active_archetype_id, c_lvl, pref_slugs, exclude_names=exclude_names)

    elif expected_keys and "pitfalls" in expected_keys:
        return {
            "pitfalls": [
                {
                    "title": "High Hydration Sticky Zone",
                    "message": "The formula hydration is high relative to your grain blend. Ensure you use stretch-and-fold techniques rather than intensive mechanical kneading to maintain structure without tearing the gluten sheets."
                }
            ]
        }

    elif expected_keys and "sensory_description" in expected_keys:
        return {
            "sensory_description": "The dough should feel smooth, highly extensible, and slightly tacky but not sticky. It should hold its shape when rounded and show early signs of gas bubbles forming under the surface skin."
        }

    elif expected_keys and "geometry_evaluation" in expected_keys:
        return {
            "geometry_evaluation": {
                "status": "recommended",
                "advisory_label": "Excellent heat transfer properties and moisture retention, allowing the dough to expand fully before the crust sets.",
                "profile_adjustments": {
                    "oven_temp_offset_f": 0,
                    "bake_time_offset_m": 0,
                    "steam_override": "no-change"
                }
            }
        }

    elif expected_keys and "recommendation_tier" in expected_keys:
        hovered = user_data.get("hovered_element", "").lower()
        preset = user_data.get("preset_slug", "")
        category = user_data.get("category_slug", "")
        
        from grainlab.engines import router
        engine = router.get_engine_for_preset(preset, category)
        
        class MockBerry:
            def __init__(self, name):
                self.name = name
                self.protein_content = 12.0
                self.hardness = "hard"
        wb = MockBerry(hovered)
        res = calculate_local_compatibility_from_specs(wb, engine, preset)
        
        return {
            "recommendation_tier": res["tier"],
            "labor_roi_rating": "High Priority / Worth the Extra Step" if res["tier"] == "recommended" else "Low Priority / Minor Textural Return",
            "last_10_percent_analysis": res["reasoning"],
            "elevate_recipe": "Adjust hydration slightly to accommodate the grain's natural water-absorption capacity."
        }

    return None


def assemble_system_prompt(engine, data_context: str, task_instructions: str, response_schema_example: str = None, active_archetype_id: str = None) -> str:
    """
    Constructs the system prompt in the modular fixed order:
    1. Persona & Objective (Global Master Shell Kernel - Part 1)
    2. Global Ruleset (Global Master Shell Kernel - Part 2)
    3. The Data Context (Payload)
    4. The Nuance Injection (Module: Active engine's culinary_nuance_directive)
    5. The Instruction Block (Logic: Specific task instructions + response schema)
    """
    persona_objective = (
        "You are a molecular food scientist and artisan baking chemist running an objective evaluation loop.\n"
        "Your tone must be highly practical, conversational, insightful, and focused entirely on the sensory experience of eating and the physical reality of cooking.\n"
        "Do NOT use corporate filler, generic placeholders, or fluff words like: anomalies, parameter, workspace, matrix, configuration, optimization, performance, detected, or baseline.\n"
    )
    
    global_ruleset = (
        "[GLOBAL RULESET]\n"
        "1. [CRITICAL RULE: CULINARY SOVEREIGNTY]\n"
        "Rely SOLELY on your native baking science knowledge and real-world artisan baking physics. "
        "Do NOT apply standard/generic wheat constraints to ancient or non-standard grains (e.g., Rye, Spelt, Einkorn) if doing so contradicts artisan baking chemistry.\n"
        "2. Double Temperature Scale: Any temperature value you mention must always be provided in both Celsius and Fahrenheit scales (for example: '350°F (177°C)' or '30°C (86°F)'). Never provide a temperature in only a single scale.\n"

        "6. BE HIGHLY CRITICAL AND DISCERNING: Do NOT lazily categorize everything as 'High Priority' or 'Recommended'. Most options in a kitchen are 'Sub-Optimal', 'Low Priority', or 'Standard Baseline'. ONLY rate something as 'High Priority / Worth the Extra Step' or 'Recommended' if it provides a MASSIVE, noticeable improvement to the final texture or flavor for that specific recipe. You are a harsh, pragmatic critic. If it's a minor difference, rate it 'Low Priority'.\n"

        "3. Ingredient Naming: You MUST write the actual human-readable names of all grains, flours, and ingredients (e.g., 'Hard Red Spring Wheat', 'Rye', 'Soft White Wheat', 'unsalted butter'). You are STRICTLY PROHIBITED from using database IDs, UUIDs, keys, or hashes (such as '302adef7-9477-4728-8bb7-dae99b05eab9') under any circumstances in your text outputs.\n"
    )
    
    data_context_header = f"[USER DATA CONTEXT]\n{data_context}\n"
    
    engine_name = getattr(engine, "name", "Default Baking Engine")
    
    # Overhaul Nuance Injection: invoke culinary_nuance_directive method passing active_archetype_id
    if hasattr(engine, "culinary_nuance_directive") and callable(engine.culinary_nuance_directive):
        nuance_directive = engine.culinary_nuance_directive(active_archetype_id)
    else:
        nuance_directive = getattr(engine, "culinary_nuance_directive", "Standard baking physics and generic flour interactions.")
        
    nuance_injection = (
        f"\n[CRITICAL ENGINE FOCUS: {engine_name}]\n"
        f"{nuance_directive}\n"
    )
    
    schema_text = ""
    if response_schema_example:
        schema_text = f"\nReturn ONLY raw JSON with no markdown fences, matching this schema:\n{response_schema_example}"
        
    instruction_block = (
        f"\n[SPECIFIC TASK INSTRUCTIONS]\n"
        f"{task_instructions}\n"
        f"{schema_text}"
    )
    
    prompt = [
        persona_objective,
        global_ruleset,
        data_context_header,
        nuance_injection,
        instruction_block
    ]
    return "".join(prompt)


def heal_json_string(raw_str: str) -> str:
    """
    Sanitizes raw text streams before they are evaluated by the strict system JSON interpreter.
    Repairs mismatched braces/brackets due to truncation and strips trailing commas.
    """
    if not raw_str:
        return ""

    cleaned = raw_str.strip()

    # Find starting brace/bracket
    first_brace = cleaned.find('{')
    first_bracket = cleaned.find('[')
    
    start_idx = -1
    if first_brace != -1 and first_bracket != -1:
        start_idx = min(first_brace, first_bracket)
    elif first_brace != -1:
        start_idx = first_brace
    elif first_bracket != -1:
        start_idx = first_bracket
        
    if start_idx != -1:
        cleaned = cleaned[start_idx:]

    # Clean markdown code blocks fences if they are at the end
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()

    # Balance structural truncations: count open vs closed braces and brackets in a stack
    stack = []
    in_string = False
    escape = False
    
    import re
    i = 0
    n = len(cleaned)
    while i < n:
        char = cleaned[i]
        if escape:
            escape = False
        elif char == '\\':
            escape = True
        elif char == '"':
            in_string = not in_string
        elif not in_string:
            if char in ('{', '['):
                stack.append(char)
            elif char == '}':
                if '{' in stack:
                    while stack:
                        pop_char = stack.pop()
                        if pop_char == '{':
                            break
            elif char == ']':
                if '[' in stack:
                    while stack:
                        pop_char = stack.pop()
                        if pop_char == '[':
                            break
        i += 1

    if in_string:
        cleaned += '"'

    # Strip dangling separators: trailing commas right before closing braces or brackets,
    # or at the very end of the string.
    cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
    cleaned = re.sub(r',\s*$', '', cleaned)

    # Append missing closing delimiters in LIFO order
    while stack:
        pop_char = stack.pop()
        if pop_char == '{':
            cleaned += '}'
        elif pop_char == '[':
            cleaned += ']'

    # Double check trailing commas again after healing
    cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
    
    return cleaned


def call_gemma_api(system_prompt: str, user_prompt: str, expected_keys: list = None) -> dict | None:
    """
    Submits a structured prompt to local Gemma and parses the JSON response.
    Caches results persistently using Django file cache framework.
    Returns None if any step fails.
    """
    if not _is_ai_enabled():
        return None

    import hashlib
    # Normalize user_prompt to ensure consistent caching key
    normalized_user_prompt = user_prompt
    try:
        data = json.loads(user_prompt)
        if isinstance(data, dict):
            # Sort lists to avoid cache misses due to order variance
            for k, v in list(data.items()):
                if isinstance(v, list):
                    try:
                        data[k] = sorted(v)
                    except Exception:
                        pass
            normalized_user_prompt = json.dumps(data, sort_keys=True)
    except Exception:
        pass

    # Compute MD5 hash of prompts as cache key
    raw_key = f"{system_prompt}|||{normalized_user_prompt}"
    cache_key = hashlib.md5(raw_key.encode("utf-8")).hexdigest()

    cached_val = cache.get(cache_key)
    if cached_val:
        logger.info(f"[AI] - Cache Hit - Key: {cache_key}")
        return cached_val

    logger.info(f"[AI] - API Call Init -\nSYSTEM PROMPT:\n{system_prompt}\nUSER PROMPT:\n{normalized_user_prompt}")

    # Check if offline mock mode is active
    if getattr(settings, "MOCK_MODE", True):
        res = get_mock_gemma_response(system_prompt, normalized_user_prompt, expected_keys)
        logger.info(f"[AI] - Mock Mode Response: {res}")
        if res:
            cache.set(cache_key, res, timeout=None)
        return res

    url, model = _get_api_config()
    headers = {
        "Content-Type": "application/json"
    }
    
    # Retrieve thinking mode settings
    ai_thinking_enabled = SystemSetting.get_val("ai_thinking_enabled", "True") == "True"
    ai_thinking_effort = SystemSetting.get_val("ai_thinking_effort", "medium")

    # Inject directives into system prompt
    if ai_thinking_enabled:
        system_prompt += f"\n[CRITICAL] Use thorough reasoning and step-by-step thinking (thinking effort: {ai_thinking_effort}) before responding."
    else:
        system_prompt += "\n[CRITICAL] Do NOT use thinking/reasoning steps. Respond immediately with the direct answer."

    # Force JSON format if supported
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt + " You MUST respond with raw JSON ONLY. No markdown formatting, no codeblocks."},
            {"role": "user", "content": normalized_user_prompt}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    # Pass reasoning_effort if supported by target endpoint (e.g. OpenAI/Ollama compatible)
    if ai_thinking_enabled:
        payload["reasoning_effort"] = ai_thinking_effort

    try:
        # Enforce a 60-second timeout to allow the model sufficient time to load and generate responses
        response = requests.post(url, headers=headers, json=payload, timeout=60.0)
        logger.info(f"[AI] - HTTP Response Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            content_str = data["choices"][0]["message"]["content"].strip()
            logger.info(f"[AI] - Raw Content Received: {content_str}")
            
            # Clean possible markdown wrap ```json ... ```
            if content_str.startswith("```"):
                lines = content_str.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    content_str = "\n".join(lines[1:-1])
            
            # Resilient JSON Processing Gate: heal the JSON string
            healed_content_str = heal_json_string(content_str)
            try:
                parsed_json = json.loads(healed_content_str)
            except Exception as parse_err:
                logger.error(f"[AI] - Parsing Failed - Error: {parse_err}. Raw: {content_str}. Healed: {healed_content_str}")
                parsed_json = json.loads(content_str)
            logger.info(f"[AI] - Parsed JSON: {parsed_json}")
            
            # Validate keys if requested
            if expected_keys:
                if not all(k in parsed_json for k in expected_keys):
                    logger.warning(f"[AI] - Parsing - Response missing expected keys {expected_keys}")
                    return None
            
            cache.set(cache_key, parsed_json, timeout=None)
            return parsed_json
        else:
            logger.error(f"[AI] - HTTP Error - Endpoint returned status {response.status_code}\nRESPONSE BODY:\n{response.text}")
    except requests.Timeout:
        logger.warning("[AI] - Timeout - Gemma server timed out.")
    except Exception as e:
        logger.error(f"[AI] - Error - Failed calling local Gemma: {str(e)}")
        
    return None


# 1. Contextual Pitfall Analysis & Special Step Injection
def get_contextual_pitfalls(category_slug: str, effective_hydration: float, grain_type: str, preset_slug: str = None) -> list:
    """
    Retrieves pitfall analysis from Gemma, falling back to local python rules.
    """
    if _is_ai_enabled():
        system_prompt = (
            "Analyze the recipe variables and identify potential baking pitfalls "
            "or custom step additions (e.g., pretzel soda boiling, high-hydration sticky dough). "
            "You MUST tailor your critique specifically to the active baking category and preset. "
            "Do NOT mention ingredients or processes (e.g., yeast, rising, kneading, proofing, bread ovens, steam) that are not part of the target recipe class. For example, do not mention yeast or proofing for cookies/cakes, and do not mention cookie spread or creaming for sourdough/pizza. "
            "Return a JSON object containing a list called 'pitfalls' where each item has "
            "'title' and 'message' keys."
        )
        user_prompt = json.dumps({
            "category": category_slug,
            "hydration_pct": effective_hydration,
            "grain_type": grain_type,
            "preset": preset_slug,
        })
        
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["pitfalls"])
        if result and isinstance(result.get("pitfalls"), list):
            return result["pitfalls"]

    # Fallback to local python rule engine
    return get_local_contextual_pitfalls(category_slug, effective_hydration, grain_type, preset_slug)


# 2. Custom Sensory Benchmark Synthesizer
def get_sensory_benchmark(grain_type: str, flour_maturity: str, effective_hydration: float, category_slug: str = None, preset_slug: str = None) -> str:
    """
    Retrieves sensory text from Gemma, falling back to local description mappings.
    """
    if _is_ai_enabled():
        system_prompt = (
            "You are a baking science expert. Synthesize a descriptive sensory benchmark describing what the mixture (dough, batter, or paste) should look "
            "and feel like (texture, touch resilience, structure, visual indicators) "
            "based on the flour maturity and grain type. "
            "You MUST tailor your description specifically to the active recipe category and preset. Do NOT mention ingredients or processes "
            "(e.g., yeast, rising, kneading, proofing, bubbles) that are not part of the target recipe class. For example, do not mention rising or yeast for cookies, and do not mention cookie spread or creaming for sourdough."
            "Return a JSON object with the key 'sensory_description'."
        )
        user_prompt = json.dumps({
            "grain_type": grain_type,
            "flour_maturity": flour_maturity,
            "hydration": effective_hydration,
            "category": category_slug,
            "preset": preset_slug,
        })
        
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["sensory_description"])
        if result and result.get("sensory_description"):
            return result["sensory_description"]

    # Fallback
    return get_local_sensory_benchmark(grain_type, flour_maturity, effective_hydration, category_slug, preset_slug)


# 3. Closed-Loop Chemistry Re-Balancing (Substitutions)
def get_substitution_offset(original_ing: str, substitute_ing: str, current_recipe: dict) -> dict:
    """
    Retrieves mathematical hydration/fat offsets from Gemma, falling back to local logic.
    """
    if _is_ai_enabled():
        system_prompt = (
            "Analyze an ingredient swap (substitution) in baking. You must determine the exact composition of the SUBSTITUTE ingredient. "
            "Return a JSON object with: "
            "'substitute_water_pct' (float, between 0.0 and 1.0, e.g., 0.87 for milk), "
            "'substitute_fat_pct' (float, between 0.0 and 1.0, e.g., 0.04 for milk), "
            "'substitute_sugar_pct' (float, between 0.0 and 1.0, e.g., 0.05 for milk), "
            "and 'explanation' (string detailing the chemical makeup)."
        )
        user_prompt = json.dumps({
            "original": original_ing,
            "substitute": substitute_ing,
        })
        
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["substitute_water_pct", "substitute_fat_pct"])
        if result:
            try:
                water_pct = float(result.get("substitute_water_pct", 1.0))
                fat_pct = float(result.get("substitute_fat_pct", 0.0))
                sugar_pct = float(result.get("substitute_sugar_pct", 0.0))
                explanation = result.get("explanation", "Calculated mathematically based on AI ingredient composition.")
                
                # Math logic for perfect dough hydration balance:
                if original_ing == "water" and water_pct > 0:
                    multiplier = 1.0 / water_pct
                    return {
                        "water_offset_pct": round(multiplier - 1.0, 3),
                        "fat_offset_pct": -round(multiplier * fat_pct, 3),
                        "sugar_offset_pct": -round(multiplier * sugar_pct, 3),
                        "explanation": explanation
                    }
                elif original_ing == "fat" and fat_pct > 0:
                    multiplier = 1.0 / fat_pct
                    return {
                        "water_offset_pct": -round(multiplier * water_pct, 3),
                        "fat_offset_pct": round(multiplier - 1.0, 3),
                        "sugar_offset_pct": -round(multiplier * sugar_pct, 3),
                        "explanation": explanation
                    }
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.warning(f"[Gemma Client] - Warning - AI returned malformed composition numbers: {e}")

    # Fallback default math-based offset objects matching our local engine
    # In view layer, we process substitutions natively; gemma client returns standard defaults matching bakers_math
    if original_ing == "water" and substitute_ing == "whole_milk":
        return {
            "water_offset_pct": 0.15,  # Needs 15% more volume to reach same water level
            "fat_offset_pct": -0.046,  # Reduces fat by 4.6% of flour weight
            "sugar_offset_pct": -0.057,
            "explanation": "Whole Milk is 87% water, 4% fat, and 5% sugar. Hydration increased to compensate for milk solids, and fat/sugar weights reduced."
        }
    elif original_ing == "water" and substitute_ing == "almond_milk":
        return {
            "water_offset_pct": 0.03,
            "fat_offset_pct": -0.01,
            "sugar_offset_pct": 0.0,
            "explanation": "Almond Milk is 97% water, 1% fat. Liquid volume increased by 3% to compensate for solids."
        }
    elif original_ing == "fat" and substitute_ing == "butter":
        return {
            "water_offset_pct": -0.225, # Subtract water content
            "fat_offset_pct": 0.25,     # Requires 25% more butter weight
            "sugar_offset_pct": 0.0,
            "explanation": "Butter contains 80% fat and 18% water. Butter weight scaled up by 25% and formula hydration decreased to balance water input."
        }
        
    return {
        "water_offset_pct": 0.0,
        "fat_offset_pct": 0.0,
        "sugar_offset_pct": 0.0,
        "explanation": "No adjustments required."
    }


# 4. Structured Milling Profile & Sourdough Diagnostic Calibration
def calibrate_fermentation(starter_feed_hours: str, rise_speed: str, mill_type: str, is_sifted: bool) -> dict:
    """
    Computes diagnostic parameters based on sourdough activity and sifting factors.
    """
    if _is_ai_enabled():
        system_prompt = (
            "Calibrate bulk fermentation countdown targets and ash estimate based on "
            "starter feeding schedule and milling profile. Return a JSON object with: "
            "'ash_content_estimate' (float), 'estimated_bulk_fermentation_hours' (float), "
            "and 'notes' (string)."
        )
        user_prompt = json.dumps({
            "starter_feed_hours": starter_feed_hours,
            "rise_speed": rise_speed,
            "mill_type": mill_type,
            "is_sifted": is_sifted,
        })
        
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["estimated_bulk_fermentation_hours", "ash_content_estimate"])
        if result:
            return result

    # Fallback calculations based on bread-science equations
    # Ash estimate: stoneground = 1.5%, steel roller = 0.5%. Sifting reduces ash by 0.3%.
    ash = 1.5 if mill_type == "stoneground" else 0.5
    if is_sifted:
        ash = max(0.4, ash - 0.3)
        
    # Fermentation target: active feed (4-8 hours) = 4 hours bulk, slow feed (12+ hours) = 7 hours bulk
    hours = 4.0
    if starter_feed_hours == "12_18":
        hours = 6.0
    elif starter_feed_hours == "18_plus":
        hours = 8.0
        
    if rise_speed == "slow":
        hours += 1.5
    elif rise_speed == "fast":
        hours = max(3.0, hours - 1.0)
        
    notes = (
        f"Milling profile: {mill_type} (sifted={is_sifted}). Estimated ash content of {ash}%. "
        f"Starter fed {starter_feed_hours.replace('_', '-')} hours ago shows {rise_speed} activity. "
        f"Target bulk fermentation set to {hours} hours."
    )
    
    return {
        "ash_content_estimate": ash,
        "estimated_bulk_fermentation_hours": hours,
        "notes": notes,
    }


def analyze_wheat_berry_ai(name: str) -> dict | None:
    """
    Asks Gemma to estimate protein content, hardness, moisture absorption, and notes for a wheat berry.
    """
    system_prompt = (
        "You are a food science assistant. Analyze the wheat berry name provided and estimate its properties. "
        "Return a JSON object with keys: "
        "'protein_content' (float, default 12.0), "
        "'hardness' (string: 'hard', 'soft', 'durum', or 'ancient'), "
        "'moisture_absorption_coef' (float, default 1.0; standard AP is 1.0, whole wheat is 1.03, spelt is 1.05, durum is 1.08, einkorn is 1.04), "
        "and 'notes' (string, summary description of properties)."
    )
    user_prompt = json.dumps({"name": name})
    
    if _is_ai_enabled():
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["protein_content", "hardness", "moisture_absorption_coef"])
        if result:
            try:
                result["protein_content"] = float(result.get("protein_content", 12.0))
                result["moisture_absorption_coef"] = float(result.get("moisture_absorption_coef", 1.0))
                result["hardness"] = str(result.get("hardness", "hard")).lower()
                if result["hardness"] not in ('hard', 'soft', 'durum', 'ancient'):
                    result["hardness"] = 'hard'
                result["notes"] = str(result.get("notes", "Analyzed via local Gemma model."))
                return result
            except Exception as e:
                logger.error(f"[AI] - Parsing - Failed converting wheat berry analysis data: {e}")
    
    # Fallback/mock responses if AI disabled or api fails
    name_lower = name.lower()
    if "spelt" in name_lower:
        return {"protein_content": 11.5, "hardness": "ancient", "moisture_absorption_coef": 1.05, "notes": "Ancient grain with highly water-soluble gluten. Adds nutty flavor."}
    elif "einkorn" in name_lower:
        return {"protein_content": 12.5, "hardness": "ancient", "moisture_absorption_coef": 1.04, "notes": "Most ancient cultivated wheat. Soft gluten, rich yellow carotenoids."}
    elif "soft" in name_lower or "white" in name_lower:
        return {"protein_content": 9.5, "hardness": "soft", "moisture_absorption_coef": 0.97, "notes": "Low protein, weak gluten. Ideal for tender pastries, cookies, and soft rolls."}
    elif "durum" in name_lower or "semolina" in name_lower:
        return {"protein_content": 13.5, "hardness": "durum", "moisture_absorption_coef": 1.08, "notes": "Extremely hard durum wheat. Provides yellow tint and high stretch resilience."}
    elif "spring" in name_lower:
        return {"protein_content": 14.5, "hardness": "hard", "moisture_absorption_coef": 1.02, "notes": "High protein spring wheat. Extremely strong gluten, excellent for sourdough."}
    else:
        return {"protein_content": 13.0, "hardness": "hard", "moisture_absorption_coef": 1.0, "notes": "Standard hard wheat berry. Good gluten strength for general crusty breads."}


def analyze_equipment_ai(name: str, equipment_type: str) -> dict | None:
    """
    Asks Gemma to estimate friction heat factor and notes/details for an equipment item.
    """
    system_prompt = (
        "You are a food science assistant. Analyze the equipment name and type provided and estimate its specifications. "
        "Return a JSON object with keys: "
        "'friction_heat_factor' (float, friction temperature rise in Fahrenheit. For mixers/kneaders, standard stand mixers add 10.0, Ankarsrum/spiral mixers add 6.0, manual hand kneading is 2.0, bread machines add 15.0. For other non-mixer equipment type, return 0.0), "
        "'notes' (string, summary description of capabilities and recommendations), "
        "and 'details' (JSON object containing other details like 'capacity_grams' (integer, estimated capacity) or 'recommended_speed' (string))."
    )
    user_prompt = json.dumps({"name": name, "type": equipment_type})

    if _is_ai_enabled():
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["friction_heat_factor", "notes", "details"])
        if result:
            try:
                result["friction_heat_factor"] = float(result.get("friction_heat_factor", 0.0))
                result["notes"] = str(result.get("notes", "Analyzed via local Gemma model."))
                if not isinstance(result.get("details"), dict):
                    result["details"] = {}
                return result
            except Exception as e:
                logger.error(f"[AI] - Parsing - Failed converting equipment analysis data: {e}")

    # Fallback/mock responses if AI disabled or api fails
    name_lower = name.lower()
    if equipment_type == "mixer":
        if "kitchenaid" in name_lower or "classic" in name_lower:
            return {
                "friction_heat_factor": 10.0,
                "notes": "Planetary stand mixer. High speed mixing can introduce significant heat to dough.",
                "details": {"capacity_grams": 1000, "recommended_speed": "Speed 2"}
            }
        elif "ankarsrum" in name_lower or "spiral" in name_lower:
            return {
                "friction_heat_factor": 6.0,
                "notes": "Rotating bowl spiral mixer. Low friction design, preserves dough temperature well.",
                "details": {"capacity_grams": 2500, "recommended_speed": "Medium low"}
            }
        elif "machine" in name_lower:
            return {
                "friction_heat_factor": 15.0,
                "notes": "Enclosed bread machine motor. High friction and heat generation.",
                "details": {"capacity_grams": 800, "recommended_speed": "Automatic"}
            }
        else:
            return {
                "friction_heat_factor": 8.0,
                "notes": "Standard dough mixer. Moderate friction heating.",
                "details": {"capacity_grams": 1200}
            }
    elif equipment_type == "mill":
        return {
            "friction_heat_factor": 0.0,
            "notes": "Grain mill for processing wheat berries. Check stone temp during long runs to avoid overheating flour.",
            "details": {"capacity_grams": 500}
        }
    else:
        return {
            "friction_heat_factor": 0.0,
            "notes": "Baking accessory helper.",
            "details": {}
        }


def optimize_grain_blend(preset_slug: str, preset_name: str, active_berries: list) -> tuple[dict, str | None] | None:
    """
    Queries Gemma model to optimize the percentage blend of active wheat berries
    for a specific bread preset.
    Returns: (shares_dict, structural_warning) or None
    """
    if not _is_ai_enabled():
        return None
        
    system_prompt = (
        "You are a food science assistant specializing in flour milling. "
        "Analyze the requested bread preset and the active wheat berries available. "
        "Optimize the percentage blend (between 0.0 and 1.0, summing to 1.0) of each active wheat berry "
        "to achieve the best structural and flavor profile for the preset. "
        "If the preset is a high-rise bread (like Boule, Baguette, Ciabatta, French Loaf, Pizza, Bagel) "
        "and the user has selected a blend that lacks sufficient gluten strength (e.g. too much soft wheat/ancient grains), "
        "you MUST set 'structural_warning' to a warning string explaining the hazard, and adjust the blend to include "
        "at least 70% of a hard/structural wheat berry. "
        "Return a JSON object containing:\n"
        "1. 'shares': a dictionary mapping each active wheat berry name to its float share (e.g., {\"Hard Red Spring Wheat\": 0.7, \"Soft White Wheat\": 0.3})\n"
        "2. 'structural_warning': a string warning if the configuration is impossible/unsafe, or null/empty if safe."
    )
    
    # Serialize berries to simple representation for the model
    berries_data = []
    for b in active_berries:
        berries_data.append({
            "name": _get_val(b, 'name'),
            "protein_content": _get_val(b, 'protein_content', 12.0),
            "hardness": _get_val(b, 'hardness', 'hard'),
            "moisture_absorption_coef": _get_val(b, 'moisture_absorption_coef', 1.0)
        })
        
    user_prompt = json.dumps({
        "preset_slug": preset_slug,
        "preset_name": preset_name,
        "active_berries": berries_data
    })
    
    result = call_gemma_api(system_prompt, user_prompt, expected_keys=["shares"])
    if result and isinstance(result.get("shares"), dict):
        return result.get("shares"), result.get("structural_warning")
    return None


def get_grain_advisory_ai(
    preset_slug: str,
    category_slug: str = None,
    selected_grains: str = None,
    only_evaluations: bool = False,
    only_elevate: bool = False,
    preset_name: str = None,
    active_archetype_id: str = None,
    lipid: str = None,
    liquid: str = None,
    binder: str = None
) -> dict | None:
    """
    Evaluates raw kitchen inventory against target archetype mechanics using the dynamic pipeline.
    """
    from apps.core.models import WheatBerry, BreadPreset
    from grainlab.engines import router
    import json
    
    preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
    if not category_slug and preset and preset.dough_category:
        category_slug = preset.dough_category.slug
    engine = router.get_engine_for_preset(preset_slug, category_slug)
    
    active_berries = list(WheatBerry.objects.filter(is_active=True))
    if not active_berries:
        return {"grain_evaluations": [], "elevate_recipe": []}

    if _is_ai_enabled():
        selected_ids = [s.strip() for s in selected_grains.split(",") if s.strip()] if selected_grains else []
        selected_berries = [wb for wb in active_berries if str(wb.id) in selected_ids]
        selected_names = [wb.name for wb in selected_berries]

        archetype_display, mechanics = get_archetype_mechanics(engine, active_archetype_id, preset_slug)

        # Resolve recommended grains and specialty ingredients natively part of the preset_slug
        recommended_slugs = []
        specialty_ingredients = []
        
        # Read specialty inclusions directly from the localized request payload at the moment of execution
        has_selections = (lipid is not None) or (liquid is not None) or (binder is not None)
        if has_selections:
            if lipid and lipid != "none":
                specialty_ingredients.append(lipid.replace("_", " "))
            if liquid and liquid != "none" and liquid != "pure_water" and liquid != "water":
                specialty_ingredients.append(liquid.replace("_", " "))
            if binder and binder != "none":
                specialty_ingredients.append(binder.replace("_", " "))
        elif preset_slug:
            native_details = get_local_recipe_details(
                recipe_slug=preset_slug,
                recipe_name=preset_name or preset_slug,
                engine_id=engine.slug if engine else "default",
                active_archetype_id=active_archetype_id or "default",
                selected_grains=selected_grains
            )
            recommended_slugs = native_details.get("recommended_grain_ids", [])
            sec_ingredients = native_details.get("secondary_ingredients", {})
            native_lipid = sec_ingredients.get("lipids", {}).get("required", "none")
            native_liquid = sec_ingredients.get("liquids", {}).get("required", "pure_water")
            native_binder = sec_ingredients.get("binders", {}).get("required", "none")
            
            if native_lipid != "none":
                specialty_ingredients.append(native_lipid.replace("_", " "))
            if native_liquid != "none" and native_liquid != "pure_water" and native_liquid != "water":
                specialty_ingredients.append(native_liquid.replace("_", " "))
            if native_binder != "none":
                specialty_ingredients.append(native_binder.replace("_", " "))
                
        # Resolve recommended grain names from slugs
        native_grain_names = []
        for slug in recommended_slugs:
            for wb in active_berries:
                import re
                wb_slug = re.sub(r'[^a-z0-9]', '_', wb.name.lower()).strip('_')
                wb_slug = re.sub(r'_+', '_', wb_slug)
                if wb_slug == slug or slug in wb_slug or wb_slug in slug:
                    native_grain_names.append(wb.name)
                    break
        
        # If the user has not selected an item, pass empty array bounds [] to force the model to reason about macro mechanics
        if selected_names:
            active_grains_list = selected_names
        else:
            active_grains_list = []

        expected_keys = ["grain_evaluations", "elevate_recipe"]

        if only_evaluations:
            from apps.core.models import Equipment
            mills = Equipment.objects.filter(equipment_type='mill').order_by('name')
            mills_text = "\n".join([f"- {m.id} ({m.name})" for m in mills])
            
            data_context = (
                f"[TARGET PRODUCTION ARCHETYPE MECHANICS]\n"
                f"* Core Archetype: {archetype_display} (Engine: {getattr(engine, 'name', 'Default')})\n"
                f"* Required Gluten Elasticity: {mechanics.get('required_gluten_elasticity')}\n"
                f"* Desired Horizontal Flow: {mechanics.get('desired_horizontal_flow')}\n"
                f"* Moisture/Lipid Ratio: {mechanics.get('moisture_lipid_ratio')}\n"
                f"* Target Protein Window: {mechanics.get('optimal_protein_window')}\n"
                f"\n[AVAILABLE MILL MACHINERY]\n{mills_text}\n"
            )
            task_instructions = (
                "Evaluate each raw material grain against the mechanics and assign RECOMMENDED, SUB-OPTIMAL, or NOT RECOMMENDED compatibility tier, and write a 2-sentence chemistry justification.\n"
                "Also evaluate the milling setup: recommend whether bran separation (sifted high-extraction flour) or whole grain (unsifted) is optimal for this archetype, and explain why in 1 sentence.\n"
                "Also recommend the best mill type from the list provided (if any), with a 1-sentence reason."
            )
            response_schema = (
                "{\n"
                "  \"grain_evaluations\": [\n"
                "    {\n"
                "      \"grain_id\": \"string (UUID of the grain)\",\n"
                "      \"tier\": \"recommended | sub-optimal | not-recommended\",\n"
                "      \"reasoning\": \"A concise 2-sentence analytical justification.\"\n"
                "    }\n"
                "  ],\n"
                "  \"mill_recommendation\": {\n"
                "    \"mill_id\": \"string (ID of the recommended mill, or null if no preference)\",\n"
                "    \"reasoning\": \"1 sentence explaining why this mill is best for the archetype.\"\n"
                "  },\n"
                "  \"sifted_recommendation\": {\n"
                "    \"should_sift\": true,\n"
                "    \"reasoning\": \"1 sentence explaining whether bran separation helps or hurts this recipe type.\"\n"
                "  }\n"
                "}"
            )
            system_prompt = assemble_system_prompt(engine, data_context, task_instructions, response_schema, active_archetype_id=active_archetype_id)
            expected_keys = ["grain_evaluations"]
        elif only_elevate:
            data_context = (
                f"[TARGET PRODUCTION ARCHETYPE MECHANICS]\n"
                f"* Core Archetype: {archetype_display} (Engine: {getattr(engine, 'name', 'Default')})\n"
                f"* Required Gluten Elasticity: {mechanics.get('required_gluten_elasticity')}\n"
                f"* Desired Horizontal Flow: {mechanics.get('desired_horizontal_flow')}\n"
                f"* Moisture/Lipid Ratio: {mechanics.get('moisture_lipid_ratio')}\n"
                f"* Target Protein Window: {mechanics.get('optimal_protein_window')}\n"
            )
            task_instructions = (
                "Given the active selected material inputs and target archetype mechanics, "
                "suggest 3 to 5 distinct ways to enhance the physical and chemical outcome of the formulation.\n"
                "🚨 [CRITICAL INPUT CONTEXT SANITY CHECK]\n"
                "You are STRICTLY PROHIBITED from mentioning, recommending, or referencing any grains, modifiers, or specialty ingredients "
                "that are not explicitly provided in the user prompt payload. For example, if rye is not in the list of grains, "
                "do NOT mention rye modifiers, and if eggs are not in the specialty ingredients, do NOT mention egg-based adjustments."
            )
            response_schema = (
                "{\n"
                "  \"elevate_recipe\": [\"suggestion 1\", \"suggestion 2\"]\n"
                "}"
            )
            system_prompt = assemble_system_prompt(engine, data_context, task_instructions, response_schema, active_archetype_id=active_archetype_id)
            expected_keys = ["elevate_recipe"]
        else:
            data_context = (
                f"[TARGET PRODUCTION ARCHETYPE MECHANICS]\n"
                f"* Core Archetype: {archetype_display} (Engine: {getattr(engine, 'name', 'Default')})\n"
                f"* Required Gluten Elasticity: {mechanics.get('required_gluten_elasticity')}\n"
                f"* Desired Horizontal Flow: {mechanics.get('desired_horizontal_flow')}\n"
                f"* Moisture/Lipid Ratio: {mechanics.get('moisture_lipid_ratio')}\n"
                f"* Target Protein Window: {mechanics.get('optimal_protein_window')}\n"
            )
            task_instructions = (
                "Evaluate each raw material grain against the mechanics and assign RECOMMENDED, SUB-OPTIMAL, or NOT RECOMMENDED compatibility tier, and write a 2-sentence chemistry justification.\n"
                "Also suggest 3 to 5 distinct ways to enhance the physical and chemical outcome of the formulation.\n"
                "Also evaluate the milling setup: recommend whether bran separation (sifted high-extraction flour) or whole grain (unsifted) is optimal for this archetype, and explain why in 1 sentence.\n"
                "Also recommend the best mill type from the 'mills' list provided (if any), with a 1-sentence reason.\n"
                "🚨 [CRITICAL INPUT CONTEXT SANITY CHECK]\n"
                "When generating the `elevate_recipe` suggestions, you are STRICTLY PROHIBITED from mentioning, recommending, or referencing any grains, modifiers, or specialty ingredients "
                "that are not explicitly provided in the 'grains' and 'specialty_ingredients' lists of the user prompt payload. For example, if rye is not in 'grains', "
                "do NOT mention rye modifiers, and if eggs are not in 'specialty_ingredients', do NOT mention egg-based adjustments."
            )
            response_schema = (
                "{\n"
                "  \"grain_evaluations\": [\n"
                "    {\n"
                "      \"grain_id\": \"string (UUID of the grain)\",\n"
                "      \"tier\": \"recommended | sub-optimal | not-recommended\",\n"
                "      \"reasoning\": \"A concise 2-sentence analytical justification.\"\n"
                "    }\n"
                "  ],\n"
                "  \"elevate_recipe\": [\n"
                "    \"string suggestion 1\",\n"
                "    \"string suggestion 2\"\n"
                "  ],\n"
                "  \"mill_recommendation\": {\n"
                "    \"mill_id\": \"string (ID of the recommended mill, or null if no preference)\",\n"
                "    \"reasoning\": \"1 sentence explaining why this mill is best for the archetype.\"\n"
                "  },\n"
                "  \"sifted_recommendation\": {\n"
                "    \"should_sift\": true,\n"
                "    \"reasoning\": \"1 sentence explaining whether bran separation helps or hurts this recipe type.\"\n"
                "  }\n"
                "}"
            )
            system_prompt = assemble_system_prompt(engine, data_context, task_instructions, response_schema, active_archetype_id=active_archetype_id)

        from apps.core.models import Equipment
        mills_qs = Equipment.objects.filter(equipment_type='mill', deleted_at__isnull=True)
        payload = {
            "engine_id": engine.slug if engine else "default",
            "active_archetype_id": active_archetype_id,
            "selected_grains": selected_names,
            "grains": active_grains_list,
            "specialty_ingredients": specialty_ingredients,
            "mills": [{"id": str(m.id), "name": m.name} for m in mills_qs],
            "inventory": [
                {
                    "id": str(wb.id),
                    "name": wb.name,
                    "crude_protein_percentage": get_grain_registry_profile(wb.name).get("crude_protein_percentage"),
                    "gluten_binding_capacity": get_grain_registry_profile(wb.name).get("gluten_binding_capacity"),
                    "pentosan_concentration": get_grain_registry_profile(wb.name).get("pentosan_concentration"),
                    "bran_tannin_profile": get_grain_registry_profile(wb.name).get("bran_tannin_profile")
                }
                for wb in active_berries
            ]
        }
        
        user_prompt = json.dumps(payload)
        import re
        res = call_gemma_api(system_prompt, user_prompt, expected_keys=expected_keys)
        if res and isinstance(res, dict):
            evaluations = res.get("grain_evaluations", [])
            if isinstance(evaluations, list):
                for evaluation in evaluations:
                    if not isinstance(evaluation, dict):
                        continue
                    matched_wb = None
                    # 1. Exact match on grain_id
                    for wb in active_berries:
                        if str(wb.id) == str(evaluation.get("grain_id", "")).strip():
                            matched_wb = wb
                            break
                    # 2. Case-insensitive name match or slug match on grain_id
                    if not matched_wb:
                        for wb in active_berries:
                            wb_slug = re.sub(r'[^a-z0-9]', '', wb.name.lower())
                            id_slug = re.sub(r'[^a-z0-9]', '', str(evaluation.get("grain_id", "")).lower())
                            if wb_slug == id_slug or wb_slug in id_slug or id_slug in wb_slug:
                                matched_wb = wb
                                break
                    # 3. Matching via grain name inside reasoning
                    if not matched_wb:
                        reasoning_lower = evaluation.get("reasoning", "").lower()
                        for wb in active_berries:
                            if wb.name.lower() in reasoning_lower:
                                matched_wb = wb
                                break
                    if matched_wb:
                        evaluation["grain_id"] = str(matched_wb.id)
            return res

    # Local fallback
    evaluations = []
    if not only_elevate:
        for wb in active_berries:
            res = evaluate_single_grain(wb, engine, preset_name=preset_name, preset_slug=preset_slug, active_archetype_id=active_archetype_id)
            evaluations.append({
                "grain_id": str(wb.id),
                "tier": res["tier"],
                "reasoning": res["reasoning"]
            })

    elevate_recipe = []
    if not only_evaluations:
        elevate_recipe = [
            "Adjust initial water temperature to regulate yeast/enzymatic activity under current ambient conditions.",
            "Incorporate a 30-minute autolyse stage to fully hydrate raw bran and soften the structural network.",
            "Utilize gradual, gentle folding rather than intensive mechanical mixing to control gluten elasticity."
        ]

    return {
        "grain_evaluations": evaluations,
        "elevate_recipe": elevate_recipe
    }


def evaluate_single_grain(wb, engine, preset_name: str = None, preset_slug: str = None, active_archetype_id: str = None) -> dict:
    """
    Polymorphically evaluates a single grain against target mechanics using the two-dataset prompt.
    """
    import json
    from django.conf import settings
    
    engine_id = engine.slug if engine else "default"
    archetype_id = active_archetype_id or "default"
    variant_id = preset_slug or "default"
    grain_id = str(wb.id)
    cache_key = f"engine_{engine_id}::arch_{archetype_id}::var_{variant_id}::grain_{grain_id}"
    
    cached_val = cache.get(cache_key)
    if cached_val:
        logger.info(f"[AI] - Cache Hit - Key: {cache_key}")
        return cached_val
        
    # 1. Fetch intrinsic chemical profile of the grain from grain_registry.json
    grain_profile = get_grain_registry_profile(wb.name)
    
    # 2. Fetch target archetype mechanics from active engine (force explicit dynamic prompt binding)
    archetype_display, mechanics = get_archetype_mechanics(engine, active_archetype_id, preset_slug)
    
    if _is_ai_enabled():
        data_context = (
            f"[INTRINSIC RAW MATERIAL PROFILE]\n"
            f"* Element Name: {wb.name}\n"
            f"* Crude Protein: {grain_profile.get('crude_protein_percentage', '12.0%')}\n"
            f"* Gluten Binding Capacity: {grain_profile.get('gluten_binding_capacity', 'high')}\n"
            f"* Pentosan Concentration: {grain_profile.get('pentosan_concentration', 'low_standard')}\n"
            f"* Bran Flavor Profile: {grain_profile.get('bran_tannin_profile', 'none_neutral')}\n\n"
            f"[TARGET PRODUCTION ARCHETYPE MECHANICS]\n"
            f"* Core Archetype: {archetype_display} (Engine: {getattr(engine, 'name', 'Default')})\n"
            f"* Required Gluten Elasticity: {mechanics.get('required_gluten_elasticity', 'high_retention')}\n"
            f"* Desired Horizontal Flow: {mechanics.get('desired_horizontal_flow', 'controlled_expansion')}\n"
            f"* Moisture/Lipid Ratio: {mechanics.get('moisture_lipid_ratio', 'balanced_emulsion')}\n"
            f"* Target Protein Window: {mechanics.get('optimal_protein_window', '11.0% - 13.0%')}\n"
        )
        task_instructions = (
            "1. Relational Matching: Analyze how the raw ingredient's chemical attributes will behave under the thermal, hydraulic, and mechanical demands of the target archetype.\n"
            "2. Determine Compatibility Tier: Select exactly one tier string: \"RECOMMENDED\", \"SUB-OPTIMAL\", or \"NOT RECOMMENDED\".\n"
            "   - If the grain's native properties directly support or enhance the mechanical goals (even if it breaks traditional wheat rules, like an ancient grain with zero gluten maximizing tenderness where minimal elasticity is requested), classify it as RECOMMENDED.\n"
            "   - If the grain's native properties directly conflict with the physical targets (like an extreme-tensile bread flour causing toughness where high horizontal flow is requested), classify it as NOT RECOMMENDED.\n"
            "3. Chemistry-Driven Critique: Write a concise, 2-sentence conversational analysis explaining the precise molecular interaction (e.g., starch gelatinization, protein cross-linking, pentosan water-hoarding, lipid crystallization) driving your tier selection."
        )
        response_schema = (
            "{\n"
            "  \"evaluation_result\": {\n"
            "    \"compatibility_tier\": \"RECOMMENDED | SUB-OPTIMAL | NOT RECOMMENDED\",\n"
            "    \"technical_justification\": \"A conversational, expert 2-sentence food science breakdown.\"\n"
            "  }\n"
            "}"
        )
        system_prompt = assemble_system_prompt(engine, data_context, task_instructions, response_schema)
        
        user_prompt = json.dumps({
            "grain_id": str(wb.id),
            "grain_name": wb.name,
            "engine_id": engine.slug if engine else "default",
            "active_archetype_id": active_archetype_id
        })
        
        try:
            res = call_gemma_api(system_prompt, user_prompt, expected_keys=["evaluation_result"])
            if res and "grain_evaluations" in res:
                evals = res["grain_evaluations"]
                for e in evals:
                    e_id = str(e.get("grain_id", ""))
                    if e_id == str(wb.id) or wb.name.lower() in e_id.lower() or e_id.lower() in wb.name.lower():
                        res_dict = {
                            "tier": e.get("tier", "SUB-OPTIMAL").lower().replace("_", "-"),
                            "reasoning": e.get("reasoning", "")
                        }
                        cache.set(cache_key, res_dict, timeout=None)
                        return res_dict
            if res and "evaluation_result" in res:
                eval_result = res["evaluation_result"]
                tier_raw = str(eval_result.get("compatibility_tier", "SUB-OPTIMAL")).upper().strip()
                if "NOT" in tier_raw:
                    tier = "not-recommended"
                elif "SUB" in tier_raw:
                    tier = "sub-optimal"
                else:
                    tier = "recommended"
                    
                res_dict = {
                    "tier": tier,
                    "reasoning": eval_result.get("technical_justification", "Analyzed physical targets and chemical profile successfully.")
                }
                cache.set(cache_key, res_dict, timeout=None)
                return res_dict
        except Exception as e:
            logger.error(f"[Gemma Client] - Error - Failed evaluation for grain {wb.name}: {e}")

    # Local fallback
    res_dict = calculate_local_compatibility_from_specs(wb, engine, preset_slug, active_archetype_id)
    cache.set(cache_key, res_dict, timeout=None)
    return res_dict


def evaluate_grains_batch(grains: list, engine, preset_name: str = None, preset_slug: str = None, active_archetype_id: str = None) -> dict:
    """
    Evaluates multiple grains in a single LLM API call, caching the results individually.
    """
    import json
    
    engine_id = engine.slug if engine else "default"
    archetype_id = active_archetype_id or "default"
    variant_id = preset_slug or "default"
    
    results = {}
    uncached_grains = []
    
    # 1. Try to load from cache first
    for wb in grains:
        grain_id = str(wb.id)
        cache_key = f"engine_{engine_id}::arch_{archetype_id}::var_{variant_id}::grain_{grain_id}"
        
        cached_val = cache.get(cache_key)
        if cached_val:
            results[grain_id] = cached_val
        else:
            uncached_grains.append(wb)
            
    if not uncached_grains:
        return results
        
    # 2. If there are uncached grains, query the LLM or run fallback
    if _is_ai_enabled():
        archetype_display, mechanics = get_archetype_mechanics(engine, active_archetype_id, preset_slug)
        
        data_context = (
            f"[TARGET PRODUCTION ARCHETYPE MECHANICS]\n"
            f"* Core Archetype: {archetype_display} (Engine: {getattr(engine, 'name', 'Default')})\n"
            f"* Required Gluten Elasticity: {mechanics.get('required_gluten_elasticity')}\n"
            f"* Desired Horizontal Flow: {mechanics.get('desired_horizontal_flow')}\n"
            f"* Moisture/Lipid Ratio: {mechanics.get('moisture_lipid_ratio')}\n"
            f"* Target Protein Window: {mechanics.get('optimal_protein_window')}\n"
        )
        task_instructions = (
            "Evaluate each raw material grain provided in the user context against the mechanics and assign RECOMMENDED, SUB-OPTIMAL, or NOT RECOMMENDED compatibility tier, and write a 2-sentence chemistry justification."
        )
        response_schema = (
            "{\n"
            "  \"grain_evaluations\": [\n"
            "    {\n"
            "      \"grain_id\": \"string (UUID of the grain)\",\n"
            "      \"tier\": \"recommended | sub-optimal | not-recommended\",\n"
            "      \"reasoning\": \"A concise 2-sentence analytical justification.\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        system_prompt = assemble_system_prompt(engine, data_context, task_instructions, response_schema)
        
        payload = {
            "engine_id": engine_id,
            "active_archetype_id": active_archetype_id,
            "grains": [
                {
                    "id": str(wb.id),
                    "name": wb.name,
                    "crude_protein_percentage": get_grain_registry_profile(wb.name).get("crude_protein_percentage"),
                    "gluten_binding_capacity": get_grain_registry_profile(wb.name).get("gluten_binding_capacity"),
                    "pentosan_concentration": get_grain_registry_profile(wb.name).get("pentosan_concentration"),
                    "bran_tannin_profile": get_grain_registry_profile(wb.name).get("bran_tannin_profile")
                }
                for wb in uncached_grains
            ]
        }
        
        try:
            res = call_gemma_api(system_prompt, json.dumps(payload), expected_keys=["grain_evaluations"])
            if res and isinstance(res, dict) and "grain_evaluations" in res:
                for ev in res["grain_evaluations"]:
                    ev_id = str(ev.get("grain_id", "")).strip()
                    # Find matching grain from uncached_grains to get the exact UUID
                    matched_wb = None
                    for wb in uncached_grains:
                        if str(wb.id) == ev_id or wb.name.lower() in ev_id.lower() or ev_id.lower() in wb.name.lower():
                            matched_wb = wb
                            break
                    if matched_wb:
                        grain_id = str(matched_wb.id)
                        res_dict = {
                            "tier": ev.get("tier", "SUB-OPTIMAL").lower().replace("_", "-"),
                            "reasoning": ev.get("reasoning", "Analyzed successfully.")
                        }
                        # Write to persistent cache
                        cache_key = f"engine_{engine_id}::arch_{archetype_id}::var_{variant_id}::grain_{grain_id}"
                        cache.set(cache_key, res_dict, timeout=None)
                        results[grain_id] = res_dict
        except Exception as e:
            logger.error(f"[Gemma Client] - Batch Error - Failed batch evaluation: {e}")
            
    # 3. For any grains that are still not evaluated, evaluate using programmatic fallback
    for wb in uncached_grains:
        grain_id = str(wb.id)
        if grain_id not in results:
            res_dict = calculate_local_compatibility_from_specs(wb, engine, preset_slug, active_archetype_id)
            cache_key = f"engine_{engine_id}::arch_{archetype_id}::var_{variant_id}::grain_{grain_id}"
            cache.set(cache_key, res_dict, timeout=None)
            results[grain_id] = res_dict
            
    return results


def get_local_grain_advisory(preset_slug: str, category_slug: str = None, preset_name: str = None, active_archetype_id: str = None) -> dict:
    """
    Local fallback logic performing programmatic evaluation of kitchen inventory 
    using the active sub-engine mechanics.
    """
    from apps.core.models import WheatBerry, BreadPreset
    from grainlab.engines import router
 
    preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
    if not category_slug and preset and preset.dough_category:
        category_slug = preset.dough_category.slug
    engine = router.get_engine_for_preset(preset_slug, category_slug)
 
    active_berries = list(WheatBerry.objects.filter(is_active=True))
    evaluations = []
 
    for wb in active_berries:
        res = evaluate_single_grain(wb, engine, preset_name=preset_name, preset_slug=preset_slug, active_archetype_id=active_archetype_id)
        evaluations.append({
            "grain_id": str(wb.id),
            "tier": res["tier"],
            "reasoning": res["reasoning"]
        })
 
    return {
        "grain_evaluations": evaluations
    }


CATEGORY_TO_ENGINE = {
    "lean-crusty": "hearth",
    "enriched-soft": "pan",
    "alkaline-bath": "bath",
    "flatbreads-griddles": "flat",
    "quick-breads-scones": "quick",
    "cakes-batters": "batter",
    "pastry-lamination": "pastry",
    "choux-paste": "choux",
    "cookies-shortbread": "cookie",
    "fried-doughs": "fry",
    "fresh-pasta-noodles": "pasta",
}

def get_geometry_advisory(preset_slug: str, preset_name: str, category_slug: str, form_factor_slug: str) -> dict:
    """
    Evaluates form factor suitability for the given recipe preset and category using Gemma.
    """
    engine_slug = CATEGORY_TO_ENGINE.get(category_slug, "base")
    
    fallback_data = {
        "status": "recommended",
        "advisory_label": f"Standard baking geometry for {preset_name or category_slug}.",
        "profile_adjustments": {
            "oven_temp_offset_f": 0,
            "bake_time_offset_m": 0,
            "steam_override": "no-change"
        }
    }
    
    if not _is_ai_enabled():
        return {
            "geometry_evaluation": fallback_data
        }

    system_prompt = (
        "You are an expert baking science assistant. Evaluate the suitability of the selected baking geometry (equipment form factor) "
        "for the active recipe type and return a structured JSON response. Consider thermal mass, heat conduction, expansion, and steam dynamics.\n"
        "Your response MUST be pure JSON matching this schema exactly:\n"
        "{\n"
        "  \"geometry_evaluation\": {\n"
        "    \"status\": \"recommended\" or \"sub-optimal\",\n"
        "    \"advisory_label\": \"A clear 1-2 sentence structural justification explaining heat penetration, expansion, or steam mechanics.\",\n"
        "    \"profile_adjustments\": {\n"
        "      \"oven_temp_offset_f\": integer offset,\n"
        "      \"bake_time_offset_m\": integer offset,\n"
        "      \"steam_override\": \"no-change\" or \"force-on\" or \"force-off\"\n"
        "    }\n"
        "  }\n"
        "}"
    )
    
    user_prompt = (
        f"Active Recipe Preset: {preset_name or preset_slug or 'Custom'}\n"
        f"Active Recipe Category: {category_slug} (Sub-Engine: {engine_slug})\n"
        f"Selected Form Factor (Geometry): {form_factor_slug}\n"
        f"Generate the suitability status, a scientific advisory label, and the recommended oven temperature offset (°F), "
        f"bake time offset (minutes), and steam override choice. Do not rely on any preset baselines; calculate the ideal offsets directly. "
        f"Output ONLY valid JSON."
    )
    
    try:
        response = call_gemma_api(system_prompt, user_prompt, expected_keys=["geometry_evaluation"])
        if response and "geometry_evaluation" in response:
            ge = response["geometry_evaluation"]
            status = ge.get("status", fallback_data["status"])
            if status not in ["recommended", "sub-optimal"]:
                status = fallback_data["status"]
            
            advisory_label = ge.get("advisory_label", fallback_data["advisory_label"])
            
            adjustments = ge.get("profile_adjustments", {})
            oven_temp_offset = int(adjustments.get("oven_temp_offset_f", 0))
            bake_time_offset = int(adjustments.get("bake_time_offset_m", 0))
            steam_override = adjustments.get("steam_override", "no-change")
            if steam_override not in ["no-change", "force-on", "force-off"]:
                steam_override = "no-change"
                
            return {
                "geometry_evaluation": {
                    "status": status,
                    "advisory_label": advisory_label,
                    "profile_adjustments": {
                        "oven_temp_offset_f": oven_temp_offset,
                        "bake_time_offset_m": bake_time_offset,
                        "steam_override": steam_override
                    }
                }
            }
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling geometry advisory API: {str(e)}")
        
    return {
        "geometry_evaluation": fallback_data
    }


def get_sidebar_insight_ai(element: str, category_slug: str, preset_slug: str) -> dict | None:
    """
    Queries Gemma to generate a custom labor ROI tag, recommendation tier, and 'Last 10%' critique/reasoning.
    """
    import json
    import re
    from apps.core.models import BreadPreset, WheatBerry
    from grainlab.engines import router
    
    preset = BreadPreset.objects.filter(slug=preset_slug).first()
    preset_name = preset.name if preset else (preset_slug.replace("-", " ").title() if preset_slug else "Custom / Manual Blend")
    
    # Query inactive wheat berries (not on hand) to pass to the AI
    inactive_grains = list(WheatBerry.all_objects.filter(is_active=False, deleted_at__isnull=True))
    inactive_grain_names = [g.name for g in inactive_grains]
    
    # Fetch active engine's parametric profile details
    try:
        engine = router.get_engine_for_preset(preset_slug, category_slug)
    except Exception:
        # Default or fallback engine-like attributes
        class MockEngine:
            name = "Default Hearth Engine"
            target_protein_min = 11.0
            target_protein_max = 13.0
            gluten_behavior = "standard"
            flavor_affinity = ""
            tannin_sensitive = False
        engine = MockEngine()

    # Find the wheat berry matching element if hovered element is a grain
    wb = None
    if element.startswith("grain_"):
        key_part = element.lower().replace("grain_", "")
        for b in WheatBerry.all_objects.filter(deleted_at__isnull=True):
            b_name_slug = re.sub(r'[^a-z0-9]', '_', b.name.lower())
            if key_part in b_name_slug or b_name_slug in key_part:
                wb = b
                break

    # Retrieve factual description
    factual_desc = FACTUAL_DICTIONARY.get(element.lower(), '')
    if not factual_desc:
        for k, v in FACTUAL_DICTIONARY.items():
            if element.lower() in k or k in element.lower():
                factual_desc = v
                break

    system_prompt = (
        "You are an expert, highly practical food scientist who values human time and forearm fatigue. "
        "The tone must be conversational, insightful, and focused entirely on the sensory experience of eating and the physical reality of cooking. "
        "Analyze the provided hovered workspace setting relative to the active baking category and preset. "
        "You MUST tailor your critique specifically to the active baking category and preset. "
        "Do NOT mention ingredients or processes (e.g., yeast, rising, kneading, proofing, bread ovens, steam) that are not part of the target recipe class. For example, do not mention yeast or proofing for cookies/cakes, and do not mention cookie spread or creaming for sourdough/pizza. "
        "\n"
        "[CRITICAL RULE: CULINARY SOVEREIGNTY]\n"
        "You must rely SOLELY on your native baking science knowledge and real-world artisan baking physics. "
        "Do NOT apply standard/generic wheat constraints to ancient or non-standard grains (e.g., Rye, Spelt, Einkorn) if doing so contradicts artisan baking chemistry. "
        "For example, Rye is highly recommended for cookies due to pentosans blocking gluten to maximize cookie tenderness, even though its protein is low. "
        "Evaluate the hovered element purely based on real-world baking physics for the active preset.\n"
        "\n"
        "🚨 CRITICAL RULES:\n"
        "1. Banned Terminology: You are strictly prohibited from using these words or variants in your generated JSON response: "
        "anomalies, parameter, workspace, matrix, objective, configuration, optimization, performance, detected, asset, baseline.\n"
        "2. Strict Context Anchoring: The 'last_10_percent_analysis' field must explicitly synthesize the hovered element name directly with the active recipe target name (e.g. 'Soft White Wheat' + 'Chewy Chocolate Chip Cookies'). It cannot output generic definitions.\n"
        "3. TRULY INSIGHTFUL ANALYSIS & OUT-OF-STOCK ALTERNATIVES:\n"
        f"   - If the hovered element is sub-optimal or can be elevated, look at the following wheat grains that are currently NOT on hand (out of stock/inactive in the user's inventory): {inactive_grain_names}.\n"
        "   - Suggest acquiring or activating a specific grain from this out-of-stock list if it would significantly enhance the flavor or yield a superior texture for the target preset. Give a clear explanation of its impact.\n"
        "4. INGREDIENTS MUST USE HUMAN-READABLE NAMES: You MUST write the actual human-readable names of all grains, flours, and ingredients (e.g. 'Hard Red Spring Wheat', 'Rye', 'Soft White Wheat', 'unsalted butter'). You are STRICTLY PROHIBITED from using database IDs, UUIDs, keys, or hashes (such as '302adef7-9477-4728-8bb7-dae99b05eab9') under any circumstances in your text outputs.\n"
        "5. DOUBLE TEMPERATURE SCALE REQUIRED: Any temperature value you mention must always be provided in both Celsius and Fahrenheit scales (for example: '350°F (177°C)' or '30°C (86°F)'). Never provide a temperature in only a single scale.\n"

        "6. BE HIGHLY CRITICAL AND DISCERNING: Do NOT lazily categorize everything as 'High Priority' or 'Recommended'. Most options in a kitchen are 'Sub-Optimal', 'Low Priority', or 'Standard Baseline'. ONLY rate something as 'High Priority / Worth the Extra Step' or 'Recommended' if it provides a MASSIVE, noticeable improvement to the final texture or flavor for that specific recipe. You are a harsh, pragmatic critic. If it's a minor difference, rate it 'Low Priority'.\n"

        "\n"
        "Return a JSON object containing:\n"
        "- 'recommendation_tier': a string of 'highly-recommended', 'recommended', 'standard', 'sub-optimal', or 'not-recommended' representing the rating of this choice for the active preset.\n"
        "- 'labor_roi_rating': a string tag representing ranking (e.g., 'High Priority / Worth the Extra Step', 'Low Priority / Minor Textural Return', 'High Priority / Absolute Requirement')\n"
        "- 'last_10_percent_analysis': a tight 2-sentence conversational critique.\n"
        "- 'elevate_recipe': a 1-2 sentence recommendation on a potential way to elevate this recipe, suggesting a specific grain to mix in (regardless of inventory), a particular secondary ingredient (like a fat/liquid swap), or a specific method (like autolyse, cold proofing) to achieve greater results.\n"
        "\n"
        "EXAMPLES:\n"
        "Example A (Hovering 'Soft White Wheat' on 'Chewy Chocolate Chip Cookies'):\n"
        "{\n"
        "  \"recommendation_tier\": \"recommended\",\n"
        "  \"labor_roi_rating\": \"High Priority / Worth the Extra Step\",\n"
        "  \"last_10_percent_analysis\": \"Using Soft White Wheat here ensures your cookies melt into a perfectly tender, uniform pool instead of puffing up into cakey domes. To unlock the real magic, give this fresh-milled dough a 12-hour rest in the fridge before baking so the bran has time to fully absorb the butter fat.\",\n"
        "  \"elevate_recipe\": \"For an even richer flavor profile, substitute 20% of the soft white wheat with fresh-milled Rye (regardless of inventory) to introduce pentosans that keep the cookie center exceptionally gooey.\"\n"
        "}\n"
        "\n"
        "Example B (Hovering 'Manual Spatula' on 'Chewy Chocolate Chip Cookies'):\n"
        "{\n"
        "  \"recommendation_tier\": \"sub-optimal\",\n"
        "  \"labor_roi_rating\": \"Low Priority / Minor Textural Return\",\n"
        "  \"last_10_percent_analysis\": \"There is zero reason to wear out your forearm hand-mixing a massive batch of cookie dough. Throw it in the stand mixer with the paddle attachment on low speed; you will get the exact same tender crumb without the manual exhaustion.\",\n"
        "  \"elevate_recipe\": \"Using a paddle attachment on a stand mixer develops uniform sugar hydration without building unwanted gluten toughness.\"\n"
        "}\n"
        "\n"
        "Example C (Hovering 'Manual Spatula' on 'Buttermilk Biscuits'):\n"
        "{\n"
        "  \"recommendation_tier\": \"recommended\",\n"
        "  \"labor_roi_rating\": \"High Priority / Absolute Requirement\",\n"
        "  \"last_10_percent_analysis\": \"Put the electric mixers away. Hand-folding your wet ingredients with a spatula is the exact threshold where biscuit magic lives; a machine will activate the gluten webs in seconds, turning a flaky, layered biscuit into a tough hockey puck.\",\n"
        "  \"elevate_recipe\": \"Incorporate cold lard instead of butter to create distinct fat barriers for maximum flaky lamination rise.\"\n"
        "}"
    )
    
    # Format the element name to human readable form for the prompt
    element_clean = element.replace("grain_", "").replace("_", " ").title()
    
    user_prompt = json.dumps({
        "hovered_element": element_clean,
        "recipe_target_name": preset_name,
        "category_slug": category_slug,
        "preset_slug": preset_slug,
        "inactive_grains_not_on_hand": inactive_grain_names
    })
    
    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["recommendation_tier", "labor_roi_rating", "last_10_percent_analysis", "elevate_recipe"])
        if result and "labor_roi_rating" in result and "last_10_percent_analysis" in result:
            return {
                "recommendation_tier": result.get("recommendation_tier", "recommended"),
                "labor_roi": result["labor_roi_rating"],
                "last_10_percent_analysis": result["last_10_percent_analysis"],
                "elevate_recipe": result.get("elevate_recipe", "")
            }
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling sidebar insight API: {str(e)}")
    return None


def generate_recipe_variants(engine_id: str, active_archetype_id: str, inventory: list, exclude_names: list = None, count: int = 5) -> dict | None:
    """
    Given the active engine slug, selected archetype ID, and inventory grain list,
    asks the LLM to generate a list of recipe variants with descriptions
    and recommended_grain_ids for golden highlight ring binding.
    """
    import json

    system_prompt = (
        "You are a baking science variant generator. Given an engine type and structural archetype, "
        f"generate exactly {count} distinct recipe variants optimized for fresh-milled whole grains.\n"
        f"CRITICAL: The variants must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        "You are strictly prohibited from generating recipes crossing over into other archetypes or categories.\n"
        f"CRITICAL: The generated variants must NOT repeat or have the same flavor/recipe name as these primary/existing recipes: {exclude_names or []}.\n"
        "CRITICAL: The variants MUST be 100% unique. Do NOT generate duplicate recipes.\n"
        "CRITICAL: Do NOT append words like 'Classic', 'Modern', 'Variant', or 'Level' to the variant names. The names should be simple and natural.\n"
        "CRITICAL: The variants must be defined by their culinary/flavor targets (e.g. Chocolate Chip, Snickerdoodle, Roasted Garlic Herb, Fig & Walnut, Cinnamon Swirl, Blueberry Lemon, etc.), NOT by the specific grains used (e.g. do not call them 'Spelt Cookie' or 'Rye Batard'). The grains in the inventory should be used to accentuate and pair with these flavor targets, and specified in the recommended_grain_ids list.\n"
        "\n"
        "Each variant must match this JSON schema:\n"
        "{\n"
        "  \"generated_variants\": [\n"
        "    {\n"
        "      \"variant_id\": \"unique_slug\",\n"
        "      \"variant_name\": \"Human readable variant label (representing a culinary/flavor target)\",\n"
        "      \"description\": \"1-2 sentence description explaining the structural/flavor tweak and how it pairs with the whole grain notes.\",\n"
        "      \"menu_description\": \"A rich, descriptive flavor profile written in the style of a high-end restaurant menu item description.\",\n"
        "      \"recommended_grain_ids\": [\"grain_name_slug\"]\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "IMPORTANT: recommended_grain_ids must be lowercase name slugs matching grains from the provided inventory. "
        "Return ONLY raw JSON with no markdown fences."
    )

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "inventory": inventory,
        "exclude_names": exclude_names or [],
    })

    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["generated_variants"])
        if result and isinstance(result.get("generated_variants"), list):
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_recipe_variants: {str(e)}")

    # Fall back to mock
    mock = get_mock_gemma_response(system_prompt, user_prompt, expected_keys=["generated_variants"])
    return mock


def generate_creativity_recipes(engine_id: str, active_archetype_id: str, inventory: list) -> dict | None:
    """
    Given the engine slug, selected archetype ID, and inventory grain list, asks the LLM to generate
    exactly 10 recipe profiles (5 per Creativity Level: 1 and 2).
    """
    import json

    system_prompt = (
        "You are a baking science expert. Given an engine type, target archetype, and inventory grain list, "
        "generate exactly 10 distinct recipe profiles matching these two Creativity Levels (exactly 5 recipes per level):\n"
        f"CRITICAL: All 10 generated recipe profiles must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        "You are strictly prohibited from generating recipes crossing over into other archetypes or categories.\n"
        "- Creativity Level 1: Baseline Standard Profiles. (Simple, classic, highly traditional, reliable profiles. NO unusual flavors).\n"
        "- Creativity Level 2: Advanced Modern Profiles. (Wildly creative, unconventional, artisanal, or avant-garde flavor combinations).\n"
        "\n"
        "CRITICAL: The recipe profiles MUST be 100% unique. Do NOT generate duplicate recipes.\n"
        "CRITICAL: Do NOT append words like 'Classic', 'Modern', 'Variant', or 'Level' to the variant names. The names should be simple and natural.\n"
        "CRITICAL: The recipe profiles must be defined by their culinary/flavor targets (e.g. Chocolate Chip, Snickerdoodle, Roasted Garlic Herb, Fig & Walnut, Cinnamon Swirl, Blueberry Lemon, etc.), NOT by the specific grains used (e.g. do not call them 'Spelt Cookie' or 'Rye Batard').\n"
        "\n"
        "Each recipe must match this JSON schema:\n"
        "{\n"
        "  \"recipes\": [\n"
        "    {\n"
        "      \"recipe_id\": \"unique_slug\",\n"
        "      \"recipe_name\": \"Human readable title (representing a culinary/flavor target)\",\n"
        "      \"creativity_level\": 1,  // must be 1 or 2\n"
        "      \"description\": \"1-2 sentence description explaining the flavor structure\",\n"
        "      \"menu_description\": \"A rich, descriptive flavor profile written in the style of a high-end restaurant menu item description.\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Return ONLY raw JSON with no markdown fences."
    )

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "inventory": inventory,
    })

    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["recipes"])
        if result and isinstance(result.get("recipes"), list):
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_creativity_recipes: {str(e)}")

    # Fall back to mock
    mock = get_mock_gemma_response(system_prompt, user_prompt, expected_keys=["recipes"])
    return mock


def generate_creativity_variants(engine_id: str, creativity_level: int, active_archetype_id: str, inventory: list, exclude_names: list = None, count: int = 5) -> dict | None:
    """
    Given the engine, target creativity level, parent recipe, and inventory grain list,
    asks the LLM to generate 8 alternative recipe variations matching ONLY that creativity level.
    """
    import json

    system_prompt = (
        f"You are a baking science expert. Given an engine type, a parent recipe ID, and a target Creativity Level of {creativity_level}, "
        f"generate exactly {count} alternative structural profile variations matching ONLY that creativity level.\n"
        f"CRITICAL: The variations must belong strictly to the exact same archetype category: '{active_archetype_id}'. "
        f"You are strictly prohibited from generating recipes crossing over into other archetypes or categories.\n"
        f"CRITICAL: The generated variants must NOT repeat or have the same flavor/recipe name as these primary/existing recipes: {exclude_names or []}.\n"
        "CRITICAL: The generated variations MUST be 100% unique. Do NOT generate duplicate recipes.\n"
        "CRITICAL: Do NOT append words like 'Classic', 'Modern', 'Variant', or 'Level' to the variant names. The names should be simple and natural.\n"
        "CRITICAL: The variations must be defined by their culinary/flavor targets (e.g. Chocolate Chip, Snickerdoodle, Roasted Garlic Herb, Fig & Walnut, Cinnamon Swirl, Blueberry Lemon, etc.), NOT by the specific grains used (e.g. do not call them 'Spelt Cookie' or 'Rye Batard').\n"
        "\n"
        "Each variation must match this JSON schema:\n"
        "{\n"
        "  \"generated_variants\": [\n"
        "    {\n"
        "      \"variant_id\": \"unique_slug\",\n"
        "      \"variant_name\": \"Human readable variant label (representing a culinary/flavor target)\",\n"
        "      \"description\": \"1-2 sentence description explaining the structural/flavor tweak and how it pairs with the whole grain notes.\",\n"
        "      \"menu_description\": \"A rich, descriptive flavor profile written in the style of a high-end restaurant menu item description.\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Return ONLY raw JSON with no markdown fences."
    )

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "creativity_level": creativity_level,
        "active_archetype_id": active_archetype_id,
        "inventory": inventory,
        "exclude_names": exclude_names or [],
    })

    try:
        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["generated_variants"])
        if result and isinstance(result.get("generated_variants"), list):
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_creativity_variants: {str(e)}")

    # Fall back to mock
    mock = get_mock_gemma_response(system_prompt, user_prompt, expected_keys=["generated_variants"])
    return mock


def generate_recipe_details(engine_id: str, active_archetype_id: str, recipe_slug: str, recipe_name: str, selected_grains: str, category_slug: str) -> dict | None:
    """
    Asks the LLM to generate the detailed science profile and ways to elevate (last_10_percent_magic)
    for a specific selected recipe.
    """
    import json
    
    # Retrieve thinking mode settings
    ai_thinking_enabled = SystemSetting.get_val("ai_thinking_enabled", "True") == "True"
    ai_thinking_effort = SystemSetting.get_val("ai_thinking_effort", "medium")

    system_prompt = (
        "You are a baking science expert. Given an engine type, target archetype, a specific selected recipe slug, "
        "the human-readable recipe name, and a list of active selected grains, generate the menu description, technical science profile, recommended grain selections, and required secondary ingredients (including permissible substitutions).\n"
        "CRITICAL RULE FOR SECONDARY INGREDIENTS:\n"
        "You MUST provide AT LEAST 3 overarching categories for lipids (e.g., 'Butter', 'Oil', 'Shortening'), liquids, and binders.\n"
        "You MUST also provide categories and options for sweeteners, leaveners, and additives ONLY IF they are required for the target dough archetype. If they are not needed (e.g., no leaveners in pasta), omit them entirely or return empty lists.\n"
        "Inside EACH category, you MUST provide AT LEAST 3-4 specific options.\n"
        "Do NOT just return a single ingredient. You must populate the JSON with a wide variety of valid alternatives.\n"
        "Here is an EXACT EXAMPLE of the structure expected for lipids. You must replicate this high level of variety for all required categories:\n"
        "{\n"
        "  \"required_category\": \"Butter or Neutral Oil\",\n"
        "  \"ai_recommendation\": \"A brief explanation of why this specific fat category is recommended for this recipe's crumb structure.\",\n"
        "  \"categories\": [\n"
        "    {\n"
        "      \"name\": \"Dairy Butter\",\n"
        "      \"options\": [\n"
        "        {\"name\": \"unsalted_butter\", \"temperature_options\": [\"Room Temp\", \"Melted\", \"Browned\"]},\n"
        "        {\"name\": \"salted_butter\", \"temperature_options\": [\"Room Temp\", \"Melted\", \"Browned\"]},\n"
        "        {\"name\": \"cultured_butter\", \"temperature_options\": [\"Room Temp\", \"Melted\"]}\n"
        "      ]\n"
        "    },\n"
        "    {\n"
        "      \"name\": \"Plant Oils\",\n"
        "      \"options\": [\n"
        "        {\"name\": \"olive_oil\", \"temperature_options\": [\"Liquid\"]},\n"
        "        {\"name\": \"avocado_oil\", \"temperature_options\": [\"Liquid\"]},\n"
        "        {\"name\": \"coconut_oil\", \"temperature_options\": [\"Solid\", \"Melted\"]}\n"
        "      ]\n"
        "    },\n"
        "    {\n"
        "      \"name\": \"Solid Plant Fats\",\n"
        "      \"options\": [\n"
        "        {\"name\": \"vegetable_shortening\", \"temperature_options\": [\"Room Temp\", \"Melted\"]},\n"
        "        {\"name\": \"vegan_butter_block\", \"temperature_options\": [\"Room Temp\", \"Melted\"]},\n"
        "        {\"name\": \"margarine\", \"temperature_options\": [\"Room Temp\", \"Melted\"]}\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Each response must match this JSON schema exactly:\n"
        "{\n"
        "  \"recommended_grain_ids\": [\"grain_name_slug\"],\n"
        "  \"flour_blend\": {\"grain_name_slug\": 80, \"another_grain_slug\": 20},\n"
        "  \"fat_starting_temp\": \"room_temp\",\n"
        "  \"required_actions\": [\"knead\", \"fold\"],\n"
        "  \"required_hardware\": [\"stand_mixer\", \"dough_whisk\"],\n"
        "  \"secondary_ingredients\": {\n"
        "    \"lipids\": { \"required_category\": \"string\", \"ai_recommendation\": \"string\", \"categories\": [{ \"name\": \"string\", \"options\": [{\"name\": \"string\", \"temperature_options\": [\"string\"]}] }] },\n"
        "    \"liquids\": { \"required_category\": \"string\", \"ai_recommendation\": \"string\", \"categories\": [{ \"name\": \"string\", \"options\": [{\"name\": \"string\", \"temperature_options\": [\"string\"]}] }] },\n"
        "    \"binders\": { \"required_category\": \"string\", \"ai_recommendation\": \"string\", \"categories\": [{ \"name\": \"string\", \"options\": [{\"name\": \"string\", \"temperature_options\": [\"string\"]}] }] },\n"
        "    \"sweeteners\": { \"required_category\": \"string\", \"ai_recommendation\": \"string\", \"categories\": [{ \"name\": \"string\", \"options\": [{\"name\": \"string\", \"temperature_options\": [\"string\"]}] }] },\n"
        "    \"leaveners\": { \"required_category\": \"string\", \"ai_recommendation\": \"string\", \"categories\": [{ \"name\": \"string\", \"options\": [{\"name\": \"string\", \"temperature_options\": [\"string\"]}] }] },\n"
        "    \"additives\": { \"required_category\": \"string\", \"ai_recommendation\": \"string\", \"categories\": [{ \"name\": \"string\", \"options\": [{\"name\": \"string\", \"temperature_options\": [\"string\"]}] }] },\n"
        "    \"flavor_inclusions\": [{ \"name\": \"string\", \"bakers_percentage\": 2.5, \"volume_description\": \"string\" }]\n"
        "  }\n"
        "}\n"
        "Return ONLY raw JSON with no markdown fences.\n"
    )
    
    from grainlab.engines import router
    engine = router.get_engine_for_preset(recipe_slug, category_slug)
    culinary_directive = engine.get_ai_culinary_directive()
    if culinary_directive:
        system_prompt += f"\n\n🚨 [ENGINE CULINARY DIRECTIVE]\n{culinary_directive}"

    if ai_thinking_enabled:
        system_prompt += f"\n[CRITICAL] Use thorough reasoning and step-by-step thinking (thinking effort: {ai_thinking_effort}) before responding."
    else:
        system_prompt += "\n[CRITICAL] Do NOT use thinking/reasoning steps. Respond immediately with the direct answer."

    user_prompt = json.dumps({
        "engine_id": engine_id,
        "active_archetype_id": active_archetype_id,
        "recipe_slug": recipe_slug,
        "recipe_name": recipe_name,
        "selected_grains": selected_grains,
        "category_slug": category_slug
    })

    logger.info(f"[Gemma Client] - Info - Calling generate_recipe_details for: {recipe_slug}")

    try:
        # Check if offline mock mode is active
        if getattr(settings, "MOCK_MODE", True):
            return get_local_recipe_details(recipe_slug, recipe_name, engine_id, active_archetype_id, selected_grains)

        result = call_gemma_api(system_prompt, user_prompt, expected_keys=["secondary_ingredients", "recommended_grain_ids"])
        if result and isinstance(result, dict) and "secondary_ingredients" in result:
            return result
    except Exception as e:
        logger.error(f"[Gemma Client] - Error - Failed calling generate_recipe_details: {str(e)}")

    # Fall back to local mock
    return get_local_recipe_details(recipe_slug, recipe_name, engine_id, active_archetype_id, selected_grains)


def get_local_recipe_details(recipe_slug: str, recipe_name: str, engine_id: str, active_archetype_id: str, selected_grains: str) -> dict:
    """
    Returns realistic local fallback recipe details with specific flavor matching.
    """
    slug = (recipe_slug or "").lower()
    name = (recipe_name or "").lower()
    category = (engine_id or "").lower()
    
    # Defaults
    sec_lipids = {
        "required_category": "Butter",
        "ai_recommendation": "Butter is recommended for its rich dairy notes and tenderizing effects on the crumb structure, which is ideal for this formula.",
        "categories": [
            {
                "name": "Butter",
                "options": [
                    {"name": "unsalted_butter", "temperature_options": ["Cold (Solid)", "Soft (Room Temp)", "Melted"]}
                ]
            },
            {
                "name": "Oil",
                "options": [
                    {"name": "avocado_oil", "temperature_options": ["Liquid (Room Temp)"]},
                    {"name": "coconut_oil", "temperature_options": ["Solid (Cold)", "Liquid (Melted)"]}
                ]
            }
        ]
    }
    sec_liquids = {
        "required_category": "Whole Milk",
        "ai_recommendation": "Whole milk provides the perfect balance of hydration, fats, and milk sugars for a soft and supple dough.",
        "categories": [
            {
                "name": "Water",
                "options": [
                    {"name": "pure_water", "temperature_options": ["Cold", "Warm", "Hot"]}
                ]
            },
            {
                "name": "Milk",
                "options": [
                    {"name": "whole_milk", "temperature_options": ["Cold", "Room Temp", "Warm"]},
                    {"name": "buttermilk", "temperature_options": ["Cold", "Room Temp"]}
                ]
            }
        ]
    }
    sec_binders = {
        "required_category": "Whole Eggs",
        "ai_recommendation": "Whole eggs offer structural binding and additional fat, creating a sturdy yet pillowy crumb that holds its shape.",
        "categories": [
            {
                "name": "None",
                "options": [
                    {"name": "none", "temperature_options": ["N/A"]}
                ]
            },
            {
                "name": "Egg",
                "options": [
                    {"name": "whole_eggs", "temperature_options": ["Cold", "Room Temp"]},
                    {"name": "egg_whites", "temperature_options": ["Cold", "Room Temp"]}
                ]
            }
        ]
    }
    sec_sweeteners = {
        "required_category": "Granulated Sugar",
        "ai_recommendation": "Sugar provides both sweetness and crucial tenderization, while also assisting in the Maillard reaction for a golden crust.",
        "categories": [
            {
                "name": "Dry Sugars",
                "options": [
                    {"name": "granulated_sugar", "temperature_options": ["Room Temp"]},
                    {"name": "brown_sugar", "temperature_options": ["Room Temp"]}
                ]
            },
            {
                "name": "Liquid Sweeteners",
                "options": [
                    {"name": "honey", "temperature_options": ["Room Temp"]},
                    {"name": "maple_syrup", "temperature_options": ["Room Temp"]}
                ]
            }
        ]
    }
    sec_leaveners = {
        "required_category": "Chemical Leavener",
        "ai_recommendation": "Baking soda and baking powder provide immediate lift without requiring fermentation time, ideal for this dough archetype.",
        "categories": [
            {
                "name": "Baking Sodas/Powders",
                "options": [
                    {"name": "baking_soda", "temperature_options": ["Room Temp"]},
                    {"name": "baking_powder", "temperature_options": ["Room Temp"]}
                ]
            },
            {
                "name": "Yeast",
                "options": [
                    {"name": "instant_dry_yeast", "temperature_options": ["Room Temp"]},
                    {"name": "active_dry_yeast", "temperature_options": ["Room Temp"]}
                ]
            }
        ]
    }
    sec_additives = {
        "required_category": "None",
        "ai_recommendation": "No special additives are required for this dough structure.",
        "categories": []
    }
    flavor_inclusions = []
    
    # Grains ratio defaults
    flour_blend = {}
    if selected_grains:
        grains = [g.strip() for g in selected_grains.split(",") if g.strip()]
        if grains:
            equal_share = round(100.0 / len(grains), 2)
            for g in grains:
                slug = g.lower().replace(" ", "_").replace("-", "_")
                flour_blend[slug] = equal_share
            flour_blend[slug] += round(100.0 - sum(flour_blend.values()), 2)
    
    fat_starting_temp = "room_temp"
    required_actions = ["knead"]
    required_hardware = ["stand_mixer"]
    
    if category in ["cookies-shortbread", "cakes-batters", "cookies_shortbread", "cakes_batters", "cookie", "batter"]:
#         sec_lipids = {"required": "unsalted_butter", "options": ["unsalted_butter", "avocado_oil", "coconut_oil"]}
#         sec_liquids = {"required": "pure_water", "options": ["pure_water"]}
#         sec_binders = {"required": "whole_eggs", "options": ["none", "whole_eggs", "egg_whites"]}
        flavor_inclusions = [
            {"name": "Dark Chocolate Chunks", "bakers_percentage": 15.0, "volume_description": "1/2 cup"},
            {"name": "Maldon Sea Salt", "bakers_percentage": 0.5, "volume_description": "1 tsp flaky"}
        ]
    elif category in ["pastry-lamination", "pastry_lamination", "pastry", "choux-paste", "choux_paste", "choux", "fry", "fried-doughs"]:
        pass
#         sec_lipids = {"required": "unsalted_butter", "options": ["unsalted_butter", "salted_butter"]}
#         sec_liquids = {"required": "whole_milk", "options": ["whole_milk", "pure_water"]}
#         sec_binders = {"required": "whole_eggs", "options": ["whole_eggs", "egg_whites"]}
    elif category in ["enriched-soft", "enriched_soft", "pan"]:
        pass
#         sec_lipids = {"required": "unsalted_butter", "options": ["unsalted_butter", "avocado_oil"]}
#         sec_liquids = {"required": "whole_milk", "options": ["whole_milk", "pure_water"]}
#         sec_binders = {"required": "none", "options": ["none", "whole_eggs"]}
        flavor_inclusions = [
            {"name": "Cinnamon Sugar Swirl", "bakers_percentage": 10.0, "volume_description": "3 tbsp"},
            {"name": "Raisins", "bakers_percentage": 20.0, "volume_description": "1/2 cup"}
        ]
    elif category in ["alkaline-bath", "alkaline_bath", "bath", "flatbreads-griddles", "flatbreads_griddles", "flat"]:
        pass
#         sec_lipids = {"required": "none", "options": ["none", "unsalted_butter"]}
#         sec_liquids = {"required": "pure_water", "options": ["pure_water", "whole_milk"]}
        
    pref_slugs = []
    if selected_grains:
        pref_slugs = [g.strip().lower().replace(" ", "_") for g in selected_grains.split(",") if g.strip()]
    if not pref_slugs:
        pref_slugs = ["hard_red_spring_wheat"]
        
    return {
        "menu_description": f"A balanced formulation of {recipe_name or slug} optimized for target mechanics.",
        "recommended_grain_ids": pref_slugs,
        "flour_blend": flour_blend,
        "fat_starting_temp": fat_starting_temp,
        "required_actions": required_actions,
        "required_hardware": required_hardware,
        "secondary_ingredients": {
            "lipids": sec_lipids,
            "liquids": sec_liquids,
            "binders": sec_binders,
            "sweeteners": sec_sweeteners,
            "leaveners": sec_leaveners,
            "additives": sec_additives,
            "flavor_inclusions": flavor_inclusions
        }
    }
