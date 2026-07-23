import { configData } from './config.js';
import { actions } from './actions.js';

document.addEventListener('alpine:init', () => {
    Alpine.data('calculatorApp', (config) => ({

    current_phase: config.current_phase,
    grain_mode: 'milled',
    selected_master: config.selected_master,
    searchOpen: false,
    query: config.query,
    engines_ff: config.engines_ff,
    enginesArchetypes: config.enginesArchetypes,
    
    global_ai_enabled: config.global_ai_enabled,
    hovered_element: null,
    sidebar_insight_loading: false,
    sidebar_labor_roi: '',
    sidebar_analysis: '',
    sidebar_tier: '',
    sidebar_elevate: '',
    sidebar_menu_description: '',
    selectedRecipeScienceProfile: '',
    selectedRecipeMenuDescription: '',
    selectedRecipeSecondaryIngredients: null,
    
    // Factual science profiles
    factual_dictionary: {
        'refined': 'Store refined commercial flour. High shelf stability and consistent protein levels, but stripped of bran and germ.',
        'milled': 'Freshly milled whole grain. Retains 100% of germ and bran oils. High enzyme activity and complex rustic flavor profile.',
        
        // Grains
        'grain_hard_red_spring': 'High-protein hard wheat. Strong, elastic gluten structure.',
        'grain_hard_red_winter': 'Moderate-high protein wheat. Balanced gluten elasticity and extensibility.',
        'grain_soft_white': 'Low-protein soft wheat. Weak, tender gluten structure.',
        'grain_hard_white': 'Mild, light-colored hard wheat. Structural strength without bitter red wheat tannins.',
        'grain_spelt': 'Ancient hulled wheat species. Extensible but weak gluten strength; water-absorbent.',
        'grain_kamut': 'Ancient Khorasan wheat. High protein, lower elasticity; absorbs water slowly.',
        'grain_rye': 'Ancient rye grass grain. High pentosan concentration and weak gluten strength.',

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
        'ambient': 'Countertop proofing. Relies on local ambient room temperature (70-75┬░F) for steady biological activity.',
        'mat': 'Open heated proofing mat. Warms the bottom of the vessel to accelerate yeast and lactic acid production.',
        'box': 'Warm, humid enclosed proofing chamber. Maximizes biological activity while preventing surface skin drying.',
        'refrigerator': 'Cold retardation (34-40┬░F). Solidifies fats and slows yeast while enzymes continue developing complex sugars.',
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
    
    /* Auto-correction and warning computed on client side */
    presetName: config.presetName,
    presetSlug: config.presetSlug,
    presetModified: false,
    
    advisoryRecommendedName: '',
    advisoryRecommendedReason: '',
    advisoryHighRiskName: '',
    advisoryHighRiskReason: '',
    advisoryLoading: false,
    advisoryLoadingMessage: '',
    phase3Loading: false,
    phase3LoadingMessage: '',
    phase3_generation_steps: [],
    grainEvaluations: [],
    globalElevateRecipe: '',
    advisoryTimeout: null,
    advisoryAbortController: null,
    hoverAbortController: null,
    creativityRecipesAbortController: null,
    recipeDetailsAbortController: null,
    alternativeVariantsAbortController: null,
    
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
    mill_recommendation: null,
    sifted_recommendation: null,
    variant_loading: false,
    hovered_variant: null,
    /* Engine archetypes map keyed by category slug */
    enginesArchetypes: config.enginesArchetypes,

    creativity_recipes: [],
    creativity_loading: false,
    expanded_level: null,
    alternative_variants: [],
    selected_recipe_id: null,
    recipe_selected: config.recipe_selected,
    recipe_details_loading: false,
    recipe_gen_interval: null,
    recipe_details_interval: null,
    recipe_gen_resolved: false,
    recipe_gen_data: null,
    recipe_details_resolved: false,
    recipe_details_data: null,
    recipe_generation_steps: [
        { text: 'Initializing workspace sub-engines...', active: false, completed: false },
        { text: 'Analyzing active whole grain profiles...', active: false, completed: false },
        { text: 'Computing thermodynamic heat margins...', active: false, completed: false },
        { text: 'Calibrating water temperature target...', active: false, completed: false },
        { text: 'Synthesizing custom baker\'s formulas...', active: false, completed: false },
        { text: 'Drafting artisan recipe variants...', active: false, completed: false }
    ],
    recipe_details_steps: [
        { text: 'Deconstructing grain protein specs...', active: false, completed: false },
        { text: 'Simulating starch-lipid hydration...', active: false, completed: false },
        { text: 'Formulating artisanal baking tips...', active: false, completed: false }
    ],
    advisory_resolved: false,
    advisory_interval: null,
    advisory_steps: [
        { text: 'Deconstructing grain protein specs...', active: false, completed: false },
        { text: 'Simulating starch-lipid hydration...', active: false, completed: false },
        { text: 'Formulating artisanal baking tips...', active: false, completed: false }
    ],
        ...configData,
        ...actions
    }));
});
