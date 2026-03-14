from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# =============================================================================
# 1. Sales Tax Engine
# =============================================================================

class TaxJurisdiction(TenantAwareModel):
    """Defines a geographic tax jurisdiction at various levels."""
    JURISDICTION_LEVEL_CHOICES = [
        ('federal', 'Federal'),
        ('state', 'State'),
        ('county', 'County'),
        ('city', 'City'),
        ('district', 'Special District'),
    ]

    code = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    jurisdiction_level = models.CharField(
        max_length=10, choices=JURISDICTION_LEVEL_CHOICES, default='state'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children'
    )
    country = models.CharField(max_length=100, default='US')
    state_code = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class TaxRate(TenantAwareModel):
    """Tax rate for a jurisdiction with effective dates."""
    jurisdiction = models.ForeignKey(
        TaxJurisdiction, on_delete=models.CASCADE, related_name='rates'
    )
    rate_name = models.CharField(max_length=255)
    rate = models.DecimalField(
        max_digits=8, decimal_places=5, default=Decimal('0.00000'),
        help_text='Tax rate as percentage (e.g., 8.25000 for 8.25%)'
    )
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_compound = models.BooleanField(
        default=False, help_text='If true, this tax is calculated on top of other taxes'
    )
    priority = models.IntegerField(default=0, help_text='Calculation order (lower = first)')
    gl_tax_collected_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='tx_rate_collected',
        help_text='Sales tax payable / tax collected account'
    )
    gl_tax_paid_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='tx_rate_paid',
        help_text='Input tax / tax receivable account'
    )
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.jurisdiction.code} - {self.rate_name} ({self.rate}%)"


class TaxRule(TenantAwareModel):
    """Product/service taxability rules per jurisdiction."""
    RULE_TYPE_CHOICES = [
        ('exempt', 'Exempt'),
        ('reduced', 'Reduced Rate'),
        ('zero_rated', 'Zero Rated'),
        ('standard', 'Standard Rate'),
        ('surtax', 'Surtax'),
    ]

    code = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    jurisdiction = models.ForeignKey(
        TaxJurisdiction, on_delete=models.CASCADE, related_name='rules'
    )
    rule_type = models.CharField(max_length=15, choices=RULE_TYPE_CHOICES, default='standard')
    product_category = models.CharField(
        max_length=100, blank=True,
        help_text='Product/service category this rule applies to'
    )
    rate_override = models.DecimalField(
        max_digits=8, decimal_places=5, null=True, blank=True,
        help_text='Override rate for this rule (leave blank to use jurisdiction default)'
    )
    description = models.TextField(blank=True)
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class TaxGroup(TenantAwareModel):
    """Groups multiple tax rates for combined rate calculation."""
    code = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def combined_rate(self):
        """Calculate the combined rate from all active members."""
        from apps.tax.services import calculate_combined_rate
        return calculate_combined_rate(self)


class TaxGroupMember(models.Model):
    """Junction table linking tax rates to tax groups."""
    tax_group = models.ForeignKey(
        TaxGroup, on_delete=models.CASCADE, related_name='members'
    )
    tax_rate = models.ForeignKey(
        TaxRate, on_delete=models.CASCADE, related_name='group_memberships'
    )
    priority = models.IntegerField(default=0, help_text='Calculation order within the group')

    class Meta:
        ordering = ['priority']
        unique_together = ('tax_group', 'tax_rate')

    def __str__(self):
        return f"{self.tax_group.code} → {self.tax_rate.rate_name}"


# =============================================================================
# 2. Tax Returns
# =============================================================================

class TaxReturn(TenantAwareModel):
    """Tax return header for various tax types."""
    RETURN_TYPE_CHOICES = [
        ('sales_tax', 'Sales Tax'),
        ('vat', 'VAT'),
        ('gst', 'GST'),
        ('income_tax', 'Income Tax'),
        ('payroll_tax', 'Payroll Tax'),
        ('use_tax', 'Use Tax'),
        ('other', 'Other'),
    ]
    PERIOD_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('reviewed', 'Reviewed'),
        ('filed', 'Filed'),
        ('amended', 'Amended'),
    ]

    return_number = models.CharField(max_length=30, db_index=True)
    return_type = models.CharField(max_length=15, choices=RETURN_TYPE_CHOICES)
    jurisdiction = models.ForeignKey(
        TaxJurisdiction, on_delete=models.PROTECT, related_name='tax_returns'
    )
    period_type = models.CharField(max_length=15, choices=PERIOD_TYPE_CHOICES, default='monthly')
    period_start = models.DateField()
    period_end = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')

    total_taxable_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_tax_due = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_credits = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    net_tax_due = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    amount_paid = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    filed_date = models.DateField(null=True, blank=True)
    confirmation_number = models.CharField(max_length=100, blank=True)
    gl_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tx_returns'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        null=True, blank=True, related_name='tx_returns'
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='tx_returns_created'
    )
    filed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tx_returns_filed'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-period_end']
        unique_together = ('tenant', 'return_number')

    def __str__(self):
        return f"{self.return_number} - {self.get_return_type_display()}"

    @staticmethod
    def generate_return_number(tenant):
        from datetime import date
        prefix = f"TR-{date.today().year}-"
        last = TaxReturn.unscoped.filter(
            tenant=tenant, return_number__startswith=prefix
        ).order_by('-return_number').first()
        if last:
            last_num = int(last.return_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"

    @property
    def balance_due(self):
        return self.net_tax_due - self.amount_paid


class TaxReturnLine(models.Model):
    """Individual line item on a tax return."""
    tax_return = models.ForeignKey(
        TaxReturn, on_delete=models.CASCADE, related_name='lines'
    )
    line_number = models.IntegerField()
    description = models.CharField(max_length=500)
    gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        null=True, blank=True, related_name='tx_return_lines'
    )
    taxable_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    tax_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    rate_applied = models.DecimalField(
        max_digits=8, decimal_places=5, default=Decimal('0.00000')
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['line_number']

    def __str__(self):
        return f"Line {self.line_number}: {self.description}"


class TaxReturnPayment(TenantAwareModel):
    """Tracks payments made on tax returns."""
    PAYMENT_METHOD_CHOICES = [
        ('eft', 'EFT'),
        ('check', 'Check'),
        ('wire', 'Wire'),
        ('other', 'Other'),
    ]

    tax_return = models.ForeignKey(
        TaxReturn, on_delete=models.CASCADE, related_name='payments'
    )
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_METHOD_CHOICES, default='eft'
    )
    reference = models.CharField(max_length=100, blank=True)
    gl_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tx_return_payments'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment {self.amount} on {self.payment_date}"


# =============================================================================
# 3. Use Tax Tracking
# =============================================================================

class UseTaxAssessment(TenantAwareModel):
    """Tracks purchases requiring use tax self-assessment."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accrued', 'Accrued'),
        ('paid', 'Paid'),
        ('exempt', 'Exempt'),
    ]

    assessment_number = models.CharField(max_length=30, db_index=True)
    vendor = models.ForeignKey(
        'accounts_payable.Vendor', on_delete=models.PROTECT,
        related_name='use_tax_assessments'
    )
    bill = models.ForeignKey(
        'accounts_payable.Bill', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='use_tax_assessments'
    )
    jurisdiction = models.ForeignKey(
        TaxJurisdiction, on_delete=models.PROTECT, related_name='use_tax_assessments'
    )
    purchase_date = models.DateField()
    purchase_amount = models.DecimalField(max_digits=18, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=8, decimal_places=5)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    gl_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tx_use_tax_assessments'
    )
    gl_use_tax_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='tx_use_tax_liability',
        help_text='Use tax payable account'
    )
    gl_expense_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='tx_use_tax_expense',
        help_text='Expense account for use tax'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='tx_use_tax_created'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-purchase_date']
        unique_together = ('tenant', 'assessment_number')

    def __str__(self):
        return f"{self.assessment_number} - {self.vendor}"

    @staticmethod
    def generate_assessment_number(tenant):
        from datetime import date
        prefix = f"UT-{date.today().year}-"
        last = UseTaxAssessment.unscoped.filter(
            tenant=tenant, assessment_number__startswith=prefix
        ).order_by('-assessment_number').first()
        if last:
            last_num = int(last.assessment_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class UseTaxAccrual(TenantAwareModel):
    """Periodic use tax accrual summary."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ]

    accrual_number = models.CharField(max_length=30, db_index=True)
    period_start = models.DateField()
    period_end = models.DateField()
    total_purchases = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_tax_accrued = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    gl_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tx_use_tax_accruals'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='tx_accruals_created'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-period_end']
        unique_together = ('tenant', 'accrual_number')

    def __str__(self):
        return f"{self.accrual_number} ({self.period_start} - {self.period_end})"

    @staticmethod
    def generate_accrual_number(tenant):
        from datetime import date
        prefix = f"UTA-{date.today().year}-"
        last = UseTaxAccrual.unscoped.filter(
            tenant=tenant, accrual_number__startswith=prefix
        ).order_by('-accrual_number').first()
        if last:
            last_num = int(last.accrual_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 4. Income Tax Provision
# =============================================================================

class IncomeTaxProvision(TenantAwareModel):
    """Current year income tax provision."""
    PROVISION_TYPE_CHOICES = [
        ('current', 'Current Tax'),
        ('deferred', 'Deferred Tax'),
        ('total', 'Total Provision'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('reviewed', 'Reviewed'),
        ('finalized', 'Finalized'),
    ]

    provision_number = models.CharField(max_length=30, db_index=True)
    fiscal_year = models.ForeignKey(
        'company.FiscalYear', on_delete=models.PROTECT, related_name='tx_provisions'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        null=True, blank=True, related_name='tx_provisions'
    )
    provision_type = models.CharField(
        max_length=10, choices=PROVISION_TYPE_CHOICES, default='total'
    )
    pretax_income = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    statutory_rate = models.DecimalField(
        max_digits=8, decimal_places=5, default=Decimal('0.00000'),
        help_text='Statutory tax rate as percentage (e.g., 21.00000%)'
    )
    computed_tax = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00'),
        help_text='pretax_income × statutory_rate'
    )
    permanent_differences = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    temporary_differences = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    tax_credits = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    current_tax_expense = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    deferred_tax_expense = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_tax_expense = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    effective_tax_rate = models.DecimalField(
        max_digits=8, decimal_places=5, default=Decimal('0.00000'),
        help_text='Effective tax rate (total_tax_expense / pretax_income)'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    gl_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tx_provisions'
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='tx_provisions_created'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-fiscal_year__start_date']
        unique_together = ('tenant', 'provision_number')

    def __str__(self):
        return f"{self.provision_number} - {self.get_provision_type_display()}"

    @staticmethod
    def generate_provision_number(tenant):
        from datetime import date
        prefix = f"ITP-{date.today().year}-"
        last = IncomeTaxProvision.unscoped.filter(
            tenant=tenant, provision_number__startswith=prefix
        ).order_by('-provision_number').first()
        if last:
            last_num = int(last.provision_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class DeferredTaxItem(models.Model):
    """Individual temporary difference line item."""
    ITEM_TYPE_CHOICES = [
        ('asset', 'Deferred Tax Asset'),
        ('liability', 'Deferred Tax Liability'),
    ]

    provision = models.ForeignKey(
        IncomeTaxProvision, on_delete=models.CASCADE, related_name='deferred_items'
    )
    description = models.CharField(max_length=255)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    book_basis = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    tax_basis = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    temporary_difference = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    tax_rate = models.DecimalField(
        max_digits=8, decimal_places=5, default=Decimal('0.00000')
    )
    deferred_tax_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        null=True, blank=True, related_name='tx_deferred_items'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.get_item_type_display()}: {self.description}"


class ETRReconciliation(models.Model):
    """Effective tax rate reconciliation line."""
    provision = models.ForeignKey(
        IncomeTaxProvision, on_delete=models.CASCADE, related_name='etr_lines'
    )
    description = models.CharField(max_length=255)
    rate_impact = models.DecimalField(
        max_digits=8, decimal_places=5, default=Decimal('0.00000'),
        help_text='Impact in percentage points'
    )
    amount_impact = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    line_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['line_order']

    def __str__(self):
        return f"{self.description} ({self.rate_impact}%)"


# =============================================================================
# 5. Tax Calendar
# =============================================================================

class TaxDeadline(TenantAwareModel):
    """Individual tax filing deadline."""
    TAX_TYPE_CHOICES = [
        ('sales_tax', 'Sales Tax'),
        ('vat', 'VAT'),
        ('gst', 'GST'),
        ('income_tax', 'Income Tax'),
        ('payroll_tax', 'Payroll Tax'),
        ('property_tax', 'Property Tax'),
        ('use_tax', 'Use Tax'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('in_progress', 'In Progress'),
        ('filed', 'Filed'),
        ('overdue', 'Overdue'),
        ('extended', 'Extended'),
    ]
    RECURRENCE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ]

    deadline_number = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=255)
    tax_type = models.CharField(max_length=15, choices=TAX_TYPE_CHOICES)
    jurisdiction = models.ForeignKey(
        TaxJurisdiction, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='deadlines'
    )
    due_date = models.DateField()
    reminder_days = models.IntegerField(
        default=7, help_text='Send reminder N days before due date'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='upcoming')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tx_deadlines_assigned'
    )
    tax_return = models.ForeignKey(
        TaxReturn, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='deadlines'
    )
    extended_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(
        max_length=15, choices=RECURRENCE_CHOICES, blank=True
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['due_date']
        unique_together = ('tenant', 'deadline_number')

    def __str__(self):
        return f"{self.deadline_number} - {self.name} (Due: {self.due_date})"

    @staticmethod
    def generate_deadline_number(tenant):
        from datetime import date
        prefix = f"TD-{date.today().year}-"
        last = TaxDeadline.unscoped.filter(
            tenant=tenant, deadline_number__startswith=prefix
        ).order_by('-deadline_number').first()
        if last:
            last_num = int(last.deadline_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"

    @property
    def effective_due_date(self):
        return self.extended_date if self.extended_date else self.due_date


class TaxDeadlineReminder(models.Model):
    """Reminder log entry for a tax deadline."""
    deadline = models.ForeignKey(
        TaxDeadline, on_delete=models.CASCADE, related_name='reminders'
    )
    reminder_date = models.DateField()
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tx_reminders_received'
    )

    class Meta:
        ordering = ['-reminder_date']

    def __str__(self):
        return f"Reminder for {self.deadline.name} on {self.reminder_date}"


# =============================================================================
# 6. Audit Support
# =============================================================================

class TaxAudit(TenantAwareModel):
    """Tax audit period tracking."""
    TAX_TYPE_CHOICES = TaxDeadline.TAX_TYPE_CHOICES
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('responded', 'Responded'),
        ('closed_no_change', 'Closed - No Change'),
        ('closed_adjustment', 'Closed - Adjustment'),
        ('appealed', 'Appealed'),
    ]

    audit_number = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=255)
    tax_type = models.CharField(max_length=15, choices=TAX_TYPE_CHOICES)
    jurisdiction = models.ForeignKey(
        TaxJurisdiction, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audits'
    )
    auditing_authority = models.CharField(max_length=255, blank=True)
    audit_period_start = models.DateField()
    audit_period_end = models.DateField()
    notification_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tx_audits_assigned'
    )
    total_proposed_adjustment = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_agreed_adjustment = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    gl_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tx_audits'
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='tx_audits_created'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-audit_period_end']
        unique_together = ('tenant', 'audit_number')

    def __str__(self):
        return f"{self.audit_number} - {self.name}"

    @staticmethod
    def generate_audit_number(tenant):
        from datetime import date
        prefix = f"TA-{date.today().year}-"
        last = TaxAudit.unscoped.filter(
            tenant=tenant, audit_number__startswith=prefix
        ).order_by('-audit_number').first()
        if last:
            last_num = int(last.audit_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class AuditFinding(TenantAwareModel):
    """Individual finding within a tax audit."""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('agreed', 'Agreed'),
        ('disputed', 'Disputed'),
        ('resolved', 'Resolved'),
    ]

    audit = models.ForeignKey(
        TaxAudit, on_delete=models.CASCADE, related_name='findings'
    )
    finding_number = models.IntegerField()
    description = models.TextField()
    proposed_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    agreed_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    response = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['finding_number']

    def __str__(self):
        return f"Finding #{self.finding_number}: {self.description[:50]}"


class AuditDocument(TenantAwareModel):
    """Document attached to a tax audit."""
    DOCUMENT_TYPE_CHOICES = [
        ('notice', 'Notice'),
        ('correspondence', 'Correspondence'),
        ('workpaper', 'Workpaper'),
        ('supporting_doc', 'Supporting Document'),
        ('response', 'Response'),
        ('assessment', 'Assessment'),
        ('other', 'Other'),
    ]

    audit = models.ForeignKey(
        TaxAudit, on_delete=models.CASCADE, related_name='documents'
    )
    name = models.CharField(max_length=255)
    document_type = models.CharField(
        max_length=15, choices=DOCUMENT_TYPE_CHOICES, default='supporting_doc'
    )
    file = models.FileField(upload_to='tax/audit_documents/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tx_audit_docs_uploaded'
    )
    description = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"


# =============================================================================
# 7. Nexus Tracking
# =============================================================================

class NexusJurisdiction(TenantAwareModel):
    """Tracks nexus status per jurisdiction."""
    NEXUS_TYPE_CHOICES = [
        ('physical', 'Physical Presence'),
        ('economic', 'Economic Nexus'),
        ('affiliate', 'Affiliate Nexus'),
        ('click_through', 'Click-Through Nexus'),
    ]
    REGISTRATION_STATUS_CHOICES = [
        ('not_required', 'Not Required'),
        ('pending', 'Pending'),
        ('registered', 'Registered'),
        ('expired', 'Expired'),
    ]

    jurisdiction = models.ForeignKey(
        TaxJurisdiction, on_delete=models.CASCADE, related_name='nexus_tracking'
    )
    nexus_type = models.CharField(max_length=15, choices=NEXUS_TYPE_CHOICES, default='economic')
    has_nexus = models.BooleanField(default=False)
    registration_number = models.CharField(max_length=100, blank=True)
    registration_date = models.DateField(null=True, blank=True)
    registration_status = models.CharField(
        max_length=15, choices=REGISTRATION_STATUS_CHOICES, default='not_required'
    )
    economic_threshold_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00'),
        help_text='Sales threshold amount (e.g., $100,000)'
    )
    economic_threshold_transactions = models.IntegerField(
        default=0, help_text='Transaction count threshold (e.g., 200)'
    )
    current_period_sales = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    current_period_transactions = models.IntegerField(default=0)
    threshold_percentage = models.DecimalField(
        max_digits=7, decimal_places=2, default=Decimal('0.00'),
        help_text='Percentage of threshold reached'
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['jurisdiction__code']
        unique_together = ('tenant', 'jurisdiction', 'nexus_type')

    def __str__(self):
        return f"{self.jurisdiction.code} - {self.get_nexus_type_display()}"

    @property
    def sales_threshold_pct(self):
        if self.economic_threshold_amount and self.economic_threshold_amount > 0:
            return (self.current_period_sales / self.economic_threshold_amount * 100).quantize(
                Decimal('0.01')
            )
        return Decimal('0.00')

    @property
    def transaction_threshold_pct(self):
        if self.economic_threshold_transactions and self.economic_threshold_transactions > 0:
            return Decimal(
                self.current_period_transactions / self.economic_threshold_transactions * 100
            ).quantize(Decimal('0.01'))
        return Decimal('0.00')


class NexusActivity(TenantAwareModel):
    """Log of nexus-relevant activity per period."""
    nexus_jurisdiction = models.ForeignKey(
        NexusJurisdiction, on_delete=models.CASCADE, related_name='activities'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    sales_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    transaction_count = models.IntegerField(default=0)
    has_physical_presence = models.BooleanField(default=False)
    physical_presence_details = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-period_end']

    def __str__(self):
        return f"{self.nexus_jurisdiction} ({self.period_start} - {self.period_end})"
