from django import forms

class GrainAdvisoryForm(forms.Form):
    preset_slug = forms.CharField(required=False)
    preset_name = forms.CharField(required=False)
    category_slug = forms.CharField(required=False)
    selected_grains = forms.CharField(required=False)
    only_evaluations = forms.BooleanField(required=False, initial=False)
    only_elevate = forms.BooleanField(required=False, initial=False)
    active_archetype_id = forms.CharField(required=False)
    active_variation_id = forms.CharField(required=False)
    lipid = forms.CharField(required=False)
    liquid = forms.CharField(required=False)
    binder = forms.CharField(required=False)
    stream = forms.BooleanField(required=False, initial=False)
    target = forms.CharField(required=False, initial="all")
    
    def clean_active_archetype_id(self):
        val = self.cleaned_data.get('active_archetype_id', '')
        if val:
            for suffix in ["_level", "_l1", "_l2", "_l3", "_v1", "_v2", "_v3", "_alt"]:
                if suffix in val:
                    return val.split(suffix)[0]
        return val

    def clean_preset_slug(self):
        val = self.cleaned_data.get('preset_slug', '')
        if val:
            for suffix in ["_level", "_l1", "_l2", "_l3", "_v1", "_v2", "_v3", "_alt"]:
                if suffix in val:
                    return val.split(suffix)[0]
        return val
