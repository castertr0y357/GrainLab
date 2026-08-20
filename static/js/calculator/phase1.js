// phase1.js - Archetype Selection
window.phase1App = function(initialState = {}) {
    return {
        selected_master: initialState.selected_master || '',
        presetSlug: initialState.presetSlug || '',
        presetName: initialState.presetName || '',
        selected_idea: null,
        query: '',
        creative_query: '',
        creative_streaming: false,
        creative_ideas: [],
        searchOpen: false,
        phase1_categories: {
            'lean-crusty': {
                title: 'Lean & Crusty',
                definition: 'High-hydration dough systems relying entirely on flour, water, salt, and yeast. Focuses on long fermentation and intense thermal heat to gelatinize starches and form a thick, crisp crust.',
                presets: ['Hearth Boule / Batard', 'High-Hydration Slab', 'Tapered Baguette', 'Flash Pizza Crust']
            },
            'enriched-soft': {
                title: 'Enriched & Soft',
                definition: 'Dough systems enriched with fats, dairy, or sugar to tenderize the crumb. Inhibits gluten development to yield soft, pillowy, highly extensible structures.',
                presets: ['Sandwich Pan Loaf', 'Freeform Braided Loaf', 'Soft Dinner Roll', 'Filled Sweet Roll']
            },
            'alkaline-bath': {
                title: 'Alkaline Bath',
                definition: 'Doughs that undergo a hot alkaline water dip (using lye or baking soda) before baking. This alters surface pH, accelerating the Maillard reaction for a shiny, deep-brown crust and a distinct chew.',
                presets: ['Twisted Pretzel', 'Boiled Bagel', 'Laugen Bun / Roll', 'Pretzel Stick / Cracker']
            },
            'flatbreads-griddles': {
                title: 'Flatbreads & Griddles',
                definition: 'Highly extensible dough systems, often cooked on hot stone or steel griddles. Emphasizes steam expansion or minimal rise for flexible, pocketed, or thin flatbreads.',
                presets: ['Leavened Flatbread', 'Unleavened Stretched', 'Blistered Griddle Cake', 'Crisp Crispbread / Lavash']
            },
            'quick-breads-scones': {
                title: 'Quick Breads & Scones',
                definition: 'Chemically leavened doughs that rely on baking powder or baking soda rather than yeast. Features minimal mechanical mixing to prevent gluten strength and preserve crumbly, tender textures.',
                presets: ['Chemical Loaf', 'Layered Wedge Scone', 'Dropped / Cut Biscuit', 'Textured Muffin']
            },
            'cakes-batters': {
                title: 'Cakes & Batters',
                definition: 'Fluid batter systems featuring highly aerated emulsions of fat, sugar, and eggs. Emphasizes low-protein flour to maximize tenderness, support structure, and control crumb cell size.',
                presets: ['Foam / Sponge Cake', 'Creamed Layer Cake', 'High-Ratio Pound Cake', 'Fluid Griddle Batter']
            },
            'pastry-lamination': {
                title: 'Pastry & Lamination',
                definition: 'Dough systems that layer cold fat (typically butter) between dough sheets. The water inside the fat vaporizes during baking, pushing the layers apart to create hundreds of flaky, crisp leaves.',
                presets: ['Layered Viennoiserie', 'Inverted Puff Pastry', 'Shortcrust Tart Casing', 'Paper-Thin Phyllo / Strudel']
            },
            'choux-paste': {
                title: 'Choux Paste',
                definition: 'A unique pre-cooked dough system where flour is cooked in boiling liquid to gelatinize starches before egg integration. Relies entirely on intense steam expansion to inflate into hollow, crisp-shelled pastries.',
                presets: ['Piped Shell', 'Extrusion Fried Paste', 'Savory Emulsion']
            },
            'cookies-shortbread': {
                title: 'Cookies & Shortbread',
                definition: 'Low-moisture, high-fat confections engineered for controlled horizontal spread. Focuses on fat and sugar melting thresholds before the structural crumb sets in the oven.',
                presets: ['Drop Cookie', 'Bar / Slab', 'Slice & Bake', 'Rolled Cutout']
            },
            'fried-doughs': {
                title: 'Fried Doughs',
                definition: 'Yeast or chemically leavened doughs designed for rapid immersion frying. Relies on instant heat transfer to expand the leavened gas bubbles while cooking a thin, crisp, non-greasy crust.',
                presets: ['Yeast-Raised Donut', 'Cake / Chemical Donut', 'Batter Fritter / Beignet', 'Fried Laminated']
            },
            'fresh-pasta-noodles': {
                title: 'Fresh Pasta & Noodles',
                definition: 'Unfermented, dense flour and egg systems mixed under high compaction. Emphasizes protein alignment and gluten density for a resilient, firm bite (al dente) after boiling.',
                presets: ['Sheeted Ribbon Pastas', 'Stuffed / Encased Pockets', 'Extruded Die Shapes', 'Alkaline Cut Noodles']
            }
        },
        init() {
            console.log("Phase 1 initialized with master:", this.selected_master);
        },
        selectCreativeIdea(idea) {
            this.selected_idea = idea;
            this.selected_master = idea.category_slug;
            this.presetSlug = idea.archetype_id; 
            this.presetName = idea.recipe_name;
        },
        async generateCreativeIdeas() {
            if (!this.creative_query.trim()) return;
            
            this.creative_ideas = [];
            this.creative_streaming = true;
            
            try {
                const response = await fetch(`/generate-creative-ideas/?prompt=${encodeURIComponent(this.creative_query)}`);
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                let buffer = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); 
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const dataStr = line.replace('data: ', '').trim();
                            if (dataStr && dataStr !== '{}') {
                                try {
                                    const idea = JSON.parse(dataStr);
                                    if (idea.generated_ideas) {
                                        this.creative_ideas.push(...idea.generated_ideas);
                                    } else {
                                        this.creative_ideas.push(idea);
                                    }
                                } catch (e) {
                                    console.error("Error parsing creative idea stream data", e);
                                }
                            }
                        }
                    }
                }
            } catch (e) {
                console.error("Failed to generate creative ideas", e);
            } finally {
                this.creative_streaming = false;
            }
        }
    };
};
