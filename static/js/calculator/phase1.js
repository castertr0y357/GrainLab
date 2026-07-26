// phase1.js - Archetype Selection
window.phase1App = function(initialState = {}) {
    return {
        selected_master: initialState.selected_master || '',
        presetSlug: initialState.presetSlug || '',
        query: '',
        searchOpen: false,
        phase1_categories: {
            'lean-crusty': {
                title: 'Lean & Crusty',
                definition: 'High-hydration dough systems relying entirely on flour, water, salt, and yeast. Focuses on long fermentation and intense thermal heat to gelatinize starches and form a thick, crisp crust.',
                presets: ['Sourdough Boule', 'Baguette', 'Artisan Pizza', 'Ciabatta']
            },
            'enriched-soft': {
                title: 'Enriched & Soft',
                definition: 'Dough systems enriched with fats, dairy, or sugar to tenderize the crumb. Inhibits gluten development to yield soft, pillowy, highly extensible structures.',
                presets: ['Everyday Sandwich', 'Brioche', 'Challah', 'Burger Buns', 'Cinnamon Rolls']
            },
            'alkaline-bath': {
                title: 'Alkaline Bath',
                definition: 'Doughs that undergo a hot alkaline water dip (using lye or baking soda) before baking. This alters surface pH, accelerating the Maillard reaction for a shiny, deep-brown crust and a distinct chew.',
                presets: ['Soft Pretzels', 'Boiled Bagels']
            },
            'flatbreads-griddles': {
                title: 'Flatbreads & Griddles',
                definition: 'Highly extensible dough systems, often cooked on hot stone or steel griddles. Emphasizes steam expansion or minimal rise for flexible, pocketed, or thin flatbreads.',
                presets: ['Naan', 'Flour Tortillas', 'Pita Bread', 'Crackers']
            },
            'quick-breads-scones': {
                title: 'Quick Breads & Scones',
                definition: 'Chemically leavened doughs that rely on baking powder or baking soda rather than yeast. Features minimal mechanical mixing to prevent gluten strength and preserve crumbly, tender textures.',
                presets: ['Southern Buttermilk Biscuits', 'Scones', 'Muffins', 'Irish Soda Bread']
            },
            'cakes-batters': {
                title: 'Cakes & Batters',
                definition: 'Fluid batter systems featuring highly aerated emulsions of fat, sugar, and eggs. Emphasizes low-protein flour to maximize tenderness, support structure, and control crumb cell size.',
                presets: ['Yellow Layer Cake', 'Pancakes', 'Waffles', 'Sponge Cake']
            },
            'pastry-lamination': {
                title: 'Pastry & Lamination',
                definition: 'Dough systems that layer cold fat (typically butter) between dough sheets. The water inside the fat vaporizes during baking, pushing the layers apart to create hundreds of flaky, crisp leaves.',
                presets: ['Classic Croissants', 'Puff Pastry', 'Flaky Pie Crust']
            },
            'choux-paste': {
                title: 'Choux Paste',
                definition: 'A unique pre-cooked dough system where flour is cooked in boiling liquid to gelatinize starches before egg integration. Relies entirely on intense steam expansion to inflate into hollow, crisp-shelled pastries.',
                presets: ['Chocolate Éclairs', 'Cream Puffs', 'Gougères', 'Churros']
            },
            'cookies-shortbread': {
                title: 'Cookies & Shortbread',
                definition: 'Low-moisture, high-fat confections engineered for controlled horizontal spread. Focuses on fat and sugar melting thresholds before the structural crumb sets in the oven.',
                presets: ['Chocolate Chip Cookies', 'Shortbread Wedges', 'Biscotti', 'Macarons']
            },
            'fried-doughs': {
                title: 'Fried Doughs',
                definition: 'Yeast or chemically leavened doughs designed for rapid immersion frying. Relies on instant heat transfer to expand the leavened gas bubbles while cooking a thin, crisp, non-greasy crust.',
                presets: ['Yeast-Raised Donuts', 'Beignets', 'Fritters']
            },
            'fresh-pasta-noodles': {
                title: 'Fresh Pasta & Noodles',
                definition: 'Unfermented, dense flour and egg systems mixed under high compaction. Emphasizes protein alignment and gluten density for a resilient, firm bite (al dente) after boiling.',
                presets: ['Fresh Egg Tagliatelle', 'Ramen', 'Lasagna Sheets']
            }
        },
        init() {
            console.log("Phase 1 initialized with master:", this.selected_master);
        }
    };
};
