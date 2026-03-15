from django.conf import settings
from django.db import models

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# =============================================================================
# 1. Financial Statements
# =============================================================================

class FinancialStatement(TenantAwareModel):
    """Financial statement record — Balance Sheet, P&L, Cash Flow, Equity."""

    STATEMENT_TYPE_CHOICES = [
        ('balance_sheet', 'Balance Sheet'),
        ('income_statement', 'Income Statement (P&L)'),
        ('cash_flow', 'Cash Flow Statement'),
        ('equity_statement', 'Statement of Changes in Equity'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('published', 'Published'),
    ]

    statement_number = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=255)
    statement_type = models.CharField(max_length=20, choices=STATEMENT_TYPE_CHOICES)
    fiscal_year = models.ForeignKey(
        'company.FiscalYear', on_delete=models.PROTECT, related_name='rc_financial_statements'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        null=True, blank=True, related_name='rc_financial_statements'
    )
    as_of_date = models.DateField(help_text='Reporting date for the statement')
    comparative_date = models.DateField(
        null=True, blank=True, help_text='Prior period date for comparison'
    )
    currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT,
        null=True, blank=True, related_name='rc_financial_statements'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    generated_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_statements_generated'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_statements_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-as_of_date']
        unique_together = ('tenant', 'statement_number')

    def __str__(self):
        return f"{self.statement_number} - {self.name}"


class FinancialStatementLine(TenantAwareModel):
    """Line item within a financial statement."""

    LINE_TYPE_CHOICES = [
        ('header', 'Section Header'),
        ('account', 'Account Line'),
        ('subtotal', 'Subtotal'),
        ('total', 'Total'),
        ('blank', 'Blank Line'),
    ]

    statement = models.ForeignKey(
        FinancialStatement, on_delete=models.CASCADE, related_name='lines'
    )
    line_order = models.IntegerField(default=0)
    line_type = models.CharField(max_length=10, choices=LINE_TYPE_CHOICES, default='account')
    label = models.CharField(max_length=255)
    account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_statement_lines'
    )
    indent_level = models.IntegerField(default=0)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    prior_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    variance_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    variance_percent = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_bold = models.BooleanField(default=False)
    is_underline = models.BooleanField(default=False)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['statement', 'line_order']

    def __str__(self):
        return f"{self.statement.statement_number} - {self.label}"


# =============================================================================
# 2. Management Reports
# =============================================================================

class ManagementReport(TenantAwareModel):
    """Departmental P&L or variance analysis report."""

    REPORT_TYPE_CHOICES = [
        ('departmental_pl', 'Departmental P&L'),
        ('variance_analysis', 'Variance Analysis'),
        ('budget_vs_actual', 'Budget vs Actual'),
        ('trend_analysis', 'Trend Analysis'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('distributed', 'Distributed'),
    ]

    report_number = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    department = models.CharField(max_length=255, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)
    fiscal_year = models.ForeignKey(
        'company.FiscalYear', on_delete=models.PROTECT, related_name='rc_mgmt_reports'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_mgmt_reports_generated'
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-period_end']
        unique_together = ('tenant', 'report_number')

    def __str__(self):
        return f"{self.report_number} - {self.name}"


class ManagementReportLine(TenantAwareModel):
    """Line item with budget vs actual amounts."""

    report = models.ForeignKey(
        ManagementReport, on_delete=models.CASCADE, related_name='lines'
    )
    line_order = models.IntegerField(default=0)
    label = models.CharField(max_length=255)
    account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_mgmt_report_lines'
    )
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    variance_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    variance_percent = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    prior_period_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_favorable = models.BooleanField(null=True, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['report', 'line_order']

    def __str__(self):
        return f"{self.report.report_number} - {self.label}"


# =============================================================================
# 3. Custom Report Builder
# =============================================================================

class CustomReport(TenantAwareModel):
    """User-defined report definition."""

    LAYOUT_CHOICES = [
        ('tabular', 'Tabular'),
        ('summary', 'Summary'),
        ('matrix', 'Matrix / Pivot'),
        ('chart', 'Chart Only'),
    ]

    BASE_ENTITY_CHOICES = [
        ('gl_account', 'GL Accounts'),
        ('journal_entry', 'Journal Entries'),
        ('customer', 'Customers'),
        ('vendor', 'Vendors'),
        ('invoice', 'Invoices'),
        ('bill', 'Bills'),
        ('asset', 'Fixed Assets'),
        ('project', 'Projects'),
        ('employee', 'Employees'),
    ]

    report_code = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    base_entity = models.CharField(max_length=20, choices=BASE_ENTITY_CHOICES)
    layout_type = models.CharField(max_length=10, choices=LAYOUT_CHOICES, default='tabular')
    is_public = models.BooleanField(
        default=False, help_text='Visible to all users in the tenant'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_custom_reports'
    )
    sql_query = models.TextField(
        blank=True, help_text='Optional raw SQL for advanced users'
    )
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['name']
        unique_together = ('tenant', 'report_code')

    def __str__(self):
        return f"{self.report_code} - {self.name}"


class ReportColumn(TenantAwareModel):
    """Column definition for a custom report."""

    AGGREGATION_CHOICES = [
        ('none', 'None'),
        ('sum', 'Sum'),
        ('avg', 'Average'),
        ('count', 'Count'),
        ('min', 'Minimum'),
        ('max', 'Maximum'),
    ]

    report = models.ForeignKey(
        CustomReport, on_delete=models.CASCADE, related_name='columns'
    )
    column_order = models.IntegerField(default=0)
    field_name = models.CharField(max_length=255, help_text='Model field or expression')
    display_name = models.CharField(max_length=255)
    aggregation = models.CharField(max_length=10, choices=AGGREGATION_CHOICES, default='none')
    format_string = models.CharField(
        max_length=50, blank=True, help_text='Python format string (e.g., ,.2f)'
    )
    width = models.IntegerField(default=0, help_text='Column width in pixels (0=auto)')
    is_visible = models.BooleanField(default=True)
    is_sortable = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['report', 'column_order']

    def __str__(self):
        return f"{self.report.report_code} - {self.display_name}"


class ReportFilter(TenantAwareModel):
    """Filter definition for a custom report."""

    OPERATOR_CHOICES = [
        ('eq', 'Equals'),
        ('neq', 'Not Equals'),
        ('gt', 'Greater Than'),
        ('gte', 'Greater Than or Equal'),
        ('lt', 'Less Than'),
        ('lte', 'Less Than or Equal'),
        ('contains', 'Contains'),
        ('startswith', 'Starts With'),
        ('in', 'In List'),
        ('between', 'Between'),
        ('isnull', 'Is Null'),
    ]

    report = models.ForeignKey(
        CustomReport, on_delete=models.CASCADE, related_name='filters'
    )
    field_name = models.CharField(max_length=255)
    operator = models.CharField(max_length=15, choices=OPERATOR_CHOICES, default='eq')
    default_value = models.CharField(max_length=500, blank=True)
    is_required = models.BooleanField(default=False)
    is_parameter = models.BooleanField(
        default=False, help_text='If true, the user is prompted for this value at runtime'
    )
    filter_order = models.IntegerField(default=0)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['report', 'filter_order']

    def __str__(self):
        return f"{self.report.report_code} - {self.field_name} {self.operator}"


# =============================================================================
# 4. Scheduled Reports
# =============================================================================

class ReportSchedule(TenantAwareModel):
    """Schedule for automated report distribution."""

    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]

    OUTPUT_FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('expired', 'Expired'),
    ]

    schedule_name = models.CharField(max_length=255)
    report = models.ForeignKey(
        CustomReport, on_delete=models.CASCADE,
        null=True, blank=True, related_name='schedules',
        help_text='Custom report to schedule'
    )
    financial_statement = models.ForeignKey(
        FinancialStatement, on_delete=models.CASCADE,
        null=True, blank=True, related_name='schedules',
        help_text='Financial statement to schedule'
    )
    frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES, default='monthly')
    day_of_week = models.IntegerField(
        null=True, blank=True, help_text='0=Monday to 6=Sunday (for weekly)'
    )
    day_of_month = models.IntegerField(
        null=True, blank=True, help_text='Day of month (for monthly/quarterly/annually)'
    )
    time_of_day = models.TimeField(
        null=True, blank=True, help_text='Time to run'
    )
    output_format = models.CharField(
        max_length=10, choices=OUTPUT_FORMAT_CHOICES, default='pdf'
    )
    next_run = models.DateTimeField(null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_report_schedules'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['schedule_name']

    def __str__(self):
        return self.schedule_name


class ScheduleRecipient(TenantAwareModel):
    """Email recipient for a scheduled report."""

    schedule = models.ForeignKey(
        ReportSchedule, on_delete=models.CASCADE, related_name='recipients'
    )
    email = models.EmailField()
    name = models.CharField(max_length=255, blank=True)
    is_cc = models.BooleanField(default=False)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['schedule', 'email']
        unique_together = ('schedule', 'email')

    def __str__(self):
        return f"{self.schedule.schedule_name} → {self.email}"


class ScheduleExecution(TenantAwareModel):
    """Execution log for a scheduled report run."""

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    schedule = models.ForeignKey(
        ReportSchedule, on_delete=models.CASCADE, related_name='executions'
    )
    run_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')
    output_file = models.FileField(
        upload_to='reporting/scheduled/', null=True, blank=True
    )
    recipients_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-run_at']

    def __str__(self):
        return f"{self.schedule.schedule_name} @ {self.run_at}"


# =============================================================================
# 5. XBRL/EDGAR Filing
# =============================================================================

class XBRLFiling(TenantAwareModel):
    """SEC/regulatory XBRL filing record."""

    FILING_TYPE_CHOICES = [
        ('10-K', '10-K (Annual Report)'),
        ('10-Q', '10-Q (Quarterly Report)'),
        ('8-K', '8-K (Current Report)'),
        ('20-F', '20-F (Foreign Annual Report)'),
        ('6-K', '6-K (Foreign Current Report)'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('tagging', 'Tagging in Progress'),
        ('validated', 'Validated'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    filing_number = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=255)
    filing_type = models.CharField(max_length=10, choices=FILING_TYPE_CHOICES)
    cik_number = models.CharField(
        max_length=20, blank=True, help_text='SEC Central Index Key'
    )
    fiscal_year = models.ForeignKey(
        'company.FiscalYear', on_delete=models.PROTECT, related_name='rc_xbrl_filings'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    taxonomy_version = models.CharField(
        max_length=50, default='us-gaap-2024',
        help_text='XBRL taxonomy version'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    submission_reference = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_xbrl_filings'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-period_end']
        unique_together = ('tenant', 'filing_number')

    def __str__(self):
        return f"{self.filing_number} - {self.name}"


class XBRLTag(TenantAwareModel):
    """Mapping between GL accounts and XBRL taxonomy elements."""

    filing = models.ForeignKey(
        XBRLFiling, on_delete=models.CASCADE, related_name='tags'
    )
    account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='rc_xbrl_tags'
    )
    xbrl_element = models.CharField(
        max_length=255, help_text='XBRL taxonomy element name (e.g., us-gaap:Assets)'
    )
    xbrl_context = models.CharField(
        max_length=100, blank=True, help_text='XBRL context reference'
    )
    value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, default='USD')
    is_extension = models.BooleanField(
        default=False, help_text='True if this is a company-specific extension element'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['filing', 'xbrl_element']

    def __str__(self):
        return f"{self.filing.filing_number} - {self.xbrl_element}"


class FilingDocument(TenantAwareModel):
    """Document attached to an XBRL filing."""

    DOCUMENT_TYPE_CHOICES = [
        ('instance', 'Instance Document'),
        ('schema', 'Schema'),
        ('calculation', 'Calculation Linkbase'),
        ('definition', 'Definition Linkbase'),
        ('label', 'Label Linkbase'),
        ('presentation', 'Presentation Linkbase'),
        ('reference', 'Reference Linkbase'),
        ('pre', 'Pre-Filing Document'),
        ('other', 'Other'),
    ]

    filing = models.ForeignKey(
        XBRLFiling, on_delete=models.CASCADE, related_name='documents'
    )
    document_type = models.CharField(max_length=15, choices=DOCUMENT_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='reporting/xbrl/')
    file_size = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_filing_documents'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['filing', 'document_type']

    def __str__(self):
        return f"{self.filing.filing_number} - {self.name}"


# =============================================================================
# 6. Statutory Reporting
# =============================================================================

class StatutoryTemplate(TenantAwareModel):
    """Template for jurisdiction-specific financial reports."""

    FRAMEWORK_CHOICES = [
        ('us_gaap', 'US GAAP'),
        ('ifrs', 'IFRS'),
        ('local_gaap', 'Local GAAP'),
        ('tax_basis', 'Tax Basis'),
        ('other', 'Other'),
    ]

    template_code = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    framework = models.CharField(max_length=15, choices=FRAMEWORK_CHOICES, default='us_gaap')
    description = models.TextField(blank=True)
    version = models.CharField(max_length=20, default='1.0')
    effective_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['country', 'template_code']
        unique_together = ('tenant', 'template_code')

    def __str__(self):
        return f"{self.template_code} - {self.name}"


class StatutoryReport(TenantAwareModel):
    """Generated statutory report instance."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('filed', 'Filed'),
    ]

    report_number = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=255)
    template = models.ForeignKey(
        StatutoryTemplate, on_delete=models.PROTECT, related_name='reports'
    )
    fiscal_year = models.ForeignKey(
        'company.FiscalYear', on_delete=models.PROTECT, related_name='rc_statutory_reports'
    )
    as_of_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    filing_deadline = models.DateField(null=True, blank=True)
    filed_date = models.DateField(null=True, blank=True)
    filing_reference = models.CharField(max_length=100, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_statutory_generated'
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-as_of_date']
        unique_together = ('tenant', 'report_number')

    def __str__(self):
        return f"{self.report_number} - {self.name}"


class StatutoryReportLine(TenantAwareModel):
    """Line item in a statutory report."""

    report = models.ForeignKey(
        StatutoryReport, on_delete=models.CASCADE, related_name='lines'
    )
    line_order = models.IntegerField(default=0)
    label = models.CharField(max_length=255)
    account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_statutory_lines'
    )
    local_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text='Amount in local currency'
    )
    reporting_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text='Amount in reporting currency'
    )
    adjustment_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text='Local GAAP adjustment amount'
    )
    note_reference = models.CharField(max_length=50, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['report', 'line_order']

    def __str__(self):
        return f"{self.report.report_number} - {self.label}"


# =============================================================================
# 7. Consolidation Reports
# =============================================================================

class ConsolidationPackage(TenantAwareModel):
    """Group-level reporting package."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('collecting', 'Collecting Data'),
        ('consolidated', 'Consolidated'),
        ('reviewed', 'Reviewed'),
        ('published', 'Published'),
    ]

    package_number = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=255)
    consolidation_group = models.ForeignKey(
        'multi_entity.ConsolidationGroup', on_delete=models.PROTECT,
        related_name='rc_packages'
    )
    fiscal_year = models.ForeignKey(
        'company.FiscalYear', on_delete=models.PROTECT, related_name='rc_consol_packages'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    reporting_currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT,
        null=True, blank=True, related_name='rc_consol_packages'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    include_eliminations = models.BooleanField(default=True)
    include_minority_interest = models.BooleanField(default=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_consol_generated'
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-period_end']
        unique_together = ('tenant', 'package_number')

    def __str__(self):
        return f"{self.package_number} - {self.name}"


class ConsolidationPackageEntity(TenantAwareModel):
    """Entity-level data within a consolidation package."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    package = models.ForeignKey(
        ConsolidationPackage, on_delete=models.CASCADE, related_name='entities'
    )
    entity = models.ForeignKey(
        'multi_entity.Entity', on_delete=models.PROTECT,
        related_name='rc_consol_package_entries'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_consol_entity_submitted'
    )
    total_assets = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_liabilities = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_equity = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['package', 'entity__name']
        unique_together = ('package', 'entity')

    def __str__(self):
        return f"{self.package.package_number} - {self.entity.name}"


class ConsolidationPackageLine(TenantAwareModel):
    """Consolidated line item with eliminations."""

    package = models.ForeignKey(
        ConsolidationPackage, on_delete=models.CASCADE, related_name='lines'
    )
    line_order = models.IntegerField(default=0)
    label = models.CharField(max_length=255)
    account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_consol_lines'
    )
    entity_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text='Sum of entity amounts before eliminations'
    )
    elimination_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text='Intercompany elimination amount'
    )
    minority_interest_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    consolidated_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text='Final consolidated amount'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['package', 'line_order']

    def __str__(self):
        return f"{self.package.package_number} - {self.label}"


# =============================================================================
# 8. Dashboards
# =============================================================================

class ReportDashboard(TenantAwareModel):
    """Executive or operational dashboard configuration."""

    LAYOUT_CHOICES = [
        ('grid_2', '2-Column Grid'),
        ('grid_3', '3-Column Grid'),
        ('grid_4', '4-Column Grid'),
        ('freeform', 'Freeform'),
    ]

    VISIBILITY_CHOICES = [
        ('private', 'Private'),
        ('team', 'Team'),
        ('organization', 'Organization'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    layout = models.CharField(max_length=10, choices=LAYOUT_CHOICES, default='grid_3')
    visibility = models.CharField(
        max_length=15, choices=VISIBILITY_CHOICES, default='private'
    )
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_dashboards'
    )
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DashboardWidget(TenantAwareModel):
    """Widget on a reporting dashboard."""

    WIDGET_TYPE_CHOICES = [
        ('kpi_card', 'KPI Card'),
        ('bar_chart', 'Bar Chart'),
        ('line_chart', 'Line Chart'),
        ('pie_chart', 'Pie Chart'),
        ('donut_chart', 'Donut Chart'),
        ('area_chart', 'Area Chart'),
        ('table', 'Data Table'),
        ('gauge', 'Gauge'),
        ('trend', 'Trend Indicator'),
    ]

    DATA_SOURCE_CHOICES = [
        ('revenue', 'Revenue'),
        ('expenses', 'Expenses'),
        ('net_income', 'Net Income'),
        ('cash_flow', 'Cash Flow'),
        ('ar_aging', 'AR Aging'),
        ('ap_aging', 'AP Aging'),
        ('budget_variance', 'Budget Variance'),
        ('asset_value', 'Asset Value'),
        ('custom_query', 'Custom Query'),
    ]

    dashboard = models.ForeignKey(
        ReportDashboard, on_delete=models.CASCADE, related_name='widgets'
    )
    title = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=15, choices=WIDGET_TYPE_CHOICES, default='kpi_card')
    data_source = models.CharField(max_length=20, choices=DATA_SOURCE_CHOICES)
    position_row = models.IntegerField(default=0)
    position_col = models.IntegerField(default=0)
    width = models.IntegerField(default=1, help_text='Width in grid columns')
    height = models.IntegerField(default=1, help_text='Height in grid rows')
    config_json = models.JSONField(
        default=dict, blank=True,
        help_text='Additional widget configuration (colors, thresholds, etc.)'
    )
    refresh_interval = models.IntegerField(
        default=0, help_text='Auto-refresh interval in seconds (0=disabled)'
    )
    is_visible = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['dashboard', 'position_row', 'position_col']

    def __str__(self):
        return f"{self.dashboard.name} - {self.title}"


class DashboardSnapshot(TenantAwareModel):
    """Point-in-time snapshot of dashboard data."""

    dashboard = models.ForeignKey(
        ReportDashboard, on_delete=models.CASCADE, related_name='snapshots'
    )
    snapshot_name = models.CharField(max_length=255)
    snapshot_date = models.DateTimeField(auto_now_add=True)
    data_json = models.JSONField(
        default=dict, help_text='Captured dashboard data at point in time'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rc_dashboard_snapshots'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"{self.dashboard.name} - {self.snapshot_name}"
