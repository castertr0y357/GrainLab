from django.urls import path
from apps.core import views

urlpatterns = [
    path('', views.calculator, name='calculator'),
    path('search/', views.search_presets, name='search_presets'),
    path('load-preset/<int:preset_id>/', views.load_preset, name='load_preset'),
    path('calculate/', views.calculate_recipe_ajax, name='calculate_recipe_ajax'),
    path('settings/', views.settings_page, name='settings_page'),
    path('settings/save/', views.save_settings, name='save_settings'),
    path('sourdough-calibrate/', views.sourdough_calibrate, name='sourdough_calibrate'),
    
    # Inventory routes
    path('inventory/', views.inventory_page, name='inventory_page'),
    path('inventory/wheat-berry/add/', views.add_wheat_berry, name='add_wheat_berry'),
    path('inventory/wheat-berry/toggle/<int:id>/', views.toggle_wheat_berry_active, name='toggle_wheat_berry_active'),
    path('inventory/wheat-berry/delete/<int:id>/', views.delete_wheat_berry, name='delete_wheat_berry'),
    path('inventory/wheat-berry/analyze/<int:id>/', views.ai_analyze_wheat_berry, name='ai_analyze_wheat_berry'),
    path('inventory/equipment/add/', views.add_equipment, name='add_equipment'),
    path('inventory/equipment/delete/<int:id>/', views.delete_equipment, name='delete_equipment'),
    path('inventory/equipment/analyze/<int:id>/', views.ai_analyze_equipment, name='ai_analyze_equipment'),
    path('inventory/bulk-analyze/', views.bulk_ai_analyze, name='bulk_ai_analyze'),
    path('inventory/redo-analyze/<str:item_type>/<int:id>/', views.redo_ai_analysis, name='redo_ai_analysis'),
]
