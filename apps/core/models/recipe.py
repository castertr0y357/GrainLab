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

    @property
    def display_category(self):
        from apps.core.models import DoughCategory
        try:
            return DoughCategory.objects.get(slug=self.category_slug).name
        except Exception:
            return self.category_slug.replace('-', ' ').replace('_', ' ').title()

    @property
    def category_icon(self):
        icons = {
            'lean-crusty': '🌾',
            'enriched-soft': '🍞',
            'alkaline-bath': '🥨',
            'flatbreads-griddles': '🫓',
            'quick-breads-scones': '🧁',
            'cakes-batters': '🥞',
            'pastry-lamination': '🥐',
            'choux-paste': '🥯',
            'cookies-shortbread': '🍪',
            'fried-doughs': '🍩',
            'fresh-pasta-noodles': '🍝',
        }
        return icons.get(self.category_slug, '🍞')

    @property
    def display_archetype(self):
        from apps.core.engines.router import get_engine_for_preset
        engine = get_engine_for_preset(None, self.category_slug)
        if engine and hasattr(engine, 'archetypes'):
            arch = engine.archetypes.get(self.archetype_slug)
            if arch and 'label' in arch:
                return arch['label']
        return self.archetype_slug.replace('-', ' ').replace('_', ' ').title()

    @property
    def archetype_icon(self):
        from apps.core.engines.router import get_engine_for_preset
        engine = get_engine_for_preset(None, self.category_slug)
        if engine and hasattr(engine, 'archetypes'):
            arch = engine.archetypes.get(self.archetype_slug)
            if arch and 'icon' in arch:
                return arch['icon']
        return '🧬'
