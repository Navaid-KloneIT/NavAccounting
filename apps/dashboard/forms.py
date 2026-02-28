from django import forms

from .models import DashboardWidgetConfig


class WidgetConfigForm(forms.ModelForm):
    class Meta:
        model = DashboardWidgetConfig
        fields = ['widget_type', 'position', 'column_span', 'is_visible']
        widgets = {
            'widget_type': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.NumberInput(attrs={'class': 'form-control'}),
            'column_span': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
