from django import forms

from .models import CustomUser, UserInvitation, UserProfile


class ProfileForm(forms.Form):
    """Combined form for user + tenant profile editing."""
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    phone = forms.CharField(max_length=20, required=False)
    avatar = forms.ImageField(required=False)
    job_title = forms.CharField(max_length=100, required=False)
    department = forms.CharField(max_length=100, required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    timezone = forms.CharField(max_length=50, required=False)
    date_format = forms.CharField(max_length=20, required=False)


class UserInviteForm(forms.Form):
    """Form to invite a user to a tenant."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    role = forms.IntegerField(required=False, widget=forms.Select(attrs={'class': 'form-select'}))
