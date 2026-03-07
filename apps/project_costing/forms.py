from django import forms
from django.forms import inlineformset_factory

from apps.general_ledger.models import Account

from .models import (
    Project, WBSElement, ProjectBudget, BillingRule,
    TimeEntry, ExpenseEntry,
    RevenueRecognition, ProjectMilestone,
    ProjectInvoice, ProjectInvoiceLine,
    ProfitabilitySnapshot, ResourceAssignment,
)


# =============================================================================
# 1. Project Setup
# =============================================================================

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ['tenant', 'created_at', 'updated_at', 'project_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'client_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'billing_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'budget_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'revenue_account': forms.Select(attrs={'class': 'form-select'}),
            'expense_account': forms.Select(attrs={'class': 'form-select'}),
            'retention_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.payroll.models import Employee
            self.fields['manager'].queryset = Employee.unscoped.filter(
                tenant=tenant, is_active=True
            )
            gl_qs = Account.unscoped.filter(tenant=tenant, is_active=True, is_header=False)
            self.fields['revenue_account'].queryset = gl_qs
            self.fields['expense_account'].queryset = gl_qs


class WBSElementForm(forms.ModelForm):
    class Meta:
        model = WBSElement
        exclude = ['tenant', 'created_at', 'updated_at', 'project']
        widgets = {
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1.1.1'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'level': forms.NumberInput(attrs={'class': 'form-control'}),
            'budget_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'budget_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_billable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['parent'].queryset = WBSElement.unscoped.filter(
                project=project, is_active=True
            )


class ProjectBudgetForm(forms.ModelForm):
    class Meta:
        model = ProjectBudget
        exclude = ['tenant', 'created_at', 'updated_at', 'project']
        widgets = {
            'wbs_element': forms.Select(attrs={'class': 'form-select'}),
            'gl_account': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'budget_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'budget_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'budget_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'revised_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['wbs_element'].queryset = WBSElement.unscoped.filter(
                project=project, is_active=True
            )
        if tenant:
            gl_qs = Account.unscoped.filter(tenant=tenant, is_active=True, is_header=False)
            self.fields['gl_account'].queryset = gl_qs
            from apps.company.models import FiscalPeriod
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


class BillingRuleForm(forms.ModelForm):
    class Meta:
        model = BillingRule
        exclude = ['tenant', 'created_at', 'updated_at', 'project']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'rate_type': forms.Select(attrs={'class': 'form-select'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'markup_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =============================================================================
# 2. Time & Expense
# =============================================================================

class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        exclude = ['tenant', 'created_at', 'updated_at', 'total_amount',
                    'billing_status', 'approved_by', 'approved_date']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'wbs_element': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'entry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'is_billable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.payroll.models import Employee
            self.fields['project'].queryset = Project.unscoped.filter(
                tenant=tenant, is_active=True, status='active'
            )
            self.fields['employee'].queryset = Employee.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['wbs_element'].queryset = WBSElement.unscoped.filter(
                project__tenant=tenant, is_active=True
            )


class ExpenseEntryForm(forms.ModelForm):
    class Meta:
        model = ExpenseEntry
        exclude = ['tenant', 'created_at', 'updated_at', 'billing_status', 'billed_amount']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'wbs_element': forms.Select(attrs={'class': 'form-select'}),
            'gl_account': forms.Select(attrs={'class': 'form-select'}),
            'entry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vendor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_billable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'markup_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'receipt_reference': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['project'].queryset = Project.unscoped.filter(
                tenant=tenant, is_active=True, status='active'
            )
            self.fields['wbs_element'].queryset = WBSElement.unscoped.filter(
                project__tenant=tenant, is_active=True
            )
            gl_qs = Account.unscoped.filter(tenant=tenant, is_active=True, is_header=False)
            self.fields['gl_account'].queryset = gl_qs


# =============================================================================
# 3. Revenue Recognition
# =============================================================================

class RevenueRecognitionForm(forms.ModelForm):
    class Meta:
        model = RevenueRecognition
        exclude = ['tenant', 'created_at', 'updated_at', 'status',
                    'gl_journal_entry', 'total_recognized_prior',
                    'recognized_this_period', 'cumulative_recognized']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'recognition_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'completion_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'contract_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['project'].queryset = Project.unscoped.filter(
                tenant=tenant, is_active=True
            )
            from apps.company.models import FiscalPeriod
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


# =============================================================================
# 4. Project Billing
# =============================================================================

class ProjectMilestoneForm(forms.ModelForm):
    class Meta:
        model = ProjectMilestone
        exclude = ['tenant', 'created_at', 'updated_at', 'project', 'status', 'actual_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'target_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'completion_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ProjectInvoiceForm(forms.ModelForm):
    class Meta:
        model = ProjectInvoice
        exclude = ['tenant', 'created_at', 'updated_at', 'invoice_number',
                    'subtotal', 'retention_amount', 'tax_amount', 'total_amount',
                    'status', 'gl_journal_entry']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['project'].queryset = Project.unscoped.filter(
                tenant=tenant, is_active=True
            )
            from apps.company.models import FiscalPeriod
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


class ProjectInvoiceLineForm(forms.ModelForm):
    class Meta:
        model = ProjectInvoiceLine
        exclude = ['invoice']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
            'wbs_element': forms.Select(attrs={'class': 'form-select'}),
            'line_type': forms.Select(attrs={'class': 'form-select'}),
        }


ProjectInvoiceLineFormSet = inlineformset_factory(
    ProjectInvoice,
    ProjectInvoiceLine,
    form=ProjectInvoiceLineForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


# =============================================================================
# 5. Profitability
# =============================================================================

class ProfitabilitySnapshotForm(forms.ModelForm):
    class Meta:
        model = ProfitabilitySnapshot
        exclude = ['tenant', 'created_at', 'updated_at', 'project']
        widgets = {
            'snapshot_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'budget_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'actual_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'actual_revenue': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'committed_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimate_at_completion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimate_to_complete': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'earned_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost_variance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'schedule_variance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost_performance_index': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'schedule_performance_index': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalPeriod
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


# =============================================================================
# 6. Resource Planning
# =============================================================================

class ResourceAssignmentForm(forms.ModelForm):
    class Meta:
        model = ResourceAssignment
        exclude = ['tenant', 'created_at', 'updated_at', 'actual_hours']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'wbs_element': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'allocation_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'planned_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.payroll.models import Employee
            self.fields['project'].queryset = Project.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['employee'].queryset = Employee.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['wbs_element'].queryset = WBSElement.unscoped.filter(
                project__tenant=tenant, is_active=True
            )
