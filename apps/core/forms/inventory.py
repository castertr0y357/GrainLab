from django import forms

from apps.core.models import Equipment, WheatBerry


class WheatBerryForm(forms.ModelForm):
    class Meta:
        model = WheatBerry
        fields = ["name", "protein_content", "hardness", "moisture_absorption_coef", "is_active", "notes"]


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ["name", "equipment_type", "friction_heat_factor", "notes"]
