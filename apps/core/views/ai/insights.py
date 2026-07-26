import logging
import math
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views import View

from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting, WheatBerry, Equipment, BackgroundTask
from apps.core import bakers_math
from apps.core import gemma
from apps.core.views.tasks import run_async_task, ai_analyze_wheat_berry_task, ai_analyze_equipment_task, bulk_ai_analyze_task, redo_ai_analysis_task
from apps.core.views.ai.advisory import get_inactive_grain_recommendations

logger = logging.getLogger("grainlab.views")
executor = ThreadPoolExecutor(max_workers=2)


class AiSidebarInsightView(View):
    def get(self, request):
        """
        Returns dynamic labor ROI and critique analysis for the hovered element.
        """
        from django.http import JsonResponse
        from apps.core import gemma
    
        element = request.GET.get("element", "").strip()
        category_slug = request.GET.get("category_slug", "").strip()
        preset_slug = request.GET.get("preset_slug", "").strip()
        active_archetype_id = request.GET.get("active_archetype_id", "").strip() or None
    
        if not element:
            return JsonResponse({
                "labor_roi": "Low Priority / Minor Textural Return",
                "last_10_percent_analysis": "Hover over any ingredient or control setting on the left to see objective science and AI magic diagnostics."
            })
        
        # Determine the category group to guarantee recipe-aware fallback diagnostics
        if category_slug in ['lean-crusty', 'enriched-soft', 'alkaline-bath', 'flatbreads-griddles', 'fried-doughs']:
            group = "bread"
        elif category_slug in ['quick-breads-scones', 'cakes-batters', 'pastry-lamination', 'cookies-shortbread', 'choux-paste']:
            group = "sweet_tender"
        elif category_slug in ['fresh-pasta-noodles']:
            group = "pasta"
        else:
            group = "bread"
        
        # Recipe-aware python local fallback dictionary definition
        fallbacks = {}
    
        if group == "bread":
            fallbacks = {
                "refined": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Commercial refined flour handles consistently without requiring hydration shifts. However, it lacks the deep, nutty cellular flavor matrix of fresh-milled grain."
                },
                "milled": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Fresh-milled whole grains possess active wheat germ oils and enzymes that elevate flavor profiles and crust blister complexes. Adjust hydration dynamically to accommodate increased bran absorption."
                },
                "grain_hard_red_spring": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Spring wheat brings massive gluten elasticity and gas holding power to hearth baking, ensuring a high-rise open crumb. Highly worth milling fresh for rustic breads."
                },
                "grain_hard_red_winter": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "An all-purpose workhorse hard wheat. Good balance of elasticity and extensibility, but lacks the high-torque ceiling of spring varieties."
                },
                "grain_soft_white": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Soft white wheat lacks the gluten strength needed to support high-rising loaves. Using it will result in a flat, dense bake with poor gas retention."
                },
                "grain_hard_white": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Provides strong structure without the bitter tannin flavors of red wheats. Useful if you want mild flavor with high lift."
                },
                "grain_spelt": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Ancient grain that injects deep nutty flavor and high extensibility. Restrict mechanical energy to avoid collapsing its fragile gluten bonds."
                },
                "grain_kamut": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Ancient Khorasan wheat adds a rich golden color and sweet flavor. Absorbs liquid slowly, demanding patience during mixing."
                },
                "grain_rye": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Savory rye grass grain that introduces high pentosans and complex earthy sweetness. Expect sticky handling and a tight, moist crumb."
                },
                "stand_mixer": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Develops gluten rapidly but introduces planetary friction heat. A machine can easily handle this step, but watch internal temperatures."
                },
                "bread_machine": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Enclosed, high-friction kneader. Convenient for zero-effort development but risks over-warming yeast and restricting airy rise."
                },
                "food_processor": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Intense blade shearing forces rapid hydration and gluten alignment. Great for quick buns, but easy to over-mix."
                },
                "hand_beaters": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not recommended. Lacks the torque required for heavy yeast doughs, risking motor burnout."
                },
                "whisk": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Useful only for pre-mixing liquid starters or hydrating flour during autolyse. Lacks the structure to knead."
                },
                "spatula_bowl": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Ideal for initial ingredient incorporation and dynamic stretch-and-folds during bulk fermentation."
                },
                "knead": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Kneading develops the structural gluten matrix needed to trap gas and support oven spring. Highly worth the effort for crusty loaves."
                },
                "cream": {
                    "labor_roi": "Low Priority / Sub-Optimal Selection",
                    "last_10_percent_analysis": "Rarely used, except for certain sweet brioches. In bread, we want gluten development first, not fat encapsulation."
                },
                "fold": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Gentle folding layers the dough and develops structure without degassing. Crucial for retaining large, irregular open crumb cells."
                },
                "cut_in": {
                    "labor_roi": "Low Priority / Sub-Optimal Selection",
                    "last_10_percent_analysis": "Occasionally used in laminated brioche. In normal bread, fat is kneaded in as soft butter rather than cut in."
                },
                "sheet": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Used in laminated croissants and danishes to layer butter. For general breads, sheeting is avoided to preserve crumb aeration."
                },
                "extrude": {
                    "labor_roi": "Low Priority / Sub-Optimal Selection",
                    "last_10_percent_analysis": "Not used. Breads are shaped manually or portioned to preserve the delicate, fermented cell structure."
                },
                "ambient": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Countertop proofing provides a steady, natural rise at room temperature. Safe and consistent, requiring minimal intervention."
                },
                "mat": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "A heated mat speeds up yeast activity by warming the bowl bottom. Saves time but can result in uneven fermentation temperatures."
                },
                "box": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Warm, humid enclosed chamber prevents the dough surface from drying out. Ensures a uniform rise and excellent crust browning."
                },
                "refrigerator": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Cold retardation solidifies butter fats and allows active enzymes to release sugars. Essential for creating complex flavors and deep blisters."
                },
                "bench_rest": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Relaxing the gluten matrix prevents dough from snapping back during final shaping, guaranteeing uniform size and structure."
                },
                "cast-iron-dutch-oven": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Retains intense heat and traps steam released from the dough. Ensures optimal starch gelatinization and maximum oven spring."
                },
                "open-baking-stone-steel": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Transfers heat instantly to the bottom of the dough. Crucial for a crisp bottom crust and rapid gas expansion in hearth loaves."
                },
                "standard-9x5-pan": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Forces the dough to rise vertically by restricting lateral expansion. Great for soft sandwich breads, but has low structural ROI."
                },
                "perforated-baking-sheet": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Enables even heat circulation and steam escape around portioned dough, forming the signature shiny crust of bagels and pretzels."
                },
                            "sifted_high_extraction_flour": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Sifting removes the sharp, fibrous bran particles that slice through delicate gluten strands. Essential for achieving a lighter, more open artisan crumb structure at the cost of some fiber."
                },
                "whole_grain_unsifted_flour": {
                    "labor_roi": "Standard Baseline",
                    "last_10_percent_analysis": "Leaving the bran in maximizes nutritional yield and provides a rustic, hearty texture. Note that the bran will absorb more water and restrict maximum oven spring."
                },
                "sifted_high_extraction_flour": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Sifting out the coarse bran results in a much finer, softer pastry flour. Critical for achieving a meltingly tender crumb in cookies and cakes without gritty mouthfeel."
                },
                "whole_grain_unsifted_flour": {
                    "labor_roi": "Low Priority / Flavor Shift",
                    "last_10_percent_analysis": "Retains all the whole-grain fiber and nutty flavor, but the bran particles can make delicate confections taste dense and gritty."
                },
                "sifted_high_extraction_flour": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Sifting removes the sharp, fibrous bran particles that slice through delicate gluten strands. Essential for achieving a lighter, more open artisan crumb structure at the cost of some fiber."
                },
                "whole_grain_unsifted_flour": {
                    "labor_roi": "Standard Baseline",
                    "last_10_percent_analysis": "Leaving the bran in maximizes nutritional yield and provides a rustic, hearty texture. Note that the bran will absorb more water and restrict maximum oven spring."
                },
"butter": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Adds rich dairy fat to soften the crumb. Reduces gluten tensile strength, yielding a tender, melt-in-the-mouth brioche."
                },
                "unsalted_butter": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Allows precise control over salt while providing dairy fats to tenderize the loaf crumb."
                },
                "salted_butter": {
                    "labor_roi": "Seamless Math Adjustment",
                    "last_10_percent_analysis": "Salted butter detected. The engine has automatically reduced the standalone fine sea salt weight by 1.5% of the total butter mass to maintain perfect flavor balance and prevent over-seasoning your cookie crumb."
                },
                "olive_oil": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Liquid fats coat gluten strands completely, producing an exceptionally extensible dough and a moist, long-lasting tender crumb."
                },
                "canola_oil": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Provides liquid fat to soften the crumb without introducing strong flavors. Useful for everyday sandwich loaves."
                },
                "vegetable_oil": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Softens the crumb structure and extends shelf life by preventing retrogradation (staling)."
                },
                "whole_milk": {
                    "labor_roi": "Sub-Optimal Crumb Shift",
                    "last_10_percent_analysis": "Swapping water for milk introduces lactose and dairy fats to a lean hearth dough. This will cause the crust to brown significantly faster in the oven and will soften the traditional crisp, open-cell artisan chew into a sandwich-style crumb."
                },
                "almond_milk": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Nut proteins and water substitute standard liquid. Lacks the tenderizing fats of dairy milk, yielding a slightly tougher bake."
                },
                "coconut_oil": {
                    "labor_roi": "Low Priority / Flavor Shift",
                    "last_10_percent_analysis": "Coconut oil provides a clean, plant-based solid lipid profile. It solidifies at cooler room temperatures, imparting a faint tropical aroma."
                },
                "avocado_oil": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Avocado oil is a neutral liquid lipid that remains fluid at room temperature. It coats gluten strands completely to produce an incredibly soft, moist, and long-lasting crumb."
                },
                "pure_water": {
                    "labor_roi": "Standard Baseline",
                    "last_10_percent_analysis": "Pure water provides clean, zero-interference hydration. It is the absolute optimal choice for lean hearth loaves to keep the crumb airy and the crust crispy."
                },
                "heavy_cream": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Heavy cream adds immense dairy fat richness (37% fat) and milk sugars. It tenderizes the crumb dramatically, yielding an ultra-soft slice at the cost of some oven rise."
                },
                "buttermilk": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Buttermilk introduces active lactic acidity. This chemically tenderizes the gluten matrix and triggers chemical leavening reactions, yielding an exceptionally tender crumb."
                },
                "none": {
                    "labor_roi": "Standard Baseline",
                    "last_10_percent_analysis": "No binder selected. The recipe relies purely on the gluten network and hydration matrix to establish structural integrity."
                },
                "whole_eggs": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Whole eggs contribute fat, moisture, and lecithin emulsifiers. They bind the structure together and promote rich browning and a soft, custard-like crumb."
                },
                "egg_whites": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Egg whites contribute pure albumin protein and hydration. They dry and solidify during baking, creating a taller, lighter, and crisper crust structure."
                },
                "aquafaba_vegan": {
                    "labor_roi": "Critical Structural Risk",
                    "last_10_percent_analysis": "Choux paste relies completely on the intense protein coagulation and water-binding capacity of whole egg lipids to hold its hollow balloon shape. Substituting a vegan binder here introduces a massive inflation failure risk; the shells will likely collapse into flat discs."
                }
            }
        elif group == "sweet_tender":
            fallbacks = {
                "refined": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Provides highly consistent, low-protein performance. Ideal for ensuring a tender, delicate structure in confections and pastries without gluten toughness."
                },
                "milled": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Adds a rustic, earthy flavor dimension. However, the presence of sharp bran flakes can cut gluten networks and alter fat absorption, requiring careful mixing adjustment."
                },
                "grain_hard_red_spring": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Spring wheat contains excessively strong, elastic gluten. This is not recommended, as it will fight spread and make pastries tough and rubbery."
                },
                "grain_hard_red_winter": {
                    "labor_roi": "Low Priority / Sub-Optimal Selection",
                    "last_10_percent_analysis": "Moderate protein content can lead to gluten toughness if over-mixed. Best reserved for bread systems rather than tender confections."
                },
                "grain_soft_white": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Soft white wheat delivers an exceptionally tender crumb for cookies and pastries by avoiding gluten toughness. Critical for achieving melting spread."
                },
                "grain_hard_white": {
                    "labor_roi": "Low Priority / Sub-Optimal Selection",
                    "last_10_percent_analysis": "Offers a mild flavor but possesses moderate gluten strength. Can toughen cookies and cakes if the mixing is not carefully controlled."
                },
                "grain_spelt": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Ancient grain with highly extensible, soft gluten. Excellent for tender tarts and cookies, adding a nutty sweetness without rubbery toughness."
                },
                "grain_kamut": {
                    "labor_roi": "Low Priority / Sub-Optimal Selection",
                    "last_10_percent_analysis": "Extremely hard grain that resists moisture absorption. Its high protein content can make pastries too dense and chewy."
                },
                "grain_rye": {
                    "labor_roi": "High Priority / Flavor Enhancement Opportunity",
                    "last_10_percent_analysis": "Brings dark, spiced flavor notes to shortbreads and cookies. Lacks gluten-forming proteins, ensuring a highly short and tender bite."
                },
                "stand_mixer": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Ideal for creaming butter and sugar, or whipping egg whites to aerate batters. Watch speeds to prevent over-mixing once flour is added."
                },
                "bread_machine": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not recommended. Enclosed heating and harsh paddle action will over-knead delicate batters, yielding a rubbery, tough texture."
                },
                "food_processor": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Excellent for cutting cold fat into flour for pie crusts or biscuits. Blade action creates distinct fat pockets before gluten forms."
                },
                "hand_beaters": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Light whipping beaters are perfect for aerating eggs and creamed fat. A machine is highly recommended here to build micro-bubbles."
                },
                "whisk": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Manual whisking is perfect for aerating pancake or cake batters. Requires minimal physical effort while keeping gluten development low."
                },
                "spatula_bowl": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Zero-friction manual mixing is critical for delicate batters. Using a hand spatula prevents gluten development, preserving short tenderness."
                },
                "knead": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not recommended for tender confections. Kneading develops gluten, which destroys the melting tenderness of cookies and cakes."
                },
                "cream": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Creaming traps microscopic air bubbles inside the fat phase, creating the tender crumb of cookies and cakes. Essential for proper rise."
                },
                "fold": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Used to incorporate whipped egg whites or delicate dry ingredients into batters without collapsing the trapped air pocket bubbles."
                },
                "cut_in": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Distributing cold fat pieces throughout dry flour creates flat butter pockets. Crucial for baking flaky, laminated scone and pastry layers."
                },
                "sheet": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Aligns fats and dough sheets in puff pastry and croissants, driving steam-lift lamination. Keep cold to prevent fat melting."
                },
                "extrude": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Used for spritz cookies or piped pastries (choux). Assures uniform portioning while avoiding structural handling."
                },
                "ambient": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Ideal for resting cookie dough briefly or bringing cake ingredients to room temp to optimize emulsion stability."
                },
                "mat": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not recommended. Heat will melt solid fats (butter/shortening) prematurely, ruining the structure of cookies and pastries."
                },
                "box": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Used for yeast-raised donuts or danishes. Humid warmth allows yeast expansion without forming a dry surface skin."
                },
                "refrigerator": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Resting cookie or pastry dough solidifies butter fats and hydrates starch. Crucial for controlling cookie spread and preventing pastry shrinkage."
                },
                "bench_rest": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Allows gluten developed during mixing to relax, ensuring cookies spread evenly and pastries roll out without shrinking."
                },
                "cast-iron-dutch-oven": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not recommended. Enclosed high-heat environment will scorch sugar-rich confections and ruin delicate pastries."
                },
                "open-baking-stone-steel": {
                    "labor_roi": "Low Priority / Sub-Optimal Selection",
                    "last_10_percent_analysis": "Useful for cookies or flat pastries if lined with parchment, but direct steel contact can burn bottom sugars rapidly."
                },
                "standard-9x5-pan": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Excellent for quick breads and pound cakes. Provides structured vertical support for heavy batters."
                },
                "perforated-baking-sheet": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Excellent for delicate macarons or eclairs, letting heat distribute evenly to dry out shells without warping."
                },
                            "sifted_high_extraction_flour": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Sifting out the coarse bran results in a much finer, softer pastry flour. Critical for achieving a meltingly tender crumb in cookies and cakes without gritty mouthfeel."
                },
                "whole_grain_unsifted_flour": {
                    "labor_roi": "Low Priority / Flavor Shift",
                    "last_10_percent_analysis": "Retains all the whole-grain fiber and nutty flavor, but the bran particles can make delicate confections taste dense and gritty."
                },
"butter": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Solid butter contains 18% water, which turns to steam and creates tiny layers during baking. Crucial for a flaky, melting texture."
                },
                "unsalted_butter": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Unsalted solid butter allows precise control over salt while providing emulsified dairy fats for a tender crumb."
                },
                "salted_butter": {
                    "labor_roi": "Seamless Math Adjustment",
                    "last_10_percent_analysis": "Salted butter detected. The engine has automatically reduced the standalone fine sea salt weight by 1.5% of the total butter mass to maintain perfect flavor balance and prevent over-seasoning your cookie crumb."
                },
                "olive_oil": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Brings a fruity, savory note to specialized olive oil cakes and shortbreads. Keeps the crumb extremely moist."
                },
                "canola_oil": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Provides pure liquid fat to tenderize dough without contributing any flavor. Great for neutral cakes or flatbreads."
                },
                "vegetable_oil": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Neutral liquid fat that remains fluid at room temp, keeping the baked crumb soft and preventing dryness."
                },
                "whole_milk": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Adds fat, sugar, and moisture to balance cake batters. Lactose promotes beautiful caramelization and crust color."
                },
                "almond_milk": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Acts as a dairy-free liquid substitute. Lacks milk fats, yielding a slightly drier and more open crumb."
                },
                "coconut_oil": {
                    "labor_roi": "Low Priority / Flavor Shift",
                    "last_10_percent_analysis": "Coconut oil provides a clean, plant-based solid lipid profile. It solidifies at cooler room temperatures, imparting a faint tropical aroma."
                },
                "avocado_oil": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Avocado oil is a neutral liquid lipid that remains fluid at room temperature. It coats gluten strands completely to produce an incredibly soft, moist, and long-lasting crumb."
                },
                "pure_water": {
                    "labor_roi": "Standard Baseline",
                    "last_10_percent_analysis": "Pure water provides clean, zero-interference hydration. It is the absolute optimal choice for lean hearth loaves to keep the crumb airy and the crust crispy."
                },
                "heavy_cream": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Heavy cream adds immense dairy fat richness (37% fat) and milk sugars. It tenderizes the crumb dramatically, yielding an ultra-soft slice at the cost of some oven rise."
                },
                "buttermilk": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Buttermilk introduces active lactic acidity. This chemically tenderizes the gluten matrix and triggers chemical leavening reactions, yielding an exceptionally tender crumb."
                },
                "none": {
                    "labor_roi": "Standard Baseline",
                    "last_10_percent_analysis": "No binder selected. The recipe relies purely on the gluten network and hydration matrix to establish structural integrity."
                },
                "whole_eggs": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Whole eggs contribute fat, moisture, and lecithin emulsifiers. They bind the structure together and promote rich browning and a soft, custard-like crumb."
                },
                "egg_whites": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Egg whites contribute pure albumin protein and hydration. They dry and solidify during baking, creating a taller, lighter, and crisper crust structure."
                },
                "aquafaba_vegan": {
                    "labor_roi": "Critical Structural Risk",
                    "last_10_percent_analysis": "Choux paste relies completely on the intense protein coagulation and water-binding capacity of whole egg lipids to hold its hollow balloon shape. Substituting a vegan binder here introduces a massive inflation failure risk; the shells will likely collapse into flat discs."
                }
            }
        elif group == "pasta":
            fallbacks = {
                "refined": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Allows smooth, uniform extrusion and dough sheet alignment. Provides a clean, bright appearance for fresh pasta."
                },
                "milled": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Produces a rustic whole-grain noodle with high mineral tooth (al dente). Requires extra resting time to allow complete bran hydration before sheeting."
                },
                "grain_hard_red_spring": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Hard spring wheat provides good tensile strength for noodles, but can be too elastic for rolling thin pasta sheets without snapping back."
                },
                "grain_hard_red_winter": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Good all-purpose option. Provides reasonable structural integrity for fresh noodles without making the dough too difficult to roll."
                },
                "grain_soft_white": {
                    "labor_roi": "Low Priority / Sub-Optimal Selection",
                    "last_10_percent_analysis": "Soft wheat lacks the structural resilience needed for al dente pasta, causing the noodles to become mushy when boiled."
                },
                "grain_hard_white": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Good structural candidate. Yields clean, pale noodles with high breaking strength and excellent chew."
                },
                "grain_spelt": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Produces a delicate, nutty specialty pasta. Requires minimal handling and rolling to prevent tearing the weak gluten structure."
                },
                "grain_kamut": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Golden ancient grain closely related to durum. Imparts a bright yellow hue, high tensile strength, and a sweet, buttery bite to pasta."
                },
                "grain_rye": {
                    "labor_roi": "Low Priority / Sub-Optimal Selection",
                    "last_10_percent_analysis": "High pentosan content makes pasta dough extremely sticky and brittle. Best blended in small fractions (under 15%) for rustic noodles."
                },
                "stand_mixer": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Efficiently forces moisture into dense semolina/egg dough. Excellent for initial compaction before hand kneading."
                },
                "bread_machine": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Can be used to mix pasta dough, but the motor will struggle with the extremely low hydration required for noodles."
                },
                "food_processor": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Combines flour and liquid in seconds. The fast spinning blade mimics high pressure compaction, perfect for pasta dough preparation."
                },
                "hand_beaters": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not recommended. Lacks the torque to mix dense, dry pasta dough."
                },
                "whisk": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Useful for beating eggs into a well of flour before incorporating, but cannot handle mixing the final dough."
                },
                "spatula_bowl": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Useful for initial dough clean-up and gathering scrap flour before tipping onto the bench for hand kneading."
                },
                "knead": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Essential step. Heavy hand-kneading aligns gluten proteins under tension, giving the noodle its resilient al dente snap."
                },
                "cream": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not used. Fat in pasta is typically egg yolks or oil mixed directly into the flour, not creamed."
                },
                "fold": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Folding during rolling layers the dough, aligning the proteins uniformly for a smooth, tear-free sheet."
                },
                "cut_in": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not used. Pasta relies on uniform hydration rather than solid fat pockets."
                },
                "sheet": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Repeated passing through rollers aligns gluten strands and egg proteins, yielding a smooth, thin noodle that holds its shape when boiled."
                },
                "extrude": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Forcing dense dough through shaped dies under pressure. Commercial brass dies yield a rougher sauce-binding noodle surface."
                },
                "ambient": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Allows gluten strands to relax at room temp, making the dough highly extensible and easy to roll out."
                },
                "mat": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Warm environments are unnecessary; pasta contains no yeast and heat can dry out the dough, making it brittle."
                },
                "box": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not recommended. Excess humidity makes pasta sticky and difficult to sheet."
                },
                "refrigerator": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Useful for resting pasta dough overnight if needed, but wrap tightly to prevent drying out and graying from oxidation."
                },
                "bench_rest": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Crucial 30-minute rest allows the flour to hydrate fully and the gluten to relax, making sheeting effortless without snapping."
                },
                "cast-iron-dutch-oven": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not used. Pasta is boiled in a pot, not baked in a dutch oven."
                },
                "open-baking-stone-steel": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not used."
                },
                "standard-9x5-pan": {
                    "labor_roi": "Low Priority / Dangerous Structural Choice",
                    "last_10_percent_analysis": "Not used."
                },
                "perforated-baking-sheet": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Used occasionally for drying cut noodles to prevent condensation buildup."
                },
                            "sifted_high_extraction_flour": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Sifting creates a smooth, silky pasta dough that is much easier to sheet thinly without tearing."
                },
                "whole_grain_unsifted_flour": {
                    "labor_roi": "Low Priority / Sub-Optimal Selection",
                    "last_10_percent_analysis": "Whole bran particles can cause the pasta sheet to tear easily when rolled thin, resulting in a rough, overly rustic noodle."
                },
"butter": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Occasionally added to filled pasta doughs for richness, but typically not a standard sheeting ingredient."
                },
                "unsalted_butter": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Not a standard pasta component; fat is typically provided by egg yolks."
                },
                "salted_butter": {
                    "labor_roi": "Seamless Math Adjustment",
                    "last_10_percent_analysis": "Salted butter detected. The engine has automatically reduced the standalone fine sea salt weight by 1.5% of the total butter mass to maintain perfect flavor balance and prevent over-seasoning your cookie crumb."
                },
                "olive_oil": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "A classic addition. Enhances dough extensibility, making hand-sheeting easier and adding a subtle sheen to noodles."
                },
                "canola_oil": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Rarely used; olive oil is preferred for its flavor affinity."
                },
                "vegetable_oil": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Rarely used."
                },
                "whole_milk": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Rarely used; eggs provide the required liquid phase."
                },
                "almond_milk": {
                    "labor_roi": "Low Priority / Minor Textural Return",
                    "last_10_percent_analysis": "Not used."
                },
                "coconut_oil": {
                    "labor_roi": "Low Priority / Flavor Shift",
                    "last_10_percent_analysis": "Coconut oil provides a clean, plant-based solid lipid profile. It solidifies at cooler room temperatures, imparting a faint tropical aroma."
                },
                "avocado_oil": {
                    "labor_roi": "Low Priority / Effortless Texture Shift",
                    "last_10_percent_analysis": "Avocado oil is a neutral liquid lipid that remains fluid at room temperature. It coats gluten strands completely to produce an incredibly soft, moist, and long-lasting crumb."
                },
                "pure_water": {
                    "labor_roi": "Standard Baseline",
                    "last_10_percent_analysis": "Pure water provides clean, zero-interference hydration. It is the optimal choice for lean hearth loaves to keep the crumb airy and the crust crispy."
                },
                "heavy_cream": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Heavy cream adds immense dairy fat richness (37% fat) and milk sugars. It tenderizes the crumb dramatically, yielding an ultra-soft slice at the cost of some oven rise."
                },
                "buttermilk": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Buttermilk introduces active lactic acidity. This chemically tenderizes the gluten matrix and triggers chemical leavening reactions, yielding an exceptionally tender crumb."
                },
                "none": {
                    "labor_roi": "Standard Baseline",
                    "last_10_percent_analysis": "No binder selected. The recipe relies purely on the gluten network and hydration matrix to establish structural integrity."
                },
                "whole_eggs": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Whole eggs contribute fat, moisture, and lecithin emulsifiers. They bind the structure together and promote rich browning and a soft, custard-like crumb."
                },
                "egg_whites": {
                    "labor_roi": "High Priority / Worth the Extra Step",
                    "last_10_percent_analysis": "Egg whites contribute pure albumin protein and hydration. They dry and solidify during baking, creating a taller, lighter, and crisper crust structure."
                },
                "aquafaba_vegan": {
                    "labor_roi": "Critical Structural Risk",
                    "last_10_percent_analysis": "Choux paste relies completely on the intense protein coagulation and water-binding capacity of whole egg lipids to hold its hollow balloon shape. Substituting a vegan binder here introduces a massive inflation failure risk; the shells will likely collapse into flat discs."
                }
            }
    
        # Try querying Gemma if AI is active and enabled
        ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"
        insight = None
        if ai_enabled:
            try:
                insight = gemma.get_sidebar_insight_ai(element, category_slug, preset_slug)
            except Exception as e:
                logger.error(f"[AI] - Sidebar - Failed querying Gemma: {e}")
            
        if not insight:
            # Fall back to our clean recipe-aware local dictionary mapping
            # 1. First, check if it's a grain (only if AI is NOT enabled, to prevent applying algorithmic rules)
            if not ai_enabled and element.startswith("grain_"):
                from apps.core.models import WheatBerry, BreadPreset
                from grainlab.engines import router
                from apps.core.gemma import evaluate_single_grain

                preset = BreadPreset.objects.filter(slug=preset_slug).first() if preset_slug else None
                category_slug = category_slug or (preset.dough_category.slug if preset and preset.dough_category else None)
            
                try:
                    engine = router.get_engine_for_preset(preset_slug, category_slug)
                except Exception:
                    engine = None
                
                if engine:
                    # Find the hovered grain in DB (active or inactive)
                    grain_obj = None
                    for wb in WheatBerry.all_objects.filter(deleted_at__isnull=True):
                        import re
                        wb_slug = "grain_" + re.sub(r'[^a-z0-9]', '_', wb.name.lower())
                        if wb_slug == element or element in wb_slug or wb_slug in element:
                            grain_obj = wb
                            break
                        
                    if grain_obj:
                        res = evaluate_single_grain(grain_obj, engine, preset_slug=preset_slug)
                        # Determine labor_roi based on tier
                        if res["tier"] == "recommended":
                            roi = "High Priority / Flavor Enhancement Opportunity"
                        elif res["tier"] == "sub-optimal":
                            roi = "Low Priority / Minor Textural Return"
                        else:
                            roi = "Low Priority / Dangerous Structural Choice"
                        
                        insight = {
                            "recommendation_tier": res["tier"],
                            "labor_roi": roi,
                            "last_10_percent_analysis": res["reasoning"]
                        }
                    
            # 2. If not a grain, or not resolved, look up in the static fallbacks
            if not insight:
                insight = fallbacks.get(element)
                if not insight and element.startswith("grain_"):
                    # fallback for matching similar keys
                    for k, val in fallbacks.items():
                        if k.startswith("grain_") and (k in element or element in k):
                            insight = val
                            break
                if insight:
                    # Copy fallback to customize
                    insight = dict(insight)
                    # Map dynamic recommendation_tier based on labor_roi
                    roi_lower = insight.get("labor_roi", "").lower()
                    if "dangerous" in roi_lower or "sub-optimal" in roi_lower or "critical" in roi_lower:
                        insight["recommendation_tier"] = "not-recommended" if "dangerous" in roi_lower or "critical" in roi_lower else "sub-optimal"
                    else:
                        insight["recommendation_tier"] = "recommended"
                else:
                    insight = {
                        "recommendation_tier": "recommended",
                        "labor_roi": "Low Priority / Minor Textural Return",
                        "last_10_percent_analysis": "An objective workspace configuration parameter. No significant performance anomalies or hidden labor opportunities detected."
                    }
                
            # 3. Dynamic out-of-stock grain suggestion (only when AI is NOT enabled)
            if not ai_enabled:
                inactive_recs = get_inactive_grain_recommendations(preset_slug, category_slug, active_archetype_id=active_archetype_id)
                if inactive_recs:
                    # Avoid duplicate recommendations if the hovered element itself is that out-of-stock grain
                    rec = inactive_recs[0]
                    hovered_clean = element.replace("grain_", "").replace("_", " ").lower()
                    if rec["name"].lower() not in hovered_clean:
                        suggestion = f" Since {rec['name']} is currently out of stock, consider acquiring some; its {rec['protein']}% protein profile will enhance flavor and allow for superior texture."
                        analysis = insight.get("last_10_percent_analysis", "")
                        if suggestion not in analysis:
                            insight["last_10_percent_analysis"] = analysis.rstrip() + suggestion
        
        if insight and "elevate_recipe" not in insight:
            insight["elevate_recipe"] = ""
        
        return JsonResponse(insight)


class AiBatchInsightsView(View):
    def get(self, request):
        from django.http import JsonResponse
        from apps.core import gemma
        import json
        from django.http import HttpRequest
    
        elements_raw = request.GET.get("elements", "[]")
        try:
            elements = json.loads(elements_raw)
        except:
            elements = []
        
        category_slug = request.GET.get("category_slug", "").strip()
        preset_slug = request.GET.get("preset_slug", "").strip()
        active_archetype_id = request.GET.get("active_archetype_id", "").strip() or None
    
        results = {}
    
        for el in elements:
            # Construct mock request to re-use ai_sidebar_insight logic directly
            req = HttpRequest()
            req.GET = {
                "element": el,
                "category_slug": category_slug,
                "preset_slug": preset_slug,
                "active_archetype_id": active_archetype_id or ""
            }
            res = AiSidebarInsightView().get(req)
            try:
                results[el] = json.loads(res.content)
            except Exception as e:
                results[el] = {}
            
        return JsonResponse({"batch_insights": results})


