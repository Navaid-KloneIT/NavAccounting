from django import forms
from django.forms import inlineformset_factory

from apps.general_ledger.models import Account
from apps.company.models import FiscalYear, FiscalPeriod

from .models import (
    Budget, BudgetLineItem, BudgetVersion,
    PlanningDriver, PlanningDriverPeriod,
    RollingForecast, ForecastLineItem,
    VarianceAnalysis,
    ScenarioModel, ScenarioAdjustment,
    WorkforcePlan, WorkforcePlanPosition,
)


# ──────────────────────────────────────────────
# Budget
# ──────────────────────────────────────────────
class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        exclude = ['tenant', 'created_at', 'updated_at', 'budget_number',
                    'created_by', 'approved_by', 'approved_at', 'total_amount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'budget_type': forms.Select(attrs={'class': 'form-select'}),
            'approach': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_year': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['fiscal_year'].queryset = FiscalYear.unscoped.filter(tenant=tenant)


class BudgetLineItemForm(forms.ModelForm):
    class Meta:
        model = BudgetLineItem
        exclude = ['tenant', 'created_at', 'updated_at', 'budget']
        widgets = {
            'gl_account': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['gl_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                fiscal_year__tenant=tenant
            )


BudgetLineItemFormSet = inlineformset_factory(
    Budget, BudgetLineItem,
    form=BudgetLineItemForm,
    extra=1, can_delete=True,
)


# ──────────────────────────────────────────────
# Budget Version
# ──────────────────────────────────────────────
class BudgetVersionForm(forms.ModelForm):
    class Meta:
        model = BudgetVersion
        exclude = ['tenant', 'created_at', 'updated_at', 'version_number',
                    'created_by', 'snapshot_data', 'total_amount']
        widgets = {
            'budget': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'version_type': forms.Select(attrs={'class': 'form-select'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['budget'].queryset = Budget.unscoped.filter(tenant=tenant)


# ──────────────────────────────────────────────
# Planning Driver
# ──────────────────────────────────────────────
class PlanningDriverForm(forms.ModelForm):
    class Meta:
        model = PlanningDriver
        exclude = ['tenant', 'created_at', 'updated_at', 'driver_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_type': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'base_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'growth_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'gl_account': forms.Select(attrs={'class': 'form-select'}),
            'budget': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['gl_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )
            self.fields['budget'].queryset = Budget.unscoped.filter(tenant=tenant)


class PlanningDriverPeriodForm(forms.ModelForm):
    class Meta:
        model = PlanningDriverPeriod
        exclude = ['tenant', 'created_at', 'updated_at', 'driver', 'calculated_amount']
        widgets = {
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                fiscal_year__tenant=tenant
            )


PlanningDriverPeriodFormSet = inlineformset_factory(
    PlanningDriver, PlanningDriverPeriod,
    form=PlanningDriverPeriodForm,
    extra=1, can_delete=True,
)


# ──────────────────────────────────────────────
# Rolling Forecast
# ──────────────────────────────────────────────
class RollingForecastForm(forms.ModelForm):
    class Meta:
        model = RollingForecast
        exclude = ['tenant', 'created_at', 'updated_at', 'forecast_number', 'created_by']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'budget': forms.Select(attrs={'class': 'form-select'}),
            'forecast_type': forms.Select(attrs={'class': 'form-select'}),
            'horizon_periods': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'as_of_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['budget'].queryset = Budget.unscoped.filter(tenant=tenant)


class ForecastLineItemForm(forms.ModelForm):
    class Meta:
        model = ForecastLineItem
        exclude = ['tenant', 'created_at', 'updated_at', 'forecast',
                    'actual_amount', 'variance_amount', 'variance_pct']
        widgets = {
            'gl_account': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'forecast_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['gl_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                fiscal_year__tenant=tenant
            )


ForecastLineItemFormSet = inlineformset_factory(
    RollingForecast, ForecastLineItem,
    form=ForecastLineItemForm,
    extra=1, can_delete=True,
)


# ──────────────────────────────────────────────
# Variance Analysis
# ──────────────────────────────────────────────
class VarianceAnalysisForm(forms.ModelForm):
    class Meta:
        model = VarianceAnalysis
        exclude = ['tenant', 'created_at', 'updated_at', 'analysis_number',
                    'generated_at', 'generated_by',
                    'total_budget', 'total_actual', 'total_variance']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'budget': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['budget'].queryset = Budget.unscoped.filter(tenant=tenant)
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                fiscal_year__tenant=tenant
            )


# ──────────────────────────────────────────────
# Scenario Model
# ──────────────────────────────────────────────
class ScenarioForm(forms.ModelForm):
    class Meta:
        model = ScenarioModel
        exclude = ['tenant', 'created_at', 'updated_at', 'scenario_number',
                    'created_by', 'result_summary']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'budget': forms.Select(attrs={'class': 'form-select'}),
            'scenario_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['budget'].queryset = Budget.unscoped.filter(tenant=tenant)


class ScenarioAdjustmentForm(forms.ModelForm):
    class Meta:
        model = ScenarioAdjustment
        exclude = ['tenant', 'created_at', 'updated_at', 'scenario',
                    'original_amount', 'adjusted_amount']
        widgets = {
            'gl_account': forms.Select(attrs={'class': 'form-select'}),
            'adjustment_type': forms.Select(attrs={'class': 'form-select'}),
            'adjustment_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['gl_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                fiscal_year__tenant=tenant
            )


ScenarioAdjustmentFormSet = inlineformset_factory(
    ScenarioModel, ScenarioAdjustment,
    form=ScenarioAdjustmentForm,
    extra=1, can_delete=True,
)


# ──────────────────────────────────────────────
# Workforce Plan
# ──────────────────────────────────────────────
class WorkforcePlanForm(forms.ModelForm):
    class Meta:
        model = WorkforcePlan
        exclude = ['tenant', 'created_at', 'updated_at', 'plan_number',
                    'created_by', 'total_headcount', 'total_salary_cost',
                    'total_benefit_cost', 'total_cost']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'budget': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['budget'].queryset = Budget.unscoped.filter(tenant=tenant)


class WorkforcePlanPositionForm(forms.ModelForm):
    class Meta:
        model = WorkforcePlanPosition
        exclude = ['tenant', 'created_at', 'updated_at', 'workforce_plan',
                    'benefit_amount', 'total_cost']
        widgets = {
            'position_title': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'headcount': forms.NumberInput(attrs={'class': 'form-control'}),
            'annual_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'benefit_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gl_salary_account': forms.Select(attrs={'class': 'form-select'}),
            'gl_benefit_account': forms.Select(attrs={'class': 'form-select'}),
            'is_new_position': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            gl_qs = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )
            self.fields['gl_salary_account'].queryset = gl_qs
            self.fields['gl_benefit_account'].queryset = gl_qs


WorkforcePlanPositionFormSet = inlineformset_factory(
    WorkforcePlan, WorkforcePlanPosition,
    form=WorkforcePlanPositionForm,
    extra=1, can_delete=True,
)
