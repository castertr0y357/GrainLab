// phase3.js
document.addEventListener('alpine:init', () => {
    Alpine.data('phase3App', (initialData) => ({
        // State variables required for Phase 3
        current_phase: initialData.current_phase || 3,
        selected_master: initialData.selected_master || null,
        global_ai_enabled: initialData.global_ai_enabled || true,
        enginesArchetypes: initialData.enginesArchetypes || {},
        engines_ff: initialData.engines_ff || {},
        
        hydration: initialData.hydration || 70,
        fat: initialData.fat || 0,
        sugar: initialData.sugar || 0,
        starter: initialData.starter || 20,
        
        mill_type: initialData.mill_type || null,
        is_sifted: initialData.is_sifted || false,
        custom_mixer: initialData.custom_mixer || null,
        
        selectedRecipeSecondaryIngredients: initialData.selectedRecipeSecondaryIngredients || null,
        recipe_name: initialData.recipe_name || '',
        preset_slug: initialData.preset_slug || '',
        activeBerries: initialData.active_berries || [],
        flavor_inclusions: initialData.flavor_inclusions || [],
        flour_blend: initialData.flour_blend || {},
        flour_blend_reasoning: initialData.flour_blend_reasoning || '',
        default_yield_amount: initialData.default_yield_amount || 1,
        yield_unit: initialData.yield_unit || 'loaf',
        is_portionable: initialData.is_portionable || false,
        
        // Loading State
        phase3Loading: false,
        phase3LoadingMessage: '',
        phase3Error: null,
        // Progressive Disclosure State
        activeSubstituteCategory: null,
        substitutesCache: {},
        substituteLoading: false,

        phase3_generation_steps: [],
        
        // Secondary Ingredient Selections
        secondary_lipid_category: 'None',
        secondary_lipid_option: 'None',
        secondary_lipid_temp: 'N/A',
        secondary_liquid_category: 'None',
        secondary_liquid_option: 'None',
        secondary_liquid_temp: 'N/A',
        secondary_binder_category: 'None',
        secondary_binder_option: 'None',
        secondary_binder_temp: 'N/A',
        secondary_sweetener_category: 'None',
        secondary_sweetener_option: 'None',
        secondary_sweetener_temp: 'N/A',
        secondary_leavener_category: 'None',
        secondary_leavener_option: 'None',
        secondary_leavener_temp: 'N/A',
        secondary_additive_category: 'None',
        secondary_additive_option: 'None',
        secondary_additive_temp: 'N/A',
        
        // Form Factor stuff (if needed in phase 3)
        ff_expanded: null,
        
        // Hover state variables
        hovered_element: null,
        sidebar_tier: '',
        sidebar_labor_roi: '',
        sidebar_analysis: '',
        sidebar_insight_loading: false,
        
        // Pre-fetched insights
        batchInsightsMap: {},
        factual_dictionary: {},
        mill_recommendation: null,
        sifted_recommendation: null,
        
        
        fetchSubstitutes(categoryKey) {
            if (this.substitutesCache[categoryKey]) {
                this.activeSubstituteCategory = categoryKey;
                return;
            }

            this.substituteLoading = true;
            this.activeSubstituteCategory = categoryKey;

            const originalRec = this.selectedRecipeSecondaryIngredients[categoryKey];
            const inventory_ids = (this.activeBerries || []).map(b => b.id).join(',');

            const payload = {
                engine_id: this.selected_master,
                active_archetype_id: this.preset_slug,
                recipe_slug: this.preset_slug,
                recipe_name: this.recipe_name,
                selected_grains: inventory_ids,
                target_category: categoryKey,
                original_recommendation: originalRec
            };

            fetch(`/generate-substitutes/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrf_token
                },
                body: JSON.stringify(payload)
            })
            .then(async res => {
                if (!res.ok) {
                    let errData;
                    try { errData = await res.json(); } catch(e) {}
                    throw new Error(errData?.error || `HTTP error! status: ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                if (data.substitutes) {
                    this.substitutesCache[categoryKey] = data.substitutes;
                }
                this.substituteLoading = false;
            })
            .catch(err => {
                console.error("Failed fetching substitutes:", err);
                // Instead of failing entirely, just close it or show an error
                this.substituteLoading = false;
                this.substitutesCache[categoryKey] = [];
            });
        },
        
                
        generateMoreSubstitutes(categoryKey) {
            this.substituteLoading = true;
            this.activeSubstituteCategory = categoryKey;

            const originalRec = this.selectedRecipeSecondaryIngredients[categoryKey];
            const inventory_ids = (this.activeBerries || []).map(b => b.id).join(',');
            
            // Get currently displayed substitute names to exclude them
            const currentSubstitutes = this.substitutesCache[categoryKey] || [];
            const excludeNames = currentSubstitutes.map(s => s.name);

            const payload = {
                engine_id: this.selected_master,
                active_archetype_id: this.preset_slug,
                recipe_slug: this.preset_slug,
                recipe_name: this.recipe_name,
                selected_grains: inventory_ids,
                target_category: categoryKey,
                original_recommendation: originalRec,
                exclude_names: excludeNames
            };

            fetch(`/generate-substitutes/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrf_token
                },
                body: JSON.stringify(payload)
            })
            .then(async res => {
                if (!res.ok) {
                    let errData;
                    try { errData = await res.json(); } catch(e) {}
                    throw new Error(errData?.error || `HTTP error! status: ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                if (data.substitutes) {
                    // Append new substitutes instead of replacing
                    const existing = this.substitutesCache[categoryKey] || [];
                    this.substitutesCache[categoryKey] = [...existing, ...data.substitutes];
                }
                this.substituteLoading = false;
            })
            .catch(err => {
                console.error("Failed fetching more substitutes:", err);
                this.substituteLoading = false;
            });
        },
        confirmSubstitute(categoryKey, substituteObj) {
            let originalRatioSum = 1.0;
            if (this.selectedRecipeSecondaryIngredients[categoryKey] && this.selectedRecipeSecondaryIngredients[categoryKey].length > 0) {
                originalRatioSum = this.selectedRecipeSecondaryIngredients[categoryKey].reduce((sum, item) => sum + (item.ratio || 1.0), 0);
            }
            this.selectedRecipeSecondaryIngredients[categoryKey] = [{
                category_key: categoryKey,
                category_name: substituteObj.category_name || categoryKey,
                name: substituteObj.name,
                temperature: substituteObj.temperature,
                reasoning: substituteObj.difference_explanation,
                ratio: originalRatioSum
            }];
            this.activeSubstituteCategory = null;
        },
        initializePhase3() {
            console.log("Phase 3 App Initialized.");
            this.csrf_token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            this.fetchSecondaryIngredients();
        },

        extractPartialObjects(arrayContent) {
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
            
            repaired = repaired.replace(/,\s*$/, '');
            if (repaired.match(/:\s*$/)) {
                repaired += 'null';
            }
            
            let openBraces = (repaired.match(/\{/g) || []).length;
            let closeBraces = (repaired.match(/\}/g) || []).length;
            let openBrackets = (repaired.match(/\[/g) || []).length;
            let closeBrackets = (repaired.match(/\]/g) || []).length;
            
            while (openBrackets > closeBrackets) {
                repaired += ']';
                closeBrackets++;
            }
            while (openBraces > closeBraces) {
                repaired += '}';
                closeBraces++;
            }
            
            try {
                return JSON.parse(repaired);
            } catch(e) {
                return null;
            }
        },

        extractPhase3State(buffer) {
            const extractStringField = (key) => {
                const regex = new RegExp(`"${key}"\\s*:\\s*"([^"\\\\]*(?:\\\\.[^"\\\\]*)*)`);
                const match = buffer.match(regex);
                return match ? match[1] : null;
            };
            
            const extractNumberField = (key) => {
                const regex = new RegExp(`"${key}"\\s*:\\s*(\\d+)`);
                const match = buffer.match(regex);
                return match ? parseInt(match[1]) : null;
            };

            const extractFloatField = (key) => {
                const regex = new RegExp(`"${key}"\\s*:\\s*(-?\\d+(?:\\.\\d+)?)`);
                const match = buffer.match(regex);
                return match ? parseFloat(match[1]) : null;
            };
            
            const extractArray = (key) => {
                const regex = new RegExp(`"${key}"\\s*:\\s*\\[([\\s\\S]*)`);
                const match = buffer.match(regex);
                if (!match) return [];
                
                let arrContent = match[1];
                const endMatch = arrContent.match(/\],\\s*"/);
                if (endMatch) {
                    arrContent = arrContent.substring(0, endMatch.index);
                }
                
                const objStrings = this.extractPartialObjects(arrContent);
                const results = [];
                for (const objStr of objStrings) {
                    const parsed = this.repairAndParse(objStr);
                    if (parsed) results.push(parsed);
                }
                return results;
            };
            
            return {
                sidebar_science_profile: extractStringField("sidebar_science_profile"),
                fat_starting_temp: extractStringField("fat_starting_temp"),
                default_yield_amount: extractNumberField("default_yield_amount"),
                yield_unit: extractStringField("yield_unit"),
                target_fat_pct: extractFloatField("target_fat_pct"),
                target_sugar_pct: extractFloatField("target_sugar_pct"),
                target_hydration_pct: extractFloatField("target_hydration_pct"),
                target_binder_pct: extractFloatField("target_binder_pct"),
                target_leaven_pct: extractFloatField("target_leaven_pct"),
                target_salt_pct: extractFloatField("target_salt_pct"),
                target_friction_factor: extractFloatField("target_friction_factor"),
                target_bake_temp: extractNumberField("target_bake_temp"),
                target_bake_time: extractNumberField("target_bake_time"),
                flour_blend: extractArray("flour_blend"),
                flavor_inclusions: extractArray("flavor_inclusions"),
                secondary_ingredients: extractArray("secondary_ingredients")
            };
        },

        fetchSecondaryIngredients() {
            if (this.global_ai_enabled) {
                if (!this.selectedRecipeSecondaryIngredients || Object.keys(this.selectedRecipeSecondaryIngredients).length === 0) {
                    const engineData = this.engines_ff?.[this.selected_master]?.secondary_ingredients;
                    if (engineData) {
                        this.selectedRecipeSecondaryIngredients = JSON.parse(JSON.stringify(engineData));
                    }
                }
            }
            
            // Clear existing static data to show loading placeholder cards
            this.selectedRecipeSecondaryIngredients = {};
            this.flavor_inclusions = [];
            this.selectedRecipeScienceProfile = '';
            
            this.phase3Loading = true;
            this.phase3LoadingMessage = 'Formulating Final Secondary Ingredients...';
            this.phase3_generation_steps = [
                { id: '1', text: 'Analyzing grain blend structural profile...', active: true, completed: false },
                { id: '2', text: 'Calculating hydration interactions...', active: false, completed: false },
                { id: '3', text: 'Finalizing secondary ingredient recommendations...', active: false, completed: false }
            ];

            let stepInt = setInterval(() => {
                let activeIndex = this.phase3_generation_steps.findIndex(s => s.active);
                if (activeIndex >= 0 && activeIndex < this.phase3_generation_steps.length - 1) {
                    this.phase3_generation_steps[activeIndex].active = false;
                    this.phase3_generation_steps[activeIndex].completed = true;
                    this.phase3_generation_steps[activeIndex + 1].active = true;
                }
            }, 2500);

            const inventory_ids = (this.activeBerries || []).map(b => b.name).join(',');
            const params = new URLSearchParams({
                recipe_slug: this.preset_slug,
                engine_id: this.selected_master,
                active_archetype_id: this.preset_slug,
                selected_grains: inventory_ids,
                recipe_name: this.recipe_name,
                mill_type: this.mill_type,
                is_sifted: this.is_sifted ? 'true' : 'false',
                stream: 'true'
            });

            const eventSource = new EventSource(`/ai-recipe-details/?${params.toString()}`);
            let rawBuffer = "";
            eventSource.onmessage = (e) => {
                const dataStr = e.data;
                if (dataStr === "[DONE]") {
                    eventSource.close();
                    clearInterval(stepInt);
                    this.phase3_generation_steps.forEach(s => { s.active = false; s.completed = true; });
                    setTimeout(() => {
                        this.phase3Loading = false;
                    }, 500);
                    return;
                }
                
                try {
                    const parsed = JSON.parse(dataStr);
                    if (typeof parsed === 'string') {
                        // Raw streaming chunks
                        rawBuffer += parsed;
                        const state = this.extractPhase3State(rawBuffer);
                        
                        if (state.default_yield_amount) this.default_yield_amount = state.default_yield_amount;
                        if (state.yield_unit) this.yield_unit = state.yield_unit;
                        if (state.fat_starting_temp) this.fat_starting_temp = state.fat_starting_temp;

                        // AI driven base percentage updates
                        if (state.target_fat_pct !== null && state.target_fat_pct !== undefined) this.fat = state.target_fat_pct;
                        if (state.target_sugar_pct !== null && state.target_sugar_pct !== undefined) this.sugar = state.target_sugar_pct;
                        if (state.target_hydration_pct !== null && state.target_hydration_pct !== undefined) this.hydration = state.target_hydration_pct;
                        if (state.target_binder_pct !== null && state.target_binder_pct !== undefined) this.binder = state.target_binder_pct;
                        if (state.target_leaven_pct !== null && state.target_leaven_pct !== undefined) this.leaven_pct = state.target_leaven_pct;
                        if (state.target_salt_pct !== null && state.target_salt_pct !== undefined) this.salt_pct = state.target_salt_pct;
                        if (state.target_friction_factor !== null && state.target_friction_factor !== undefined) this.friction_factor = state.target_friction_factor;
                        if (state.target_bake_temp !== null && state.target_bake_temp !== undefined) this.bake_temp = state.target_bake_temp;
                        if (state.target_bake_time !== null && state.target_bake_time !== undefined) this.bake_time = state.target_bake_time;
                        
                        // We also assign this to selectedRecipeScienceProfile so it displays properly if that variable is used elsewhere
                        if (state.sidebar_science_profile) {
                            this.selectedRecipeScienceProfile = state.sidebar_science_profile;
                        }
                        
                        if (state.flour_blend && state.flour_blend.length > 0) {
                            const blend = state.flour_blend[0];
                            this.flour_blend = this.normalizeFlourBlend(blend.ratios || blend);
                            this.flour_blend_reasoning = blend.reasoning || '';
                        }
                        
                        if (state.flavor_inclusions && state.flavor_inclusions.length > 0) {
                            const validFlavors = state.flavor_inclusions.filter(f => f.name && f.name.toLowerCase() !== 'none' && f.name.toLowerCase() !== 'n/a');
                            if (validFlavors.length > 0) {
                                this.flavor_inclusions = validFlavors;
                            }
                        }
                        
                        if (state.secondary_ingredients && state.secondary_ingredients.length > 0) {
                            const validKeys = ['lipids', 'liquids', 'binders', 'sweeteners', 'leaveners', 'additives'];
                            for (const k of validKeys) {
                                const itemsForKey = state.secondary_ingredients.filter(sec => 
                                    sec.category_key === k && 
                                    sec.name && 
                                    sec.name.toLowerCase() !== 'none' && 
                                    sec.name.toLowerCase() !== 'n/a'
                                );
                                this.selectedRecipeSecondaryIngredients[k] = itemsForKey;
                            }
                            // DEBUG LOGGING
                            console.log("[Phase 3 Stream] Parsed Secondary Ingredients: ", JSON.parse(JSON.stringify(this.selectedRecipeSecondaryIngredients)));
                        }
                        
                    } else if (parsed.type === "secondary" && parsed.category_key) {
                        // Fallback block if backend doesn't yield raw string chunks
                        if (parsed.name && parsed.name.toLowerCase() !== 'none' && parsed.name.toLowerCase() !== 'n/a') {
                            this.selectedRecipeSecondaryIngredients[parsed.category_key] = parsed;
                            console.log(`[Phase 3 Stream Fallback] Secondary Ingredient: ${parsed.name} -> ${parsed.category_key}`);
                        }
                    } else if (parsed.type === "flavor") {
                        if (!this.flavor_inclusions.some(f => f.name.toLowerCase() === parsed.name.toLowerCase())) {
                            this.flavor_inclusions.push(parsed);
                        }
                    } else if (parsed.type === "blend") {
                        this.flour_blend = this.normalizeFlourBlend(parsed.ratios || parsed);
                        this.flour_blend_reasoning = parsed.reasoning || '';
                        if (parsed.default_yield_amount) this.default_yield_amount = parsed.default_yield_amount;
                    } else if (parsed.flour_blend) {
                        this.flour_blend = this.normalizeFlourBlend(parsed.flour_blend.ratios || parsed.flour_blend);
                        this.flour_blend_reasoning = parsed.flour_blend.reasoning || '';
                        if (parsed.default_yield_amount) this.default_yield_amount = parsed.default_yield_amount;
                    } else if (parsed.ratios) {
                        this.flour_blend = this.normalizeFlourBlend(parsed.ratios);
                        this.flour_blend_reasoning = parsed.reasoning || '';
                    } else {
                        if (parsed.secondary_ingredients) {
                            this.selectedRecipeSecondaryIngredients = parsed.secondary_ingredients;
                        }
                        if (parsed.flavor_inclusions) {
                            this.flavor_inclusions = parsed.flavor_inclusions;
                        }
                        if (parsed.flour_blend) {
                            this.flour_blend = this.normalizeFlourBlend(parsed.flour_blend.ratios || parsed.flour_blend);
                        }
                        if (parsed.default_yield_amount !== undefined) {
                            this.default_yield_amount = parsed.default_yield_amount;
                        }
                        if (parsed.yield_unit) {
                            this.yield_unit = parsed.yield_unit;
                        }
                        if (parsed.is_portionable !== undefined) {
                            this.is_portionable = parsed.is_portionable;
                        }
                        if (parsed.target_fat_pct !== undefined) this.fat = parsed.target_fat_pct;
                        if (parsed.target_sugar_pct !== undefined) this.sugar = parsed.target_sugar_pct;
                        if (parsed.target_hydration_pct !== undefined) this.hydration = parsed.target_hydration_pct;
                        if (parsed.target_binder_pct !== undefined) this.binder = parsed.target_binder_pct;
                        if (parsed.target_leaven_pct !== undefined) this.leaven_pct = parsed.target_leaven_pct;
                        if (parsed.target_salt_pct !== undefined) this.salt_pct = parsed.target_salt_pct;
                        if (parsed.target_friction_factor !== undefined) this.friction_factor = parsed.target_friction_factor;
                        if (parsed.target_bake_temp !== undefined) this.bake_temp = parsed.target_bake_temp;
                        if (parsed.target_bake_time !== undefined) this.bake_time = parsed.target_bake_time;
                    }
                } catch (err) {
                    console.warn("Could not parse SSE chunk:", dataStr);
                }
            };
            eventSource.onerror = (err) => {
                eventSource.close();
                clearInterval(stepInt);
                this.phase3Error = "Failed to load ingredients. Connection lost.";
                this.phase3Loading = false;
            };
        },

        // Inherit all methods from original actions.js
        


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
        
        
        if (key.startsWith('substitute_')) {
            const index = parseInt(key.replace('substitute_', ''));
            const sub = this.substitutesCache[this.activeSubstituteCategory]?.[index];
            if (sub) {
                this.sidebar_tier = '';
                this.sidebar_analysis = `<strong>Quality Impact:</strong><br/>${sub.difference_explanation}`;
                this.sidebar_insight_loading = false;
            }
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

        if (key.startsWith('specialty_')) {
            const name = key.replace('specialty_', '');
            this.sidebar_insight_loading = false;
            this.sidebar_labor_roi = '';
            this.sidebar_tier = 'recommended';
            this.sidebar_analysis = `Flavor inclusion precisely calculated to complement ${this.recipe_name}.`;
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
            this.sidebar_tier = '';
            this.sidebar_analysis = 'Could not find details for this component.';
            this.sidebar_insight_loading = false;
        }
    },

    hasValidSecondary(secObj) {
        if (!secObj) return false;
        if (!secObj.categories || secObj.categories.length === 0) return false;
        if (secObj.categories.length === 1 && (secObj.categories[0].name.toLowerCase() === 'none' || secObj.categories[0].name.toLowerCase() === 'n/a')) return false;
        if (secObj.required_category && (secObj.required_category.toLowerCase() === 'none' || secObj.required_category.toLowerCase() === 'n/a')) return false;
        return true;
    },

    normalizeFlourBlend(blendObj) {
        if (!blendObj) return {};
        const sanitize = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
        let newBlend = {};
        let total = 0;
        
        for (const b of (this.activeBerries || [])) {
            const bClean = sanitize(b.name);
            const bNameHTML = b.name.toLowerCase().replace(/ /g, '_').replace(/-/g, '_');
            const matchKey = Object.keys(blendObj).find(k => sanitize(k) === bClean);
            if (matchKey) {
                newBlend[bNameHTML] = parseFloat(blendObj[matchKey]) || 0;
                total += newBlend[bNameHTML];
            } else {
                newBlend[bNameHTML] = 0;
            }
        }
        
        if (total === 0 && this.activeBerries && this.activeBerries.length > 0) {
            const eq = 100 / this.activeBerries.length;
            for (const b of this.activeBerries) {
                const bNameHTML = b.name.toLowerCase().replace(/ /g, '_').replace(/-/g, '_');
                newBlend[bNameHTML] = eq;
            }
        } else if (total > 0 && total !== 100) {
            // Normalize to 100
            for (let k in newBlend) {
                newBlend[k] = (newBlend[k] / total) * 100;
            }
        }
        return newBlend;
    },

    updateFlourBlend(key, value) {
        let val = parseFloat(value) || 0;
        this.flour_blend[key] = val;
        
        // Auto balance the rest
        let others = Object.keys(this.flour_blend).filter(k => k !== key);
        let currentTotalOthers = 0;
        for (let k of others) {
            currentTotalOthers += this.flour_blend[k];
        }
        
        let remaining = 100 - val;
        if (currentTotalOthers === 0 && others.length > 0) {
            let eq = remaining / others.length;
            for (let k of others) {
                this.flour_blend[k] = eq;
            }
        } else if (others.length > 0) {
            for (let k of others) {
                this.flour_blend[k] = (this.flour_blend[k] / currentTotalOthers) * remaining;
            }
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
