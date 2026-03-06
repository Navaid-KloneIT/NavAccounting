from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# =============================================================================
# 1. Employee Master
# =============================================================================

class Employee(TenantAwareModel):
    """Master record for an employee in the payroll system."""
    PAY_TYPE_CHOICES = [
        ('salary', 'Salary'),
        ('hourly', 'Hourly'),
    ]
    PAY_FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('semimonthly', 'Semi-Monthly'),
        ('monthly', 'Monthly'),
    ]
    FILING_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_of_household', 'Head of Household'),
    ]

    employee_number = models.CharField(max_length=20, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)

    pay_type = models.CharField(max_length=10, choices=PAY_TYPE_CHOICES, default='salary')
    pay_rate = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    pay_frequency = models.CharField(max_length=15, choices=PAY_FREQUENCY_CHOICES, default='biweekly')

    filing_status = models.CharField(
        max_length=20, choices=FILING_STATUS_CHOICES, default='single'
    )
    federal_allowances = models.IntegerField(default=0)
    state_allowances = models.IntegerField(default=0)

    gl_expense_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='pr_employee_expense',
        help_text='GL account for salary/wage expense'
    )
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = ('tenant', 'employee_number')

    def __str__(self):
        return f"{self.employee_number} - {self.last_name}, {self.first_name}"

    @staticmethod
    def generate_employee_number(tenant):
        prefix = "EMP-"
        last = Employee.unscoped.filter(
            tenant=tenant, employee_number__startswith=prefix
        ).order_by('-employee_number').first()
        if last:
            last_num = int(last.employee_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


# =============================================================================
# 2. Payroll Journal
# =============================================================================

class PayrollJournal(TenantAwareModel):
    """A payroll run for a specific pay period."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('approved', 'Approved'),
        ('posted', 'Posted'),
        ('void', 'Void'),
    ]

    journal_number = models.CharField(max_length=30, db_index=True)
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    pay_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')

    total_gross = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_net = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, null=True, blank=True,
        related_name='pr_journals'
    )
    gl_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pr_journals'
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='pr_journals_created'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-pay_date']
        unique_together = ('tenant', 'journal_number')

    def __str__(self):
        return f"{self.journal_number} ({self.pay_period_start} to {self.pay_period_end})"

    @staticmethod
    def generate_journal_number(tenant):
        year = timezone.now().year
        prefix = f"PR-{year}-"
        last = PayrollJournal.unscoped.filter(
            tenant=tenant, journal_number__startswith=prefix
        ).order_by('-journal_number').first()
        if last:
            last_num = int(last.journal_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class PayrollJournalLine(models.Model):
    """Individual employee pay detail within a payroll journal."""
    payroll_journal = models.ForeignKey(
        PayrollJournal, on_delete=models.CASCADE, related_name='lines'
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name='payroll_lines'
    )

    regular_hours = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    gross_pay = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    overtime_pay = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    federal_tax = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    state_tax = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    local_tax = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    social_security = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    medicare = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    benefits_deduction = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    garnishment_deduction = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    other_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_pay = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ['employee__last_name']

    def __str__(self):
        return f"{self.employee} - {self.payroll_journal.journal_number}"


# =============================================================================
# 3. Tax Management
# =============================================================================

TAX_TYPE_CHOICES = [
    ('federal', 'Federal Income Tax'),
    ('state', 'State Income Tax'),
    ('local', 'Local Income Tax'),
    ('social_security', 'Social Security (FICA)'),
    ('medicare', 'Medicare'),
    ('futa', 'Federal Unemployment (FUTA)'),
    ('suta', 'State Unemployment (SUTA)'),
]


class TaxWithholding(TenantAwareModel):
    """Tax withholding configuration for an employee."""
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='tax_withholdings'
    )
    tax_type = models.CharField(max_length=20, choices=TAX_TYPE_CHOICES)
    rate = models.DecimalField(
        max_digits=7, decimal_places=4, default=Decimal('0.0000'),
        help_text='Withholding rate as a percentage (e.g. 22.0000 = 22%)'
    )
    ytd_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    annual_limit = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text='Annual wage base limit (e.g. Social Security cap)'
    )
    is_employer_paid = models.BooleanField(
        default=False, help_text='If true, this is an employer-side tax (FUTA, SUTA)'
    )
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['employee', 'tax_type']
        unique_together = ('tenant', 'employee', 'tax_type', 'effective_date')

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_tax_type_display()}"


class TaxRemittance(TenantAwareModel):
    """Tracking of tax remittance payments to government agencies."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]

    remittance_number = models.CharField(max_length=30, db_index=True)
    tax_type = models.CharField(max_length=20, choices=TAX_TYPE_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    amount_due = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    gl_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pr_tax_remittances'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-due_date']
        unique_together = ('tenant', 'remittance_number')

    def __str__(self):
        return f"{self.remittance_number} - {self.get_tax_type_display()}"

    @staticmethod
    def generate_remittance_number(tenant):
        year = timezone.now().year
        prefix = f"TR-{year}-"
        last = TaxRemittance.unscoped.filter(
            tenant=tenant, remittance_number__startswith=prefix
        ).order_by('-remittance_number').first()
        if last:
            last_num = int(last.remittance_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 4. Benefits Accounting
# =============================================================================

class BenefitPlan(TenantAwareModel):
    """A benefit plan offered by the company."""
    BENEFIT_TYPE_CHOICES = [
        ('401k', '401(k)'),
        ('health_insurance', 'Health Insurance'),
        ('dental', 'Dental Insurance'),
        ('vision', 'Vision Insurance'),
        ('life', 'Life Insurance'),
        ('hsa', 'HSA'),
        ('fsa', 'FSA'),
        ('other', 'Other'),
    ]
    CONTRIBUTION_TYPE_CHOICES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage of Gross'),
        ('match', 'Employer Match'),
    ]

    code = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    benefit_type = models.CharField(max_length=20, choices=BENEFIT_TYPE_CHOICES)
    description = models.TextField(blank=True)

    employer_contribution_type = models.CharField(
        max_length=12, choices=CONTRIBUTION_TYPE_CHOICES, default='fixed'
    )
    employer_contribution_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text='Fixed amount or percentage depending on contribution type'
    )
    employer_match_limit = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text='Maximum employer match per period (for 401k match type)'
    )

    gl_expense_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='pr_benefit_expense',
        help_text='GL account for employer benefit expense'
    )
    gl_liability_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='pr_benefit_liability',
        help_text='GL account for benefit liability/payable'
    )
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class EmployeeBenefit(models.Model):
    """Enrollment of an employee in a benefit plan."""
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='benefits'
    )
    benefit_plan = models.ForeignKey(
        BenefitPlan, on_delete=models.PROTECT, related_name='enrollments'
    )
    employee_contribution = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text='Employee contribution per pay period'
    )
    enrollment_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['employee', 'benefit_plan']
        unique_together = ('employee', 'benefit_plan')

    def __str__(self):
        return f"{self.employee.full_name} - {self.benefit_plan.name}"


# =============================================================================
# 5. Garnishments
# =============================================================================

class Garnishment(TenantAwareModel):
    """Court-ordered deduction for an employee."""
    GARNISHMENT_TYPE_CHOICES = [
        ('child_support', 'Child Support'),
        ('tax_levy', 'Tax Levy'),
        ('student_loan', 'Student Loan'),
        ('creditor', 'Creditor Garnishment'),
        ('bankruptcy', 'Bankruptcy'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('suspended', 'Suspended'),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='garnishments'
    )
    garnishment_type = models.CharField(max_length=15, choices=GARNISHMENT_TYPE_CHOICES)
    case_number = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text='Deduction amount per period (or percentage if is_percentage)'
    )
    is_percentage = models.BooleanField(default=False)
    max_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('25.00'),
        help_text='Maximum percentage of disposable income'
    )
    priority = models.IntegerField(
        default=1, help_text='Deduction priority order (lower = higher priority)'
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    total_required = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text='Total amount required to satisfy the garnishment'
    )
    total_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='active')
    issuing_authority = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['employee', 'priority']

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_garnishment_type_display()} ({self.case_number})"

    @property
    def remaining_balance(self):
        if self.total_required > 0:
            return self.total_required - self.total_paid
        return Decimal('0.00')


# =============================================================================
# 6. Workers Comp
# =============================================================================

class WorkersCompClass(TenantAwareModel):
    """Workers compensation classification code."""
    code = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rate = models.DecimalField(
        max_digits=8, decimal_places=4, default=Decimal('0.0000'),
        help_text='Rate per $100 of payroll'
    )
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    gl_expense_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='pr_workers_comp_expense',
        help_text='GL account for workers comp expense'
    )
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')
        verbose_name = 'Workers comp class'
        verbose_name_plural = 'Workers comp classes'

    def __str__(self):
        return f"{self.code} - {self.name}"


class WorkersCompAssignment(models.Model):
    """Assignment of an employee to a workers comp class."""
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='workers_comp_assignments'
    )
    comp_class = models.ForeignKey(
        WorkersCompClass, on_delete=models.PROTECT, related_name='assignments'
    )
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['employee', '-effective_date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.comp_class.code}"


# =============================================================================
# 7. Payroll Reconciliation
# =============================================================================

class PayrollReconciliation(TenantAwareModel):
    """Gross-to-net payroll reconciliation record."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('reconciled', 'Reconciled'),
        ('exception', 'Exception'),
    ]

    reconciliation_number = models.CharField(max_length=30, db_index=True)
    payroll_journal = models.ForeignKey(
        PayrollJournal, on_delete=models.PROTECT, related_name='reconciliations'
    )
    reconciliation_date = models.DateField()

    total_gross = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_taxes = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_benefits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_garnishments = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_net = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    variance_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='pr_reconciliations', null=True, blank=True
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-reconciliation_date']
        unique_together = ('tenant', 'reconciliation_number')

    def __str__(self):
        return f"{self.reconciliation_number} - {self.payroll_journal.journal_number}"

    @staticmethod
    def generate_reconciliation_number(tenant):
        year = timezone.now().year
        prefix = f"REC-{year}-"
        last = PayrollReconciliation.unscoped.filter(
            tenant=tenant, reconciliation_number__startswith=prefix
        ).order_by('-reconciliation_number').first()
        if last:
            last_num = int(last.reconciliation_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"
