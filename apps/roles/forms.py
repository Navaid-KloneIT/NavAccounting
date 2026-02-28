from django import forms

from .models import Permission, Role


class RoleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Role
        fields = ['name', 'description', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class RoleAssignForm(forms.Form):
    user = forms.IntegerField(widget=forms.Select(attrs={'class': 'form-select'}))
    role = forms.IntegerField(widget=forms.Select(attrs={'class': 'form-select'}))
