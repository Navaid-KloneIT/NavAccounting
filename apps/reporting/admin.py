from django.contrib import admin

from .models import (
    FinancialStatement, FinancialStatementLine,
    ManagementReport, ManagementReportLine,
    CustomReport, ReportColumn, ReportFilter,
    ReportSchedule, ScheduleRecipient, ScheduleExecution,
    XBRLFiling, XBRLTag, FilingDocument,
    StatutoryTemplate, StatutoryReport, StatutoryReportLine,
    ConsolidationPackage, ConsolidationPackageEntity, ConsolidationPackageLine,
    ReportDashboard, DashboardWidget, DashboardSnapshot,
)


# =============================================================================
# Financial Statements
# =============================================================================

class FinancialStatementLineInline(admin.TabularInline):
    model = FinancialStatementLine
    extra = 0


@admin.register(FinancialStatement)
class FinancialStatementAdmin(admin.ModelAdmin):
    list_display = ('statement_number', 'name', 'statement_type', 'fiscal_year',
                    'as_of_date', 'status', 'tenant')
    list_filter = ('statement_type', 'status', 'tenant')
    search_fields = ('statement_number', 'name')
    ordering = ['-as_of_date']
    inlines = [FinancialStatementLineInline]


# =============================================================================
# Management Reports
# =============================================================================

class ManagementReportLineInline(admin.TabularInline):
    model = ManagementReportLine
    extra = 0


@admin.register(ManagementReport)
class ManagementReportAdmin(admin.ModelAdmin):
    list_display = ('report_number', 'name', 'report_type', 'department',
                    'period_start', 'period_end', 'status', 'tenant')
    list_filter = ('report_type', 'status', 'tenant')
    search_fields = ('report_number', 'name', 'department')
    ordering = ['-period_end']
    inlines = [ManagementReportLineInline]


# =============================================================================
# Custom Report Builder
# =============================================================================

class ReportColumnInline(admin.TabularInline):
    model = ReportColumn
    extra = 0


class ReportFilterInline(admin.TabularInline):
    model = ReportFilter
    extra = 0


@admin.register(CustomReport)
class CustomReportAdmin(admin.ModelAdmin):
    list_display = ('report_code', 'name', 'base_entity', 'layout_type',
                    'is_public', 'is_active', 'tenant')
    list_filter = ('base_entity', 'layout_type', 'is_public', 'is_active', 'tenant')
    search_fields = ('report_code', 'name')
    ordering = ['name']
    inlines = [ReportColumnInline, ReportFilterInline]


# =============================================================================
# Scheduled Reports
# =============================================================================

class ScheduleRecipientInline(admin.TabularInline):
    model = ScheduleRecipient
    extra = 0


class ScheduleExecutionInline(admin.TabularInline):
    model = ScheduleExecution
    extra = 0


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ('schedule_name', 'frequency', 'output_format',
                    'next_run', 'last_run', 'status', 'is_active', 'tenant')
    list_filter = ('frequency', 'status', 'is_active', 'tenant')
    search_fields = ('schedule_name',)
    ordering = ['schedule_name']
    inlines = [ScheduleRecipientInline, ScheduleExecutionInline]


# =============================================================================
# XBRL/EDGAR Filing
# =============================================================================

class XBRLTagInline(admin.TabularInline):
    model = XBRLTag
    extra = 0


class FilingDocumentInline(admin.TabularInline):
    model = FilingDocument
    extra = 0


@admin.register(XBRLFiling)
class XBRLFilingAdmin(admin.ModelAdmin):
    list_display = ('filing_number', 'name', 'filing_type', 'cik_number',
                    'period_start', 'period_end', 'status', 'tenant')
    list_filter = ('filing_type', 'status', 'tenant')
    search_fields = ('filing_number', 'name', 'cik_number')
    ordering = ['-period_end']
    inlines = [XBRLTagInline, FilingDocumentInline]


# =============================================================================
# Statutory Reporting
# =============================================================================

@admin.register(StatutoryTemplate)
class StatutoryTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_code', 'name', 'country', 'framework',
                    'version', 'is_active', 'tenant')
    list_filter = ('framework', 'country', 'is_active', 'tenant')
    search_fields = ('template_code', 'name', 'country')
    ordering = ['country', 'template_code']


class StatutoryReportLineInline(admin.TabularInline):
    model = StatutoryReportLine
    extra = 0


@admin.register(StatutoryReport)
class StatutoryReportAdmin(admin.ModelAdmin):
    list_display = ('report_number', 'name', 'template', 'fiscal_year',
                    'as_of_date', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('report_number', 'name')
    ordering = ['-as_of_date']
    inlines = [StatutoryReportLineInline]


# =============================================================================
# Consolidation Reports
# =============================================================================

class ConsolidationPackageEntityInline(admin.TabularInline):
    model = ConsolidationPackageEntity
    extra = 0


class ConsolidationPackageLineInline(admin.TabularInline):
    model = ConsolidationPackageLine
    extra = 0


@admin.register(ConsolidationPackage)
class ConsolidationPackageAdmin(admin.ModelAdmin):
    list_display = ('package_number', 'name', 'consolidation_group',
                    'period_start', 'period_end', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('package_number', 'name')
    ordering = ['-period_end']
    inlines = [ConsolidationPackageEntityInline, ConsolidationPackageLineInline]


# =============================================================================
# Dashboards
# =============================================================================

class DashboardWidgetInline(admin.TabularInline):
    model = DashboardWidget
    extra = 0


@admin.register(ReportDashboard)
class ReportDashboardAdmin(admin.ModelAdmin):
    list_display = ('name', 'layout', 'visibility', 'is_default',
                    'is_active', 'tenant')
    list_filter = ('layout', 'visibility', 'is_default', 'is_active', 'tenant')
    search_fields = ('name',)
    ordering = ['name']
    inlines = [DashboardWidgetInline]


@admin.register(DashboardSnapshot)
class DashboardSnapshotAdmin(admin.ModelAdmin):
    list_display = ('dashboard', 'snapshot_name', 'snapshot_date',
                    'created_by', 'tenant')
    list_filter = ('tenant',)
    search_fields = ('snapshot_name',)
    ordering = ['-snapshot_date']
