from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# =============================================================================
# 1. Entity Management
# =============================================================================

class Entity(TenantAwareModel):
    """Represents a subsidiary, branch, or division within a tenant group."""

    ENTITY_TYPE_CHOICES = [
        ('parent', 'Parent Company'),
        ('subsidiary', 'Subsidiary'),
        ('branch', 'Branch'),
        ('division', 'Division'),
        ('joint_venture', 'Joint Venture'),
        ('associate', 'Associate'),
    ]
    CONSOLIDATION_METHOD_CHOICES = [
        ('full', 'Full Consolidation'),
        ('proportional', 'Proportional Consolidation'),
        ('equity', 'Equity Method'),
        ('none', 'Not Consolidated'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('dissolved', 'Dissolved'),
    ]

    code = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPE_CHOICES, default='subsidiary')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children'
    )
    functional_currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT, related_name='entities'
    )
    ownership_percentage = models.DecimalField(
        max_digits=7, decimal_places=4, default=Decimal('100.0000'),
        help_text='Percentage owned by parent entity'
    )
    consolidation_method = models.CharField(
        max_length=20, choices=CONSOLIDATION_METHOD_CHOICES, default='full'
    )

    # Regulatory
    tax_id = models.CharField(max_length=50, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    local_gaap = models.CharField(max_length=100, blank=True, help_text='e.g. US GAAP, IFRS, UK GAAP')

    # GL account mapping for intercompany
    ic_receivable_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='entity_ic_receivable',
        help_text='Default Due From (IC Receivable) account'
    )
    ic_payable_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='entity_ic_payable',
        help_text='Default Due To (IC Payable) account'
    )
    cta_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='entity_cta',
        help_text='Cumulative Translation Adjustment equity account'
    )
    minority_interest_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='entity_minority_interest',
        help_text='Non-controlling interest equity account'
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    description = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')
        verbose_name_plural = 'Entities'

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_ancestors(self):
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    @property
    def minority_percentage(self):
        return Decimal('100.0000') - self.ownership_percentage


# =============================================================================
# 2. Inter-company Transactions
# =============================================================================

class IntercompanyTransaction(TenantAwareModel):
    """A transaction between two entities within the same tenant."""

    TRANSACTION_TYPE_CHOICES = [
        ('sale', 'Intercompany Sale'),
        ('purchase', 'Intercompany Purchase'),
        ('service', 'Intercompany Service'),
        ('loan', 'Intercompany Loan'),
        ('dividend', 'Dividend'),
        ('capital', 'Capital Contribution'),
        ('expense_allocation', 'Expense Allocation'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]

    transaction_number = models.CharField(max_length=20, db_index=True)
    from_entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT, related_name='ic_transactions_from'
    )
    to_entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT, related_name='ic_transactions_to'
    )
    transaction_type = models.CharField(
        max_length=25, choices=TRANSACTION_TYPE_CHOICES, default='sale'
    )
    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT, related_name='+'
    )
    exchange_rate = models.DecimalField(
        max_digits=18, decimal_places=8, default=Decimal('1.00000000')
    )
    reference = models.CharField(max_length=100, blank=True)

    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, related_name='ic_transactions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Linked journal entries (one per entity side)
    from_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ic_transactions_from'
    )
    to_journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ic_transactions_to'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='ic_transactions_created'
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ic_transactions_confirmed'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-date', '-transaction_number']
        unique_together = ('tenant', 'transaction_number')

    def __str__(self):
        return f"{self.transaction_number} - {self.from_entity.code} -> {self.to_entity.code}"

    @staticmethod
    def generate_transaction_number(tenant):
        year = timezone.now().year
        prefix = f"ICX-{year}-"
        last = IntercompanyTransaction.unscoped.filter(
            tenant=tenant, transaction_number__startswith=prefix
        ).order_by('-transaction_number').first()
        if last:
            last_num = int(last.transaction_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"

    def clean(self):
        if self.from_entity_id and self.to_entity_id:
            if self.from_entity_id == self.to_entity_id:
                raise ValidationError('From and To entities must be different.')


class IntercompanyBalance(TenantAwareModel):
    """Running due-to/due-from balance between entity pairs per period."""

    from_entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT, related_name='ic_balances_from'
    )
    to_entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT, related_name='ic_balances_to'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, related_name='ic_balances'
    )
    currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT, related_name='+'
    )

    # From entity perspective: positive = receivable, negative = payable
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    last_reconciled_at = models.DateTimeField(null=True, blank=True)
    is_reconciled = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-fiscal_period__period_number']
        unique_together = ('tenant', 'from_entity', 'to_entity', 'fiscal_period', 'currency')

    def __str__(self):
        return f"IC Balance: {self.from_entity.code} / {self.to_entity.code} - {self.fiscal_period}"


# =============================================================================
# 3. Currency Translation
# =============================================================================

class CurrencyTranslationRule(TenantAwareModel):
    """Defines which exchange rate type to use for account types during translation."""

    RATE_TYPE_CHOICES = [
        ('current', 'Current Rate (Period End)'),
        ('historical', 'Historical Rate'),
        ('average', 'Average Rate (Period)'),
        ('fixed', 'Fixed Rate'),
    ]
    ACCOUNT_SCOPE_CHOICES = [
        ('account_type', 'By Account Type'),
        ('specific_account', 'Specific Account'),
    ]

    name = models.CharField(max_length=255)
    account_scope = models.CharField(
        max_length=20, choices=ACCOUNT_SCOPE_CHOICES, default='account_type'
    )
    account_type = models.ForeignKey(
        'company.AccountType', on_delete=models.PROTECT,
        null=True, blank=True, related_name='translation_rules',
        help_text='Apply rule to all accounts of this type'
    )
    specific_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        null=True, blank=True, related_name='translation_rules',
        help_text='Apply rule to this specific account only'
    )
    rate_type = models.CharField(max_length=15, choices=RATE_TYPE_CHOICES, default='current')
    fixed_rate = models.DecimalField(
        max_digits=18, decimal_places=8, null=True, blank=True,
        help_text='Only used if rate_type is "fixed"'
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_rate_type_display()})"


class TranslationAdjustment(TenantAwareModel):
    """CTA entry generated per entity per period."""

    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name='translation_adjustments'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, related_name='translation_adjustments'
    )
    from_currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT, related_name='+'
    )
    to_currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT, related_name='+'
    )

    # Computed translated amounts
    total_assets_translated = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_liabilities_translated = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_equity_translated = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_income_translated = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_expense_translated = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    cta_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00'),
        help_text='Cumulative Translation Adjustment for this period'
    )
    cta_cumulative = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00'),
        help_text='Running cumulative CTA through this period'
    )

    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='translation_adjustments'
    )
    calculated_at = models.DateTimeField(auto_now_add=True)
    calculated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-fiscal_period__period_number']
        unique_together = ('tenant', 'entity', 'fiscal_period')

    def __str__(self):
        return f"CTA: {self.entity.code} - {self.fiscal_period} ({self.cta_amount})"


# =============================================================================
# 4. Consolidation Engine
# =============================================================================

class ConsolidationGroup(TenantAwareModel):
    """Defines a set of entities to consolidate together."""

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, db_index=True)
    parent_entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT,
        related_name='consolidation_groups_as_parent',
        help_text='The parent/reporting entity'
    )
    reporting_currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT, related_name='+'
    )
    entities = models.ManyToManyField(Entity, related_name='consolidation_groups', blank=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['name']
        unique_together = ('tenant', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class ConsolidationRun(TenantAwareModel):
    """Tracks each execution of the consolidation process."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
    ]

    run_number = models.CharField(max_length=20, db_index=True)
    consolidation_group = models.ForeignKey(
        ConsolidationGroup, on_delete=models.PROTECT, related_name='runs'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, related_name='consolidation_runs'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')

    # Summary
    total_eliminations = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_minority_interest = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_cta = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='consolidation_runs_created'
    )
    notes = models.TextField(blank=True)
    error_log = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-started_at']
        unique_together = ('tenant', 'run_number')

    def __str__(self):
        return f"{self.run_number} - {self.consolidation_group.name} ({self.fiscal_period})"

    @staticmethod
    def generate_run_number(tenant):
        year = timezone.now().year
        prefix = f"CON-{year}-"
        last = ConsolidationRun.unscoped.filter(
            tenant=tenant, run_number__startswith=prefix
        ).order_by('-run_number').first()
        if last:
            last_num = int(last.run_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class EliminationRule(TenantAwareModel):
    """Configurable rules for automatic intercompany eliminations."""

    RULE_TYPE_CHOICES = [
        ('ic_receivable_payable', 'IC Receivable/Payable'),
        ('ic_revenue_expense', 'IC Revenue/Expense'),
        ('ic_investment_equity', 'Investment/Equity'),
        ('ic_dividend', 'Intercompany Dividends'),
        ('ic_inventory_profit', 'Unrealized Inventory Profit'),
        ('custom', 'Custom Rule'),
    ]

    name = models.CharField(max_length=255)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPE_CHOICES)
    consolidation_group = models.ForeignKey(
        ConsolidationGroup, on_delete=models.CASCADE, related_name='elimination_rules'
    )

    debit_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='elimination_rules_debit',
        help_text='Account to debit in the elimination entry'
    )
    credit_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='elimination_rules_credit',
        help_text='Account to credit in the elimination entry'
    )

    is_auto = models.BooleanField(default=True, help_text='Automatically apply during consolidation runs')
    is_active = models.BooleanField(default=True)
    priority = models.PositiveSmallIntegerField(default=100)
    description = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['priority', 'name']
        unique_together = ('tenant', 'name')

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class EliminationEntry(TenantAwareModel):
    """Generated elimination journal entries from a consolidation run."""

    consolidation_run = models.ForeignKey(
        ConsolidationRun, on_delete=models.CASCADE, related_name='elimination_entries'
    )
    elimination_rule = models.ForeignKey(
        EliminationRule, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='entries'
    )
    from_entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT, related_name='elimination_entries_from'
    )
    to_entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT, related_name='elimination_entries_to'
    )

    debit_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT, related_name='+'
    )
    credit_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT, related_name='+'
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    description = models.TextField()

    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='elimination_entries'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'Elimination entries'

    def __str__(self):
        return f"Elim: {self.from_entity.code}/{self.to_entity.code} - {self.amount}"


class MinorityInterest(TenantAwareModel):
    """Tracks non-controlling interest per entity per period."""

    consolidation_run = models.ForeignKey(
        ConsolidationRun, on_delete=models.CASCADE, related_name='minority_interests'
    )
    entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT, related_name='minority_interests'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, related_name='minority_interests'
    )

    minority_percentage = models.DecimalField(max_digits=7, decimal_places=4)
    net_income = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00'),
        help_text='Total net income of the entity for the period'
    )
    minority_share = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00'),
        help_text='Non-controlling interest share of net income'
    )
    total_equity = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00'),
        help_text='Total equity of the entity'
    )
    minority_equity = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00'),
        help_text='Non-controlling interest share of equity'
    )

    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='minority_interest_entries'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-fiscal_period__period_number']
        unique_together = ('tenant', 'consolidation_run', 'entity')

    def __str__(self):
        return f"NCI: {self.entity.code} ({self.minority_percentage}%) - {self.minority_share}"


# =============================================================================
# 5. Transfer Pricing
# =============================================================================

class TransferPricingPolicy(TenantAwareModel):
    """Inter-company pricing documentation and method configuration."""

    PRICING_METHOD_CHOICES = [
        ('cup', 'Comparable Uncontrolled Price'),
        ('resale_price', 'Resale Price Method'),
        ('cost_plus', 'Cost Plus Method'),
        ('tnmm', 'Transactional Net Margin Method'),
        ('profit_split', 'Profit Split Method'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]

    policy_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    from_entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT, related_name='tp_policies_from'
    )
    to_entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT, related_name='tp_policies_to'
    )
    pricing_method = models.CharField(
        max_length=20, choices=PRICING_METHOD_CHOICES, default='cost_plus'
    )
    markup_percentage = models.DecimalField(
        max_digits=7, decimal_places=4, default=Decimal('0.0000')
    )

    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')

    documentation = models.TextField(blank=True, help_text='Transfer pricing documentation/justification')
    comparable_data = models.TextField(blank=True, help_text="Arm's length comparable data references")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-effective_from']
        unique_together = ('tenant', 'policy_number')
        verbose_name_plural = 'Transfer pricing policies'

    def __str__(self):
        return f"{self.policy_number} - {self.name}"

    @staticmethod
    def generate_policy_number(tenant):
        year = timezone.now().year
        prefix = f"TPP-{year}-"
        last = TransferPricingPolicy.unscoped.filter(
            tenant=tenant, policy_number__startswith=prefix
        ).order_by('-policy_number').first()
        if last:
            last_num = int(last.policy_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class TransferPricingTransaction(TenantAwareModel):
    """Tracks inter-company transactions with arm's length pricing analysis."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('flagged', 'Flagged for Review'),
    ]

    policy = models.ForeignKey(
        TransferPricingPolicy, on_delete=models.PROTECT, related_name='transactions'
    )
    intercompany_transaction = models.ForeignKey(
        IntercompanyTransaction, on_delete=models.PROTECT, related_name='tp_transactions'
    )

    transfer_price = models.DecimalField(
        max_digits=18, decimal_places=2, help_text='Actual intercompany price'
    )
    arms_length_price = models.DecimalField(
        max_digits=18, decimal_places=2, help_text="Comparable arm's length price"
    )
    variance = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    variance_percentage = models.DecimalField(
        max_digits=7, decimal_places=4, default=Decimal('0.0000')
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TP: {self.intercompany_transaction.transaction_number} ({self.variance})"

    def save(self, *args, **kwargs):
        if self.transfer_price and self.arms_length_price:
            self.variance = self.transfer_price - self.arms_length_price
            if self.arms_length_price != Decimal('0.00'):
                self.variance_percentage = (
                    self.variance / self.arms_length_price * 100
                ).quantize(Decimal('0.0001'))
        super().save(*args, **kwargs)


# =============================================================================
# 6. Regulatory Reporting
# =============================================================================

class LocalGAAPAdjustment(TenantAwareModel):
    """Adjustments from group GAAP to local GAAP per entity."""

    ADJUSTMENT_TYPE_CHOICES = [
        ('reclassification', 'Reclassification'),
        ('measurement', 'Measurement Difference'),
        ('disclosure', 'Disclosure Adjustment'),
        ('recognition', 'Recognition Difference'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('reviewed', 'Reviewed'),
        ('posted', 'Posted'),
    ]

    adjustment_number = models.CharField(max_length=20, db_index=True)
    entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT, related_name='gaap_adjustments'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, related_name='gaap_adjustments'
    )

    adjustment_type = models.CharField(
        max_length=20, choices=ADJUSTMENT_TYPE_CHOICES, default='measurement'
    )
    from_standard = models.CharField(max_length=50, help_text='Group reporting standard, e.g. IFRS')
    to_standard = models.CharField(max_length=50, help_text='Local GAAP standard, e.g. US GAAP')

    debit_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT, related_name='+'
    )
    credit_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT, related_name='+'
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    description = models.TextField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='gaap_adjustments'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'adjustment_number')

    def __str__(self):
        return f"{self.adjustment_number} - {self.entity.code} ({self.get_adjustment_type_display()})"

    @staticmethod
    def generate_adjustment_number(tenant):
        year = timezone.now().year
        prefix = f"GAP-{year}-"
        last = LocalGAAPAdjustment.unscoped.filter(
            tenant=tenant, adjustment_number__startswith=prefix
        ).order_by('-adjustment_number').first()
        if last:
            last_num = int(last.adjustment_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class RegulatoryReport(TenantAwareModel):
    """Generated regulatory/statutory reports per entity."""

    REPORT_TYPE_CHOICES = [
        ('local_fs', 'Local Financial Statements'),
        ('tax_return', 'Tax Return Package'),
        ('statutory', 'Statutory Filing'),
        ('regulatory', 'Regulatory Return'),
        ('custom', 'Custom Report'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('filed', 'Filed'),
    ]

    report_number = models.CharField(max_length=20, db_index=True)
    entity = models.ForeignKey(
        Entity, on_delete=models.PROTECT, related_name='regulatory_reports'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, related_name='regulatory_reports'
    )
    report_type = models.CharField(
        max_length=15, choices=REPORT_TYPE_CHOICES, default='local_fs'
    )
    name = models.CharField(max_length=255)
    gaap_standard = models.CharField(max_length=50, help_text='Reporting standard, e.g. IFRS, US GAAP')

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    generated_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )
    filed_at = models.DateTimeField(null=True, blank=True)
    filing_reference = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)
    # WARNING: Do not store sensitive credentials in this field
    report_data = models.JSONField(default=dict, blank=True, help_text='Structured report output data')

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-generated_at']
        unique_together = ('tenant', 'report_number')

    def __str__(self):
        return f"{self.report_number} - {self.entity.code} ({self.get_report_type_display()})"

    @staticmethod
    def generate_report_number(tenant):
        year = timezone.now().year
        prefix = f"REG-{year}-"
        last = RegulatoryReport.unscoped.filter(
            tenant=tenant, report_number__startswith=prefix
        ).order_by('-report_number').first()
        if last:
            last_num = int(last.report_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"
