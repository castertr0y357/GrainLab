import json

from django import forms


class Phase4Form(forms.Form):
    action = forms.CharField(required=False)
    process_recommendations = forms.CharField(required=False)
    flavor_inclusions = forms.CharField(required=False)
    secondary_ingredients = forms.CharField(required=False)
    texture = forms.CharField(required=False)
    crumb = forms.CharField(required=False)
    starter = forms.CharField(required=False)
    mixing_method = forms.CharField(required=False)
    active_action = forms.CharField(required=False)

    def clean_process_recommendations(self):
        val = self.cleaned_data.get("process_recommendations")
        if not val:
            return {}
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return {}

    def clean_flavor_inclusions(self):
        val = self.cleaned_data.get("flavor_inclusions")
        if not val:
            return []
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return []

    def clean_secondary_ingredients(self):
        val = self.cleaned_data.get("secondary_ingredients")
        if not val:
            return {}
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return {}
