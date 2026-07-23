export const actions = {


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

        
        // Use pre-fetched batch insights instead of lazily fetching
        this.sidebar_insight_loading = true;
        if (this.batchInsightsMap[key]) {
            const data = this.batchInsightsMap[key];
            this.sidebar_labor_roi = data.labor_roi || 'Low Priority / Minor Textural Return';
            this.sidebar_analysis = data.last_10_percent_analysis || 'No detailed analysis returned.';
            this.sidebar_tier = data.recommendation_tier || '';
            this.sidebar_insight_loading = false;
        } else {
            // Fallback if not loaded
            this.sidebar_labor_roi = 'Low Priority / Minor Textural Return';
            this.sidebar_analysis = 'Loading insight... Please wait.';
            this.sidebar_tier = '';
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
            .then(res => res.json())
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
                if (err.name !== 'AbortError') {
                    console.error('[GrainLab] Failed fetching creativity recipes:', err);
                }
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
                            
};
