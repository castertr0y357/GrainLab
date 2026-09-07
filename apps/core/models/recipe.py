import uuid

from django.conf import settings
from django.db import models

from .base import SoftDeleteModel


class SavedRecipe(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, help_text="e.g. 'My Sourdough Boule'")

    # Core categorization
    category = models.ForeignKey(
        "core.DoughCategory", on_delete=models.SET_NULL, null=True, blank=True, related_name="recipes"
    )
    archetype_slug = models.CharField(max_length=100)

    # State storage
    configuration_state = models.JSONField(help_text="The session state dictionary used to calculate this formula")
    compiled_data = models.JSONField(help_text="The final output of calculate_final_recipe(state)")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def display_category(self):
        if self.category:
            return self.category.name
        return "Unknown"

    @property
    def category_icon(self):
        if self.category and self.category.icon:
            return self.category.icon
        return "🍞"

    @property
    def display_archetype(self):
        from apps.core.engines.router import get_engine_for_preset

        cat_slug = self.category.slug if self.category else None
        engine = get_engine_for_preset(None, cat_slug)
        if engine and hasattr(engine, "archetypes"):
            arch = engine.archetypes.get(self.archetype_slug)
            if arch and "label" in arch:
                return arch["label"]
        return self.archetype_slug.replace("-", " ").replace("_", " ").title()

    @property
    def archetype_icon(self):
        from apps.core.engines.router import get_engine_for_preset

        cat_slug = self.category.slug if self.category else None
        engine = get_engine_for_preset(None, cat_slug)
        if engine and hasattr(engine, "archetypes"):
            arch = engine.archetypes.get(self.archetype_slug)
            if arch and "icon" in arch:
                return arch["icon"]
        return "🧬"
