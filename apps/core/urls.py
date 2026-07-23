from django.urls import path
from apps.core import views

urlpatterns = [
    path('', views.CalculatorView.as_view(), name='calculator'),
    path('search/', views.SearchPresetsView.as_view(), name='search_presets'),
    path('load-preset/<int:preset_id>/', views.LoadPresetView.as_view(), name='load_preset'),
    path('calculate/', views.CalculateRecipeAjaxView.as_view(), name='calculate_recipe_ajax'),
    path('settings/', views.SettingsPageView.as_view(), name='settings_page'),
    path('settings/save/', views.SaveSettingsView.as_view(), name='save_settings'),
    path('sourdough-calibrate/', views.SourdoughCalibrateView.as_view(), name='sourdough_calibrate'),
    
    # Inventory routes
    path('inventory/', views.InventoryPageView.as_view(), name='inventory_page'),
    path('inventory/wheat-berry/add/', views.AddWheatBerryView.as_view(), name='add_wheat_berry'),
    path('inventory/wheat-berry/toggle/<uuid:id>/', views.ToggleWheatBerryActiveView.as_view(), name='toggle_wheat_berry_active'),
    path('inventory/wheat-berry/delete/<uuid:id>/', views.DeleteWheatBerryView.as_view(), name='delete_wheat_berry'),
    path('inventory/wheat-berry/analyze/<uuid:id>/', views.AiAnalyzeWheatBerryView.as_view(), name='ai_analyze_wheat_berry'),
    path('inventory/equipment/add/', views.AddEquipmentView.as_view(), name='add_equipment'),
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
]
