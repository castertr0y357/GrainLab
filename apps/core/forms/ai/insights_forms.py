import json

from django import forms


class SidebarInsightForm(forms.Form):
    element = forms.CharField(required=False)
    category_slug = forms.CharField(required=False)
    preset_slug = forms.CharField(required=False)
    active_archetype_id = forms.CharField(required=False)


class BatchInsightsForm(forms.Form):
    elements = forms.CharField(required=False, initial="[]")
    category_slug = forms.CharField(required=False)
    preset_slug = forms.CharField(required=False)
    active_archetype_id = forms.CharField(required=False)

    def clean_elements(self):
        val = self.cleaned_data.get("elements", "[]")
        try:
            return json.loads(val)
        except Exception:
            return []
