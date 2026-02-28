from django import forms

from .models import Tenant


class TenantCreateForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'company-slug'}),
        }
