from django import forms
from django.forms import inlineformset_factory

from apps.general_ledger.models import Account

from .models import (
    Employee,
    PayrollJournal, PayrollJournalLine,
    TaxWithholding, TaxRemittance,
    BenefitPlan, EmployeeBenefit,
    Garnishment,
    WorkersCompClass, WorkersCompAssignment,
    PayrollReconciliation,
)


# =============================================================================
# 1. Employee Master
# =============================================================================

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        exclude = ['tenant', 'created_at', 'updated_at', 'employee_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'termination_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pay_type': forms.Select(attrs={'class': 'form-select'}),
            'pay_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pay_frequency': forms.Select(attrs={'class': 'form-select'}),
            'filing_status': forms.Select(attrs={'class': 'form-select'}),
            'federal_allowances': forms.NumberInput(attrs={'class': 'form-control'}),
            'state_allowances': forms.NumberInput(attrs={'class': 'form-control'}),
            'gl_expense_account': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            gl_qs = Account.unscoped.filter(tenant=tenant, is_active=True, is_header=False)
            self.fields['gl_expense_account'].queryset = gl_qs


# =============================================================================
# 2. Payroll Journal
# =============================================================================

class PayrollJournalForm(forms.ModelForm):
    class Meta:
        model = PayrollJournal
        exclude = ['tenant', 'created_at', 'updated_at', 'journal_number',
                    'total_gross', 'total_deductions', 'total_net',
                    'gl_journal_entry', 'created_by', 'status']
        widgets = {
            'pay_period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pay_period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pay_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalPeriod
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


class PayrollJournalLineForm(forms.ModelForm):
    class Meta:
        model = PayrollJournalLine
        exclude = ['payroll_journal', 'gross_pay', 'overtime_pay',
                    'federal_tax', 'state_tax', 'local_tax',
                    'social_security', 'medicare', 'benefits_deduction',
                    'garnishment_deduction', 'total_deductions', 'net_pay']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'regular_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'overtime_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_deductions': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


PayrollJournalLineFormSet = inlineformset_factory(
    PayrollJournal, PayrollJournalLine,
    form=PayrollJournalLineForm,
    extra=1, can_delete=True,
)


# =============================================================================
# 3. Tax Management
# =============================================================================

class TaxWithholdingForm(forms.ModelForm):
    class Meta:
        model = TaxWithholding
        exclude = ['tenant', 'created_at', 'updated_at', 'ytd_amount']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'tax_type': forms.Select(attrs={'class': 'form-select'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'annual_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_employer_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['employee'].queryset = Employee.unscoped.filter(
                tenant=tenant, is_active=True
            )


class TaxRemittanceForm(forms.ModelForm):
    class Meta:
        model = TaxRemittance
        exclude = ['tenant', 'created_at', 'updated_at', 'remittance_number',
                    'amount_paid', 'paid_date', 'gl_journal_entry', 'status']
        widgets = {
            'tax_type': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount_due': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# =============================================================================
# 4. Benefits
# =============================================================================

class BenefitPlanForm(forms.ModelForm):
    class Meta:
        model = BenefitPlan
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'benefit_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employer_contribution_type': forms.Select(attrs={'class': 'form-select'}),
            'employer_contribution_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'employer_match_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gl_expense_account': forms.Select(attrs={'class': 'form-select'}),
            'gl_liability_account': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            gl_qs = Account.unscoped.filter(tenant=tenant, is_active=True, is_header=False)
            self.fields['gl_expense_account'].queryset = gl_qs
            self.fields['gl_liability_account'].queryset = gl_qs


class EmployeeBenefitForm(forms.ModelForm):
    class Meta:
        model = EmployeeBenefit
        fields = ['employee', 'benefit_plan', 'employee_contribution',
                   'enrollment_date', 'end_date', 'is_active']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'benefit_plan': forms.Select(attrs={'class': 'form-select'}),
            'employee_contribution': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'enrollment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['employee'].queryset = Employee.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['benefit_plan'].queryset = BenefitPlan.unscoped.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# 5. Garnishments
# =============================================================================

class GarnishmentForm(forms.ModelForm):
    class Meta:
        model = Garnishment
        exclude = ['tenant', 'created_at', 'updated_at', 'total_paid']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'garnishment_type': forms.Select(attrs={'class': 'form-select'}),
            'case_number': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_percentage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_required': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'issuing_authority': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['employee'].queryset = Employee.unscoped.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# 6. Workers Comp
# =============================================================================

class WorkersCompClassForm(forms.ModelForm):
    class Meta:
        model = WorkersCompClass
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gl_expense_account': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            gl_qs = Account.unscoped.filter(tenant=tenant, is_active=True, is_header=False)
            self.fields['gl_expense_account'].queryset = gl_qs


class WorkersCompAssignmentForm(forms.ModelForm):
    class Meta:
        model = WorkersCompAssignment
        fields = ['employee', 'comp_class', 'effective_date', 'end_date']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'comp_class': forms.Select(attrs={'class': 'form-select'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['employee'].queryset = Employee.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['comp_class'].queryset = WorkersCompClass.unscoped.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# 7. Reconciliation
# =============================================================================

class PayrollReconciliationForm(forms.ModelForm):
    class Meta:
        model = PayrollReconciliation
        exclude = ['tenant', 'created_at', 'updated_at', 'reconciliation_number',
                    'total_gross', 'total_taxes', 'total_benefits', 'total_garnishments',
                    'total_net', 'variance_amount', 'status', 'reconciled_by']
        widgets = {
            'payroll_journal': forms.Select(attrs={'class': 'form-select'}),
            'reconciliation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['payroll_journal'].queryset = PayrollJournal.unscoped.filter(
                tenant=tenant, status__in=['calculated', 'approved', 'posted']
            )
