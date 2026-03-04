from django import forms
from django.forms import inlineformset_factory

from apps.general_ledger.models import Account

from .models import (
    BankAccount, BankAccountSignatory, BankFeed, BankTransaction,
    BankReconciliation, AutoMatchRule,
    CashForecast, CashForecastLine, IntercompanyTransfer, BankFee
)


# =============================================================================
# Bank Account Forms
# =============================================================================

class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        exclude = ['tenant', 'created_at', 'updated_at', 'account_number_display',
                    'account_number_masked', 'current_balance']
        widgets = {
            'gl_account': forms.Select(attrs={'class': 'form-select'}),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Bank name'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Full account number'
            }),
            'routing_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Routing/sort code'
            }),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'swift_bic': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'SWIFT/BIC code'
            }),
            'iban': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'IBAN'
            }),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'opening_balance': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['gl_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='ASSET'
            )


class BankAccountSignatoryForm(forms.ModelForm):
    class Meta:
        model = BankAccountSignatory
        fields = ['name', 'title', 'signature_level', 'authorization_limit', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Full name'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Job title'
            }),
            'signature_level': forms.Select(attrs={'class': 'form-select'}),
            'authorization_limit': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


BankAccountSignatoryFormSet = inlineformset_factory(
    BankAccount, BankAccountSignatory,
    form=BankAccountSignatoryForm,
    extra=2,
    can_delete=True,
)


# =============================================================================
# Bank Feed Forms
# =============================================================================

class BankFeedForm(forms.ModelForm):
    class Meta:
        model = BankFeed
        exclude = ['tenant', 'created_at', 'updated_at', 'last_sync_at', 'connection_config']
        widgets = {
            'bank_account': forms.Select(attrs={'class': 'form-select'}),
            'feed_source': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['bank_account'].queryset = BankAccount.unscoped.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# Bank Transaction Forms
# =============================================================================

class BankTransactionFilterForm(forms.Form):
    """Filter form for bank transaction list."""
    bank_account = forms.ModelChoiceField(
        required=False,
        queryset=BankAccount.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    transaction_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + BankTransaction.TRANSACTION_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    matched = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('yes', 'Matched'), ('no', 'Unmatched')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['bank_account'].queryset = BankAccount.unscoped.filter(
                tenant=tenant, is_active=True
            )


class BankTransactionImportForm(forms.Form):
    """File upload form for importing bank transactions."""
    bank_account = forms.ModelChoiceField(
        queryset=BankAccount.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control', 'accept': '.csv,.ofx,.qfx'
        }),
        help_text='Upload CSV, OFX, or QFX files'
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['bank_account'].queryset = BankAccount.unscoped.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# Reconciliation Forms
# =============================================================================

class BankReconciliationForm(forms.ModelForm):
    class Meta:
        model = BankReconciliation
        fields = ['bank_account', 'fiscal_period', 'statement_date', 'statement_balance', 'notes']
        widgets = {
            'bank_account': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'statement_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'statement_balance': forms.NumberInput(attrs={
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
            self.fields['bank_account'].queryset = BankAccount.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant
            )


class AutoMatchRuleForm(forms.ModelForm):
    class Meta:
        model = AutoMatchRule
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Rule name'
            }),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'pattern': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': '{"field": "reference", "value": "CHK*"}'
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '1'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =============================================================================
# Cash Forecast Forms
# =============================================================================

class CashForecastForm(forms.ModelForm):
    class Meta:
        model = CashForecast
        exclude = ['tenant', 'created_at', 'updated_at', 'forecast_number', 'created_by']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Forecast name'
            }),
            'forecast_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
        }


class CashForecastLineForm(forms.ModelForm):
    class Meta:
        model = CashForecastLine
        fields = ['line_date', 'category', 'description', 'expected_amount', 'actual_amount']
        widgets = {
            'line_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Description'
            }),
            'expected_amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01'
            }),
            'actual_amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01'
            }),
        }


CashForecastLineFormSet = inlineformset_factory(
    CashForecast, CashForecastLine,
    form=CashForecastLineForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


# =============================================================================
# Inter-company Transfer Forms
# =============================================================================

class IntercompanyTransferForm(forms.ModelForm):
    class Meta:
        model = IntercompanyTransfer
        exclude = ['tenant', 'created_at', 'updated_at', 'transfer_number',
                    'status', 'created_by', 'approved_by', 'journal_entry']
        widgets = {
            'from_bank_account': forms.Select(attrs={'class': 'form-select'}),
            'to_bank_account': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0.01'
            }),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.00000001'
            }),
            'transfer_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Reference number'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['from_bank_account'].queryset = BankAccount.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['to_bank_account'].queryset = BankAccount.unscoped.filter(
                tenant=tenant, is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        from_account = cleaned_data.get('from_bank_account')
        to_account = cleaned_data.get('to_bank_account')
        if from_account and to_account and from_account == to_account:
            raise forms.ValidationError('Source and destination accounts must be different.')
        return cleaned_data


# =============================================================================
# Bank Fee Forms
# =============================================================================

class BankFeeForm(forms.ModelForm):
    class Meta:
        model = BankFee
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'bank_account': forms.Select(attrs={'class': 'form-select'}),
            'fee_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'fee_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Fee description'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'category': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Category (optional)'
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['bank_account'].queryset = BankAccount.unscoped.filter(
                tenant=tenant, is_active=True
            )


class BankFeeFilterForm(forms.Form):
    """Filter form for bank fee list."""
    bank_account = forms.ModelChoiceField(
        required=False,
        queryset=BankAccount.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    fee_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + BankFee.FEE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['bank_account'].queryset = BankAccount.unscoped.filter(
                tenant=tenant, is_active=True
            )
