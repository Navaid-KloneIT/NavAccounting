from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# =============================================================================
# 1. Bank Account Management
# =============================================================================

class BankAccount(TenantAwareModel):
    """Bank account linked to a GL account for cash management."""
    ACCOUNT_TYPE_CHOICES = [
        ('checking', 'Checking'),
        ('savings', 'Savings'),
        ('money_market', 'Money Market'),
        ('credit_line', 'Credit Line'),
    ]

    account_number_display = models.CharField(max_length=20, db_index=True)
    gl_account = models.ForeignKey(
        'general_ledger.Account',
        on_delete=models.PROTECT,
        related_name='bank_accounts'
    )
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    account_number_masked = models.CharField(max_length=20, blank=True)
    routing_number = models.CharField(max_length=20, blank=True)
    account_type = models.CharField(
        max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='checking'
    )
    swift_bic = models.CharField(max_length=11, blank=True, verbose_name='SWIFT/BIC')
    iban = models.CharField(max_length=34, blank=True, verbose_name='IBAN')
    currency = models.ForeignKey(
        'company.Currency',
        on_delete=models.PROTECT,
        related_name='+'
    )
    opening_balance = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    current_balance = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['account_number_display']
        unique_together = ('tenant', 'account_number_display')

    def __str__(self):
        return f"{self.account_number_display} - {self.bank_name}"

    def save(self, *args, **kwargs):
        if self.account_number and not self.account_number_masked:
            self.account_number_masked = '****' + self.account_number[-4:]
        super().save(*args, **kwargs)

    @staticmethod
    def generate_account_number(tenant):
        prefix = "BNK-"
        last = BankAccount.unscoped.filter(
            tenant=tenant, account_number_display__startswith=prefix
        ).order_by('-account_number_display').first()
        if last:
            last_num = int(last.account_number_display.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class BankAccountSignatory(models.Model):
    """Authorized signatories for a bank account."""
    SIGNATURE_LEVEL_CHOICES = [
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
    ]

    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name='signatories'
    )
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=100, blank=True)
    signature_level = models.CharField(
        max_length=20, choices=SIGNATURE_LEVEL_CHOICES, default='primary'
    )
    authorization_limit = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['signature_level', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_signature_level_display()})"


# =============================================================================
# 2. Bank Feeds & Transaction Import
# =============================================================================

class BankFeed(TenantAwareModel):
    """Configuration for automated bank transaction import."""
    FEED_SOURCE_CHOICES = [
        ('manual_csv', 'Manual CSV'),
        ('ofx', 'OFX/QFX'),
        ('plaid', 'Plaid'),
        ('yodlee', 'Yodlee'),
        ('open_banking', 'Open Banking'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('error', 'Error'),
    ]

    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name='feeds'
    )
    feed_source = models.CharField(
        max_length=20, choices=FEED_SOURCE_CHOICES, default='manual_csv'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active'
    )
    last_sync_at = models.DateTimeField(null=True, blank=True)
    connection_config = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-last_sync_at']

    def __str__(self):
        return f"{self.bank_account} - {self.get_feed_source_display()}"


class BankTransaction(TenantAwareModel):
    """Individual bank transaction (imported or manually entered)."""
    TRANSACTION_TYPE_CHOICES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    transaction_number = models.CharField(max_length=20, db_index=True)
    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name='transactions'
    )
    transaction_date = models.DateField()
    post_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_TYPE_CHOICES
    )
    description = models.CharField(max_length=500)
    reference = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    is_matched = models.BooleanField(default=False)
    matched_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='matched_bank_transactions'
    )
    import_batch = models.CharField(max_length=50, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-transaction_date', '-transaction_number']
        unique_together = ('tenant', 'transaction_number')

    def __str__(self):
        return f"{self.transaction_number} - {self.description[:50]}"

    @staticmethod
    def generate_transaction_number(tenant):
        year = timezone.now().year
        prefix = f"BTX-{year}-"
        last = BankTransaction.unscoped.filter(
            tenant=tenant, transaction_number__startswith=prefix
        ).order_by('-transaction_number').first()
        if last:
            last_num = int(last.transaction_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 3. Reconciliation Engine
# =============================================================================

class BankReconciliation(TenantAwareModel):
    """Bank statement reconciliation for a specific account and period."""
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
    ]

    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name='reconciliations'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod',
        on_delete=models.PROTECT,
        related_name='bank_reconciliations'
    )
    statement_date = models.DateField()
    statement_balance = models.DecimalField(max_digits=18, decimal_places=2)
    gl_balance = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    adjusted_balance = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='in_progress'
    )
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='bank_reconciliations'
    )
    reconciled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-statement_date']
        unique_together = ('tenant', 'bank_account', 'fiscal_period')

    def __str__(self):
        return f"Recon: {self.bank_account} - {self.fiscal_period}"

    @property
    def difference(self):
        return self.statement_balance - self.adjusted_balance


class ReconciliationItem(models.Model):
    """Individual matched/unmatched item within a reconciliation."""
    MATCH_TYPE_CHOICES = [
        ('auto', 'Auto-matched'),
        ('manual', 'Manual'),
        ('exception', 'Exception'),
    ]
    STATUS_CHOICES = [
        ('matched', 'Matched'),
        ('unmatched', 'Unmatched'),
        ('exception', 'Exception'),
    ]

    reconciliation = models.ForeignKey(
        BankReconciliation, on_delete=models.CASCADE, related_name='items'
    )
    bank_transaction = models.ForeignKey(
        BankTransaction,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reconciliation_items'
    )
    journal_entry_line = models.ForeignKey(
        'general_ledger.JournalEntryLine',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reconciliation_items'
    )
    match_type = models.CharField(
        max_length=20, choices=MATCH_TYPE_CHOICES, default='manual'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='unmatched'
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        ordering = ['status', '-amount']

    def __str__(self):
        return f"Item: {self.amount} ({self.get_status_display()})"


class AutoMatchRule(TenantAwareModel):
    """Rules for automatically matching bank transactions to GL entries."""
    RULE_TYPE_CHOICES = [
        ('exact_amount', 'Exact Amount'),
        ('reference_match', 'Reference Match'),
        ('date_range', 'Date Range'),
        ('description_pattern', 'Description Pattern'),
    ]

    name = models.CharField(max_length=255)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPE_CHOICES)
    pattern = models.JSONField(default=dict)
    priority = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['priority', 'name']

    def __str__(self):
        return self.name


# =============================================================================
# 4. Treasury Forecasting
# =============================================================================

class CashForecast(TenantAwareModel):
    """Cash flow forecast for planning purposes."""
    FORECAST_TYPE_CHOICES = [
        ('short_term', 'Short Term'),
        ('long_term', 'Long Term'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]

    forecast_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    forecast_type = models.CharField(
        max_length=20, choices=FORECAST_TYPE_CHOICES, default='short_term'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='cash_forecasts'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-start_date']
        unique_together = ('tenant', 'forecast_number')

    def __str__(self):
        return f"{self.forecast_number} - {self.name}"

    @staticmethod
    def generate_forecast_number(tenant):
        year = timezone.now().year
        prefix = f"FCT-{year}-"
        last = CashForecast.unscoped.filter(
            tenant=tenant, forecast_number__startswith=prefix
        ).order_by('-forecast_number').first()
        if last:
            last_num = int(last.forecast_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class CashForecastLine(models.Model):
    """Individual line item in a cash forecast."""
    CATEGORY_CHOICES = [
        ('ar_collections', 'AR Collections'),
        ('ap_payments', 'AP Payments'),
        ('payroll', 'Payroll'),
        ('tax', 'Tax Payments'),
        ('loan', 'Loan Payments'),
        ('other', 'Other'),
    ]

    forecast = models.ForeignKey(
        CashForecast, on_delete=models.CASCADE, related_name='lines'
    )
    line_date = models.DateField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=255)
    expected_amount = models.DecimalField(max_digits=18, decimal_places=2)
    actual_amount = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )
    variance = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    class Meta:
        ordering = ['line_date', 'category']

    def __str__(self):
        return f"{self.line_date} - {self.get_category_display()}: {self.expected_amount}"

    def save(self, *args, **kwargs):
        if self.actual_amount is not None:
            self.variance = self.actual_amount - self.expected_amount
        super().save(*args, **kwargs)


# =============================================================================
# 5. Inter-company Transfers
# =============================================================================

class IntercompanyTransfer(TenantAwareModel):
    """Fund transfer between bank accounts (including cross-entity)."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    transfer_number = models.CharField(max_length=20, db_index=True)
    from_bank_account = models.ForeignKey(
        BankAccount, on_delete=models.PROTECT, related_name='outgoing_transfers'
    )
    to_bank_account = models.ForeignKey(
        BankAccount, on_delete=models.PROTECT, related_name='incoming_transfers'
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.ForeignKey(
        'company.Currency',
        on_delete=models.PROTECT,
        related_name='+'
    )
    exchange_rate = models.DecimalField(
        max_digits=18, decimal_places=8, default=Decimal('1.00000000')
    )
    transfer_date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transfers_created'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='transfers_approved'
    )
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='intercompany_transfers'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-transfer_date']
        unique_together = ('tenant', 'transfer_number')

    def __str__(self):
        return f"{self.transfer_number} - {self.amount}"

    @staticmethod
    def generate_transfer_number(tenant):
        year = timezone.now().year
        prefix = f"ICT-{year}-"
        last = IntercompanyTransfer.unscoped.filter(
            tenant=tenant, transfer_number__startswith=prefix
        ).order_by('-transfer_number').first()
        if last:
            last_num = int(last.transfer_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 6. Bank Fee Analysis
# =============================================================================

class BankFee(TenantAwareModel):
    """Bank fees and charges for analysis and optimization."""
    FEE_TYPE_CHOICES = [
        ('monthly_maintenance', 'Monthly Maintenance'),
        ('transaction', 'Transaction Fee'),
        ('wire', 'Wire Transfer Fee'),
        ('overdraft', 'Overdraft Fee'),
        ('atm', 'ATM Fee'),
        ('foreign_exchange', 'Foreign Exchange Fee'),
        ('other', 'Other'),
    ]

    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name='fees'
    )
    fee_date = models.DateField()
    fee_type = models.CharField(max_length=30, choices=FEE_TYPE_CHOICES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    is_recurring = models.BooleanField(default=False)
    category = models.CharField(max_length=100, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-fee_date']

    def __str__(self):
        return f"{self.fee_date} - {self.get_fee_type_display()}: {self.amount}"
