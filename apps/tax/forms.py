from django import forms
from django.forms import inlineformset_factory

from apps.general_ledger.models import Account

from .models import (
    TaxJurisdiction, TaxRate, TaxRule, TaxGroup, TaxGroupMember,
    TaxReturn, TaxReturnLine, TaxReturnPayment,
    UseTaxAssessment, UseTaxAccrual,
    IncomeTaxProvision, DeferredTaxItem, ETRReconciliation,
    TaxDeadline,
    TaxAudit, AuditFinding, AuditDocument,
    NexusJurisdiction, NexusActivity,
)


# =============================================================================
# Sales Tax Engine
# =============================================================================

class TaxJurisdictionForm(forms.ModelForm):
    class Meta:
        model = TaxJurisdiction
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'jurisdiction_level': forms.Select(attrs={'class': 'form-select'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'state_code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['parent'].queryset = TaxJurisdiction.unscoped.filter(
                tenant=tenant, is_active=True
            )


class TaxRateForm(forms.ModelForm):
    class Meta:
        model = TaxRate
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'jurisdiction': forms.Select(attrs={'class': 'form-select'}),
            'rate_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00001'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_compound': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'gl_tax_collected_account': forms.Select(attrs={'class': 'form-select'}),
            'gl_tax_paid_account': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['jurisdiction'].queryset = TaxJurisdiction.unscoped.filter(
                tenant=tenant, is_active=True
            )
            gl_qs = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )
            self.fields['gl_tax_collected_account'].queryset = gl_qs
            self.fields['gl_tax_paid_account'].queryset = gl_qs


class TaxRuleForm(forms.ModelForm):
    class Meta:
        model = TaxRule
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'jurisdiction': forms.Select(attrs={'class': 'form-select'}),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'product_category': forms.TextInput(attrs={'class': 'form-control'}),
            'rate_override': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00001'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['jurisdiction'].queryset = TaxJurisdiction.unscoped.filter(
                tenant=tenant, is_active=True
            )


class TaxGroupForm(forms.ModelForm):
    class Meta:
        model = TaxGroup
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TaxGroupMemberForm(forms.ModelForm):
    class Meta:
        model = TaxGroupMember
        fields = ['tax_rate', 'priority']
        widgets = {
            'tax_rate': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
        }


TaxGroupMemberFormSet = inlineformset_factory(
    TaxGroup, TaxGroupMember,
    form=TaxGroupMemberForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# Tax Returns
# =============================================================================

class TaxReturnForm(forms.ModelForm):
    class Meta:
        model = TaxReturn
        exclude = [
            'tenant', 'created_at', 'updated_at', 'return_number',
            'status', 'total_taxable_amount', 'total_tax_due', 'total_credits',
            'net_tax_due', 'amount_paid', 'filed_date', 'filed_by',
            'gl_journal_entry', 'confirmation_number', 'created_by',
        ]
        widgets = {
            'return_type': forms.Select(attrs={'class': 'form-select'}),
            'jurisdiction': forms.Select(attrs={'class': 'form-select'}),
            'period_type': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['jurisdiction'].queryset = TaxJurisdiction.unscoped.filter(
                tenant=tenant, is_active=True
            )
            from apps.company.models import FiscalPeriod
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                fiscal_year__tenant=tenant
            )


class TaxReturnLineForm(forms.ModelForm):
    class Meta:
        model = TaxReturnLine
        fields = ['line_number', 'description', 'gl_account', 'taxable_amount',
                  'tax_amount', 'rate_applied', 'notes']
        widgets = {
            'line_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'gl_account': forms.Select(attrs={'class': 'form-select'}),
            'taxable_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rate_applied': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00001'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


TaxReturnLineFormSet = inlineformset_factory(
    TaxReturn, TaxReturnLine,
    form=TaxReturnLineForm,
    extra=1,
    can_delete=True,
)


class TaxReturnPaymentForm(forms.ModelForm):
    class Meta:
        model = TaxReturnPayment
        exclude = ['tenant', 'created_at', 'updated_at', 'gl_journal_entry', 'tax_return']
        widgets = {
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# =============================================================================
# Use Tax Tracking
# =============================================================================

class UseTaxAssessmentForm(forms.ModelForm):
    class Meta:
        model = UseTaxAssessment
        exclude = [
            'tenant', 'created_at', 'updated_at', 'assessment_number',
            'status', 'gl_journal_entry', 'created_by',
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'bill': forms.Select(attrs={'class': 'form-select'}),
            'jurisdiction': forms.Select(attrs={'class': 'form-select'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00001'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'gl_use_tax_account': forms.Select(attrs={'class': 'form-select'}),
            'gl_expense_account': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['jurisdiction'].queryset = TaxJurisdiction.unscoped.filter(
                tenant=tenant, is_active=True
            )
            gl_qs = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )
            self.fields['gl_use_tax_account'].queryset = gl_qs
            self.fields['gl_expense_account'].queryset = gl_qs

            from apps.accounts_payable.models import Vendor, Bill
            self.fields['vendor'].queryset = Vendor.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['bill'].queryset = Bill.unscoped.filter(tenant=tenant)


class UseTaxAccrualForm(forms.ModelForm):
    class Meta:
        model = UseTaxAccrual
        exclude = [
            'tenant', 'created_at', 'updated_at', 'accrual_number',
            'total_purchases', 'total_tax_accrued', 'status',
            'gl_journal_entry', 'created_by',
        ]
        widgets = {
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# =============================================================================
# Income Tax Provision
# =============================================================================

class IncomeTaxProvisionForm(forms.ModelForm):
    class Meta:
        model = IncomeTaxProvision
        exclude = [
            'tenant', 'created_at', 'updated_at', 'provision_number',
            'computed_tax', 'temporary_differences', 'current_tax_expense',
            'deferred_tax_expense', 'total_tax_expense', 'effective_tax_rate',
            'status', 'gl_journal_entry', 'created_by',
        ]
        widgets = {
            'fiscal_year': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'provision_type': forms.Select(attrs={'class': 'form-select'}),
            'pretax_income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'statutory_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00001'}),
            'permanent_differences': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_credits': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalYear, FiscalPeriod
            self.fields['fiscal_year'].queryset = FiscalYear.unscoped.filter(
                tenant=tenant
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                fiscal_year__tenant=tenant
            )


class DeferredTaxItemForm(forms.ModelForm):
    class Meta:
        model = DeferredTaxItem
        fields = ['description', 'item_type', 'book_basis', 'tax_basis',
                  'tax_rate', 'gl_account', 'notes']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'book_basis': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_basis': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00001'}),
            'gl_account': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


DeferredTaxItemFormSet = inlineformset_factory(
    IncomeTaxProvision, DeferredTaxItem,
    form=DeferredTaxItemForm,
    extra=1,
    can_delete=True,
)


class ETRReconciliationForm(forms.ModelForm):
    class Meta:
        model = ETRReconciliation
        fields = ['description', 'rate_impact', 'amount_impact', 'line_order']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'rate_impact': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00001'}),
            'amount_impact': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'line_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


ETRReconciliationFormSet = inlineformset_factory(
    IncomeTaxProvision, ETRReconciliation,
    form=ETRReconciliationForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# Tax Calendar
# =============================================================================

class TaxDeadlineForm(forms.ModelForm):
    class Meta:
        model = TaxDeadline
        exclude = [
            'tenant', 'created_at', 'updated_at', 'deadline_number',
            'status', 'tax_return',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_type': forms.Select(attrs={'class': 'form-select'}),
            'jurisdiction': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reminder_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'extended_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'recurrence_pattern': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['jurisdiction'].queryset = TaxJurisdiction.unscoped.filter(
                tenant=tenant, is_active=True
            )
            from django.contrib.auth import get_user_model
            User = get_user_model()
            from apps.tenants.models import TenantMembership
            user_ids = TenantMembership.objects.filter(
                tenant=tenant
            ).values_list('user_id', flat=True)
            self.fields['assigned_to'].queryset = User.objects.filter(id__in=user_ids)


# =============================================================================
# Audit Support
# =============================================================================

class TaxAuditForm(forms.ModelForm):
    class Meta:
        model = TaxAudit
        exclude = [
            'tenant', 'created_at', 'updated_at', 'audit_number',
            'status', 'total_proposed_adjustment', 'total_agreed_adjustment',
            'gl_journal_entry', 'created_by',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_type': forms.Select(attrs={'class': 'form-select'}),
            'jurisdiction': forms.Select(attrs={'class': 'form-select'}),
            'auditing_authority': forms.TextInput(attrs={'class': 'form-control'}),
            'audit_period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'audit_period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notification_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['jurisdiction'].queryset = TaxJurisdiction.unscoped.filter(
                tenant=tenant, is_active=True
            )
            from django.contrib.auth import get_user_model
            User = get_user_model()
            from apps.tenants.models import TenantMembership
            user_ids = TenantMembership.objects.filter(
                tenant=tenant
            ).values_list('user_id', flat=True)
            self.fields['assigned_to'].queryset = User.objects.filter(id__in=user_ids)


class AuditFindingForm(forms.ModelForm):
    class Meta:
        model = AuditFinding
        exclude = ['tenant', 'created_at', 'updated_at', 'audit']
        widgets = {
            'finding_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'proposed_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'agreed_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'response': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class AuditDocumentForm(forms.ModelForm):
    class Meta:
        model = AuditDocument
        exclude = ['tenant', 'created_at', 'updated_at', 'audit', 'uploaded_by']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# =============================================================================
# Nexus Tracking
# =============================================================================

class NexusJurisdictionForm(forms.ModelForm):
    class Meta:
        model = NexusJurisdiction
        exclude = [
            'tenant', 'created_at', 'updated_at',
            'current_period_sales', 'current_period_transactions',
            'threshold_percentage',
        ]
        widgets = {
            'jurisdiction': forms.Select(attrs={'class': 'form-select'}),
            'nexus_type': forms.Select(attrs={'class': 'form-select'}),
            'has_nexus': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'registration_status': forms.Select(attrs={'class': 'form-select'}),
            'economic_threshold_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'economic_threshold_transactions': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['jurisdiction'].queryset = TaxJurisdiction.unscoped.filter(
                tenant=tenant, is_active=True
            )


class NexusActivityForm(forms.ModelForm):
    class Meta:
        model = NexusActivity
        exclude = ['tenant', 'created_at', 'updated_at', 'nexus_jurisdiction']
        widgets = {
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sales_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transaction_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'has_physical_presence': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'physical_presence_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
