from django.views.generic import ListView
from apps.core.models.recipe import SavedRecipe

class RecipeListView(ListView):
    model = SavedRecipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    ordering = ['-created_at']
