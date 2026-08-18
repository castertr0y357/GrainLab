// phase2.js
document.addEventListener('alpine:init', () => {
    Alpine.data('phase2App', (initialData) => ({
        // State variables required for Phase 2
        current_phase: initialData.current_phase || 2,
        selected_master: initialData.selected_master || null,
        global_ai_enabled: initialData.global_ai_enabled || true,
        enginesArchetypes: initialData.enginesArchetypes || {},
        engines_ff: initialData.engines_ff || {},
        
        // Phase 2 specific state
        active_archetype_id: null,
        creativity_loading: false,
        creativity_streaming: false,
        phase2Error: null,
        creativity_recipes: [],
        creativityRecipesAbortController: null,
        recipe_generation_steps: [],
        expanded_level: null,
        variant_loading: false,
        alternative_variants: [],
        selected_recipe_id: null,
        recipe_selected: false,
        advisoryLoading: false,
        advisory_steps: [],
        activeBerries: initialData.berries || [],
        mill_type: null,
        is_sifted: false,
        custom_mixer: null,
        
        // Hover state variables
        hovered_element: null,
        sidebar_tier: '',
        sidebar_labor_roi: '',
        sidebar_analysis: '',
        sidebar_insight_loading: false,
        sidebar_menu_description: '',
        selectedRecipeScienceProfile: '',
        selectedRecipeMenuDescription: '',
        advisory_resolved: false,
        recipe_name: '',
        
        // Pre-fetched insights
        batchInsightsMap: {},
        factual_dictionary: {},
        grainEvaluations: [],
        recommended_grain_ids: [],
        mill_evaluations: [],
        sifter_evaluations: {},
        selectedRecipeSecondaryIngredients: null,
        
        init() {
            console.log("Phase 2 App Initialized.");
            this.csrf_token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            // Optionally, we could automatically expand an archetype or start a generation process here.
        },

        extractPartialObjects(buffer) {
            // Find the array content to ignore the root object wrapper
            const match = buffer.match(/\[([\s\S]*)/);
            if (!match) return [];
            let arrayContent = match[1];
            
            const results = [];
            let depth = 0;
            let inString = false;
            let escape = false;
            let objStart = -1;
            
            for (let i = 0; i < arrayContent.length; i++) {
                const char = arrayContent[i];
                if (escape) { escape = false; continue; }
                if (char === '\\') { escape = true; continue; }
                if (char === '"') { inString = !inString; continue; }
                
                if (!inString) {
                    if (char === '{') {
                        if (depth === 0) objStart = i;
                        depth++;
                    } else if (char === '}') {
                        depth--;
                        if (depth === 0 && objStart !== -1) {
                            results.push(arrayContent.substring(objStart, i + 1));
                            objStart = -1;
                        }
                    }
                }
            }
            
            if (objStart !== -1) {
                results.push(arrayContent.substring(objStart));
            }
            return results;
        },

        repairAndParse(str) {
            let repaired = str.trim();
            let quotes = 0;
            let escape = false;
            for (let i = 0; i < repaired.length; i++) {
                if (escape) { escape = false; continue; }
                if (repaired[i] === '\\') { escape = true; continue; }
                if (repaired[i] === '"') { quotes++; }
            }
            if (quotes % 2 !== 0) {
                repaired += '"'; 
            }
            
            // Fix trailing commas or colons
            repaired = repaired.replace(/,\s*$/, '');
            if (repaired.match(/:\s*$/)) {
                repaired += '""';
            }
            
            if (!repaired.endsWith('}')) {
                repaired += '}';
            }
            
            try {
                return JSON.parse(repaired);
            } catch(e) {
                return null;
            }
        },

        get siftedAdvisory() { return this.sifted_recommendation; },
        get millAdvisory() { return this.mill_recommendation; },

        getRecipesForLevel(level) {
            return this.creativity_recipes.filter(r => r.creativity_level === level);
        },

        sortedBerriesFor(berries) {
            const tierOrder = {
                'recommended': 1,
                'sub-optimal': 2,
                'indifferent': 3,
                'not-recommended': 4
            };
            return [...berries].sort((a, b) => {
                const tierA = tierOrder[this.getGrainTier(a)] || 99;
                const tierB = tierOrder[this.getGrainTier(b)] || 99;
                if (tierA !== tierB) return tierA - tierB;
                return a.name.localeCompare(b.name);
            });
        },

        showStructuralWarning() {
            return false;
        },

        getWarningMessage() {
            return "";
        },

        resetAdvisory() {
            this.advisory_steps = [];
            this.advisoryLoading = false;
            this.sifter_evaluations = {};
            this.mill_evaluations = [];
        },

        // Inherit all methods from original actions.js
        


    setHoveredElement(key, metadata = null) {
        if (!key) return;
        this.hovered_element = key;
        this.hover_metadata = metadata;
        
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

    getGrainTier(berry) {
        const ev = this.grainEvaluationsMap[berry.id];
        if (ev) return ev.tier;
        const slug = berry.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
        if (this.recommendedGrainsMap[slug]) return 'recommended';
        return 'indifferent';
    },

    getHoverInfo() {
        if (!this.hovered_element) return null;
        if (this.hovered_element.startsWith('grain_')) {
            const slug = this.hovered_element.replace('grain_', '');
            const berry = this.activeBerries.find(b => b.name.toLowerCase().replace(/[^a-z0-9]/g, '_') === slug);
            if (!berry) return null;
            const tier = this.getGrainTier(berry);
            let reason = this.getGrainReasoning(berry);
            if (!reason) {
                if (tier === 'recommended') reason = 'Selected by AI as an optimal grain for this recipe profile, enhancing flavor and structure.';
                else reason = 'This grain can be used, though it may alter the target characteristics slightly.';
            }
            return {
                title: berry.name,
                status: tier,
                reason: reason,
                icon: '🌾'
            };
        }
        if (this.hovered_element.startsWith('mill_')) {
            const millId = String(this.hovered_element.replace('mill_', ''));
            const millName = this.hover_metadata;
            const evaluation = this.mill_evaluations ? this.mill_evaluations.find(m => String(m.mill_id) === millId || (millName && String(m.mill_id).toLowerCase() === String(millName).toLowerCase())) : null;
            const tier = evaluation ? (evaluation.tier || 'info') : 'info';
            const reason = evaluation ? evaluation.reasoning : 'No AI evaluation available for this mill.';

            return {
                title: this.hover_metadata || 'Mill',
                status: tier,
                reason: reason,
                icon: '⚙️'
            };
        }
        if (this.hovered_element.startsWith('sifter_')) {
            const is_sifted = this.hovered_element === 'sifter_sifted';
            const evaluation = this.sifter_evaluations ? (is_sifted ? this.sifter_evaluations.sifted : this.sifter_evaluations.unsifted) : null;
            const tier = evaluation ? (evaluation.tier || 'info') : 'info';
            const reason = evaluation ? evaluation.reasoning : (is_sifted ? 'Removes the largest bran particles to lighten the crumb while retaining germ nutrition.' : 'Retains 100% of the berry for maximum flavor, nutrition, and hydration capacity.');
            
            return {
                title: is_sifted ? 'Sifted (High Extraction)' : 'Whole Grain (Unsifted)',
                status: tier,
                reason: reason,
                icon: '🌪️'
            };
        }
        return null;
    },

    getClassificationLabel(berry) {
        const tier = this.getGrainTier(berry);
        if (tier === 'recommended') return 'Recommended';
        if (tier === 'sub-optimal') return 'Sub-Optimal';
        if (tier === 'not-recommended') return 'Not Recommended';
        return '';
    },

    getClassificationBadgeStyle(berry) {
        const tier = this.getGrainTier(berry);
        if (tier === 'recommended') return 'color: #ffd700; background: rgba(255,215,0,0.1); padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.65rem; font-weight: 700; border: 1px solid rgba(255,215,0,0.3);';
        if (tier === 'sub-optimal') return 'color: var(--warning); background: rgba(255,193,7,0.1); padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.65rem; font-weight: 700; border: 1px solid rgba(255,193,7,0.3);';
        if (tier === 'not-recommended') return 'color: var(--danger); background: rgba(220,53,69,0.1); padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.65rem; font-weight: 700; border: 1px solid rgba(220,53,69,0.3);';
        return '';
    },

    getGrainStyle(berry) {
        const tier = this.getGrainTier(berry);
        if (tier === 'recommended') {
            return berry.selected
                ? 'border-color: #ffd700; box-shadow: 0 0 18px rgba(255, 215, 0, 0.9); background-color: rgba(255, 215, 0, 0.12); outline: 2px solid rgba(255, 215, 0, 0.6);'
                : 'border-color: #ffd700; box-shadow: 0 0 14px rgba(255, 215, 0, 0.7); background-color: rgba(255, 215, 0, 0.06); outline: 1px solid rgba(255, 215, 0, 0.4);';
        } else if (tier === 'sub-optimal') {
            return berry.selected
                ? 'border-color: var(--warning); box-shadow: 0 0 12px rgba(255,193,7,0.6); background-color: rgba(255,193,7,0.08);'
                : 'border-color: var(--warning); box-shadow: 0 0 8px rgba(255,193,7,0.3); background-color: rgba(255,193,7,0.02);';
        } else if (tier === 'not-recommended') {
            return berry.selected
                ? 'border-color: var(--danger); box-shadow: 0 0 12px rgba(220,53,69,0.6); background-color: rgba(220,53,69,0.08);'
                : 'border-color: var(--danger); box-shadow: 0 0 8px rgba(220,53,69,0.3); background-color: rgba(220,53,69,0.02);';
        }
        return berry.selected
            ? 'border-color: var(--accent); background-color: rgba(255,136,0,0.05);'
            : '';
    },

    getMillStyle(millId, millName) {
        if (!this.mill_evaluations || this.mill_evaluations.length === 0) return {};
        const evaluation = this.mill_evaluations.find(m => String(m.mill_id) === String(millId) || (millName && String(m.mill_id).toLowerCase() === String(millName).toLowerCase()));
        if (!evaluation || !evaluation.tier) return {};
        const tier = evaluation.tier;
        const isSelected = String(this.mill_type) === String(millId);
        
        if (tier === 'recommended') {
            return isSelected
                ? { 'border-color': '#ffd700', 'box-shadow': '0 0 12px rgba(255, 215, 0, 0.6)', 'background-color': 'rgba(255, 215, 0, 0.12)' }
                : { 'border-color': '#ffd700', 'box-shadow': '0 0 8px rgba(255, 215, 0, 0.3)', 'background-color': 'rgba(255, 215, 0, 0.04)' };
        } else if (tier === 'sub-optimal') {
            return isSelected
                ? { 'border-color': 'var(--warning)', 'box-shadow': '0 0 10px rgba(255,193,7,0.5)', 'background-color': 'rgba(255,193,7,0.08)' }
                : { 'border-color': 'var(--warning)', 'box-shadow': '0 0 6px rgba(255,193,7,0.2)', 'background-color': 'rgba(255,193,7,0.02)' };
        } else if (tier === 'not-recommended') {
            return isSelected
                ? { 'border-color': 'var(--danger)', 'box-shadow': '0 0 10px rgba(220,53,69,0.5)', 'background-color': 'rgba(220,53,69,0.08)' }
                : { 'border-color': 'var(--danger)', 'box-shadow': '0 0 6px rgba(220,53,69,0.2)', 'background-color': 'rgba(220,53,69,0.02)' };
        }
        return {};
    },

    getSifterStyle(isSifted) {
        if (!this.sifter_evaluations) return {};
        const evaluation = isSifted ? this.sifter_evaluations.sifted : this.sifter_evaluations.unsifted;
        if (!evaluation || !evaluation.tier) return {};
        
        const tier = evaluation.tier;
        const isSelected = this.is_sifted === isSifted;

        if (tier === 'recommended') {
            return isSelected
                ? { 'border-color': '#ffd700', 'box-shadow': '0 0 12px rgba(255, 215, 0, 0.6)', 'background-color': 'rgba(255, 215, 0, 0.12)' }
                : { 'border-color': '#ffd700', 'box-shadow': '0 0 8px rgba(255, 215, 0, 0.3)', 'background-color': 'rgba(255, 215, 0, 0.04)' };
        } else if (tier === 'sub-optimal') {
            return isSelected
                ? { 'border-color': 'var(--warning)', 'box-shadow': '0 0 10px rgba(255,193,7,0.5)', 'background-color': 'rgba(255,193,7,0.08)' }
                : { 'border-color': 'var(--warning)', 'box-shadow': '0 0 6px rgba(255,193,7,0.2)', 'background-color': 'rgba(255,193,7,0.02)' };
        } else if (tier === 'not-recommended') {
            return isSelected
                ? { 'border-color': 'var(--danger)', 'box-shadow': '0 0 10px rgba(220,53,69,0.5)', 'background-color': 'rgba(220,53,69,0.08)' }
                : { 'border-color': 'var(--danger)', 'box-shadow': '0 0 6px rgba(220,53,69,0.2)', 'background-color': 'rgba(220,53,69,0.02)' };
        }
        return {};
    },

    isMillRecommended(millId, millName) {
        if (!this.mill_evaluations || this.mill_evaluations.length === 0) return true;
        const evaluation = this.mill_evaluations.find(m => String(m.mill_id) === String(millId) || (millName && String(m.mill_id).toLowerCase() === String(millName).toLowerCase()));
        return evaluation && evaluation.tier === 'recommended';
    },

    hasOtherMills() {
        if (!this.mill_evaluations || this.mill_evaluations.length === 0) return false;
        return this.mill_evaluations.some(m => m.tier !== 'recommended');
    },

    isSifterRecommended(isSifted) {
        if (!this.sifter_evaluations || Object.keys(this.sifter_evaluations).length === 0) return true;
        const evaluation = isSifted ? this.sifter_evaluations.sifted : this.sifter_evaluations.unsifted;
        return evaluation && evaluation.tier === 'recommended';
    },

    hasOtherSifters() {
        if (!this.sifter_evaluations || Object.keys(this.sifter_evaluations).length === 0) return false;
        const evals = Object.values(this.sifter_evaluations);
        return evals.some(e => e.tier !== 'recommended');
    },

    getGrainReasoning(berry) {
        const ev = this.grainEvaluationsMap[berry.id];
        return ev ? ev.reasoning : '';
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
        
        // Clear old state before streaming
        this.recipe_selected = false;
        this.selected_recipe_id = null;
        this.expanded_level = null;
        this.alternative_variants = [];
        this.grainEvaluations = [];
        this.creativity_recipes = [];
        this.resetAdvisory();
        
        // Show the cards container immediately, so we can see them stream in
        this.creativity_loading = false;
        this.creativity_streaming = true;
        
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
                
                const reader = res.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let buffer = "";
                let rawBuffer = "";
                
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); // Keep the incomplete line in the buffer
                    
                    for (const line of lines) {
                        if (line.startsWith('event: close')) {
                            // close event
                        } else if (line.startsWith('data: ')) {
                            const dataStr = line.substring(6).trim();
                            if (dataStr && dataStr !== '{}') {
                                try {
                                    const parsed = JSON.parse(dataStr);
                                    
                                    if (typeof parsed === 'string') {
                                        // Streaming raw text chunks
                                        rawBuffer += parsed;
                                        const objects = this.extractPartialObjects(rawBuffer);
                                        console.log('rawBuffer', rawBuffer);
                                        console.log('extracted objects', objects);
                                        
                                        // Update the creativity_recipes array with the latest state
                                        const newRecipes = [];
                                        for (let i = 0; i < objects.length; i++) {
                                            const objStr = objects[i];
                                            const parsedObj = this.repairAndParse(objStr);
                                            
                                            if (parsedObj) {
                                                const norm = {};
                                                for (const key in parsedObj) {
                                                    norm[key.toLowerCase()] = parsedObj[key];
                                                }
                                                newRecipes.push(norm);
                                            } else {
                                                // If parsing fails for a partial object, retain the last known good state
                                                if (this.creativity_recipes[i]) {
                                                    newRecipes.push(this.creativity_recipes[i]);
                                                }
                                            }
                                        }
                                        // Trigger reactivity
                                        this.creativity_recipes = newRecipes;
                                        
                                    } else {
                                        // Fallback dictionary mode
                                        const norm = {};
                                        for (const key in parsed) {
                                            norm[key.toLowerCase()] = parsed[key];
                                        }
                                        this.creativity_recipes.push(norm);
                                    }
                                } catch (e) {
                                    console.error('JSON parse error', e);
                                }
                            }
                        }
                    }
                }
            })
            .catch(err => {
                if (err.name !== 'AbortError') {
                    console.error('[GrainLab] Failed fetching creativity recipes:', err);
                }
            })
            .finally(() => {
                this.creativity_streaming = false;
                if (this.creativityRecipesAbortController && this.creativityRecipesAbortController.signal === signal) {
                    this.creativityRecipesAbortController = null;
                }
            });
    },


    startRecipeGenerationProgress() {
        if (this.recipe_gen_interval) clearTimeout(this.recipe_gen_interval);
        
        // Initialize steps if empty
        if (!this.recipe_generation_steps || this.recipe_generation_steps.length === 0) {
            this.recipe_generation_steps = [
                { id: 'context', icon: '🧠', text: 'Retrieving archetype context parameters...', active: false, completed: false },
                { id: 'math', icon: '🧮', text: 'Calculating hydration and yield ratios...', active: false, completed: false },
                { id: 'creativity', icon: '🎨', text: 'Evaluating creativity variance levels...', active: false, completed: false },
                { id: 'bakers', icon: '👨‍🍳', text: 'Finalizing Baker\'s Math validation...', active: false, completed: false }
            ];
        }

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


    selectRecipe(recipe) {
        this.selected_recipe_id = recipe.recipe_id || recipe.variant_id;
        // Do NOT set this.recipe_selected = true here. The user must click "SELECT RECIPE & PROCEED".
        this.selectedRecipeScienceProfile = recipe.science_profile;
        this.selectedRecipeMenuDescription = recipe.menu_description;
        this.sidebar_menu_description = recipe.description;
        this.recipe_name = recipe.recipe_name || recipe.variant_name || recipe.name || 'Selected Formula';
        
        // Clear current details
        this.recommended_grain_ids = [];
        this.selectedRecipeSecondaryIngredients = null;
        this.sidebar_analysis = 'Fetching technical science profile and AI advisory...';
        
        this.fetchRecipeDetails(recipe);
    },

    confirmRecipeSelection() {
        this.recipe_selected = true;
        // Automatically scroll to the Grain Bin Optimizer section
        setTimeout(() => {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        }, 100);
    },

    toggleExpandLevel(level) {
        if (this.expanded_level === level) {
            this.expanded_level = null;
        } else {
            this.expanded_level = level;
            if (this.expanded_level === 1 || this.expanded_level === 2) {
                this.fetchAlternativeVariants(level);
            }
        }
    },

    generateMoreOptions(level) {
        this.fetchAlternativeVariants(level);
    },

    fetchAlternativeVariants(level) {
        // Clear previous variants before streaming
        this.alternative_variants = [];
        // Keep the loading spinner active, or we could turn it off immediately depending on UI.
        // Let's keep it true and set to false when stream ends.
        this.variant_loading = true;
        
        // Extract existing names to avoid generating the same ones again
        const excludeNames = this.creativity_recipes
            .map(v => v.recipe_name || v.name)
            .filter(Boolean)
            .join(',');

        const params = new URLSearchParams({
            engine_id: this.selected_master,
            active_archetype_id: this.active_archetype_id,
            inventory_ids: (this.activeBerries || []).map(b => b.id).join(','),
            creativity_level: level,
            global_ai_enabled: this.global_ai_enabled,
            exclude_names: excludeNames
        });
        const url = `/generate-variants/?${params.toString()}`;

        if (this.alternativeVariantsAbortController) {
            this.alternativeVariantsAbortController.abort();
        }
        this.alternativeVariantsAbortController = new AbortController();
        const signal = this.alternativeVariantsAbortController.signal;

        fetch(url, { signal })
            .then(async res => {
                if (!res.ok) {
                    let errData;
                    try { errData = await res.json(); } catch(e) {}
                    throw new Error(errData?.error || `HTTP error! status: ${res.status}`);
                }
                
                const reader = res.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let buffer = "";
                let rawBuffer = "";
                let count = 0;
                
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop();
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const dataStr = line.substring(6).trim();
                            if (dataStr === '[DONE]' || dataStr.startsWith('event: close')) break;
                            if (dataStr && dataStr !== '{}') {
                                try {
                                    const parsed = JSON.parse(dataStr);
                                    
                                    if (typeof parsed === 'string') {
                                        // Streaming raw text chunks
                                        rawBuffer += parsed;
                                        const objects = this.extractPartialObjects(rawBuffer);
                                        
                                        const newVariants = [];
                                        let vCount = 0;
                                        for (const objStr of objects) {
                                            const v = this.repairAndParse(objStr);
                                            if (v) {
                                                const mappedVariant = {
                                                    variant_id: v.variant_id || v.id || `variant-${Date.now()}-${vCount}`,
                                                    variant_name: v.variant_name || v.name || 'Generating...',
                                                    description: v.description || '',
                                                    menu_description: v.menu_description || '',
                                                    creativity_level: v.creativity_level || level
                                                };
                                                newVariants.push(mappedVariant);
                                            } else {
                                                if (this.alternative_variants[vCount]) {
                                                    newVariants.push(this.alternative_variants[vCount]);
                                                }
                                            }
                                            vCount++;
                                        }
                                        this.alternative_variants = newVariants;
                                        
                                    } else {
                                        // Fallback dictionary mode
                                        const v = parsed;
                                        const mappedVariant = {
                                            variant_id: v.variant_id || v.id || `variant-${Date.now()}-${count++}`,
                                            variant_name: v.variant_name || v.name || 'Unknown Variant',
                                            description: v.description,
                                            menu_description: v.menu_description,
                                            creativity_level: v.creativity_level || level
                                        };
                                        this.alternative_variants.push(mappedVariant);
                                    }
                                } catch (e) {
                                    console.error('JSON parse error in variants stream', e);
                                }
                            }
                        }
                    }
                }
                this.variant_loading = false;
            })
            .catch(err => {
                if (err.name !== 'AbortError') {
                    console.error('[GrainLab] Failed fetching alternative variants:', err);
                    this.variant_loading = false;
                }
            });
    },

    fetchRecipeDetails(recipe) {
        this.advisoryLoading = true;
        this.advisory_resolved = false;
        this.recipe_details_data = null;
        
        this.startRecipeDetailsProgress();
        
        if (this.recipeDetailsAbortController) {
            this.recipeDetailsAbortController.abort();
        }
        this.recipeDetailsAbortController = new AbortController();
        const signal = this.recipeDetailsAbortController.signal;
        
        const params = new URLSearchParams({
            recipe_slug: recipe.recipe_id,
            recipe_name: recipe.name || '',
            engine_id: this.selected_master,
            active_archetype_id: this.active_archetype_id,
            category_slug: this.selected_master,
            selected_grains: (this.activeBerries || []).map(b => b.id).join(','),
            global_ai_enabled: this.global_ai_enabled
        });
        const urlDetails = `/ai-recipe-details/?${params.toString()}`;
        const urlAdvisory = `/ai-grain-advisory/?${params.toString()}&only_evaluations=true&stream=true`;
        
        // Reset evaluations before streaming
        this.grainEvaluations = [];
        this.mill_evaluations = [];
        this.sifter_evaluations = {};
        if (this.activeBerries) {
            this.activeBerries.forEach(b => {
                b.classification = null;
                b.reasoning = null;
                b.selected = false;
            });
        }
        
        const detailsPromise = fetch(urlDetails, { signal }).then(async res => {
            if (!res.ok) {
                let errData;
                try { errData = await res.json(); } catch(e) {}
                throw new Error(errData?.error || `HTTP error! status: ${res.status}`);
            }
            return res.json();
        });
        
        const advisoryPromise = fetch(urlAdvisory, { signal }).then(async res => {
            if (!res.ok) {
                let errData;
                try { errData = await res.json(); } catch(e) {}
                throw new Error(errData?.error || `HTTP error! status: ${res.status}`);
            }
            const reader = res.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.substring(6).trim();
                        if (dataStr === '[DONE]') break;
                        if (dataStr && dataStr !== '{}') {
                            try {
                                const parsed = JSON.parse(dataStr);
                                
                                // Normalize tiers if AI responds creatively
                                if (parsed.tier) parsed.tier = parsed.tier.toLowerCase().trim();
                                if (parsed.tier === 'optimal') parsed.tier = 'recommended';
                                else if (parsed.tier === 'not recommended') parsed.tier = 'not-recommended';
                                else if (parsed.tier === 'sub optimal' || parsed.tier === 'suboptimal') parsed.tier = 'sub-optimal';

                                if (parsed.type === 'grain') {
                                    // Match by exact ID or by grain name (case-insensitive) in case LLM returns the name instead of UUID
                                    const berry = this.activeBerries.find(b => 
                                        b.id.toString() === parsed.id.toString() || 
                                        (b.name && b.name.toLowerCase() === parsed.id.toString().toLowerCase())
                                    );
                                    
                                    if (berry) {
                                        console.log(`[Advisory] Matched grain: ${berry.name} (${parsed.tier})`);
                                        this.grainEvaluations.push({ grain_id: berry.id, tier: parsed.tier, reasoning: parsed.reasoning });
                                        berry.classification = parsed.tier;
                                        berry.reasoning = parsed.reasoning;
                                        if (parsed.tier === 'recommended') berry.selected = true;
                                    } else {
                                        console.warn(`[Advisory] Warning: Could not match grain id/name returned by AI: "${parsed.id}"`);
                                    }
                                } else if (parsed.type === 'mill') {
                                    console.log(`[Advisory] Mill evaluation: ${parsed.id} (${parsed.tier})`);
                                    this.mill_evaluations.push({ mill_id: parsed.id, tier: parsed.tier, reasoning: parsed.reasoning });
                                } else if (parsed.type === 'sifter') {
                                    console.log(`[Advisory] Sifter evaluation: ${parsed.id} (${parsed.tier})`);
                                    this.sifter_evaluations[parsed.id] = { tier: parsed.tier, reasoning: parsed.reasoning };
                                }
                            } catch (e) { console.error('SSE Parse Error', e); }
                        }
                    }
                }
            }
        });
        
        Promise.all([detailsPromise, advisoryPromise])
            .then(([detailsData]) => {
                this.recipe_details_data = detailsData;
                
                this.recipe_details_data.grain_evaluations = this.grainEvaluations;
                this.recipe_details_data.mill_evaluations = this.mill_evaluations;
                this.recipe_details_data.sifter_evaluations = this.sifter_evaluations;
                
                if (this.recipe_details_data.sidebar_science_profile) {
                    this.sidebar_analysis = this.recipe_details_data.sidebar_science_profile;
                }
                this.advisory_resolved = true;
            })
            .catch(err => {
                if (err.name !== 'AbortError') {
                    console.error('[GrainLab] Failed fetching recipe details:', err);
                    this.advisory_resolved = true;
                    this.recipe_details_data = {
                        sidebar_science_profile: 'Failed to fetch details.',
                        recommended_grain_ids: [],
                        secondary_ingredients: null
                    };
                }
            });
    },

    startRecipeDetailsProgress() {
        if (this.recipe_details_interval) clearTimeout(this.recipe_details_interval);
        
        // Initialize steps if empty
        if (!this.advisory_steps || this.advisory_steps.length === 0) {
            this.advisory_steps = [
                { id: 'advisory', icon: '🤖', text: 'Generating Pragmatic Magic Layer...', active: false, completed: false },
                { id: 'math', icon: '🧮', text: 'Calculating ingredient proportions...', active: false, completed: false },
                { id: 'hardware', icon: '⚙️', text: 'Selecting hardware parameters...', active: false, completed: false }
            ];
        }

        // Reset steps
        this.advisory_steps.forEach(s => {
            s.active = false;
            s.completed = false;
        });
        
        // Set first step active
        this.advisory_steps[0].active = true;
        let stepIdx = 0;
        
        const tick = () => {
            if (this.recipe_details_interval) clearTimeout(this.recipe_details_interval);
            
            if (stepIdx < this.advisory_steps.length - 1) {
                this.advisory_steps[stepIdx].active = false;
                this.advisory_steps[stepIdx].completed = true;
                stepIdx++;
                this.advisory_steps[stepIdx].active = true;
                
                // Rapidly complete if resolved (150ms), else standard pacing (1000ms)
                const nextDelay = this.advisory_resolved ? 150 : 1000;
                this.recipe_details_interval = setTimeout(tick, nextDelay);
            } else {
                if (this.advisory_resolved) {
                    this.advisory_steps[stepIdx].active = false;
                    this.advisory_steps[stepIdx].completed = true;
                    
                    setTimeout(() => {
                        const data = this.recipe_details_data;
                        if (data) {
                            const profile = data.sidebar_science_profile || 'No technical analysis compiled.';
                            this.sidebar_analysis = profile;
                            this.selectedRecipeScienceProfile = profile;
                            
                            // Save recommended grains for highlighting in Phase 2
                            this.recommended_grain_ids = data.recommended_grain_ids || [];

                            // Auto-select recommended grains
                            if (this.activeBerries && this.activeBerries.length > 0) {
                                this.activeBerries.forEach(berry => {
                                    if (this.getGrainTier(berry) === 'recommended') {
                                        berry.selected = true;
                                    }
                                });
                            }

                            // Pre-select required secondary ingredients if returned by LLM
                            this.selectedRecipeSecondaryIngredients = data.secondary_ingredients || null;
                            
                            // Ad-hoc updates mapping for Phase 2 HTML
                            this.mill_evaluations = data.mill_evaluations || [];
                            this.sifter_evaluations = data.sifter_evaluations || {};
                            
                            // Broadcast the recipe-details-updated event to update the inner form component!
                            window.dispatchEvent(new CustomEvent('recipe-details-updated', {
                                detail: data
                            }));
                            this.advisoryLoading = false;
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
