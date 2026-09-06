from django import forms
import uuid
from apps.core.models import WheatBerry

class BaseRecipeForm(forms.Form):
    recipe_slug = forms.CharField(required=True)
    recipe_name = forms.CharField(required=False)
    engine_id = forms.CharField(required=False)
    active_archetype_id = forms.CharField(required=False)
    active_variation_id = forms.CharField(required=False)
    stream = forms.BooleanField(required=False, initial=False)
    
    def clean_active_archetype_id(self):
        val = self.cleaned_data.get('active_archetype_id', '')
        if val:
            for suffix in ["_level", "_l1", "_l2", "_l3", "_v1", "_v2", "_v3", "_alt"]:
                if suffix in val:
                    return val.split(suffix)[0]
        return val

class RecipeDetailsForm(BaseRecipeForm):
    selected_grains = forms.CharField(required=False)
    category_slug = forms.CharField(required=False)
    mill_type = forms.CharField(required=False)
    is_sifted = forms.BooleanField(required=False, initial=False)
    target = forms.CharField(required=False, initial="all")
    
    def clean_selected_grains(self):
        val = self.cleaned_data.get('selected_grains', '')
        if not val:
            return ""
        grain_ids = [g.strip() for g in val.split(",") if g.strip()]
        parsed_uuids = []
        raw_names = []
        for gid in grain_ids:
            try:
                parsed_uuids.append(uuid.UUID(gid))
            except ValueError:
                raw_names.append(gid)
    
        db_grains = WheatBerry.objects.filter(id__in=parsed_uuids)
        db_names = [b.name for b in db_grains]
        all_names = db_names + raw_names
        return ", ".join(all_names)

class RecipePercentagesForm(BaseRecipeForm):
    recipe_slug = forms.CharField(required=False)
    secondary_ingredients = forms.JSONField(required=False, initial=list)
    
    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('recipe_slug') and not cleaned.get('recipe_name'):
            raise forms.ValidationError("recipe_slug or recipe_name is required.")
        return cleaned

class GenerateSubstitutesForm(BaseRecipeForm):
    selected_grains = forms.CharField(required=False)
    target_category = forms.CharField(required=True)
    original_recommendation = forms.JSONField(required=False, initial=dict)
    exclude_names = forms.JSONField(required=False, initial=list)

class ProcessAlternativesForm(BaseRecipeForm):
    target_category = forms.CharField(required=True)
    original_recommendation = forms.JSONField(required=False, initial=dict)
    exclude_names = forms.JSONField(required=False, initial=list)

class ProcessDetailsForm(BaseRecipeForm):
    target = forms.CharField(required=False, initial="all")

class RecipeTweaksForm(BaseRecipeForm):
    recipe_slug = forms.CharField(required=False)
    current_ingredients = forms.JSONField(required=True)
    applied_tweaks_history = forms.JSONField(required=False, initial=list)

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('engine_id'):
            raise forms.ValidationError("engine_id is required.")
        return cleaned

class ApplyTweakForm(BaseRecipeForm):
    proposed_modifications = forms.JSONField(required=True)
    tweak_title = forms.CharField(required=False)
