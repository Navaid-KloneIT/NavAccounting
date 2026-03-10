from django import forms

from apps.company.models import AccountType, Currency, FiscalPeriod
from apps.general_ledger.models import Account

from .models import (
    ConsolidationGroup,
    ConsolidationRun,
    CurrencyTranslationRule,
    EliminationRule,
    Entity,
    IntercompanyTransaction,
    LocalGAAPAdjustment,
    RegulatoryReport,
    TransferPricingPolicy,
    TransferPricingTransaction,
)


# =============================================================================
# Entity Management Forms
# =============================================================================

class EntityForm(forms.ModelForm):
    class Meta:
        model = Entity
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'legal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'entity_type': forms.Select(attrs={'class': 'form-select'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'functional_currency': forms.Select(attrs={'class': 'form-select'}),
            'ownership_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'consolidation_method': forms.Select(attrs={'class': 'form-select'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'local_gaap': forms.TextInput(attrs={'class': 'form-control'}),
            'ic_receivable_account': forms.Select(attrs={'class': 'form-select'}),
            'ic_payable_account': forms.Select(attrs={'class': 'form-select'}),
            'cta_account': forms.Select(attrs={'class': 'form-select'}),
            'minority_interest_account': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['parent'].queryset = Entity.unscoped.filter(
                tenant=tenant, status='active'
            )
            if self.instance.pk:
                self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(
                    pk=self.instance.pk
                )
            self.fields['functional_currency'].queryset = Currency.objects.filter(is_active=True)
            accounts_qs = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )
            self.fields['ic_receivable_account'].queryset = accounts_qs
            self.fields['ic_payable_account'].queryset = accounts_qs
            self.fields['cta_account'].queryset = accounts_qs
            self.fields['minority_interest_account'].queryset = accounts_qs


# =============================================================================
# Inter-company Forms
# =============================================================================

class IntercompanyTransactionForm(forms.ModelForm):
    class Meta:
        model = IntercompanyTransaction
        exclude = [
            'tenant', 'created_at', 'updated_at', 'transaction_number',
            'created_by', 'status', 'from_journal_entry', 'to_journal_entry',
            'confirmed_by', 'confirmed_at',
        ]
        widgets = {
            'from_entity': forms.Select(attrs={'class': 'form-select'}),
            'to_entity': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'exchange_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000001'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            entity_qs = Entity.unscoped.filter(tenant=tenant, status='active')
            self.fields['from_entity'].queryset = entity_qs
            self.fields['to_entity'].queryset = entity_qs
            self.fields['currency'].queryset = Currency.objects.filter(is_active=True)
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )

    def clean(self):
        cleaned = super().clean()
        from_entity = cleaned.get('from_entity')
        to_entity = cleaned.get('to_entity')
        if from_entity and to_entity and from_entity == to_entity:
            raise forms.ValidationError('From and To entities must be different.')
        return cleaned


# =============================================================================
# Currency Translation Forms
# =============================================================================

class CurrencyTranslationRuleForm(forms.ModelForm):
    class Meta:
        model = CurrencyTranslationRule
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_scope': forms.Select(attrs={'class': 'form-select'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'specific_account': forms.Select(attrs={'class': 'form-select'}),
            'rate_type': forms.Select(attrs={'class': 'form-select'}),
            'fixed_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000001'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account_type'].queryset = AccountType.objects.all()
        if tenant:
            self.fields['specific_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )


class TranslationRunForm(forms.Form):
    """Form to select entity + period for running currency translation."""
    entity = forms.ModelChoiceField(
        queryset=Entity.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fiscal_period = forms.ModelChoiceField(
        queryset=FiscalPeriod.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['entity'].queryset = Entity.unscoped.filter(
                tenant=tenant, status='active'
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


# =============================================================================
# Consolidation Forms
# =============================================================================

class ConsolidationGroupForm(forms.ModelForm):
    class Meta:
        model = ConsolidationGroup
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_entity': forms.Select(attrs={'class': 'form-select'}),
            'reporting_currency': forms.Select(attrs={'class': 'form-select'}),
            'entities': forms.CheckboxSelectMultiple(),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            entity_qs = Entity.unscoped.filter(tenant=tenant, status='active')
            self.fields['parent_entity'].queryset = entity_qs
            self.fields['entities'].queryset = entity_qs
            self.fields['reporting_currency'].queryset = Currency.objects.filter(is_active=True)


class EliminationRuleForm(forms.ModelForm):
    class Meta:
        model = EliminationRule
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'consolidation_group': forms.Select(attrs={'class': 'form-select'}),
            'debit_account': forms.Select(attrs={'class': 'form-select'}),
            'credit_account': forms.Select(attrs={'class': 'form-select'}),
            'is_auto': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['consolidation_group'].queryset = ConsolidationGroup.unscoped.filter(
                tenant=tenant, is_active=True
            )
            accounts_qs = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )
            self.fields['debit_account'].queryset = accounts_qs
            self.fields['credit_account'].queryset = accounts_qs


class ConsolidationRunForm(forms.ModelForm):
    class Meta:
        model = ConsolidationRun
        fields = ['consolidation_group', 'fiscal_period', 'notes']
        widgets = {
            'consolidation_group': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['consolidation_group'].queryset = ConsolidationGroup.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


# =============================================================================
# Transfer Pricing Forms
# =============================================================================

class TransferPricingPolicyForm(forms.ModelForm):
    class Meta:
        model = TransferPricingPolicy
        exclude = [
            'tenant', 'created_at', 'updated_at', 'policy_number', 'created_by', 'status',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'from_entity': forms.Select(attrs={'class': 'form-select'}),
            'to_entity': forms.Select(attrs={'class': 'form-select'}),
            'pricing_method': forms.Select(attrs={'class': 'form-select'}),
            'markup_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'effective_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'documentation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'comparable_data': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            entity_qs = Entity.unscoped.filter(tenant=tenant, status='active')
            self.fields['from_entity'].queryset = entity_qs
            self.fields['to_entity'].queryset = entity_qs


class TransferPricingTransactionForm(forms.ModelForm):
    class Meta:
        model = TransferPricingTransaction
        exclude = [
            'tenant', 'created_at', 'updated_at', 'variance', 'variance_percentage',
            'reviewed_by', 'reviewed_at', 'status',
        ]
        widgets = {
            'policy': forms.Select(attrs={'class': 'form-select'}),
            'intercompany_transaction': forms.Select(attrs={'class': 'form-select'}),
            'transfer_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'arms_length_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'review_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['policy'].queryset = TransferPricingPolicy.unscoped.filter(
                tenant=tenant, status='active'
            )
            self.fields['intercompany_transaction'].queryset = (
                IntercompanyTransaction.unscoped.filter(tenant=tenant)
            )


# =============================================================================
# Regulatory Reporting Forms
# =============================================================================

class LocalGAAPAdjustmentForm(forms.ModelForm):
    class Meta:
        model = LocalGAAPAdjustment
        exclude = [
            'tenant', 'created_at', 'updated_at', 'adjustment_number',
            'created_by', 'status', 'journal_entry',
        ]
        widgets = {
            'entity': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'adjustment_type': forms.Select(attrs={'class': 'form-select'}),
            'from_standard': forms.TextInput(attrs={'class': 'form-control'}),
            'to_standard': forms.TextInput(attrs={'class': 'form-control'}),
            'debit_account': forms.Select(attrs={'class': 'form-select'}),
            'credit_account': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['entity'].queryset = Entity.unscoped.filter(
                tenant=tenant, status='active'
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )
            accounts_qs = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )
            self.fields['debit_account'].queryset = accounts_qs
            self.fields['credit_account'].queryset = accounts_qs


class RegulatoryReportForm(forms.ModelForm):
    class Meta:
        model = RegulatoryReport
        exclude = [
            'tenant', 'created_at', 'updated_at', 'report_number',
            'generated_by', 'generated_at', 'filed_at', 'filing_reference',
            'status', 'report_data',
        ]
        widgets = {
            'entity': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'gaap_standard': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['entity'].queryset = Entity.unscoped.filter(
                tenant=tenant, status='active'
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )
