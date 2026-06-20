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
]
