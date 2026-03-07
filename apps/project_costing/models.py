from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# =============================================================================
# 1. Project (Master Record)
# =============================================================================

class Project(TenantAwareModel):
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    BILLING_TYPE_CHOICES = [
        ('time_materials', 'Time & Materials'),
        ('fixed_price', 'Fixed Price'),
        ('cost_plus', 'Cost Plus'),
    ]

    project_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    client_name = models.CharField(max_length=255, blank=True)
    client_contact = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='planning')
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES, default='time_materials')

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    contract_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    manager = models.ForeignKey(
        'payroll.Employee', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_projects',
        help_text='Project manager'
    )
    revenue_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='pj_revenue_projects',
        help_text='GL account for project revenue'
    )
    expense_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='pj_expense_projects',
        help_text='GL account for project expenses'
    )
    retention_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        help_text='Retention percentage for billing'
    )
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['project_number']
        unique_together = ('tenant', 'project_number')

    def __str__(self):
        return f"{self.project_number} - {self.name}"

    @staticmethod
    def generate_project_number(tenant):
        prefix = "PJ-"
        last = Project.unscoped.filter(
            tenant=tenant, project_number__startswith=prefix
        ).order_by('-project_number').first()
        if last:
            last_num = int(last.project_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 2. WBS Element (Work Breakdown Structure)
# =============================================================================

class WBSElement(TenantAwareModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='wbs_elements'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children'
    )
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    level = models.PositiveSmallIntegerField(default=1)
    budget_hours = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    is_billable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['display_order', 'code']
        unique_together = ('project', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


# =============================================================================
# 3. Project Budget
# =============================================================================

class ProjectBudget(TenantAwareModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='budgets'
    )
    wbs_element = models.ForeignKey(
        WBSElement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='budget_lines'
    )
    gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='pj_budget_lines'
    )
    description = models.CharField(max_length=255)
    budget_hours = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    budget_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    revised_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pj_budgets'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['project', 'wbs_element', 'gl_account']

    def __str__(self):
        return f"{self.project.project_number} - {self.description}"


# =============================================================================
# 4. Billing Rule
# =============================================================================

class BillingRule(TenantAwareModel):
    RATE_TYPE_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('fixed', 'Fixed'),
        ('percentage', 'Percentage'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='billing_rules'
    )
    description = models.CharField(max_length=255)
    rate_type = models.CharField(max_length=15, choices=RATE_TYPE_CHOICES, default='hourly')
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['project', '-effective_date']

    def __str__(self):
        return f"{self.project.project_number} - {self.description}"


# =============================================================================
# 5. Time Entry
# =============================================================================

class TimeEntry(TenantAwareModel):
    BILLING_STATUS_CHOICES = [
        ('unbilled', 'Unbilled'),
        ('billed', 'Billed'),
        ('non_billable', 'Non-Billable'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='time_entries'
    )
    wbs_element = models.ForeignKey(
        WBSElement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='time_entries'
    )
    employee = models.ForeignKey(
        'payroll.Employee', on_delete=models.PROTECT,
        related_name='pj_time_entries'
    )
    entry_date = models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=2)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    description = models.CharField(max_length=500, blank=True)

    billing_status = models.CharField(
        max_length=15, choices=BILLING_STATUS_CHOICES, default='unbilled'
    )
    is_billable = models.BooleanField(default=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pj_approved_time_entries'
    )
    approved_date = models.DateField(null=True, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-entry_date', 'employee']
        verbose_name_plural = 'Time entries'

    def __str__(self):
        return f"{self.employee} - {self.entry_date} - {self.hours}h"

    def save(self, *args, **kwargs):
        self.total_amount = self.hours * self.hourly_rate
        if not self.is_billable:
            self.billing_status = 'non_billable'
        super().save(*args, **kwargs)


# =============================================================================
# 6. Expense Entry
# =============================================================================

class ExpenseEntry(TenantAwareModel):
    BILLING_STATUS_CHOICES = [
        ('unbilled', 'Unbilled'),
        ('billed', 'Billed'),
        ('non_billable', 'Non-Billable'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='expense_entries'
    )
    wbs_element = models.ForeignKey(
        WBSElement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='expense_entries'
    )
    gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='pj_expense_entries'
    )
    entry_date = models.DateField()
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    vendor_name = models.CharField(max_length=255, blank=True)

    billing_status = models.CharField(
        max_length=15, choices=BILLING_STATUS_CHOICES, default='unbilled'
    )
    is_billable = models.BooleanField(default=True)
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    billed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    receipt_reference = models.CharField(max_length=100, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-entry_date']
        verbose_name_plural = 'Expense entries'

    def __str__(self):
        return f"{self.project.project_number} - {self.entry_date} - {self.description[:50]}"

    def save(self, *args, **kwargs):
        if self.is_billable and self.markup_percentage:
            self.billed_amount = self.amount * (1 + self.markup_percentage / 100)
        elif self.is_billable:
            self.billed_amount = self.amount
        else:
            self.billed_amount = Decimal('0.00')
            self.billing_status = 'non_billable'
        super().save(*args, **kwargs)


# =============================================================================
# 7. Revenue Recognition
# =============================================================================

class RevenueRecognition(TenantAwareModel):
    METHOD_CHOICES = [
        ('percentage_complete', 'Percentage of Completion'),
        ('milestone', 'Milestone-Based'),
        ('completed_contract', 'Completed Contract'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='revenue_recognitions'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        related_name='pj_revenue_recognitions'
    )
    recognition_date = models.DateField()
    method = models.CharField(max_length=25, choices=METHOD_CHOICES, default='percentage_complete')

    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    contract_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_recognized_prior = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    recognized_this_period = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cumulative_recognized = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    gl_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pj_revenue_recognitions'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-recognition_date']

    def __str__(self):
        return f"{self.project.project_number} - {self.recognition_date} - {self.get_method_display()}"

    def calculate(self):
        if self.method == 'percentage_complete':
            self.cumulative_recognized = self.contract_amount * (self.completion_percentage / 100)
            self.recognized_this_period = self.cumulative_recognized - self.total_recognized_prior


# =============================================================================
# 8. Project Milestone
# =============================================================================

class ProjectMilestone(TenantAwareModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('billed', 'Billed'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='milestones'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    target_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['target_date']

    def __str__(self):
        return f"{self.project.project_number} - {self.name}"


# =============================================================================
# 9. Project Invoice
# =============================================================================

class ProjectInvoice(TenantAwareModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('void', 'Void'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='invoices'
    )
    invoice_number = models.CharField(max_length=30, db_index=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    description = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    retention_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pj_invoices'
    )
    gl_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pj_invoices'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-invoice_date']
        unique_together = ('tenant', 'invoice_number')

    def __str__(self):
        return f"{self.invoice_number} - {self.project.name}"

    @staticmethod
    def generate_invoice_number(tenant):
        prefix = "PJI-"
        last = ProjectInvoice.unscoped.filter(
            tenant=tenant, invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        if last:
            last_num = int(last.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 10. Project Invoice Line
# =============================================================================

class ProjectInvoiceLine(models.Model):
    LINE_TYPE_CHOICES = [
        ('time', 'Time'),
        ('expense', 'Expense'),
        ('milestone', 'Milestone'),
        ('other', 'Other'),
    ]

    invoice = models.ForeignKey(
        ProjectInvoice, on_delete=models.CASCADE, related_name='lines'
    )
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    wbs_element = models.ForeignKey(
        WBSElement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invoice_lines'
    )
    line_type = models.CharField(max_length=15, choices=LINE_TYPE_CHOICES, default='other')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.description[:50]} - {self.amount}"

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# =============================================================================
# 11. Profitability Snapshot
# =============================================================================

class ProfitabilitySnapshot(TenantAwareModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='profitability_snapshots'
    )
    snapshot_date = models.DateField()
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pj_profitability_snapshots'
    )

    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    actual_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    committed_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    estimate_at_completion = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    estimate_to_complete = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    earned_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    cost_variance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    schedule_variance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cost_performance_index = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.0000'))
    schedule_performance_index = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.0000'))

    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"{self.project.project_number} - {self.snapshot_date}"


# =============================================================================
# 12. Resource Assignment
# =============================================================================

class ResourceAssignment(TenantAwareModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='resource_assignments'
    )
    wbs_element = models.ForeignKey(
        WBSElement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='resource_assignments'
    )
    employee = models.ForeignKey(
        'payroll.Employee', on_delete=models.PROTECT,
        related_name='pj_resource_assignments'
    )
    role = models.CharField(max_length=100, blank=True)
    allocation_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    planned_hours = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    actual_hours = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['project', 'employee']

    def __str__(self):
        return f"{self.employee} - {self.project.project_number} ({self.allocation_percentage}%)"
