import uuid
from django.db import models
from .base import SoftDeleteModel

class SavedRecipe(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="e.g. 'My Sourdough Boule'")
    
    # Core categorization
    category_slug = models.CharField(max_length=100)
    archetype_slug = models.CharField(max_length=100)
    
    # State storage
    configuration_state = models.JSONField(help_text="The session state dictionary used to calculate this formula")
    compiled_data = models.JSONField(help_text="The final output of calculate_final_recipe(state)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
