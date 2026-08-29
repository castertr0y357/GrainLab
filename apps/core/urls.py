from django.urls import path
from apps.core import views
from apps.core.views.calculator.phase1 import Phase1View
from apps.core.views.calculator.phase2 import Phase2View
from apps.core.views.calculator.phase3 import Phase3View
from apps.core.views.calculator.phase4 import Phase4View
from apps.core.views.calculator.final_recipe import FinalRecipeView, FinalRecipeAIView
from apps.core.views.calculator.shared import save_recipe, shared_recipe

urlpatterns = [
    # Calculator Routes (Phases 1-4)
    path('', Phase1View.as_view(), name='calculator_phase1'),
    path('phase-2/<slug:category>/', Phase2View.as_view(), name='calculator_phase2'),
    path('phase-3/<slug:category>/<slug:archetype>/', Phase3View.as_view(), name='calculator_phase3'),
    path('phase-4/<slug:category>/<slug:archetype>/', Phase4View.as_view(), name='calculator_phase4'),
    path('recipe-final/<slug:category>/<slug:archetype>/', FinalRecipeView.as_view(), name='calculator_final_recipe'),
    path('recipe-final/<slug:category>/<slug:archetype>/ai/', FinalRecipeAIView.as_view(), name='calculator_final_recipe_ai'),
    
    # Formula Sharing Routes
    path('recipe/save/', save_recipe, name='save_recipe'),
    path('recipe/<uuid:recipe_id>/', shared_recipe, name='shared_recipe'),
    
    path('search/', views.SearchPresetsView.as_view(), name='search_presets'),
    path('generate-creative-ideas/', views.GenerateCreativeIdeasView.as_view(), name='generate_creative_ideas'),
    path('load-preset/<int:preset_id>/', views.LoadPresetView.as_view(), name='load_preset'),
    path('settings/', views.SettingsPageView.as_view(), name='settings_page'),
    path('settings/save/', views.SaveSettingsView.as_view(), name='save_settings'),
    path('settings/discover-models/', views.DiscoverModelsView.as_view(), name='discover_models'),
    path('sourdough-calibrate/', views.SourdoughCalibrateView.as_view(), name='sourdough_calibrate'),
    
    # Inventory routes
    path('inventory/', views.InventoryPageView.as_view(), name='inventory_page'),
    path('inventory/wheat-berry/add/', views.AddWheatBerryView.as_view(), name='add_wheat_berry'),
    path('inventory/wheat-berry/edit/<uuid:id>/', views.EditWheatBerryView.as_view(), name='edit_wheat_berry'),
    path('inventory/wheat-berry/toggle/<uuid:id>/', views.ToggleWheatBerryActiveView.as_view(), name='toggle_wheat_berry_active'),
    path('inventory/wheat-berry/delete/<uuid:id>/', views.DeleteWheatBerryView.as_view(), name='delete_wheat_berry'),
    path('inventory/wheat-berry/analyze/<uuid:id>/', views.AiAnalyzeWheatBerryView.as_view(), name='ai_analyze_wheat_berry'),
    path('inventory/equipment/add/', views.AddEquipmentView.as_view(), name='add_equipment'),
    path('inventory/equipment/edit/<uuid:id>/', views.EditEquipmentView.as_view(), name='edit_equipment'),
    path('inventory/equipment/delete/<uuid:id>/', views.DeleteEquipmentView.as_view(), name='delete_equipment'),
    path('inventory/equipment/analyze/<uuid:id>/', views.AiAnalyzeEquipmentView.as_view(), name='ai_analyze_equipment'),
    path('inventory/bulk-analyze/', views.BulkAiAnalyzeView.as_view(), name='bulk_ai_analyze'),
    path('inventory/redo-analyze/<str:item_type>/<uuid:id>/', views.RedoAiAnalysisView.as_view(), name='redo_ai_analysis'),
    path('tasks/status/<uuid:task_id>/', views.TaskStatusView.as_view(), name='task_status'),
    path('ai-grain-advisory/', views.AiGrainAdvisoryView.as_view(), name='ai_grain_advisory'),
    path('ai-sidebar-insight/', views.AiSidebarInsightView.as_view(), name='ai_sidebar_insight'),
    path('ai-batch-insights/', views.AiBatchInsightsView.as_view(), name='ai_batch_insights'),
    path('ai-optimize-shares/', views.AiOptimizeSharesView.as_view(), name='ai_optimize_shares'),
    path('generate-variants/', views.GenerateVariantsView.as_view(), name='generate_variants'),
    path('generate-creativity-recipes/', views.GenerateCreativityRecipesView.as_view(), name='generate_creativity_recipes'),
    path('ai-recipe-details/', views.AiRecipeDetailsView.as_view(), name='ai_recipe_details'),
    path('generate-substitutes/', views.AiGenerateSubstitutesView.as_view(), name='generate_substitutes'),
    path('ai-process-alternatives/', views.AiProcessAlternativesView.as_view(), name='ai_process_alternatives'),
    path('ai-process-details/', views.AiProcessDetailsView.as_view(), name='ai_process_details'),
    path('ai-recipe-percentages/', views.AiRecipePercentagesView.as_view(), name='ai_recipe_percentages'),
    path('ai-recipe-tweaks/', views.AiRecipeTweaksView.as_view(), name='ai_recipe_tweaks'),
    path('ai-apply-tweak/', views.AiApplyTweakView.as_view(), name='ai_apply_tweak'),
]
