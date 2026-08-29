from django.db import models

class DoughCategory(models.Model):
    """
    Represents the biological composition (ratios) of the dough.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    base_hydration = models.FloatField(help_text="Water ratio relative to flour (1.0 = 100%)")
    base_fat = models.FloatField(default=0.0, help_text="Fat ratio relative to flour")
    base_sugar = models.FloatField(default=0.0, help_text="Sugar ratio relative to flour")
    base_salt = models.FloatField(default=0.02, help_text="Salt ratio relative to flour")
    base_yeast = models.FloatField(default=0.015, help_text="Yeast ratio relative to flour (if chemically/yeast leavened)")
    base_starter = models.FloatField(default=0.0, help_text="Starter ratio relative to flour (if sourdough)")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Dough Categories"
        indexes = [
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name


class FormFactor(models.Model):
    """
    Represents the physical geometry, portioning, hardware constraints,
    and thermal profile of the bread.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    is_portioned = models.BooleanField(default=False, help_text="True if baked in count-based units rather than a single loaf")
    target_weight = models.FloatField(default=900.0, help_text="Target weight in grams for a single loaf")
    unit_weight = models.FloatField(default=80.0, help_text="Weight in grams for one portioned item")
    default_count = models.IntegerField(default=1, help_text="Default number of portioned items")
    bake_temp_f = models.IntegerField(default=375, help_text="Baking temperature in Fahrenheit")
    bake_time_min = models.IntegerField(default=35, help_text="Baking time in minutes")
    steam_required = models.BooleanField(default=False, help_text="True if steam should be introduced in the oven")
    is_enriched_profile = models.BooleanField(default=False, help_text="Determines if it uses enriched target probe temp (190F) vs lean (205F)")

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name


class BreadPreset(models.Model):
    """
    Stores historical starting points for bread targets.
    """
    class SiftingRequirement(models.TextChoices):
        MANDATORY = 'mandatory', 'Mandatory (High Extraction)'
        OPTIONAL = 'optional', 'Optional (Variable)'
        DISCOURAGED = 'discouraged', 'Discouraged (Whole Grain)'

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    
    # Relationships with explicit indices and deletion behaviors
    dough_category = models.ForeignKey(
        DoughCategory, 
        on_delete=models.CASCADE, 
        db_index=True,
        related_name="presets"
    )
    form_factor = models.ForeignKey(
        FormFactor, 
        on_delete=models.CASCADE, 
        db_index=True,
        related_name="presets"
    )
    
    hydration_override = models.FloatField(null=True, blank=True)
    fat_override = models.FloatField(null=True, blank=True)
    sugar_override = models.FloatField(null=True, blank=True)
    starter_override = models.FloatField(null=True, blank=True)
    
    flour_type_default = models.CharField(max_length=50, default="all_purpose")
    flour_maturity_default = models.CharField(max_length=50, default="matured")

    sifting_requirement = models.CharField(
        max_length=20, 
        choices=SiftingRequirement.choices, 
        default=SiftingRequirement.OPTIONAL, 
        help_text="Defines the structural baseline for bran separation."
    )

    # Classifier coordinates and anchors
    classifier_texture = models.IntegerField(default=50, help_text="0 for Crusty, 100 for Soft")
    classifier_crumb = models.IntegerField(default=50, help_text="0 for Dense, 100 for Open Crumb")
    accessibility_definition = models.TextField(blank=True, help_text="Brief accessibility definition")
    cultural_anchor = models.CharField(max_length=250, blank=True, help_text="Cultural anchor/history")
    crumb_preview = models.CharField(max_length=50, default="Balanced", help_text="Crumb Structure Preview (Open, Balanced, or Even)")

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name
