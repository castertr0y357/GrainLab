// phase4.js
document.addEventListener('alpine:init', () => {
    Alpine.data('phase4App', (initialData) => ({
        current_phase: initialData.current_phase || 4,
        phase4Error: null,
        selected_master: initialData.selected_master || null,
        global_ai_enabled: initialData.global_ai_enabled || true,
        preset_slug: initialData.preset_slug || null,
        active_variation_id: initialData.active_variation_id || null,
        flavor_inclusions: initialData.flavor_inclusions || [],
        secondary_ingredients: initialData.secondary_ingredients || {},
        enginesArchetypes: initialData.enginesArchetypes || {},
        engines_ff: initialData.engines_ff || {},
        recipe_name: initialData.recipe_name || '',
        initialIngredientNames: initialData.initialIngredientNames || [],
        appliedTweaksHistory: initialData.appliedTweaksHistory || [],
        
        default_yield_amount: initialData.default_yield_amount !== undefined ? parseFloat(initialData.default_yield_amount) : 1.0,
        yield_unit: initialData.yield_unit || 'loaf',
        is_portionable: initialData.is_portionable || false,
        scaleMultiplier: 1.0,
        
        bakeTimeMin: null,
        bakeTemp: null,
        bakeSteam: null,
        geometry_evaluation: null,
        pitfalls: [],
        sensory_description: '',
        
        mixing_method: initialData.mixing_method || 'hand_knead',
        active_action: initialData.active_action || 'stretch_fold',


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
        prepSteps: [],
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
        recipeIngredients: [],
        currentStepIndex: 0,
        timerRunning: false,
        stepTimeRemaining: 0,
        elapsedOvertime: 0,
        isAlarm: false,
        
        tweaksLoading: false,
        suggestedTweaks: [],
        progressPercent: 0,
        bakeTemp: 450,
        bakeSteam: 'Yes',
        donenessTemp: -1,
        waterTemp: -1,
        timerInterval: null,
        recipeCompiled: initialData.recipeCompiled || false,
        aiLoading: initialData.current_phase === 5 && (initialData.global_ai_enabled || true),
        globalElevateRecipe: [],
        geometry_evaluation: null,
        sensory_description: '',
        pitfalls: [],
        recipe: {},
        batchInsightsMap: {},
        applyProgressText: '',
        
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
        
        get requiresThermalProfile() {
            return this.activeProductionProfile?.thermodynamic_focus === 'biological_yeast_activity';
        },
        
        get groupedIngredients() {
            const groups = {};
            this.recipeIngredients.forEach(ing => {
                if (!groups[ing.category]) {
                    groups[ing.category] = [];
                }
                groups[ing.category].push(ing);
            });
            return groups;
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
        
        get resolvedYieldUnit() {
            const amount = this.default_yield_amount * this.scaleMultiplier;
            const isPlural = (amount > 1 || amount === 0);
            
            let unit = this.enginesArchetypes[this.selected_master]?.[this.preset_slug]?.yield_unit;
            
            if (!unit) {
                unit = this.engines_ff?.[this.selected_master]?.default_yield_unit;
            }
            
            if (!unit) {
                unit = this.yield_unit || 'portions';
            }
            
            if (isPlural && !unit.endsWith('s')) {
                if (unit === 'loaf') return 'loaves';
                if (unit === 'pastry') return 'pastries';
                return unit + 's';
            }
            
            if (!isPlural && unit.endsWith('s')) {
                if (unit === 'loaves') return 'loaf';
                if (unit === 'pastries') return 'pastry';
                return unit.slice(0, -1);
            }
            
            return unit;
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
            
            if (depth > 0 && objStart !== -1) {
                results.push(arrayContent.substring(objStart));
            }
            
            return results;
        },

        extractPhase4State(rawText) {
            let arrContent = rawText;
            const startMatch = arrContent.match(/\[/);
            if (startMatch) {
                arrContent = arrContent.substring(startMatch.index + 1);
            }
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
        },

        init() {
            // Convert legacy string inclusions to objects so the parser can match inc.name
            if (this.flavor_inclusions && Array.isArray(this.flavor_inclusions)) {
                this.flavor_inclusions = this.flavor_inclusions.map(inc => {
                    if (typeof inc === 'string') {
                        return {
                            name: inc,
                            volume_description: "To taste",
                            bakers_percentage: null
                        };
                    }
                    return inc;
                });
            }

            // Try to load ingredient weights from a script tag in the page
            const weightsEl = document.getElementById('ingredient-weights-data');
            if (weightsEl) {
                try {
                    this.ingredientWeights = JSON.parse(weightsEl.textContent || '{}');
                } catch (e) {
                    console.error("Failed to parse ingredient weights", e);
                }
            }

            if (this.global_ai_enabled) {
                this.fetchProcessDetails();
            }
        },

        fetchProcessDetails() {
            this.processRecommendationsLoading = true;
            
            this.processRecommendations = {};
            this.slider_recommendations = {};
            
            const createParams = (target) => new URLSearchParams({
                engine_id: this.selected_master,
                active_archetype_id: this.preset_slug,
                recipe_slug: this.preset_slug,
                recipe_name: 'Phase 4 Recipe',
                stream: 'true',
                target: target
            });

            const streamFetch = (params) => {
                return fetch('/ai-process-details/?' + params.toString())
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
                            const { done, value } = await reader.read();
                            if (done) break;
                            
                            buffer += decoder.decode(value, { stream: true });
                            const lines = buffer.split('\n');
                            buffer = lines.pop(); 
                            
                            for (let line of lines) {
                                if (line.startsWith("data: ")) {
                                    const dataStr = line.substring(6).trim();
                                    if (dataStr === "[DONE]" || !dataStr) continue;
                                    
                                    try {
                                        const parsedObj = JSON.parse(dataStr);
                                        if (typeof parsedObj === 'string') {
                                            rawBuffer += parsedObj;
                                        } else if (parsedObj.text) {
                                            rawBuffer += parsedObj.text;
                                        } else {
                                            rawBuffer += JSON.stringify(parsedObj);
                                        }
                                    } catch(e) {
                                        rawBuffer += dataStr;
                                    }

                                    const items = this.extractPhase4State(rawBuffer);
                                    
                                    for (const parsed of items) {
                                        if (!parsed) continue;
                                        if (parsed.type === "process" && parsed.category) {
                                            if (parsed.name && parsed.name.toLowerCase() !== 'none' && parsed.name.toLowerCase() !== 'n/a') {
                                                if (!this.processRecommendations[parsed.category]) {
                                                    this.processRecommendations[parsed.category] = parsed;
                                                } else {
                                                    this.processRecommendations[parsed.category].name = parsed.name;
                                                    this.processRecommendations[parsed.category].explanation = parsed.explanation;
                                                }
                                                if (parsed.category === 'dough_handling') {
                                                    this.active_action = parsed.name || this.active_action;
                                                }
                                            }

                                        } else if (parsed.type === "slider" && parsed.tweak_id) {
                                            if (!this.slider_recommendations[parsed.tweak_id]) {
                                                this.slider_recommendations[parsed.tweak_id] = parsed;
                                            } else {
                                                this.slider_recommendations[parsed.tweak_id].recommended_value = parsed.recommended_value;
                                                this.slider_recommendations[parsed.tweak_id].explanation = parsed.explanation;
                                            }
                                        } else if (parsed.type === "inclusion" && parsed.name && parsed.bakers_percentage !== undefined && parsed.bakers_percentage !== null) {
                                            const normalize = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
                                            const lowerParsed = normalize(parsed.name);
                                            let matched = false;
                                            const incIndex = this.flavor_inclusions.findIndex(inc => {
                                                const lowerInc = normalize(inc.name);
                                                return lowerInc === lowerParsed || lowerInc.includes(lowerParsed) || lowerParsed.includes(lowerInc);
                                            });
                                            if (incIndex !== -1) {
                                                console.log(`[Phase 4 AI Stream] Generated Percentage for inclusion ${parsed.name}: ${parsed.bakers_percentage}%`);
                                                if (!this.flavor_inclusions[incIndex].ratio && !this.flavor_inclusions[incIndex].bakers_percentage) {
                                                    this.flavor_inclusions[incIndex].bakers_percentage = parsed.bakers_percentage;
                                                }
                                                matched = true;
                                            }

                                            if (this.secondary_ingredients && Array.isArray(this.secondary_ingredients.additives)) {
                                                const addIndex = this.secondary_ingredients.additives.findIndex(add => {
                                                    const lowerAdd = normalize(add.name);
                                                    return lowerAdd === lowerParsed || lowerAdd.includes(lowerParsed) || lowerParsed.includes(lowerAdd);
                                                });
                                                if (addIndex !== -1) {
                                                    console.log(`[Phase 4 AI Stream] Generated Percentage for additive ${parsed.name}: ${parsed.bakers_percentage}%`);
                                                    if (!this.secondary_ingredients.additives[addIndex].ratio && !this.secondary_ingredients.additives[addIndex].bakers_percentage) {
                                                        this.secondary_ingredients.additives[addIndex].bakers_percentage = parsed.bakers_percentage;
                                                    }
                                                    matched = true;
                                                }
                                            }

                                            if (!matched) {
                                                const existingIndex = this.flavor_inclusions.findIndex(inc => normalize(inc.name) === lowerParsed);
                                                if (existingIndex !== -1) {
                                                    if (!this.flavor_inclusions[existingIndex].ratio && !this.flavor_inclusions[existingIndex].bakers_percentage) {
                                                        this.flavor_inclusions[existingIndex].bakers_percentage = parsed.bakers_percentage;
                                                    }
                                                } else {
                                                    console.warn(`[Phase 4 AI Stream] Generated percentage for ${parsed.name} (${parsed.bakers_percentage}%) but couldn't match it to any phase 3 inclusion or additive! Adding it to inclusions anyway.`);
                                                    this.flavor_inclusions.push({
                                                        name: parsed.name,
                                                        volume_description: "To taste",
                                                        bakers_percentage: parsed.bakers_percentage
                                                    });
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    });
            };

            Promise.allSettled([
                streamFetch(createParams('processes')),
                streamFetch(createParams('tweaks'))
            ]).then((results) => {
                results.forEach((result, idx) => {
                    if (result.status === 'rejected') {
                        console.error(`Error fetching process details stream ${idx}:`, result.reason);
                    }
                });
                this.processRecommendationsLoading = false;
            });
        },



        fetchProcessAlternatives(categoryKey) {
            if (this.processAlternativesCache[categoryKey] && this.processAlternativesCache[categoryKey].length > 0) {
                return; 
            }

            this.processAlternativesLoading = true;
            this.processAlternativesCache[categoryKey] = [];
            const originalRec = this.processRecommendations[categoryKey];

            const payload = {
                engine_id: this.selected_master,
                active_archetype_id: this.preset_slug,
                recipe_slug: this.preset_slug,
                recipe_name: 'Phase 4 Recipe',
                target_category: categoryKey,
                original_recommendation: originalRec
            };

            this.streamAlternatives(categoryKey, payload, false);
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

            this.streamAlternatives(categoryKey, payload, true);
        },

        streamAlternatives(categoryKey, payload, append) {

            let initialCacheLength = append ? (this.processAlternativesCache[categoryKey]?.length || 0) : 0;

            fetch('/ai-process-alternatives/?stream=true', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                },
                body: JSON.stringify(payload)
            })
            .then(async res => {
                if (!res.ok) {
                    let errData;
                    try { errData = await res.json(); } catch(e) {}
                    throw new Error(errData?.error || `HTTP error! status: ${res.status}`);
                }
                const reader = res.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let buffer = "";
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); 
                    
                    for (let line of lines) {
                        if (line.startsWith("data: ")) {
                            const dataStr = line.substring(6).trim();
                            if (dataStr === "[DONE]" || !dataStr) continue;
                            
                            try {
                                const parsedObj = JSON.parse(dataStr);
                                if (typeof parsedObj === 'string') {
                                    rawBuffer += parsedObj;
                                } else if (parsedObj.text) {
                                    rawBuffer += parsedObj.text;
                                } else {
                                    rawBuffer += JSON.stringify(parsedObj);
                                }
                            } catch(e) {
                                rawBuffer += dataStr;
                            }

                            const items = this.extractPhase4State(rawBuffer);
                            
                            const validItems = items.filter(i => i && i.type === 'alternative');
                            
                            if (append) {
                                const baseCache = this.processAlternativesCache[categoryKey].slice(0, initialCacheLength);
                                this.processAlternativesCache[categoryKey] = [...baseCache, ...validItems];
                            } else {
                                this.processAlternativesCache[categoryKey] = validItems;
                            }
                        }
                    }
                }
            })
            .then(() => {
                this.processAlternativesLoading = false;
            })
            .catch(err => {
                console.error('Failed fetching alternatives:', err);
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
            if (!this.global_ai_enabled) return;
            
            this.aiLoading = true;
            this.rawStreamText = "";
            this.steps.splice(0, this.steps.length); // Clear preserving reactivity
            this.bakeTemp = null;
            this.bakeTimeMin = null;
            this.bakeSteam = null;
            this.donenessTemp = -1;
            this.waterTemp = -1;
            this.pitfalls = [];
            this.sensory_description = '';
            this.geometry_evaluation = null;

            try {
                // Determine category and archetype from current path
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                let cat = this.selected_master || pathParts[1];
                let arch = this.preset_slug || pathParts[2];
                if (!cat || !arch) {
                    this.aiLoading = false;
                    return;
                }
                
                // Fire off tweaks fetch concurrently
                if (this.global_ai_enabled) {
                    this.fetchRecipeTweaks();
                }
                
                const response = await fetch(`/recipe-final/${cat}/${arch}/ai/?stream=true`, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                if (!response.body) {
                    throw new Error("No response body for streaming");
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = "";

                // Fallback for bakeTemp in case AI fails or is disabled
                if (this.bakeTemp === null && initialData.bakeTempF) {
                    this.bakeTemp = initialData.bakeTempF;
                }
                if (this.bakeTimeMin === null && initialData.bakeTimeMin) {
                    this.bakeTimeMin = initialData.bakeTimeMin;
                }
                if (this.bakeSteam === null && initialData.bakeSteam !== undefined) {
                    this.bakeSteam = initialData.bakeSteam;
                }

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    let parts = buffer.split(/\r?\n\r?\n/);
                    buffer = parts.pop();

                    // Clear old steps before starting to parse new ones from the AI stream
                    let hasClearedSteps = false;

                    for (const part of parts) {
                        if (part.startsWith('data: ')) {
                            const dataStr = part.replace('data: ', '').trim();
                            if (dataStr === "[DONE]" || !dataStr) continue;
                            
                            try {
                                const parsed = JSON.parse(dataStr);
                                if (parsed.text) {
                                    this.rawStreamText += parsed.text;
                                    this.parseRawStream();
                                }
                            } catch(e) {
                                console.error("Parse error on chunk:", dataStr, e);
                            }
                        }
                    }
                }
            } catch (err) {
                console.error("Failed to fetch AI insights", err);
            } finally {
                this.aiLoading = false;
            }
        },

        async fetchRecipeTweaks() {
            if (this.tweaksLoading) return;
            this.tweaksLoading = true;
            this.suggestedTweaks = [];
            this.rawTweaksText = "";
            
            try {
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                const cat = this.selected_master || pathParts[1];
                const arch = this.preset_slug || pathParts[2];

                const response = await fetch('/ai-recipe-tweaks/?stream=true', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        recipe_slug: arch,
                        recipe_name: this.recipe_name,
                        engine_id: cat,
                        active_archetype_id: arch,
                        current_ingredients: this.initialIngredientNames,
                        applied_tweaks_history: this.appliedTweaksHistory
                    })
                });

                if (!response.ok) throw new Error("Failed to fetch recipe tweaks");

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = "";

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    let parts = buffer.split(/\r?\n\r?\n/);
                    buffer = parts.pop();

                    for (const part of parts) {
                        if (part.startsWith('data: ')) {
                            const dataStr = part.replace('data: ', '').trim();
                            if (dataStr === "[DONE]" || !dataStr) continue;
                            
                            try {
                                const parsed = JSON.parse(dataStr);
                                if (parsed.text) {
                                    this.rawTweaksText += parsed.text;
                                    this.parseRawTweaks();
                                }
                            } catch(e) {
                                console.error("Parse error on chunk:", dataStr, e);
                            }
                        }
                    }
                }
                
                try {
                    // Try parsing the full JSON array at the end to get complete objects (especially new_ingredients)
                    const finalTweaks = JSON.parse(this.rawTweaksText);
                    if (Array.isArray(finalTweaks) && finalTweaks.length > 0) {
                        this.suggestedTweaks = finalTweaks;
                    }
                } catch(e) {
                    console.error("Failed final parse of tweaks array", e);
                }
            } catch (err) {
                console.error("Failed to fetch AI Tweaks", err);
            } finally {
                this.tweaksLoading = false;
            }
        },
        
        parseRawTweaks() {
            const tweakMatches = [...this.rawTweaksText.matchAll(/"type"\s*:\s*"tweak"(.*?)(?=\{\s*"type"|\]|$)/gs)];
            let newTweaks = [];
            for (let i = 0; i < tweakMatches.length; i++) {
                const text = tweakMatches[i][0];
                
                const titleMatch = text.match(/"tweak_title"\s*:\s*"((?:[^"\\]|\\.)*)/);
                const title = titleMatch ? titleMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"') : 'Generating...';
                
                const reasoningMatch = text.match(/"reasoning"\s*:\s*"((?:[^"\\]|\\.)*)/);
                let reasoning = reasoningMatch ? reasoningMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"') : '';
                
                const outcomeMatch = text.match(/"expected_outcome"\s*:\s*"((?:[^"\\]|\\.)*)/);
                let outcome = outcomeMatch ? outcomeMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"') : '';
                
                const modsMatch = text.match(/"proposed_modifications"\s*:\s*"((?:[^"\\]|\\.)*)/);
                let modifications = modsMatch ? modsMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"') : '';
                
                let explanation = reasoning;
                if (outcome) {
                    explanation += (explanation ? " " : "") + outcome;
                }
                
                newTweaks.push({
                    tweak_title: title,
                    reasoning: explanation,
                    proposed_modifications: modifications
                });
            }
            
            // If the AI ran out of ideas, it might return an empty list or a single 'Out of Options' tweak.
            if (newTweaks.length === 1 && newTweaks[0].tweak_title === 'Out of Options') {
                newTweaks = []; // Clear it so the 'Generating more ideas' button is hidden
            }
            
            this.suggestedTweaks = newTweaks;
        },

        async generateMoreIdeas() {
            // Feed currently un-selected tweaks into history so they aren't repeated
            this.suggestedTweaks.forEach(t => {
                this.appliedTweaksHistory.push("Discarded: " + t.tweak_title);
            });
            this.suggestedTweaks = []; 
            await this.fetchRecipeTweaks();
        },

        async applyTweak(tweak) {
            this.tweaksLoading = true;
            this.applyProgressText = "Balancing recipe formula...";
            try {
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                const cat = this.selected_master || pathParts[1];
                const arch = this.preset_slug || pathParts[2];
                
                const response = await fetch('/ai-apply-tweak/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        recipe_slug: arch,
                        recipe_name: this.recipe_name,
                        engine_id: cat,
                        active_archetype_id: arch,
                        proposed_modifications: tweak.proposed_modifications,
                        tweak_title: tweak.tweak_title
                    })
                });

                if (response.ok) {
                    this.appliedTweaksHistory.push("Applied: " + tweak.tweak_title);
                    
                    // Remove the applied tweak from suggestedTweaks so it vanishes
                    this.suggestedTweaks = this.suggestedTweaks.filter(t => t.tweak_title !== tweak.tweak_title);
                    
                    // Feed remaining un-selected tweaks into history so they aren't repeated
                    this.suggestedTweaks.forEach(t => {
                        this.appliedTweaksHistory.push("Discarded: " + t.tweak_title);
                    });
                    
                    // Clear applyProgressText so that fetchAIInsights can show its loading state and stream visually
                    this.applyProgressText = "";
                    
                    await this.fetchAIInsights();
                    
                    // Fetch new tweaks to replace the applied and discarded ones
                    await this.fetchRecipeTweaks();
                }
            } catch (err) {
                console.error("Failed to apply tweak:", err);
                this.tweaksLoading = false;
                this.applyProgressText = "";
            } finally {
                // Do not set this.applyProgressText = "" here if we are already streaming, 
                // because fetchAIInsights might take time.
                // Actually, fetchAIInsights manages its own aiLoading state, so we just clear tweaksLoading.
                this.tweaksLoading = false;
            }
        },

        parseRawStream() {
            if (!this.rawStreamText) return;
            
            const sensoryMatch = this.rawStreamText.match(/"sensory_benchmark"\s*:\s*"((?:[^"\\]|\\.)*)/);
            if (sensoryMatch) {
                this.sensory_description = sensoryMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"');
            }

            const pitfallsMatch = this.rawStreamText.match(/"contextual_pitfalls"\s*:\s*\[(.*?)\]/s);
            if (pitfallsMatch) {
                const pitfallsText = pitfallsMatch[1];
                const pitfallItems = [...pitfallsText.matchAll(/"((?:[^"\\]|\\.)*)"/g)];
                if (pitfallItems.length > 0) {
                    this.pitfalls = pitfallItems.map(m => m[1].replace(/\\n/g, '\n').replace(/\\"/g, '"'));
                }
            }
            
            const profileMatch = this.rawStreamText.match(/"type"\s*:\s*"baking_profile"(.*?)(?=\{\s*"type"|\]|$)/s);
            if (profileMatch) {
                const text = profileMatch[0];
                const tempMatch = text.match(/"oven_temp"\s*:\s*(\d+)/);
                if (tempMatch) this.bakeTemp = parseInt(tempMatch[1]);
                
                const timeMatch = text.match(/"bake_time"\s*:\s*(\d+)/);
                if (timeMatch) this.bakeTimeMin = parseInt(timeMatch[1]);
                
                const steamMatch = text.match(/"steam"\s*:\s*"((?:[^"\\]|\\.)*)/);
                if (steamMatch) this.bakeSteam = steamMatch[1];
                
                const donenessMatch = text.match(/"target_doneness"\s*:\s*(\d+)/);
                if (donenessMatch) this.donenessTemp = parseInt(donenessMatch[1]);
                
                const waterTempMatch = text.match(/"liquid_water_temp"\s*:\s*(\d+)/);
                if (waterTempMatch) this.waterTemp = parseInt(waterTempMatch[1]);
            }

            const prepMatches = [...this.rawStreamText.matchAll(/"type"\s*:\s*"prep_step"(.*?)(?=\{\s*"type"|\]|$)/gs)];
            let newPrepSteps = [];
            for (let i = 0; i < prepMatches.length; i++) {
                const text = prepMatches[i][0];
                const ingMatch = text.match(/"ingredient"\s*:\s*"((?:[^"\\]|\\.)*)/);
                const ingredient = ingMatch ? ingMatch[1].replace(/\\n/g, '\\n').replace(/\\"/g, '"') : '';
                
                const instMatch = text.match(/"instruction"\s*:\s*"((?:[^"\\]|\\.)*)/);
                const instruction = instMatch ? instMatch[1].replace(/\\n/g, '\\n').replace(/\\"/g, '"') : '';
                
                newPrepSteps.push({
                    ingredient: ingredient,
                    instruction: instruction
                });
            }
            this.prepSteps = newPrepSteps;

            const phaseMatches = [...this.rawStreamText.matchAll(/"type"\s*:\s*"phase"(.*?)(?=\{\s*"type"|\]|$)/gs)];
            let newSteps = [];
            for (let i = 0; i < phaseMatches.length; i++) {
                const text = phaseMatches[i][0];
                const stepNumMatch = text.match(/"step_number"\s*:\s*(\d+)/);
                if (!stepNumMatch) continue;
                
                const stepNum = parseInt(stepNumMatch[1]);
                const nameMatch = text.match(/"name"\s*:\s*"((?:[^"\\]|\\.)*)/);
                const name = nameMatch ? nameMatch[1].replace(/\\n/g, '\\n').replace(/\\"/g, '"') : '';
                
                const instMatch = text.match(/"instruction"\s*:\s*"((?:[^"\\]|\\.)*)/);
                const instruction = instMatch ? instMatch[1].replace(/\\n/g, '\\n').replace(/\\"/g, '"') : '';
                
                const timeMatch = text.match(/"time_estimate_sec"\s*:\s*(\d+)/);
                const timeSec = timeMatch ? parseInt(timeMatch[1]) : 0;
                
                newSteps.push({
                    key: 'step_' + stepNum + '_' + i,
                    step_number: stepNum,
                    name: name,
                    desc: instruction,
                    duration_sec: timeSec,
                    is_mix: false,
                    is_knead: false
                });
            }
            this.steps = newSteps;

            const ingredientMatches = [...this.rawStreamText.matchAll(/"type"\s*:\s*"ingredient"(.*?)(?=\{\s*"type"|\]|$)/gs)];
            let newIngredients = [];
            for (let i = 0; i < ingredientMatches.length; i++) {
                const text = ingredientMatches[i][0];
                const nameMatch = text.match(/"name"\s*:\s*"((?:[^"\\]|\\.)*)/);
                if (!nameMatch) continue;
                const name = nameMatch[1].replace(/\\n/g, '\\n').replace(/\\"/g, '"');
                
                const catMatch = text.match(/"category"\s*:\s*"((?:[^"\\]|\\.)*)/);
                const category = catMatch ? catMatch[1].replace(/\\n/g, '\\n').replace(/\\"/g, '"') : 'Other';

                const weightMatch = text.match(/"weight_grams"\s*:\s*([\d.]+)/);
                const weight_grams = weightMatch ? parseFloat(weightMatch[1]) : 0;

                const pctMatch = text.match(/"bakers_percentage"\s*:\s*([\d.]+)/);
                const bakers_percentage = pctMatch ? parseFloat(pctMatch[1]) : 0;

                newIngredients.push({
                    name: name,
                    category: category,
                    weight_grams: weight_grams,
                    bakers_percentage: bakers_percentage
                });
            }
            this.recipeIngredients = newIngredients;
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
        
        wakeLock: null,
        
        async requestWakeLock() {
            if (document.documentElement.dataset.keepAwake === 'true' && 'wakeLock' in navigator) {
                try {
                    this.wakeLock = await navigator.wakeLock.request('screen');
                    console.log('Wake Lock is active');
                } catch (err) {
                    console.error(`${err.name}, ${err.message}`);
                }
            }
        },
        
        releaseWakeLock() {
            if (this.wakeLock !== null) {
                this.wakeLock.release()
                    .then(() => {
                        this.wakeLock = null;
                        console.log('Wake Lock released');
                    });
            }
        },
        ingredientWeights: {},
        checkedIngredients: {},

        toggleIngredient(name) {
            if (this.checkedIngredients[name]) {
                this.checkedIngredients[name] = false;
            } else {
                this.checkedIngredients[name] = true;
            }
        },

        startCountertopMode() {
            this.countertopMode = true;
            this.currentStepIndex = 0;
            this.requestWakeLock();
            if(this.steps.length > 0) {
                this.stepTimeRemaining = this.steps[0].duration_sec;
                this.startTimer();
            }
        },
        
        // Inherit all methods from original actions.js
        startTimer() {
            this.timerRunning = true;
            if(this.timerInterval) clearInterval(this.timerInterval);
            this.timerInterval = setInterval(() => {
                if(this.stepTimeRemaining > 0) {
                    this.stepTimeRemaining--;
                } else {
                    clearInterval(this.timerInterval);
                    this.timerRunning = false;
                    this.isAlarm = true;
                    this.playAlarm();
                }
            }, 1000);
        },
        pauseTimer() {
            this.timerRunning = false;
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
                this.releaseWakeLock();
            }
        },
        prevStep() {
            this.stopAlarm();
            if(this.currentStepIndex > 0) {
                this.currentStepIndex--;
                this.stepTimeRemaining = this.steps[this.currentStepIndex].duration_sec;
                this.startTimer();
            }
        },
        playAlarm() {
            if (document.documentElement.dataset.audioAlerts === 'true') {
                try {
                    const ctx = new (window.AudioContext || window.webkitAudioContext)();
                    const osc = ctx.createOscillator();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(880, ctx.currentTime);
                    osc.connect(ctx.destination);
                    osc.start();
                    osc.stop(ctx.currentTime + 0.5);
                } catch (e) {
                    console.error("Audio playback failed", e);
                }
            }
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
        const baseUrl = `/generate-creativity-recipes/?engine_id=${encodeURIComponent(category_slug)}&active_archetype_id=${encodeURIComponent(archetype_id)}&inventory_ids=${encodeURIComponent(inventory_ids)}`;
        
        let recipesLevel1 = [];
        let recipesLevel2 = [];
        
        const updateUI = () => {
            this.creativity_recipes = [...recipesLevel1, ...recipesLevel2];
        };

        const fetchLevel = async (level) => {
            const url = `${baseUrl}&level=${level}`;
            try {
                const res = await fetch(url, { signal });
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
                        if (line.startsWith('event: close')) {
                            // close event
                        } else if (line.startsWith('data: ')) {
                            const dataStr = line.substring(6).trim();
                            if (dataStr && dataStr !== '{}') {
                                try {
                                    const parsed = JSON.parse(dataStr);
                                    if (typeof parsed === 'string') {
                                        rawBuffer += parsed;
                                        const objects = this.extractPartialObjects(rawBuffer);
                                        
                                        const newRecipes = [];
                                        const targetArray = level === 1 ? recipesLevel1 : recipesLevel2;
                                        
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
                                                if (targetArray[i]) {
                                                    newRecipes.push(targetArray[i]);
                                                }
                                            }
                                        }
                                        
                                        if (level === 1) {
                                            recipesLevel1 = newRecipes;
                                        } else {
                                            recipesLevel2 = newRecipes;
                                        }
                                        
                                        updateUI();
                                    }
                                } catch (e) {
                                    console.error('Error parsing chunk', e);
                                }
                            }
                        }
                    }
                }
            } catch (err) {
                if (err.name !== 'AbortError') {
                    console.error(`Error fetching creativity recipes level ${level}:`, err);
                }
            }
        };

        // Fire both levels simultaneously
        Promise.all([fetchLevel(1), fetchLevel(2)]).then(() => {
            this.creativity_streaming = false;
            // Clean up abort controller if completed normally
            if (this.creativityRecipesAbortController && !this.creativityRecipesAbortController.signal.aborted) {
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
