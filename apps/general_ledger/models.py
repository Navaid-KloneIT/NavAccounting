from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# =============================================================================
# 1. Chart of Accounts
# =============================================================================

class Account(TenantAwareModel):
    """Tenant-specific chart of accounts entry."""
    account_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    account_type = models.ForeignKey(
        'company.AccountType',
        on_delete=models.PROTECT,
        related_name='gl_accounts'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_header = models.BooleanField(default=False)
    currency = models.ForeignKey(
        'company.Currency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    display_order = models.PositiveSmallIntegerField(default=0)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['display_order', 'account_number']
        unique_together = ('tenant', 'account_number')

    def __str__(self):
        return f"{self.account_number} - {self.name}"

    @property
    def balance(self):
        """Compute current balance from all posted journal entry lines."""
        lines = JournalEntryLine.objects.filter(
            account=self,
            journal_entry__status='posted'
        )
        totals = lines.aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        debit = totals['total_debit'] or Decimal('0.00')
        credit = totals['total_credit'] or Decimal('0.00')
        if self.account_type.normal_balance == 'debit':
            return debit - credit
        return credit - debit

    def get_ancestors(self):
        """Return list of parent accounts up to root."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """Return flat list of all child accounts recursively."""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


# =============================================================================
# 2. Journal Entries
# =============================================================================

class JournalEntry(TenantAwareModel):
    """A complete journal entry (header)."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('posted', 'Posted'),
        ('rejected', 'Rejected'),
    ]
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('system', 'System Generated'),
        ('recurring', 'Recurring'),
        ('allocation', 'Allocation'),
        ('closing', 'Period Close'),
        ('ap_payment', 'AP Payment'),
        ('ar_receipt', 'AR Receipt'),
        ('ar_credit_memo', 'AR Credit Memo'),
        ('ar_write_off', 'AR Write-Off'),
        ('cm_transfer', 'Cash Management Transfer'),
        ('cm_bank_fee', 'Bank Fee'),
        ('fa_acquisition', 'FA Acquisition'),
        ('fa_depreciation', 'FA Depreciation'),
        ('fa_disposal', 'FA Disposal'),
        ('fa_impairment', 'FA Impairment'),
    ]

    entry_number = models.CharField(max_length=20, db_index=True)
    date = models.DateField()
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True)
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod',
        on_delete=models.PROTECT,
        related_name='journal_entries'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    currency = models.ForeignKey(
        'company.Currency',
        on_delete=models.PROTECT,
        related_name='+'
    )
    exchange_rate = models.DecimalField(
        max_digits=18, decimal_places=8, default=Decimal('1.00000000')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='journal_entries_created'
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entries_posted'
    )
    posted_at = models.DateTimeField(null=True, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-date', '-entry_number']
        unique_together = ('tenant', 'entry_number')
        verbose_name_plural = 'Journal entries'

    def __str__(self):
        return f"{self.entry_number} - {self.description[:50]}"

    def clean(self):
        if self.fiscal_period_id:
            if self.fiscal_period.is_closed:
                raise ValidationError('Cannot create journal entry in a closed period.')
            if self.date and not (self.fiscal_period.start_date <= self.date <= self.fiscal_period.end_date):
                raise ValidationError('Journal entry date must be within the fiscal period.')

    @property
    def total_debits(self):
        return self.lines.aggregate(total=Sum('debit'))['total'] or Decimal('0.00')

    @property
    def total_credits(self):
        return self.lines.aggregate(total=Sum('credit'))['total'] or Decimal('0.00')

    @property
    def is_balanced(self):
        return self.total_debits == self.total_credits

    @staticmethod
    def generate_entry_number(tenant):
        """Generate JE-YYYY-NNNN for the tenant."""
        from django.utils import timezone
        year = timezone.now().year
        prefix = f"JE-{year}-"
        last_entry = JournalEntry.unscoped.filter(
            tenant=tenant,
            entry_number__startswith=prefix
        ).order_by('-entry_number').first()
        if last_entry:
            last_num = int(last_entry.entry_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class JournalEntryLine(models.Model):
    """Individual debit/credit line within a journal entry."""
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='journal_lines'
    )
    description = models.CharField(max_length=500, blank=True)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    currency = models.ForeignKey(
        'company.Currency',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+'
    )
    exchange_rate = models.DecimalField(
        max_digits=18, decimal_places=8, default=Decimal('1.00000000')
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.account} - Dr:{self.debit} Cr:{self.credit}"

    def clean(self):
        if self.debit < 0 or self.credit < 0:
            raise ValidationError('Debit and credit amounts must be non-negative.')
        if self.debit > 0 and self.credit > 0:
            raise ValidationError('A line cannot have both debit and credit amounts.')
        if self.debit == 0 and self.credit == 0:
            raise ValidationError('A line must have either a debit or credit amount.')
        if self.account_id and self.account.is_header:
            raise ValidationError('Cannot post to a header account.')


# =============================================================================
# 3. Journal Approval
# =============================================================================

class JournalApproval(TenantAwareModel):
    """Approval record for a journal entry."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='journal_approvals'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Approval for {self.journal_entry.entry_number} by {self.approver}"


# =============================================================================
# 4. Period Close
# =============================================================================

class PeriodCloseChecklist(TenantAwareModel):
    """Checklist steps for closing a fiscal period."""
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod',
        on_delete=models.CASCADE,
        related_name='close_checklist'
    )
    step_name = models.CharField(max_length=255)
    step_order = models.PositiveSmallIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['step_order']
        unique_together = ('fiscal_period', 'step_name', 'tenant')

    def __str__(self):
        return f"{self.fiscal_period} - {self.step_name}"


# =============================================================================
# 5. Account Reconciliation
# =============================================================================

class AccountReconciliation(TenantAwareModel):
    """Reconciliation record for an account in a period."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reconciled', 'Reconciled'),
        ('discrepancy', 'Discrepancy'),
    ]

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='reconciliations'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod',
        on_delete=models.PROTECT,
        related_name='reconciliations'
    )
    expected_balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    actual_balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    difference = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    reconciled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-fiscal_period__period_number']
        unique_together = ('account', 'fiscal_period', 'tenant')

    def __str__(self):
        return f"Reconciliation: {self.account} - {self.fiscal_period}"

    def save(self, *args, **kwargs):
        self.difference = self.expected_balance - self.actual_balance
        if self.difference == Decimal('0.00') and self.actual_balance != Decimal('0.00'):
            self.status = 'reconciled'
        elif self.difference != Decimal('0.00'):
            self.status = 'discrepancy'
        super().save(*args, **kwargs)


# =============================================================================
# 6. Allocation Rules
# =============================================================================

class AllocationRule(TenantAwareModel):
    """Rule for allocating amounts from a source account to targets."""
    name = models.CharField(max_length=255)
    source_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='allocation_rules_as_source'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['name']
        unique_together = ('tenant', 'name')

    def __str__(self):
        return self.name


class AllocationRuleLine(models.Model):
    """Individual target in an allocation rule."""
    rule = models.ForeignKey(
        AllocationRule,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    target_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='allocation_rules_as_target'
    )
    percentage = models.DecimalField(
        max_digits=7, decimal_places=4, default=Decimal('0.0000')
    )
    fixed_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.target_account} - {self.percentage}%"


# =============================================================================
# 7. Audit Trail
# =============================================================================

class AuditTrail(TenantAwareModel):
    """Immutable audit log of all GL changes."""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    table_name = models.CharField(max_length=100, db_index=True)
    record_id = models.PositiveIntegerField()
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='+'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
        ]

    def __str__(self):
        return f"{self.action} {self.table_name}#{self.record_id} at {self.timestamp}"


# =============================================================================
# 8. Multi-Currency Support
# =============================================================================

class ExchangeRate(TenantAwareModel):
    """Historical exchange rates between currency pairs."""
    from_currency = models.ForeignKey(
        'company.Currency',
        on_delete=models.PROTECT,
        related_name='rates_from'
    )
    to_currency = models.ForeignKey(
        'company.Currency',
        on_delete=models.PROTECT,
        related_name='rates_to'
    )
    rate = models.DecimalField(max_digits=18, decimal_places=8)
    effective_date = models.DateField(db_index=True)
    source = models.CharField(max_length=100, blank=True, default='manual')

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-effective_date']
        unique_together = ('tenant', 'from_currency', 'to_currency', 'effective_date')

    def __str__(self):
        return f"{self.from_currency.code}/{self.to_currency.code} = {self.rate} ({self.effective_date})"

    @staticmethod
    def get_rate(from_currency, to_currency, date, tenant):
        """Get the most recent exchange rate for a currency pair on or before a given date."""
        if from_currency == to_currency:
            return Decimal('1.00000000')
        rate_obj = ExchangeRate.unscoped.filter(
            tenant=tenant,
            from_currency=from_currency,
            to_currency=to_currency,
            effective_date__lte=date
        ).order_by('-effective_date').first()
        if rate_obj:
            return rate_obj.rate
        return None
