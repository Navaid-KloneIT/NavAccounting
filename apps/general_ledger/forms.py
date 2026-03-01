from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from .models import (
    Account, JournalEntry, JournalEntryLine,
    AllocationRule, AllocationRuleLine,
    AccountReconciliation, ExchangeRate,
)


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'account_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 1110'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Account name'
            }),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_header': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['parent'].queryset = Account.unscoped.filter(
                tenant=tenant, is_header=True, is_active=True
            )


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['date', 'description', 'reference', 'fiscal_period', 'currency', 'exchange_rate']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'placeholder': 'Entry description'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'External reference (optional)'
            }),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.00000001'
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalPeriod
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'description', 'debit', 'credit']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Line description'
            }),
            'debit': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'credit': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )


JournalEntryLineFormSet = inlineformset_factory(
    JournalEntry,
    JournalEntryLine,
    form=JournalEntryLineForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True,
)


class AllocationRuleForm(forms.ModelForm):
    class Meta:
        model = AllocationRule
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Rule name'
            }),
            'source_account': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['source_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )


class AllocationRuleLineForm(forms.ModelForm):
    class Meta:
        model = AllocationRuleLine
        fields = ['target_account', 'percentage', 'fixed_amount']
        widgets = {
            'target_account': forms.Select(attrs={'class': 'form-select'}),
            'percentage': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.0001'
            }),
            'fixed_amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01'
            }),
        }


AllocationRuleLineFormSet = inlineformset_factory(
    AllocationRule,
    AllocationRuleLine,
    form=AllocationRuleLineForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class AccountReconciliationForm(forms.ModelForm):
    class Meta:
        model = AccountReconciliation
        fields = ['account', 'fiscal_period', 'actual_balance', 'notes']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'actual_balance': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalPeriod
            self.fields['account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant
            )


class ExchangeRateForm(forms.ModelForm):
    class Meta:
        model = ExchangeRate
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'from_currency': forms.Select(attrs={'class': 'form-select'}),
            'to_currency': forms.Select(attrs={'class': 'form-select'}),
            'rate': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.00000001'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'source': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. manual, API'
            }),
        }


class ApprovalActionForm(forms.Form):
    """Simple form for approval/rejection comments."""
    comments = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'Enter comments...'
        }),
        required=False,
    )
