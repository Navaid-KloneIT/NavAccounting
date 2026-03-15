from django import forms
from django.forms import inlineformset_factory

from apps.company.models import FiscalYear, FiscalPeriod, Currency
from apps.general_ledger.models import Account
from apps.multi_entity.models import Entity, ConsolidationGroup

from .models import (
    FinancialStatement, FinancialStatementLine,
    ManagementReport, ManagementReportLine,
    CustomReport, ReportColumn, ReportFilter,
    ReportSchedule, ScheduleRecipient,
    XBRLFiling, XBRLTag, FilingDocument,
    StatutoryTemplate, StatutoryReport, StatutoryReportLine,
    ConsolidationPackage, ConsolidationPackageEntity, ConsolidationPackageLine,
    ReportDashboard, DashboardWidget, DashboardSnapshot,
)


# =============================================================================
# Financial Statements
# =============================================================================

class FinancialStatementForm(forms.ModelForm):
    class Meta:
        model = FinancialStatement
        exclude = ['tenant', 'created_at', 'updated_at', 'generated_at',
                   'generated_by', 'approved_by', 'approved_at']
        widgets = {
            'statement_number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'statement_type': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_year': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'as_of_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'comparative_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['fiscal_year'].queryset = FiscalYear.unscoped.filter(tenant=tenant)
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                fiscal_year__tenant=tenant
            )
            self.fields['currency'].queryset = Currency.objects.all()


class FinancialStatementLineForm(forms.ModelForm):
    class Meta:
        model = FinancialStatementLine
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'statement': forms.HiddenInput(),
            'line_order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px'}),
            'line_type': forms.Select(attrs={'class': 'form-select'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'indent_level': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px'}),
            'current_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prior_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'variance_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'variance_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_bold': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_underline': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


FinancialStatementLineFormSet = inlineformset_factory(
    FinancialStatement, FinancialStatementLine,
    form=FinancialStatementLineForm,
    extra=1, can_delete=True,
)


# =============================================================================
# Management Reports
# =============================================================================

class ManagementReportForm(forms.ModelForm):
    class Meta:
        model = ManagementReport
        exclude = ['tenant', 'created_at', 'updated_at', 'generated_by', 'generated_at']
        widgets = {
            'report_number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_center': forms.TextInput(attrs={'class': 'form-control'}),
            'fiscal_year': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['fiscal_year'].queryset = FiscalYear.unscoped.filter(tenant=tenant)


class ManagementReportLineForm(forms.ModelForm):
    class Meta:
        model = ManagementReportLine
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'report': forms.HiddenInput(),
            'line_order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'budget_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'actual_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'variance_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'variance_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prior_period_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_favorable': forms.NullBooleanSelect(attrs={'class': 'form-select'}),
        }


ManagementReportLineFormSet = inlineformset_factory(
    ManagementReport, ManagementReportLine,
    form=ManagementReportLineForm,
    extra=1, can_delete=True,
)


# =============================================================================
# Custom Report Builder
# =============================================================================

class CustomReportForm(forms.ModelForm):
    class Meta:
        model = CustomReport
        exclude = ['tenant', 'created_at', 'updated_at', 'created_by']
        widgets = {
            'report_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'base_entity': forms.Select(attrs={'class': 'form-select'}),
            'layout_type': forms.Select(attrs={'class': 'form-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sql_query': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 6}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ReportColumnForm(forms.ModelForm):
    class Meta:
        model = ReportColumn
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'report': forms.HiddenInput(),
            'column_order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px'}),
            'field_name': forms.TextInput(attrs={'class': 'form-control'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'aggregation': forms.Select(attrs={'class': 'form-select'}),
            'format_string': forms.TextInput(attrs={'class': 'form-control'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_sortable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


ReportColumnFormSet = inlineformset_factory(
    CustomReport, ReportColumn,
    form=ReportColumnForm,
    extra=1, can_delete=True,
)


class ReportFilterForm(forms.ModelForm):
    class Meta:
        model = ReportFilter
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'report': forms.HiddenInput(),
            'field_name': forms.TextInput(attrs={'class': 'form-control'}),
            'operator': forms.Select(attrs={'class': 'form-select'}),
            'default_value': forms.TextInput(attrs={'class': 'form-control'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_parameter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'filter_order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px'}),
        }


ReportFilterFormSet = inlineformset_factory(
    CustomReport, ReportFilter,
    form=ReportFilterForm,
    extra=1, can_delete=True,
)


# =============================================================================
# Scheduled Reports
# =============================================================================

class ReportScheduleForm(forms.ModelForm):
    class Meta:
        model = ReportSchedule
        exclude = ['tenant', 'created_at', 'updated_at', 'created_by',
                   'next_run', 'last_run']
        widgets = {
            'schedule_name': forms.TextInput(attrs={'class': 'form-control'}),
            'report': forms.Select(attrs={'class': 'form-select'}),
            'financial_statement': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'day_of_week': forms.NumberInput(attrs={'class': 'form-control'}),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_of_day': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'output_format': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['report'].queryset = CustomReport.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['financial_statement'].queryset = FinancialStatement.unscoped.filter(
                tenant=tenant
            )


class ScheduleRecipientForm(forms.ModelForm):
    class Meta:
        model = ScheduleRecipient
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'schedule': forms.HiddenInput(),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_cc': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


ScheduleRecipientFormSet = inlineformset_factory(
    ReportSchedule, ScheduleRecipient,
    form=ScheduleRecipientForm,
    extra=1, can_delete=True,
)


# =============================================================================
# XBRL/EDGAR Filing
# =============================================================================

class XBRLFilingForm(forms.ModelForm):
    class Meta:
        model = XBRLFiling
        exclude = ['tenant', 'created_at', 'updated_at', 'created_by',
                   'submitted_at', 'accepted_at']
        widgets = {
            'filing_number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'filing_type': forms.Select(attrs={'class': 'form-select'}),
            'cik_number': forms.TextInput(attrs={'class': 'form-control'}),
            'fiscal_year': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'taxonomy_version': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'submission_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['fiscal_year'].queryset = FiscalYear.unscoped.filter(tenant=tenant)


class XBRLTagForm(forms.ModelForm):
    class Meta:
        model = XBRLTag
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'filing': forms.HiddenInput(),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'xbrl_element': forms.TextInput(attrs={'class': 'form-control'}),
            'xbrl_context': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'style': 'width:100px'}),
            'is_extension': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['account'].queryset = Account.unscoped.filter(tenant=tenant)


XBRLTagFormSet = inlineformset_factory(
    XBRLFiling, XBRLTag,
    form=XBRLTagForm,
    extra=1, can_delete=True,
)


class FilingDocumentForm(forms.ModelForm):
    class Meta:
        model = FilingDocument
        exclude = ['tenant', 'created_at', 'updated_at', 'uploaded_at',
                   'uploaded_by', 'file_size']
        widgets = {
            'filing': forms.HiddenInput(),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


# =============================================================================
# Statutory Reporting
# =============================================================================

class StatutoryTemplateForm(forms.ModelForm):
    class Meta:
        model = StatutoryTemplate
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'template_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'framework': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StatutoryReportForm(forms.ModelForm):
    class Meta:
        model = StatutoryReport
        exclude = ['tenant', 'created_at', 'updated_at', 'generated_by',
                   'generated_at', 'filed_date']
        widgets = {
            'report_number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_year': forms.Select(attrs={'class': 'form-select'}),
            'as_of_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'filing_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'filing_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['template'].queryset = StatutoryTemplate.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['fiscal_year'].queryset = FiscalYear.unscoped.filter(tenant=tenant)


class StatutoryReportLineForm(forms.ModelForm):
    class Meta:
        model = StatutoryReportLine
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'report': forms.HiddenInput(),
            'line_order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'local_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reporting_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'adjustment_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'note_reference': forms.TextInput(attrs={'class': 'form-control'}),
        }


StatutoryReportLineFormSet = inlineformset_factory(
    StatutoryReport, StatutoryReportLine,
    form=StatutoryReportLineForm,
    extra=1, can_delete=True,
)


# =============================================================================
# Consolidation Reports
# =============================================================================

class ConsolidationPackageForm(forms.ModelForm):
    class Meta:
        model = ConsolidationPackage
        exclude = ['tenant', 'created_at', 'updated_at', 'generated_by', 'generated_at']
        widgets = {
            'package_number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'consolidation_group': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_year': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reporting_currency': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'include_eliminations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'include_minority_interest': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['consolidation_group'].queryset = ConsolidationGroup.unscoped.filter(
                tenant=tenant
            )
            self.fields['fiscal_year'].queryset = FiscalYear.unscoped.filter(tenant=tenant)
            self.fields['reporting_currency'].queryset = Currency.objects.all()


class ConsolidationPackageEntityForm(forms.ModelForm):
    class Meta:
        model = ConsolidationPackageEntity
        exclude = ['tenant', 'created_at', 'updated_at', 'submitted_at', 'submitted_by']
        widgets = {
            'package': forms.HiddenInput(),
            'entity': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'total_assets': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_liabilities': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_equity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_revenue': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'net_income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['entity'].queryset = Entity.unscoped.filter(
                tenant=tenant, is_active=True
            )


ConsolidationPackageEntityFormSet = inlineformset_factory(
    ConsolidationPackage, ConsolidationPackageEntity,
    form=ConsolidationPackageEntityForm,
    extra=1, can_delete=True,
)


# =============================================================================
# Dashboards
# =============================================================================

class ReportDashboardForm(forms.ModelForm):
    class Meta:
        model = ReportDashboard
        exclude = ['tenant', 'created_at', 'updated_at', 'created_by']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'layout': forms.Select(attrs={'class': 'form-select'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DashboardWidgetForm(forms.ModelForm):
    class Meta:
        model = DashboardWidget
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'dashboard': forms.HiddenInput(),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'widget_type': forms.Select(attrs={'class': 'form-select'}),
            'data_source': forms.Select(attrs={'class': 'form-select'}),
            'position_row': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px'}),
            'position_col': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px'}),
            'config_json': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 4}),
            'refresh_interval': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:100px'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


DashboardWidgetFormSet = inlineformset_factory(
    ReportDashboard, DashboardWidget,
    form=DashboardWidgetForm,
    extra=1, can_delete=True,
)


class DashboardSnapshotForm(forms.ModelForm):
    class Meta:
        model = DashboardSnapshot
        exclude = ['tenant', 'created_at', 'updated_at', 'created_by', 'snapshot_date']
        widgets = {
            'dashboard': forms.HiddenInput(),
            'snapshot_name': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
