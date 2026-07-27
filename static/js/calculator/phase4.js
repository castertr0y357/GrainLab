// phase4.js
document.addEventListener('alpine:init', () => {
    Alpine.data('phase4App', (initialData) => ({
        current_phase: initialData.current_phase || 4,
        phase4Error: null,
        selected_master: initialData.selected_master || null,
        global_ai_enabled: initialData.global_ai_enabled || true,
        preset_slug: initialData.preset_slug || null,
        enginesArchetypes: initialData.enginesArchetypes || {},
        engines_ff: initialData.engines_ff || {},
        recipe_name: initialData.recipe_name || '',
        
        default_yield_amount: initialData.default_yield_amount !== undefined ? parseFloat(initialData.default_yield_amount) : 1.0,
        yield_unit: initialData.yield_unit || 'loaf',
        is_portionable: initialData.is_portionable || false,
        scaleMultiplier: 1.0,
        
        mixing_method: initialData.mixing_method || 'hand_knead',
        active_action: initialData.active_action || 'stretch_fold',
        texture: initialData.texture !== undefined ? initialData.texture : 50,
        crumb: initialData.crumb !== undefined ? initialData.crumb : 50,
        starter: initialData.starter !== undefined ? initialData.starter : 20,
        leaven: initialData.leaven || 'starter',

        processRecommendations: {},
        processRecommendationsLoading: false,
        slider_recommendations: {},
        
        processAlternativesCache: {},
        activeProcessCategory: null,
        phase4Loading: false,
        hovered_element: null,
        sidebar_analysis: '',
        sidebar_insight_loading: false,
        processAlternativesLoading: false,
        hovered_element: null,
        steps: [],
        currentStepIndex: 0,
        stepTimeRemaining: 0,
        isAlarm: false,
        sidebar_tier: '',
        sidebar_labor_roi: '',
        sidebar_analysis: '',
        sidebar_insight_loading: false,
        
        // Phase 4 exclusive timer state
        countertopMode: false,
        steps: [],
        currentStepIndex: 0,
        timerRunning: false,
        stepTimeRemaining: 0,
        elapsedOvertime: 0,
        isAlarm: false,
        progressPercent: 0,
        bakeTemp: 450,
        bakeSteam: 'Yes',
        donenessTemp: 205,
        waterTemp: 75,
        timerInterval: null,
        recipeCompiled: initialData.recipeCompiled || false,
        aiLoading: initialData.current_phase === 5 && (initialData.global_ai_enabled || true),
        globalElevateRecipe: [],
        geometry_evaluation: null,
        sensory_description: '',
        pitfalls: [],
        recipe: {},
        batchInsightsMap: {},
        
        hardware_registry: [
            { id: 'stand_mixer', name: 'Stand Mixer', category: 'high_torque' },
            { id: 'bread_machine', name: 'Bread Machine', category: 'high_torque' },
            { id: 'food_processor', name: 'Food Processor', category: 'high_torque' },
            { id: 'hand_beaters', name: 'Hand Beaters', category: 'whipping_whisk' },
            { id: 'whisk', name: 'Hand Whisk', category: 'whipping_whisk' },
            { id: 'spatula_bowl', name: 'Manual Spatula & Bowl', category: 'zero_friction' },
            { id: 'hand_knead', name: 'Hand Knead', category: 'zero_friction' }
        ],
        required_hardware: [],
        required_actions: [],
        
        get activeProductionProfile() {
            return this.engines_ff?.[this.selected_master]?.production_profile || {
                thermodynamic_focus: 'biological_yeast_activity',
                mechanical_energy_threshold: 'high_kneading',
                permissible_action_types: ['knead'],
                environmental_rest_strategy: 'gas_proofing'
            };
        },
        
        get filteredTools() {
            if (this.required_hardware && this.required_hardware.length > 0) {
                return this.hardware_registry.filter(t => this.required_hardware.includes(t.id));
            }
            const threshold = this.activeProductionProfile.mechanical_energy_threshold;
            if (threshold === 'high_kneading' || threshold === 'moderate_shearing' || threshold === 'mechanical_compaction') {
                return this.hardware_registry.filter(t => t.category === 'high_torque' || t.category === 'zero_friction');
            } else if (threshold === 'low_emulsifying') {
                return this.hardware_registry.filter(t => t.category === 'whipping_whisk' || t.category === 'zero_friction');
            } else if (threshold === 'minimal_folding') {
                return this.hardware_registry.filter(t => t.category === 'zero_friction');
            }
            return this.hardware_registry;
        },
        
        
        init() {
            if (this.global_ai_enabled) {
                this.fetchProcessDetails();
            }
        },

        fetchProcessDetails() {
            this.processRecommendationsLoading = true;
            
            const params = new URLSearchParams({
                engine_id: this.selected_master,
                active_archetype_id: this.preset_slug,
                recipe_slug: this.preset_slug,
                recipe_name: 'Phase 4 Recipe'
            });

            fetch('/ai-process-details/?' + params.toString())
                .then(async res => {
                    if (!res.ok) throw new Error('Failed to fetch process details');
                    return res.json();
                })
                .then(data => {
                    if (data.process_recommendations) {
                        this.processRecommendations = data.process_recommendations;
                        // Set the active action based on AI recommendation if not already set manually
                        if (this.processRecommendations.dough_handling) {
                            this.active_action = this.processRecommendations.dough_handling.name;
                        }
                    }
                    if (data.slider_recommendations) {
                        this.slider_recommendations = data.slider_recommendations;
                        if (this.slider_recommendations.enrichment && this.slider_recommendations.enrichment.recommended_value !== undefined) {
                            this.texture = this.slider_recommendations.enrichment.recommended_value;
                        }
                        if (this.slider_recommendations.hydration && this.slider_recommendations.hydration.recommended_value !== undefined) {
                            this.crumb = this.slider_recommendations.hydration.recommended_value;
                        }
                        if (this.slider_recommendations.leavening && this.slider_recommendations.leavening.recommended_value !== undefined) {
                            this.starter = this.slider_recommendations.leavening.recommended_value;
                        }
                    }
                    this.processRecommendationsLoading = false;
                })
                .catch(err => {
                    console.error('Error fetching process details:', err);
                    this.processRecommendationsLoading = false;
                });
        },

        hoverSlider(tweakId) {
            if (this.slider_recommendations && this.slider_recommendations[tweakId] && this.slider_recommendations[tweakId].explanation) {
                this.hovered_element = tweakId;
                this.sidebar_tier = '';
                this.sidebar_labor_roi = '';
                this.sidebar_analysis = this.slider_recommendations[tweakId].explanation;
                this.sidebar_insight_loading = false;
            } else {
                this.hovered_element = null;
                this.sidebar_analysis = '';
            }
        },

        fetchProcessAlternatives(categoryKey) {
            if (this.processAlternativesCache[categoryKey] && this.processAlternativesCache[categoryKey].length > 0) {
                return; 
            }

            this.processAlternativesLoading = true;
            const originalRec = this.processRecommendations[categoryKey];

            const payload = {
                engine_id: this.selected_master,
                active_archetype_id: this.preset_slug,
                recipe_slug: this.preset_slug,
                recipe_name: 'Phase 4 Recipe',
                target_category: categoryKey,
                original_recommendation: originalRec
            };

            fetch('/ai-process-alternatives/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.alternatives) {
                    this.processAlternativesCache[categoryKey] = data.alternatives;
                }
                this.processAlternativesLoading = false;
            })
            .catch(err => {
                console.error('Failed fetching alternatives:', err);
                this.processAlternativesLoading = false;
            });
        },

        generateMoreProcessAlternatives(categoryKey) {
            this.processAlternativesLoading = true;
            this.activeProcessCategory = categoryKey;

            const originalRec = this.processRecommendations[categoryKey];
            const currentAlternatives = this.processAlternativesCache[categoryKey] || [];
            const excludeNames = currentAlternatives.map(a => a.name);

            const payload = {
                engine_id: this.selected_master,
                active_archetype_id: this.preset_slug,
                recipe_slug: this.preset_slug,
                recipe_name: 'Phase 4 Recipe',
                target_category: categoryKey,
                original_recommendation: originalRec,
                exclude_names: excludeNames
            };

            fetch('/ai-process-alternatives/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.alternatives) {
                    this.processAlternativesCache[categoryKey] = [
                        ...this.processAlternativesCache[categoryKey],
                        ...data.alternatives
                    ];
                }
                this.processAlternativesLoading = false;
            })
            .catch(err => {
                console.error('Failed fetching more alternatives:', err);
                this.processAlternativesLoading = false;
            });
        },
        
        swapProcessRecommendation(categoryKey, alt) {
            this.processRecommendations[categoryKey].name = alt.name;
            this.processRecommendations[categoryKey].explanation = alt.difference_explanation;
            
            if (categoryKey === 'dough_handling') {
                this.active_action = alt.name;
            }
            if (categoryKey === 'mixing_method') {
                this.mixing_method = alt.name;
            }
        },

        openProcessAlternatives(categoryKey) {
            this.activeProcessCategory = categoryKey;
            this.fetchProcessAlternatives(categoryKey);
        },

        closeProcessAlternatives() {
            this.activeProcessCategory = null;
        },
        // Methods inherited or specific
        incrementScale() {
            if (this.is_portionable) {
                this.scaleMultiplier += 0.5;
            } else {
                this.scaleMultiplier += 1.0;
            }
        },
        
        decrementScale() {
            let decrement = this.is_portionable ? 0.5 : 1.0;
            if (this.scaleMultiplier > decrement) {
                this.scaleMultiplier -= decrement;
            }
        },

        loadCompiledData() {
            const dataEl = document.getElementById('countertop-data');
            if (dataEl) {
                try {
                    this.steps = JSON.parse(dataEl.getAttribute('data-steps') || '[]');
                    this.bakeTemp = parseInt(dataEl.getAttribute('data-bake-temp')) || 450;
                    this.bakeSteam = dataEl.getAttribute('data-bake-steam') || 'Yes';
                    this.donenessTemp = parseInt(dataEl.getAttribute('data-doneness-temp')) || 205;
                    this.waterTemp = parseInt(dataEl.getAttribute('data-water-temp')) || 75;
                } catch (e) {
                    console.error("Failed to parse countertop data", e);
                }
            }
        },

        async fetchAIInsights() {
            if (!this.global_ai_enabled || this.current_phase !== 5) return;
            
            this.aiLoading = true;
            try {
                // Determine category and archetype from current path
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                let cat = this.selected_master || pathParts[1];
                let arch = this.preset_slug || pathParts[2];
                if (!cat || !arch) {
                    this.aiLoading = false;
                    return;
                }
                
                const response = await fetch(`/recipe-final/${cat}/${arch}/ai/`, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                
                const json = await response.json();
                if (json.status === 'success' && json.data) {
                    const d = json.data;
                    this.recipe = d.recipe || {};
                    this.sensory_description = d.sensory_description || '';
                    this.pitfalls = d.pitfalls || [];
                    this.geometry_evaluation = d.geometry_evaluation || null;
                    
                    if (d.bake_temp_f) this.bakeTemp = d.bake_temp_f;
                    if (d.bake_time_min) this.bakeTimeMin = d.bake_time_min;
                    if (d.steam_required !== undefined) this.bakeSteam = d.steam_required ? 'Yes' : 'No';
                    
                    if (d.countertop_steps_json) {
                        try {
                            this.steps = JSON.parse(d.countertop_steps_json);
                        } catch (e) {}
                    }
                }
            } catch (err) {
                console.error("Failed to fetch AI insights", err);
            } finally {
                this.aiLoading = false;
            }
        },
        
        // Form trigger for the COMPILE button to ensure it pushes state and re-renders
        compileRecipe() {
            // We can just trigger an htmx save or simply let the page refresh
            // Currently, phase4.html has htmx on the form but the compile button could be a regular submit
            const form = document.getElementById('calculator-form');
            if (form) {
                form.submit();
            }
        },
        
        startCountertopMode() {
            this.countertopMode = true;
            this.currentStepIndex = 0;
            if(this.steps.length > 0) {
                this.stepTimeRemaining = this.steps[0].duration_sec;
                this.startTimer();
            }
        },
        
        // Inherit all methods from original actions.js
        startTimer() {
            if(this.timerInterval) clearInterval(this.timerInterval);
            this.timerInterval = setInterval(() => {
                if(this.stepTimeRemaining > 0) {
                    this.stepTimeRemaining--;
                } else {
                    clearInterval(this.timerInterval);
                    this.isAlarm = true;
                    this.playAlarm();
                }
            }, 1000);
        },
        pauseTimer() {
            if(this.timerInterval) clearInterval(this.timerInterval);
        },
        nextStep() {
            this.stopAlarm();
            if(this.currentStepIndex < this.steps.length - 1) {
                this.currentStepIndex++;
                this.stepTimeRemaining = this.steps[this.currentStepIndex].duration_sec;
                this.startTimer();
            } else {
                this.countertopMode = false;
            }
        },
        playAlarm() {
            // Audio context can be added here
            console.log("Alarm playing!");
        },
        stopAlarm() {
            this.isAlarm = false;
        },

        async setHoveredElement(key) {
        if (!key) return;
        this.hovered_element = key;
        
        if (key.startsWith('process_alt_')) {
            const index = parseInt(key.replace('process_alt_', ''));
            const alt = this.processAlternativesCache[this.activeProcessCategory]?.[index];
            if (alt) {
                this.sidebar_analysis = `<strong>Quality Impact:</strong><br/>${alt.difference_explanation}`;
                this.sidebar_insight_loading = false;
                this.sidebar_tier = '';
                this.sidebar_labor_roi = '';
            }
            return;
        }
        
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
            this.sidebar_tier = '';
            this.sidebar_analysis = this.getFactualProfile();
            this.sidebar_insight_loading = false;
            return;
        }

        if (key.startsWith('mill_')) {
            const millId = key.replace('mill_', '');
            this.sidebar_insight_loading = false;
            this.sidebar_labor_roi = '';
            if (this.mill_recommendation && this.mill_recommendation.mill_id === millId) {
                this.sidebar_tier = 'recommended';
                this.sidebar_analysis = this.mill_recommendation.reasoning;
            } else if (this.mill_recommendation) {
                this.sidebar_tier = 'not-recommended';
                this.sidebar_analysis = `The AI specifically recommended a different mill instead. Reason: ${this.mill_recommendation.reasoning}`;
            } else {
                this.sidebar_tier = 'not-recommended';
                this.sidebar_analysis = 'Not selected as the optimal mill for this archetype. The AI recommended a different approach.';
            }
            return;
        }

        if (key.startsWith('sifted_')) {
            const isSiftedStr = key.replace('sifted_', '');
            const isSifted = isSiftedStr === 'true';
            this.sidebar_insight_loading = false;
            this.sidebar_labor_roi = '';
            if (this.sifted_recommendation) {
                if (this.sifted_recommendation.should_sift === isSifted) {
                    this.sidebar_tier = 'recommended';
                    this.sidebar_analysis = this.sifted_recommendation.reasoning;
                } else {
                    this.sidebar_tier = 'not-recommended';
                    const optimalName = this.sifted_recommendation.should_sift ? 'Sifted (High Extraction)' : 'Whole Grain (Unsifted)';
                    this.sidebar_analysis = `The AI specifically recommended ${optimalName} instead. Reason: ${this.sifted_recommendation.reasoning}`;
                }
            } else {
                this.sidebar_tier = '';
                this.sidebar_analysis = 'No specific AI critique for this selection.';
            }
            return;
        }

        if (key.startsWith('secondary_')) {
            const type = key.replace('secondary_', ''); // 'lipid', 'liquid', or 'binder'
            const typeKey = type + 's';
            this.sidebar_insight_loading = false;
            this.sidebar_labor_roi = '';
            
            const source = (this.selectedRecipeSecondaryIngredients && this.selectedRecipeSecondaryIngredients[typeKey]) ? 
                            this.selectedRecipeSecondaryIngredients : 
                           (this.engines_ff?.[this.selected_master]?.secondary_ingredients);
                           
            if (source && source[typeKey] && source[typeKey].ai_recommendation) {
                this.sidebar_tier = 'recommended';
                this.sidebar_analysis = source[typeKey].ai_recommendation;
            } else {
                this.sidebar_tier = '';
                this.sidebar_analysis = 'No specific AI advisory available for this category.';
            }
            return;
        }

        
        if (!this.batchInsightsMap[key] && !this._fetchingInsightsMap) {
            this._fetchingInsightsMap = {};
        }
        if (!this.batchInsightsMap[key] && !this._fetchingInsightsMap[key]) {
            this._fetchingInsightsMap[key] = true;
            this.sidebar_insight_loading = true;
            this.sidebar_labor_roi = '';
            this.sidebar_analysis = 'Loading insight... Please wait.';
            this.sidebar_tier = '';
            try {
                const url = `/ai-batch-insights/?elements=["${key}"]&category_slug=${this.selected_master}&preset_slug=${this.preset_slug || ''}`;
                const resp = await fetch(url);
                if (resp.ok) {
                    const data = await resp.json();
                    if (data.batch_insights && data.batch_insights[key]) {
                        this.batchInsightsMap[key] = data.batch_insights[key];
                    } else {
                        this.batchInsightsMap[key] = {
                            labor_roi: 'Low Priority / Minor Textural Return',
                            last_10_percent_analysis: 'An objective workspace configuration parameter. No significant performance anomalies detected.',
                            recommendation_tier: ''
                        };
                    }
                    if (this.hovered_element === key) {
                        const d = this.batchInsightsMap[key];
                        this.sidebar_labor_roi = d.labor_roi || 'Low Priority / Minor Textural Return';
                        this.sidebar_analysis = d.last_10_percent_analysis || 'No detailed analysis returned.';
                        this.sidebar_tier = d.recommendation_tier || '';
                        this.sidebar_insight_loading = false;
                    }
                }
            } catch(e) {
                console.error("Failed fetching insight", e);
                if (this.hovered_element === key) {
                    this.sidebar_insight_loading = false;
                    this.sidebar_analysis = 'Failed to load AI insight.';
                }
            }
            this._fetchingInsightsMap[key] = false;
            return;
        } else if (this._fetchingInsightsMap[key]) {
            this.sidebar_insight_loading = true;
            this.sidebar_labor_roi = '';
            this.sidebar_analysis = 'Loading insight... Please wait.';
            this.sidebar_tier = '';
            return;
        }

        if (this.batchInsightsMap[key]) {
            const data = this.batchInsightsMap[key];
            this.sidebar_labor_roi = data.labor_roi || 'Low Priority / Minor Textural Return';
            this.sidebar_analysis = data.last_10_percent_analysis || 'No detailed analysis returned.';
            this.sidebar_tier = data.recommendation_tier || '';
            this.sidebar_insight_loading = false;
        }
    },


    clearHoveredElement() {
        this.hovered_element = null;
        this.sidebar_labor_roi = '';
        this.sidebar_tier = '';
        this.sidebar_insight_loading = false;
        if (this.current_phase >= 2 && this.selected_recipe_id) {
            this.sidebar_analysis = this.selectedRecipeScienceProfile;
            this.sidebar_menu_description = this.selectedRecipeMenuDescription;
        } else {
            this.sidebar_analysis = '';
            this.sidebar_menu_description = '';
        }
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

    get grainEvaluationsMap() {
        const map = {};
        (this.grainEvaluations || []).forEach(e => {
            if (e.grain_id) {
                map[e.grain_id] = e;
            }
        });
        return map;
    },

    get recommendedGrainsMap() {
        const map = {};
        (this.recommended_grain_ids || []).forEach(id => {
            map[id] = true;
        });
        return map;
    },

    get elevateWays() {
        if (Array.isArray(this.globalElevateRecipe)) {
            return this.globalElevateRecipe;
        }
        if (typeof this.globalElevateRecipe === 'string' && this.globalElevateRecipe.trim()) {
            return [this.globalElevateRecipe];
        }
        return [];
    },


    cancelAllInFlightRequests() {
        if (this.advisoryAbortController) {
            this.advisoryAbortController.abort();
            this.advisoryAbortController = null;
        }
        if (this.hoverAbortController) {
            this.hoverAbortController.abort();
            this.hoverAbortController = null;
        }
        if (this.creativityRecipesAbortController) {
            this.creativityRecipesAbortController.abort();
            this.creativityRecipesAbortController = null;
        }
        if (this.recipeDetailsAbortController) {
            this.recipeDetailsAbortController.abort();
            this.recipeDetailsAbortController = null;
        }
        if (this.alternativeVariantsAbortController) {
            this.alternativeVariantsAbortController.abort();
            this.alternativeVariantsAbortController = null;
        }
    },


    flushStateToNull() {
        this.grainEvaluations = [];
        this.recommended_grain_ids = [];
        this.creativity_recipes = [];
        this.alternative_variants = [];
        this.selected_recipe_id = null;
        this.recipe_selected = false;
        this.hovered_variant = null;
        
        this.sidebar_tier = '';
        this.sidebar_labor_roi = '';
        this.sidebar_analysis = '';
        this.sidebar_menu_description = '';
        this.selectedRecipeScienceProfile = '';
        this.selectedRecipeMenuDescription = '';
        this.selectedRecipeSecondaryIngredients = null;
        this.globalElevateRecipe = [];
        this.advisoryRecommendedName = '';
        this.advisoryRecommendedReason = '';
        this.advisoryHighRiskName = '';
        this.advisoryHighRiskReason = '';
        
        // Clear timers and intervals
        if (this.advisory_interval) {
            clearTimeout(this.advisory_interval);
            this.advisory_interval = null;
        }
        if (this.recipe_gen_interval) {
            clearTimeout(this.recipe_gen_interval);
            this.recipe_gen_interval = null;
        }
        if (this.recipe_details_interval) {
            clearTimeout(this.recipe_details_interval);
            this.recipe_details_interval = null;
        }
    },


    purgeArchetypeState() {
        this.cancelAllInFlightRequests();
        this.flushStateToNull();
        this.generated_variants = [];
        this.alternative_variants = [];
        this.grainEvaluations = [];
        this.recommended_grain_ids = [];
        this.creativity_recipes = [];
        this.selected_recipe_id = null;
        this.recipe_selected = false;
        this.expanded_level = null;
        this.hovered_variant = null;
        if (this.recipe_gen_interval) {
            clearInterval(this.recipe_gen_interval);
            this.recipe_gen_interval = null;
        }
        if (this.recipe_details_interval) {
            clearInterval(this.recipe_details_interval);
            this.recipe_details_interval = null;
        }
    },


    selectArchetype(archetype_id, engine_id) {
        this.purgeArchetypeState();
        if (this.active_archetype_id === archetype_id) {
            this.active_archetype_id = null;
            return;
        }
        this.active_archetype_id = archetype_id;
        
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
        
        this.recipe_gen_resolved = false;
        this.recipe_gen_data = null;
        this.startRecipeGenerationProgress();

        if (this.creativityRecipesAbortController) {
            this.creativityRecipesAbortController.abort();
            this.creativityRecipesAbortController = null;
        }
        this.creativityRecipesAbortController = new AbortController();
        const signal = this.creativityRecipesAbortController.signal;

        const inventory_ids = this.activeBerries.map(b => b.id).join(',');
        const url = `/generate-creativity-recipes/?engine_id=${encodeURIComponent(category_slug)}&active_archetype_id=${encodeURIComponent(archetype_id)}&inventory_ids=${encodeURIComponent(inventory_ids)}`;
        fetch(url, { signal })
            .then(async res => {
                if (!res.ok) {
                    let errData;
                    try { errData = await res.json(); } catch(e) {}
                    throw new Error(errData?.error || `HTTP error! status: ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                // Normalize keys in case of AI returning capitalized keys
                const normalized_recipes = (data.recipes || []).map(r => {
                    const norm = {};
                    for (const key in r) {
                        norm[key.toLowerCase()] = r[key];
                    }
                    return norm;
                });
                this.recipe_gen_data = {
                    category_slug: category_slug,
                    archetype_id: archetype_id,
                    recipes: normalized_recipes
                };
                this.recipe_gen_resolved = true;
            })
            .catch(err => {
                if (err.name === 'AbortError') return;
                console.error('[GrainLab] Failed fetching creativity recipes:', err);
                this.phase4Error = err.message || "Failed fetching creativity recipes.";
                this.creativity_loading = false;
                if (this.recipe_gen_interval) clearTimeout(this.recipe_gen_interval);
            })
            .finally(() => {
                if (this.creativityRecipesAbortController && this.creativityRecipesAbortController.signal === signal) {
                    this.creativityRecipesAbortController = null;
                }
            });
    },


    startRecipeGenerationProgress() {
        if (this.recipe_gen_interval) clearTimeout(this.recipe_gen_interval);
        
        // Reset steps
        this.recipe_generation_steps.forEach(s => {
            s.active = false;
            s.completed = false;
        });
        
        // Set first step active
        this.recipe_generation_steps[0].active = true;
        let stepIdx = 0;
        
        const tick = () => {
            if (this.recipe_gen_interval) clearTimeout(this.recipe_gen_interval);
            
            if (stepIdx < this.recipe_generation_steps.length - 1) {
                this.recipe_generation_steps[stepIdx].active = false;
                this.recipe_generation_steps[stepIdx].completed = true;
                stepIdx++;
                this.recipe_generation_steps[stepIdx].active = true;
                
                // Rapidly complete if resolved (200ms), else standard pacing (2000ms)
                const nextDelay = this.recipe_gen_resolved ? 200 : 2000;
                this.recipe_gen_interval = setTimeout(tick, nextDelay);
            } else {
                if (this.recipe_gen_resolved) {
                    this.recipe_generation_steps[stepIdx].active = false;
                    this.recipe_generation_steps[stepIdx].completed = true;
                    
                    setTimeout(() => {
                        if (this.recipe_gen_data && this.selected_master === this.recipe_gen_data.category_slug && this.active_archetype_id === this.recipe_gen_data.archetype_id) {
                            this.creativity_recipes = this.recipe_gen_data.recipes || [];
                        }
                        this.creativity_loading = false;
                    }, 300);
                } else {
                    // Stay on the last step until resolved
                    this.recipe_gen_interval = setTimeout(tick, 400);
                }
            }
        };
        
        this.recipe_gen_interval = setTimeout(tick, 2000);
    },


    startRecipeDetailsProgress() {
        if (this.recipe_details_interval) clearTimeout(this.recipe_details_interval);
        
        // Reset steps
        this.recipe_details_steps.forEach(s => {
            s.active = false;
            s.completed = false;
        });
        
        // Set first step active
        this.recipe_details_steps[0].active = true;
        let stepIdx = 0;
        
        const tick = () => {
            if (this.recipe_details_interval) clearTimeout(this.recipe_details_interval);
            
            if (stepIdx < this.recipe_details_steps.length - 1) {
                this.recipe_details_steps[stepIdx].active = false;
                this.recipe_details_steps[stepIdx].completed = true;
                stepIdx++;
                this.recipe_details_steps[stepIdx].active = true;
                
                // Rapidly complete if resolved (150ms), else standard pacing (1000ms)
                const nextDelay = this.recipe_details_resolved ? 150 : 1000;
                this.recipe_details_interval = setTimeout(tick, nextDelay);
            } else {
                if (this.recipe_details_resolved) {
                    this.recipe_details_steps[stepIdx].active = false;
                    this.recipe_details_steps[stepIdx].completed = true;
                    
                    setTimeout(() => {
                        const data = this.recipe_details_data;
                        if (data) {
                            const profile = data.sidebar_science_profile || 'No technical analysis compiled.';
                            this.sidebar_analysis = profile;
                            this.selectedRecipeScienceProfile = profile;
                            
                            // The menu description was already set immediately upon recipe selection
                            // using the pre-generated recipe.description

                            // Save recommended grains for highlighting in Phase 2
                            this.recommended_grain_ids = data.recommended_grain_ids || [];

                            // Pre-select required secondary ingredients if returned by LLM
                            this.selectedRecipeSecondaryIngredients = data.secondary_ingredients || null;
                            
                            // Broadcast the recipe-details-updated event to update the inner form component!
                            window.dispatchEvent(new CustomEvent('recipe-details-updated', {
                                detail: data
                            }));
                            this.recipe_details_loading = false;
                        }
                    }, 300);
                } else {
                    // Stay on the last step until resolved
                    this.recipe_details_interval = setTimeout(tick, 400);
                }
            }
        };
        
        this.recipe_details_interval = setTimeout(tick, 2000);
    },

    }));
});
