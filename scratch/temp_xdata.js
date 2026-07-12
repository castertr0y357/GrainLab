const xData = {
    current_phase: 1,
    grain_mode: 'milled',
    selected_master: '',
    searchOpen: false,
    query: '',
    
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
    
    global_ai_enabled: false,
    hovered_element: null,
    sidebar_insight_loading: false,
    sidebar_labor_roi: '',
    sidebar_analysis: '',
    sidebar_tier: '',
    sidebar_elevate: '',
    
    // Factual science profiles
    factual_dictionary: {
        'refined': 'Store refined commercial flour. High shelf stability and consistent protein levels, but stripped of bran and germ.',
        'milled': 'Freshly milled whole grain. Retains 100% of germ and bran oils. High enzyme activity and complex rustic flavor profile.',
        
        // Grains
        'grain_hard_red_spring': 'High-protein hard wheat. Strong, elastic gluten structure suitable for high-rise hearth loaves.',
        'grain_hard_red_winter': 'Moderate-high protein wheat. Balanced gluten elasticity and extensibility, highly versatile.',
        'grain_soft_white': 'Low-protein soft wheat. Weak, tender gluten structure ideal for tender pastries, cakes, and cookies.',
        'grain_hard_white': 'Mild, light-colored hard wheat. Provides structural strength without the bitter red wheat tannins.',
        'grain_spelt': 'Ancient hulled wheat species. Very extensible but weak gluten strength; highly water-absorbent.',
        'grain_kamut': 'Ancient Khorasan wheat. Rich, sweet flavor, high protein, but lower elasticity; absorbs water slowly.',
        'grain_rye': 'Ancient rye grass grain. High pentosans and weak gluten. Produces sticky, dense, complex savory doughs.',

        // Tools
        'stand_mixer': 'Planetary stand mixer. Delivers intensive mechanical shearing, building fast gluten structures but adding heat.',
        'bread_machine': 'Automated high-torque chamber mixer. Fully enclosed, creating high friction heat and rapid development.',
        'food_processor': 'High-velocity steel blade shearing. Forces hydration and gluten alignment rapidly but risks blade damage.',
        'hand_beaters': 'Light whipping beaters. Aerates liquid and fat emulsions without building strong gluten networks.',
        'whisk': 'Manual aerating whisk. Incorporates gas bubbles into fluid batters to support leavening lift.',
        'spatula_bowl': 'Zero-friction manual mixing. Minimal mechanical energy transfer to prevent any accidental gluten formation.',

        // Actions
        'knead': 'Mechanical folding and stretching of dough to align glutenin and gliadin proteins into a structural matrix.',
        'cream': 'Aeration of solid fat and sugar. Traps micro-bubbles to form the foundation of crumb leavening.',
        'fold': 'Gentle folding layers the dough and develops structure without degassing. Crucial for retaining large, irregular open crumb cells.',
        'cut_in': 'Distribution of cold fat pieces into dry flour. Forms flat fat pockets for flaky pastry lamination.',
        'sheet': 'Compressing dough through rollers to achieve a uniform thin sheet, aligning starch and gluten strands.',
        'extrude': 'Forcing dense dough through a shaped die to form structured shapes under high compaction pressure.',

        // Environments
        'ambient': 'Countertop proofing. Relies on local ambient room temperature (70-75°F) for steady biological activity.',
        'mat': 'Open heated proofing mat. Warms the bottom of the vessel to accelerate yeast and lactic acid production.',
        'box': 'Warm, humid enclosed proofing chamber. Maximizes biological activity while preventing surface skin drying.',
        'refrigerator': 'Cold retardation (34-40°F). Solidifies fats and slows yeast while enzymes continue developing complex sugars.',
        'bench_rest': 'Relaxation rest under a damp cloth. Releases elastic tension in the gluten matrix to allow final shaping.',

        // Form Factors
        'cast-iron-dutch-oven': 'Heavy cast iron pot. Retains heat and traps steam released from the dough. Ensures optimal starch gelatinization and maximum oven spring.',
        'open-baking-stone-steel': 'High-conduction hearth surface. Transports heat immediately into the base of the loaf for maximum oven spring.',
        'standard-9x5-pan': 'Metal loaf pan. Restricts lateral movement, forcing the rising dough vertically into a uniform sandwich shape.',
        'perforated-baking-sheet': 'Airflow baking tray. Promotes dry skin dehydration on all sides, crucial for crispy pretzels or bagels.',
        
        // Substitutions
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
    },

    setHoveredElement(key) {
        if (!key) return;
        this.hovered_element = key;
        
        if (key.startsWith('archetype_')) {
            const archId = key.replace('archetype_', '');
            const arch = this.enginesArchetypes[this.selected_master]?.[archId];
            this.sidebar_tier = '';
            this.sidebar_labor_roi = '';
            this.sidebar_analysis = arch ? (arch.description || `Recipes belonging to the ${arch.label || archId} archetype.`) : '';
            this.sidebar_insight_loading = false;
            return;
        }
        
        if (key.startsWith('grain_')) {
            if (this.advisoryLoading) {
                this.sidebar_insight_loading = true;
                this.sidebar_tier = '';
                this.sidebar_analysis = '';
                return;
            }
            const key_clean = key.toLowerCase().replace('grain_', '');
            const berry = this.activeBerries.find(b => {
                const bNameSlug = b.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
                return bNameSlug.includes(key_clean) || key_clean.includes(bNameSlug);
            });
            if (berry) {
                const ev = this.grainEvaluations.find(e => e.grain_id === berry.id);
                if (ev) {
                    this.sidebar_tier = ev.tier;
                    this.sidebar_analysis = ev.reasoning;
                    this.sidebar_labor_roi = ''; // Grains do not show labor ROI
                    this.sidebar_insight_loading = false;
                    return;
                }
            }
            // Fallback if not found in parent array
            this.sidebar_tier = 'recommended';
            this.sidebar_analysis = this.getFactualProfile();
            this.sidebar_insight_loading = false;
            return;
        }
        
        let url = `/ai-sidebar-insight/?element=${encodeURIComponent(key)}&category_slug=${encodeURIComponent(this.selected_master || '')}&preset_slug=${encodeURIComponent(this.presetSlug || '')}`;
        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (this.hovered_element === key) {
                    this.sidebar_labor_roi = data.labor_roi || 'Low Priority / Minor Textural Return';
                    this.sidebar_analysis = data.last_10_percent_analysis || 'No detailed analysis returned.';
                    this.sidebar_tier = data.recommendation_tier || '';
                    this.sidebar_insight_loading = false;
                }
            })
            .catch(err => {
                console.error('Failed fetching sidebar insight:', err);
                if (this.hovered_element === key) {
                    this.sidebar_insight_loading = false;
                }
            });
    },

    clearHoveredElement() {
        this.hovered_element = null;
        this.sidebar_labor_roi = '';
        this.sidebar_analysis = '';
        this.sidebar_tier = '';
        this.sidebar_insight_loading = false;
    },

    getFactualProfile() {
        if (!this.hovered_element) return '';
        const key = this.hovered_element.toLowerCase();
        
        if (this.factual_dictionary[key]) {
            return this.factual_dictionary[key];
        }
        
        for (const k in this.factual_dictionary) {
            if (key.includes(k) || k.includes(key)) {
                return this.factual_dictionary[k];
            }
        }
        return 'Factual profile description currently compiling. Evaluates starch/lipid interaction, gluten density ceiling, or thermal absorption properties relative to the active engine.';
    },

    getHoveredGrainEval() {
        if (!this.hovered_element || !this.hovered_element.startsWith('grain_')) {
            return null;
        }
        const key = this.hovered_element.toLowerCase().replace('grain_', '');
        const berry = this.activeBerries.find(b => {
            const bNameSlug = b.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
            return bNameSlug.includes(key) || key.includes(bNameSlug);
        });
        if (!berry) return null;
        return this.grainEvaluations.find(e => e.grain_id === berry.id);
    },
    
    /* Auto-correction and warning computed on client side */
    presetName: '',
    presetSlug: '',
    presetModified: false,
    
    advisoryRecommendedName: '',
    advisoryRecommendedReason: '',
    advisoryHighRiskName: '',
    advisoryHighRiskReason: '',
    advisoryLoading: false,
    advisoryLoadingMessage: '',
    grainEvaluations: [],
    globalElevateRecipe: '',
    advisoryTimeout: null,
    advisoryAbortController: null,
    get elevateWays() {
        if (Array.isArray(this.globalElevateRecipe)) {
            return this.globalElevateRecipe;
        }
        if (typeof this.globalElevateRecipe === 'string' && this.globalElevateRecipe.trim()) {
            return [this.globalElevateRecipe];
        }
        return [];
    },
    
    // Geometry evaluation and profile adjustments
    geometry_status: 'recommended',
    geometry_advisory: '',
    geometry_temp_offset: 0,
    geometry_time_offset: 0,
    geometry_steam_override: 'no-change',

    /* === POLYMORPHIC RECIPE GENERATION STATE === */
    active_archetype_id: null,
    generated_variants: [],
    recommended_grain_ids: [],
    variant_loading: false,
    hovered_variant: null,
    /* Engine archetypes map keyed by category slug */
    enginesArchetypes: JSON.parse(''),

    creativity_recipes: [],
    creativity_loading: false,
    expanded_level: null,
    alternative_variants: [],
    selected_recipe_id: null,
    recipe_selected: false,

    selectArchetype(archetype_id, engine_id) {
        if (this.active_archetype_id === archetype_id) {
            this.active_archetype_id = null;
            this.creativity_recipes = [];
            this.recipe_selected = false;
            this.selected_recipe_id = null;
            this.expanded_level = null;
            this.alternative_variants = [];
            return;
        }
        this.active_archetype_id = archetype_id;
        this.creativity_recipes = [];
        this.recipe_selected = false;
        this.selected_recipe_id = null;
        this.expanded_level = null;
        this.alternative_variants = [];
        
        // Fetch 5 recipes per creativity level for this archetype!
        this.fetchCreativityRecipes(engine_id, archetype_id);
    },

    fetchCreativityRecipes(category_slug, archetype_id) {
        if (!category_slug || category_slug === 'null' || !archetype_id) {
            this.creativity_recipes = [];
            this.creativity_loading = false;
            return;
        }
        this.creativity_loading = true;
        this.recipe_selected = false;
        this.selected_recipe_id = null;
        this.expanded_level = null;
        this.alternative_variants = [];
        this.grainEvaluations = [];
        this.resetAdvisory();

        const inventory_ids = this.activeBerries.map(b => b.id).join(',');
        const url = `/generate-creativity-recipes/?engine_id=${encodeURIComponent(category_slug)}&active_archetype_id=${encodeURIComponent(archetype_id)}&inventory_ids=${encodeURIComponent(inventory_ids)}`;
        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (this.selected_master === category_slug && this.active_archetype_id === archetype_id) {
                    this.creativity_recipes = data.recipes || [];
                }
                this.creativity_loading = false;
            })
            .catch(err => {
                console.error('[GrainLab] Failed fetching creativity recipes:', err);
                this.creativity_loading = false;
            });
    },

    toggleExpandLevel(level) {
        if (this.expanded_level === level) {
            this.expanded_level = null;
            this.alternative_variants = [];
            return;
        }
        this.expanded_level = level;
        this.alternative_variants = [];
        this.variant_loading = true;

        const concept_recipe = this.creativity_recipes.find(r => r.creativity_level === level);
        if (!concept_recipe) {
            this.variant_loading = false;
            return;
        }

        const inventory_ids = this.activeBerries.map(b => b.id).join(',');
        const url = `/generate-variants/?engine_id=${encodeURIComponent(this.selected_master)}&active_archetype_id=${encodeURIComponent(this.active_archetype_id)}&creativity_level=${level}&inventory_ids=${encodeURIComponent(inventory_ids)}`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (this.expanded_level === level) {
                    this.alternative_variants = data.generated_variants || [];
                }
                this.variant_loading = false;
            })
            .catch(err => {
                console.error('[GrainLab] Failed fetching alternative variants:', err);
                this.variant_loading = false;
            });
    },

    getRecipesForLevel(level) {
        return this.creativity_recipes.filter(r => r.creativity_level === level);
    },

    onRecipeHover(recipe) {
        if (!recipe) return;
        this.hovered_variant = recipe.recipe_id || recipe.variant_id || null;
        this.sidebar_tier = 'recommended';
        this.sidebar_analysis = recipe.sidebar_science_profile || '';
        this.sidebar_labor_roi = (recipe.sidebar_ai_insight && recipe.sidebar_ai_insight.labor_roi) || '';
        this.sidebar_insight_loading = false;
    },

    selectRecipe(recipe) {
        if (!recipe) return;
        const recipe_id = recipe.recipe_id || recipe.variant_id;
        const recipe_name = recipe.recipe_name || recipe.variant_name;
        this.selected_recipe_id = recipe_id;
        this.presetSlug = recipe_id;
        this.presetName = recipe_name;
        this.recipe_selected = true;
        this.recommended_grain_ids = recipe.recommended_grain_ids || [];
        this.sidebar_analysis = recipe.sidebar_science_profile || '';
        this.sidebar_labor_roi = (recipe.sidebar_ai_insight && recipe.sidebar_ai_insight.labor_roi) || '';

        // Select the ideal grain based on recommended list if available
        if (this.recommended_grain_ids && this.recommended_grain_ids.length > 0) {
            const firstRec = this.recommended_grain_ids[0];
            const berry = this.activeBerries.find(b => {
                const bNameSlug = b.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
                return bNameSlug.includes(firstRec) || firstRec.includes(bNameSlug);
            });
            if (berry) {
                this.activeBerries.forEach(b => {
                    b.selected = (b.id === berry.id);
                });
            } else {
                this.selectIdealGrain();
            }
        } else {
            this.selectIdealGrain();
        }

        // Trigger advisory call to fetch recommended/sub-optimal classifications
        this.fetchAdvisory(recipe_name);
    },

    getClassificationLabel(berry) {
        if (!this.grainEvaluations || this.grainEvaluations.length === 0) return '';
        const ev = this.grainEvaluations.find(e => e.grain_id === berry.id);
        if (!ev) return '';
        if (ev.tier === 'recommended') return 'Recommended';
        if (ev.tier === 'sub-optimal') return 'Sub-Optimal';
        if (ev.tier === 'not-recommended') return 'Not Recommended';
        return '';
    },

    getGrainReasoning(berry) {
        if (!this.grainEvaluations || this.grainEvaluations.length === 0) return '';
        const ev = this.grainEvaluations.find(e => e.grain_id === berry.id);
        return ev ? ev.reasoning : '';
    },

    getClassificationBadgeStyle(berry) {
        if (!this.grainEvaluations || this.grainEvaluations.length === 0) return '';
        const ev = this.grainEvaluations.find(e => e.grain_id === berry.id);
        if (!ev) return '';
        if (ev.tier === 'recommended') return 'color: #ffd700; font-weight: bold; text-transform: uppercase; font-size: 0.65rem;';
        if (ev.tier === 'sub-optimal') return 'color: var(--warning); font-weight: bold; text-transform: uppercase; font-size: 0.65rem;';
        if (ev.tier === 'not-recommended') return 'color: var(--danger); font-weight: bold; text-transform: uppercase; font-size: 0.65rem;';
        return '';
    },

    /* Grains inventory data mapped from django context */
    activeBerries: [
        []
    ],

    /* Countertop View Timers & Sequential Timeline */
    countertopMode: false,
    steps: [
        { key: 'mix', name: 'Mix', desc: 'Combine ingredients into a cohesive shaggy mass.' },
        { key: 'knead', name: 'Knead', desc: 'Work the dough to develop structural gluten alignment.' },
        { key: 'autolyse', name: 'Rest/Autolyse', desc: 'Let the dough rest to relax gluten and absorb moisture.' },
        { key: 'bulk', name: 'Bulk Ferment', desc: 'Primary fermentation: allow yeast/sourdough to aerate the dough.' },
        { key: 'proof', name: 'Proof', desc: 'Final proofing: shape and rise in baking pan/mat.' },
        { key: 'bake', name: 'Bake', desc: 'Oven bake: target internal temp and crisp crust development.' }
    ],
    currentStepIndex: 0,
    stepTimeRemaining: 0,
    stepTotalTime: 1,
    timerInterval: null,
    timerRunning: false,
    durations: { mix: 5, knead: 10, autolyse: 30, bulk: 240, proof: 120, bake: 45 },
    isAlarm: false,
    elapsedOvertime: 0,
    audioCtx: null,
    alarmInterval: null,
    bakeTemp: '',
    bakeSteam: '',
    donenessTemp: '',
    waterTemp: '',

    init() {
        this.$watch('presetSlug', value => {
            this.selectIdealGrain();
            this.fetchAdvisory(value);
            if (value) {
                this.presetModified = false;
            }
        });
        this.$watch('selected_master', value => {
            this.active_archetype_id = null;
            this.creativity_recipes = [];
            this.recipe_selected = false;
            this.selected_recipe_id = null;
            this.expanded_level = null;
            this.alternative_variants = [];
            if (value && value !== 'null') {
                this.fetchAdvisory(this.presetSlug);
            }
        });
        this.$watch('grain_mode', value => {
            /* grain_mode is hardlocked to 'milled'. Watcher retained for compatibility. */
            this.selectIdealGrain();
            this.fetchAdvisory(this.presetSlug);
        });
        this.$watch('activeBerries', () => {
            this.fetchElevateTips(this.presetSlug);
        }, { deep: true });
        this.selectIdealGrain();
        if (this.presetSlug || (this.selected_master && this.selected_master !== 'null')) {
            this.fetchAdvisory(this.presetSlug);
        }
        document.body.addEventListener('htmx:afterSwap', (e) => {
            const meta = document.getElementById('geometry-metadata');
            if (meta) {
                this.geometry_status = meta.getAttribute('data-geometry-status') || 'recommended';
                this.geometry_advisory = meta.getAttribute('data-geometry-advisory') || '';
                this.geometry_temp_offset = parseInt(meta.getAttribute('data-geometry-temp-offset') || '0', 10);
                this.geometry_time_offset = parseInt(meta.getAttribute('data-geometry-time-offset') || '0', 10);
                this.geometry_steam_override = meta.getAttribute('data-geometry-steam-override') || 'no-change';
            }
        });
    },

    fetchAdvisory(slug) {
        if (!this.recipe_selected) {
            this.resetAdvisory();
            return;
        }
        
        // Clear any existing debounce timeout
        if (this.advisoryTimeout) {
            clearTimeout(this.advisoryTimeout);
        }
        
        // Debounce for 750ms
        this.advisoryTimeout = setTimeout(() => {
            this.fetchGrainEvaluations(slug);
        }, 750);
    },

    fetchGrainEvaluations(slug) {
        if (!this.recipe_selected || !slug) {
            this.resetAdvisory();
            return;
        }

        // Abort active HTTP request if there is one
        if (this.advisoryAbortController) {
            this.advisoryAbortController.abort();
        }

        // Create a new controller for this request
        this.advisoryAbortController = new AbortController();
        const signal = this.advisoryAbortController.signal;

        this.advisoryLoading = true;
        if (this.hovered_element && this.hovered_element.startsWith('grain_')) {
            this.sidebar_insight_loading = true;
            this.sidebar_tier = '';
            this.sidebar_analysis = '';
        }
        
        // Start premium themed loading messages
        const messages = [
            'Consulting Bakers Almanac...',
            'Evaluating Gluten Matrices...',
            'Optimizing Crumb Profiles...',
            'Synthesizing Food Chemistry...'
        ];
        let idx = 0;
        this.advisoryLoadingMessage = messages[0];
        const timer = setInterval(() => {
            if (!this.advisoryLoading) {
                clearInterval(timer);
                return;
            }
            idx = (idx + 1) % messages.length;
            this.advisoryLoadingMessage = messages[idx];
        }, 750);

        let url = '/ai-grain-advisory/?preset_slug=' + encodeURIComponent(slug) + '&only_evaluations=true';
        if (this.selected_master && this.selected_master !== 'null') {
            url += '&category_slug=' + encodeURIComponent(this.selected_master);
        }

        fetch(url, { signal })
            .then(res => res.json())
            .then(data => {
                this.grainEvaluations = data.grain_evaluations || [];
                const rec = this.grainEvaluations.find(e => e.tier === 'recommended');
                const risk = this.grainEvaluations.find(e => e.tier === 'not-recommended');
                this.advisoryRecommendedName = rec ? this.getGrainNameById(rec.grain_id) : '';
                this.advisoryRecommendedReason = rec ? rec.reasoning : '';
                this.advisoryHighRiskName = risk ? this.getGrainNameById(risk.grain_id) : '';
                this.advisoryHighRiskReason = risk ? risk.reasoning : '';
                this.advisoryLoading = false;
                this.advisoryAbortController = null;
                
                // Update hovered grain details dynamically once advisory resolves
                if (this.hovered_element && this.hovered_element.startsWith('grain_')) {
                    const key_clean = this.hovered_element.toLowerCase().replace('grain_', '');
                    const berry = this.activeBerries.find(b => {
                        const bNameSlug = b.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
                        return bNameSlug.includes(key_clean) || key_clean.includes(bNameSlug);
                    });
                    if (berry) {
                        const ev = this.grainEvaluations.find(e => e.grain_id === berry.id);
                        if (ev) {
                            this.sidebar_tier = ev.tier;
                            this.sidebar_analysis = ev.reasoning;
                            this.sidebar_insight_loading = false;
                        }
                    }
                }
                
                /* Broadcast to child <form x-data> scope for cross-boundary reactivity */
                window.dispatchEvent(new CustomEvent('grain-advisory-updated', {
                    detail: { grain_evaluations: this.grainEvaluations }
                }));

                // Immediately trigger "Ways to Elevate" query last, building on user selections
                this.fetchElevateTips(slug);
            })
            .catch(err => {
                if (err.name === 'AbortError') {
                    console.log('Advisory fetch aborted.');
                    return;
                }
                console.error('Failed fetching advisory evaluations:', err);
                this.advisoryLoading = false;
                this.advisoryAbortController = null;
                if (this.hovered_element && this.hovered_element.startsWith('grain_')) {
                    this.sidebar_insight_loading = false;
                }
            });
    },

    fetchElevateTips(slug) {
        if (!this.recipe_selected || !slug) {
            this.globalElevateRecipe = '';
            return;
        }

        const selectedGrains = this.activeBerries
            .filter(b => b.selected)
            .map(b => b.id)
            .join(',');

        let url = '/ai-grain-advisory/?preset_slug=' + encodeURIComponent(slug) + '&selected_grains=' + encodeURIComponent(selectedGrains) + '&only_elevate=true';
        if (this.selected_master && this.selected_master !== 'null') {
            url += '&category_slug=' + encodeURIComponent(this.selected_master);
        }

        fetch(url)
            .then(res => res.json())
            .then(data => {
                this.globalElevateRecipe = data.elevate_recipe || '';
            })
            .catch(err => {
                console.error('Failed fetching elevate tips:', err);
            });
    },

    resetAdvisory() {
        this.advisoryRecommendedName = '';
        this.advisoryRecommendedReason = '';
        this.advisoryHighRiskName = '';
        this.advisoryHighRiskReason = '';
        this.grainEvaluations = [];
        this.globalElevateRecipe = '';
    },

    getGrainNameById(id) {
        const b = this.activeBerries.find(x => x.id === id);
        return b ? b.name : 'Unknown Grain';
    },

    getGrainStyle(berry) {
        /* === Tier 2 variant recommended_grain_ids golden ring check === */
        if (this.recommended_grain_ids && this.recommended_grain_ids.length > 0) {
            const berryNameSlug = berry.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
            const isVariantRecommended = this.recommended_grain_ids.some(rid =>
                berryNameSlug === rid || berryNameSlug.includes(rid) || rid.includes(berryNameSlug)
            );
            if (isVariantRecommended) {
                return berry.selected
                    ? 'border-color: #ffd700; box-shadow: 0 0 18px rgba(255, 215, 0, 0.9); background-color: rgba(255, 215, 0, 0.12); outline: 2px solid rgba(255, 215, 0, 0.6);'
                    : 'border-color: #ffd700; box-shadow: 0 0 14px rgba(255, 215, 0, 0.7); background-color: rgba(255, 215, 0, 0.06); outline: 1px solid rgba(255, 215, 0, 0.4);';
            }
        }
        if (this.grainEvaluations && this.grainEvaluations.length > 0) {
            const evaluation = this.grainEvaluations.find(e => e.grain_id === berry.id);
            if (evaluation) {
                if (evaluation.tier === 'recommended') {
                    return berry.selected 
                        ? 'border-color: #ffd700; box-shadow: 0 0 12px rgba(255, 215, 0, 0.6); background-color: rgba(255, 215, 0, 0.08);' 
                        : 'border-color: #ffd700; box-shadow: 0 0 8px rgba(255, 215, 0, 0.3); background-color: rgba(255, 215, 0, 0.02);';
                } else if (evaluation.tier === 'not-recommended') {
                    return berry.selected 
                        ? 'border-color: var(--danger); box-shadow: 0 0 12px rgba(220, 53, 69, 0.6); background-color: rgba(220, 53, 69, 0.08);' 
                        : 'border-color: var(--danger); box-shadow: 0 0 8px rgba(220, 53, 69, 0.3); background-color: rgba(220, 53, 69, 0.02);';
                }
            }
        }
        if (this.advisoryRecommendedName && berry.name === this.advisoryRecommendedName) {
            return berry.selected 
                ? 'border-color: #ffd700; box-shadow: 0 0 12px rgba(255, 215, 0, 0.6); background-color: rgba(255, 215, 0, 0.08);' 
                : 'border-color: #ffd700; box-shadow: 0 0 8px rgba(255, 215, 0, 0.3); background-color: rgba(255, 215, 0, 0.02);';
        } else if (this.advisoryHighRiskName && berry.name === this.advisoryHighRiskName) {
            return berry.selected 
                ? 'border-color: var(--danger); box-shadow: 0 0 12px rgba(220, 53, 69, 0.6); background-color: rgba(220, 53, 69, 0.08);' 
                : 'border-color: var(--danger); box-shadow: 0 0 8px rgba(220, 53, 69, 0.3); background-color: rgba(220, 53, 69, 0.02);';
        } else {
            return berry.selected 
                ? 'border-color: var(--accent); background-color: rgba(255, 136, 0, 0.05);' 
                : '';
        }
    },

    get sortedBerries() {
        if (!this.grainEvaluations || this.grainEvaluations.length === 0) {
            return this.activeBerries;
        }
        return [...this.activeBerries].sort((a, b) => {
            const evalA = this.grainEvaluations.find(e => e.grain_id === a.id);
            const evalB = this.grainEvaluations.find(e => e.grain_id === b.id);
            
            const tierA = evalA ? evalA.tier : 'indifferent';
            const tierB = evalB ? evalB.tier : 'indifferent';
            
            const score = {
                'recommended': 1,
                'sub-optimal': 2,
                'indifferent': 3,
                'not-recommended': 4
            };
            
            const scoreA = score[tierA] || 3;
            const scoreB = score[tierB] || 3;
            
            if (scoreA !== scoreB) {
                return scoreA - scoreB;
            }
            return a.name.localeCompare(b.name);
        });
    },

    selectIdealGrain() {
        if (!this.presetSlug) {
            this.activeBerries.forEach(b => {
                b.selected = false;
            });
            return;
        }
        let idealName = 'Hard Red Winter Wheat';
        let s = this.presetSlug.toLowerCase();
        if (['baguette', 'sourdough-boule', 'ciabatta', 'artisan-pizza', 'bagel', 'eclairs'].includes(s)) {
            idealName = 'Hard Red Spring Wheat';
        } else if (['french-loaf', 'brioche', 'pretzel', 'croissants'].includes(s)) {
            idealName = 'Hard Red Winter Wheat';
        } else if (['everyday-sandwich', 'challah', 'cinnamon-rolls', 'burger-buns', 'naan', 'donuts', 'tagliatelle'].includes(s)) {
            idealName = 'Hard White Wheat';
        } else if (['biscuits', 'cookies', 'yellow-cake'].includes(s)) {
            idealName = 'Soft White Wheat';
        }
        this.activeBerries.forEach(b => {
            b.selected = (b.name === idealName);
        });
    },

    isIdealGrain(berryName) {
        if (!this.presetSlug) {
            return false;
        }
        let idealName = 'Hard Red Winter Wheat';
        let s = this.presetSlug.toLowerCase();
        if (['baguette', 'sourdough-boule', 'ciabatta', 'artisan-pizza', 'bagel', 'eclairs'].includes(s)) {
            idealName = 'Hard Red Spring Wheat';
        } else if (['french-loaf', 'brioche', 'pretzel', 'croissants'].includes(s)) {
            idealName = 'Hard Red Winter Wheat';
        } else if (['everyday-sandwich', 'challah', 'cinnamon-rolls', 'burger-buns', 'naan', 'donuts', 'tagliatelle'].includes(s)) {
            idealName = 'Hard White Wheat';
        } else if (['biscuits', 'cookies', 'yellow-cake'].includes(s)) {
            idealName = 'Soft White Wheat';
        }
        return berryName === idealName;
    },


    startBake() {
        let el = document.getElementById('countertop-data');
        if (el) {
            let stepsData = el.getAttribute('data-steps');
            if (stepsData) {
                try {
                    this.steps = JSON.parse(stepsData);
                } catch (e) {
                    console.error('Failed to parse countertop steps:', e);
                }
            }
            this.bakeTemp = el.getAttribute('data-bake-temp') || '';
            this.bakeSteam = el.getAttribute('data-bake-steam') || '';
            this.donenessTemp = el.getAttribute('data-doneness-temp') || '';
            this.waterTemp = el.getAttribute('data-water-temp') || '';
        }
        this.countertopMode = true;
        this.currentStepIndex = 0;
        this.stepTimeRemaining = this.steps[0] ? this.steps[0].duration_sec : 0;
        this.stepTotalTime = this.stepTimeRemaining;
        
        this.stopAlarm();
        this.pauseTimer();
        
        /* Unlock AudioContext on user gesture */
        if (!this.audioCtx) {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (AudioContextClass) {
                this.audioCtx = new AudioContextClass();
            }
        }
    },

    startTimer() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        this.timerRunning = true;
        
        /* Unlock/resume AudioContext on user gesture */
        if (!this.audioCtx) {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (AudioContextClass) {
                this.audioCtx = new AudioContextClass();
            }
        } else if (this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }

        this.timerInterval = setInterval(() => {
            if (!this.isAlarm) {
                if (this.stepTimeRemaining > 0) {
                    this.stepTimeRemaining--;
                } else {
                    this.isAlarm = true;
                    this.elapsedOvertime = 0;
                    this.playAlarm();
                }
            } else {
                this.elapsedOvertime++;
            }
        }, 1000);
    },

    pauseTimer() {
        this.timerRunning = false;
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    },

    toggleTimer() {
        if (this.isAlarm) {
            this.stopAlarm();
            this.pauseTimer();
        } else if (this.timerRunning) {
            this.pauseTimer();
        } else {
            this.startTimer();
        }
    },

    nextStep() {
        this.stopAlarm();
        this.pauseTimer();
        if (this.currentStepIndex < this.steps.length - 1) {
            this.currentStepIndex++;
            this.stepTimeRemaining = this.steps[this.currentStepIndex].duration_sec;
            this.stepTotalTime = this.stepTimeRemaining;
        } else {
            alert('🎉 Baking process completed!');
        }
    },

    prevStep() {
        this.stopAlarm();
        this.pauseTimer();
        if (this.currentStepIndex > 0) {
            this.currentStepIndex--;
            this.stepTimeRemaining = this.steps[this.currentStepIndex].duration_sec;
            this.stepTotalTime = this.stepTimeRemaining;
        }
    },

    playAlarm() {
        if (this.alarmInterval) return;
        if (!this.audioCtx) {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (AudioContextClass) {
                this.audioCtx = new AudioContextClass();
            }
        }
        const playBeep = () => {
            if (!this.audioCtx) return;
            if (this.audioCtx.state === 'suspended') {
                this.audioCtx.resume();
            }
            const osc = this.audioCtx.createOscillator();
            const gainNode = this.audioCtx.createGain();
            osc.connect(gainNode);
            gainNode.connect(this.audioCtx.destination);
            osc.type = 'sine';
            osc.frequency.value = 880;
            gainNode.gain.setValueAtTime(0.3, this.audioCtx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.3);
            osc.start(this.audioCtx.currentTime);
            osc.stop(this.audioCtx.currentTime + 0.3);
        };
        playBeep();
        this.alarmInterval = setInterval(playBeep, 1000);
    },

    stopAlarm() {
        if (this.alarmInterval) {
            clearInterval(this.alarmInterval);
            this.alarmInterval = null;
        }
        this.isAlarm = false;
        this.elapsedOvertime = 0;
    },

    formatTime(seconds) {
        let hrs = Math.floor(seconds / 3600);
        let mins = Math.floor((seconds % 3600) / 60);
        let secs = seconds % 60;
        let parts = [];
        if (hrs > 0) {
            parts.push(hrs.toString().padStart(2, '0'));
        }
        parts.push(mins.toString().padStart(2, '0'));
        parts.push(secs.toString().padStart(2, '0'));
        return parts.join(':');
    },

    get progressPercent() {
        if (this.isAlarm) return 100;
        if (!this.stepTotalTime) return 0;
        return Math.round(((this.stepTotalTime - this.stepTimeRemaining) / this.stepTotalTime) * 100);
    },

    getStepDescription(key) {
        if (key === 'mix') {
            let method = 'stand_mixer';
            const methodInput = document.querySelector('input[name=mixing_method]');
            if (methodInput) {
                method = methodInput.value;
            }
            if (method === 'stand_mixer') {
                return 'Combine ingredients in the mixer bowl. Fit the mixer with the Dough Hook attachment. Mix on low speed (Speed 1-2) for 5 minutes until a cohesive shaggy mass forms and no dry flour remains.';
            } else if (method === 'bread_machine') {
                return 'Place all ingredients into the bread machine pan in the order recommended by the manufacturer. Set the machine to the dough cycle to begin the initial mixing sequence.';
            } else {
                return 'Combine all ingredients in a large mixing bowl using a sturdy spatula or your hands. Work the mixture until all dry flour is fully hydrated and a rough, shaggy dough mass is formed.';
            }
        }
        if (key === 'knead') {
            let method = 'stand_mixer';
            const methodInput = document.querySelector('input[name=mixing_method]');
            if (methodInput) {
                method = methodInput.value;
            }
            if (method === 'stand_mixer') {
                return 'Increase speed to medium-low (Speed 2-3). Knead for 8-10 minutes until the dough clears the sides of the bowl, clings to the hook, and passes the windowpane elasticity test.';
            } else if (method === 'bread_machine') {
                return 'Allow the bread machine to run its programmed kneading cycle. The paddle will develop the gluten structure dynamically until the dough is smooth, elastic, and non-sticky.';
            } else {
                return 'Turn the dough out onto a clean work surface. Hand-knead using a rhythmic fold-and-roll motion. Knead for 10-15 minutes until the dough surface is smooth, supple, and passes the windowpane test.';
            }
        }
        const step = this.steps.find(s => s.key === key);
        return step ? step.desc : '';
    },
    
    /* Helpers */
    isHighRise() {
        if (!this.presetSlug) return false;
        let slug = this.presetSlug.toLowerCase();
        return slug.includes('bagel') || slug.includes('boule') || slug.includes('artisan');
    },
    hasStructuralGrain() {
        return this.activeBerries.some(b => b.selected && b.hardness === 'hard');
    },
    showStructuralWarning() {
        if (!this.isHighRise() || this.grain_mode !== 'milled') return false;
        let selectedCount = this.activeBerries.filter(b => b.selected).length;
        if (selectedCount === 0) return true;
        
        let hardCount = this.activeBerries.filter(b => b.selected && b.hardness === 'hard').length;
        return hardCount === 0 || (hardCount / selectedCount < 0.70 && selectedCount > 1);
    },
    getWarningMessage() {
        let presetLabel = this.presetName || 'High-Rise Bread';
        let strongest = this.activeBerries.filter(b => b.hardness === 'hard').sort((a,b) => b.protein - a.protein)[0];
        let grainName = strongest ? strongest.name : 'Hard Red Wheat';
        return `❌ Structural Hazard: Selected grain blend lacks the gluten strength required for a ${presetLabel}. Adjusting blend to include 70% ${grainName} for safety.`;
    },
    weightedAbsorption() {
        let selected = this.activeBerries.filter(b => b.selected);
        if (selected.length === 0) return 1.0;
        
        let shares = {};
        let hard = selected.filter(b => b.hardness === 'hard');
        let weak = selected.filter(b => b.hardness !== 'hard');
        
        if (this.isHighRise() && this.showStructuralWarning()) {
            let hardGrains = hard.length > 0 ? hard : [ { name: 'Hard Red Winter Wheat', absorption: 1.0 } ];
            let weakGrains = weak;
            
            let hardShare = 0.70 / hardGrains.length;
            hardGrains.forEach(g => { shares[g.name] = hardShare; });
            
            if (weakGrains.length > 0) {
                let weakShare = 0.30 / weakGrains.length;
                weakGrains.forEach(g => { shares[g.name] = weakShare; });
            } else {
                let fullShare = 1.0 / hardGrains.length;
                hardGrains.forEach(g => { shares[g.name] = fullShare; });
            }
        } else {
            let share = 1.0 / selected.length;
            selected.forEach(g => { shares[g.name] = share; });
        }
        
        let sumAbs = 0.0;
        selected.forEach(g => {
            sumAbs += (shares[g.name] || 0.0) * g.absorption;
        });
        return sumAbs || 1.0;
    },
    hasAncientOrWeakGrains() {
        return this.activeBerries.some(b => b.selected && (b.hardness === 'ancient' || b.hardness === 'soft'));
    },
    get crumbMin() {
        if (this.grain_mode === 'milled') {
            let thirstMod = this.weightedAbsorption() - 1.0;
            if (thirstMod >= 0.05) {
                let minHyd = 0.45 + thirstMod;
                return Math.max(0, Math.min(100, Math.round(((minHyd - 0.45) / 0.40) * 100)));
            }
        }
        return 0;
    },
    get crumbMax() {
        if (this.grain_mode === 'milled') {
            let thirstMod = this.weightedAbsorption() - 1.0;
            if (thirstMod >= 0.05) {
                let maxHyd = 0.72;
                return Math.max(0, Math.min(100, Math.round(((maxHyd - 0.45) / 0.40) * 100)));
            }
        }
        return 100;
    }
};
module.exports = xData;