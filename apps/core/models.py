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


class SystemSetting(models.Model):
    """
    Stores application-level preference toggles and AI configurations.
    """
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['key']),
        ]

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def get_val(cls, key, default=None):
        try:
            obj = cls.objects.get(key=key)
            return obj.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_val(cls, key, val):
        cls.objects.update_or_create(key=key, defaults={'value': str(val)})


class WheatBerry(models.Model):
    """
    Represents the wheat berries in the home baker's inventory.
    """
    HARDNESS_CHOICES = [
        ('hard', 'Hard'),
        ('soft', 'Soft'),
        ('durum', 'Durum'),
        ('ancient', 'Ancient'),
    ]

    name = models.CharField(max_length=100, unique=True)
    protein_content = models.FloatField(default=12.0, help_text="Protein percentage (e.g. 14.5 for 14.5%)")
    hardness = models.CharField(max_length=20, choices=HARDNESS_CHOICES, default='hard')
    moisture_absorption_coef = models.FloatField(default=1.0, help_text="Water absorption multiplier (e.g. 1.0 for baseline)")
    is_active = models.BooleanField(default=True, db_index=True, help_text="True if currently in stock and included in calculations")
    ai_analyzed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Wheat Berries"
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.protein_content}%)"


class Equipment(models.Model):
    """
    Represents baking equipment (mixers, mills, proofing tools, etc.).
    """
    TYPE_CHOICES = [
        ('mill', 'Grain Mill'),
        ('mixer', 'Kneader / Mixer'),
        ('attachment', 'Mixer Attachment'),
        ('proofing_mat', 'Proofing Cabinet/Mat'),
        ('oven_accessory', 'Oven Accessory'),
        ('other', 'Other Equipment'),
    ]

    name = models.CharField(max_length=100, unique=True)
    equipment_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='other', db_index=True)
    friction_heat_factor = models.FloatField(default=0.0, help_text="Friction temperature rise in Fahrenheit (for mixers)")
    ai_analyzed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True, help_text="Flexible specs generated by AI")

    class Meta:
        verbose_name_plural = "Equipment"
        indexes = [
            models.Index(fields=['equipment_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_equipment_type_display()})"

