import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# =============================================================================
# 1. Customer Management
# =============================================================================

class Customer(TenantAwareModel):
    """Customer profile — the central AR entity."""
    CUSTOMER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('business', 'Business'),
        ('government', 'Government'),
        ('nonprofit', 'Non-Profit'),
        ('other', 'Other'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('check', 'Check'),
        ('ach', 'ACH'),
        ('wire', 'Wire Transfer'),
        ('credit_card', 'Credit Card'),
        ('online', 'Online Payment'),
    ]

    customer_number = models.CharField(max_length=20, db_index=True)
    company_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    customer_type = models.CharField(
        max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='business'
    )

    # Tax
    tax_id = models.CharField(max_length=50, blank=True)
    tax_exempt = models.BooleanField(default=False)
    tax_exemption_number = models.CharField(max_length=50, blank=True)

    # Billing address
    billing_address_line_1 = models.CharField(max_length=255, blank=True)
    billing_address_line_2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=100, blank=True, default='United States')

    # Shipping address
    shipping_address_line_1 = models.CharField(max_length=255, blank=True)
    shipping_address_line_2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True, default='United States')

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Financial defaults
    default_payment_term = models.ForeignKey(
        'accounts_payable.PaymentTerm', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ar_customers'
    )
    default_revenue_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ar_customer_defaults'
    )
    currency = models.ForeignKey(
        'company.Currency', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )

    # Credit management
    credit_limit = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    credit_hold = models.BooleanField(default=False)
    credit_hold_reason = models.TextField(blank=True)
    credit_rating = models.CharField(max_length=10, blank=True)

    # Payment preferences
    preferred_payment_method = models.CharField(
        max_length=15, choices=PAYMENT_METHOD_CHOICES, default='check'
    )

    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['company_name']
        unique_together = ('tenant', 'customer_number')

    def __str__(self):
        return f"{self.customer_number} - {self.display_name}"

    @staticmethod
    def generate_customer_number(tenant):
        """Generate CUST-NNNN for the tenant."""
        prefix = "CUST-"
        last = Customer.unscoped.filter(
            tenant=tenant, customer_number__startswith=prefix
        ).order_by('-customer_number').first()
        if last:
            last_num = int(last.customer_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"

    @property
    def outstanding_balance(self):
        """Sum of unpaid invoice amounts."""
        invoices = self.invoices.exclude(status__in=['draft', 'void', 'written_off'])
        total = invoices.aggregate(bal=Sum(F('total_amount') - F('amount_paid')))
        return total['bal'] or Decimal('0.00')

    @property
    def available_credit(self):
        if self.credit_limit <= Decimal('0.00'):
            return None
        return self.credit_limit - self.outstanding_balance

    @property
    def is_over_credit_limit(self):
        if self.credit_limit <= Decimal('0.00'):
            return False
        return self.outstanding_balance > self.credit_limit


class CustomerContact(models.Model):
    """Multiple contacts per customer."""
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='contacts'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_primary = models.BooleanField(default=False)
    is_billing_contact = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_primary', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# =============================================================================
# 2. Invoice Generation
# =============================================================================

class Invoice(TenantAwareModel):
    """Customer invoice — the central AR document."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('void', 'Void'),
        ('written_off', 'Written Off'),
    ]

    invoice_number = models.CharField(max_length=20, db_index=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='invoices'
    )

    # Dates
    invoice_date = models.DateField()
    due_date = models.DateField()
    sent_date = models.DateField(null=True, blank=True)

    # Financial
    payment_term = models.ForeignKey(
        'accounts_payable.PaymentTerm', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ar_invoices'
    )
    currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT, related_name='+'
    )
    exchange_rate = models.DecimalField(
        max_digits=18, decimal_places=8, default=Decimal('1.00000000')
    )
    subtotal = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    tax_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    amount_paid = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    # GL linkage
    ar_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ar_invoices', help_text='AR control account (e.g., 1210)'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, related_name='ar_invoices'
    )

    # References
    po_number = models.CharField(
        max_length=100, blank=True, help_text='Customer PO number'
    )
    so_reference = models.CharField(
        max_length=100, blank=True, help_text='Sales order reference'
    )

    # Status & workflow
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Recurring link
    recurring_template = models.ForeignKey(
        'RecurringInvoiceTemplate', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='generated_invoices'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ar_invoices_created'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-invoice_date', '-invoice_number']
        unique_together = ('tenant', 'invoice_number')

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.display_name}"

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status not in ('paid', 'void', 'written_off')

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days

    @property
    def discount_date(self):
        if self.payment_term and self.payment_term.discount_days > 0:
            return self.invoice_date + timedelta(days=self.payment_term.discount_days)
        return None

    @property
    def discount_amount(self):
        if self.payment_term and self.payment_term.discount_percentage > 0:
            return (self.total_amount * self.payment_term.discount_percentage / Decimal('100')).quantize(Decimal('0.01'))
        return Decimal('0.00')

    @property
    def discount_available(self):
        dd = self.discount_date
        return dd is not None and timezone.now().date() <= dd

    def update_totals(self):
        """Recalculate subtotal and total from lines."""
        agg = self.lines.aggregate(
            sub=Sum('amount'),
            tax=Sum('tax_amount'),
        )
        self.subtotal = agg['sub'] or Decimal('0.00')
        self.tax_amount = agg['tax'] or Decimal('0.00')
        self.total_amount = self.subtotal + self.tax_amount

    def update_payment_status(self):
        """Update status based on amount_paid vs total_amount."""
        if self.amount_paid >= self.total_amount and self.total_amount > Decimal('0.00'):
            self.status = 'paid'
        elif self.amount_paid > Decimal('0.00'):
            self.status = 'partially_paid'

    @staticmethod
    def generate_invoice_number(tenant):
        year = timezone.now().year
        prefix = f"INV-{year}-"
        last = Invoice.unscoped.filter(
            tenant=tenant, invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        if last:
            last_num = int(last.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class InvoiceLine(models.Model):
    """Individual line item on an invoice."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ar_invoice_lines'
    )
    description = models.CharField(max_length=500, blank=True)
    quantity = models.DecimalField(
        max_digits=18, decimal_places=4, default=Decimal('1.0000')
    )
    unit_price = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    tax_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.account} - {self.amount}"

    def save(self, *args, **kwargs):
        self.amount = (self.quantity * self.unit_price).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)


class InvoiceApproval(TenantAwareModel):
    """Approval record for an invoice."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='approvals'
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='invoice_approvals'
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending'
    )
    comments = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Approval for {self.invoice.invoice_number} by {self.approver}"


# =============================================================================
# 3. Payment Collection (Receipts)
# =============================================================================

class Receipt(TenantAwareModel):
    """An incoming payment from a customer."""
    METHOD_CHOICES = [
        ('check', 'Check'),
        ('ach', 'ACH'),
        ('wire', 'Wire Transfer'),
        ('credit_card', 'Credit Card'),
        ('cash', 'Cash'),
        ('online', 'Online Payment'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('void', 'Void'),
    ]

    receipt_number = models.CharField(max_length=20, db_index=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='receipts'
    )
    receipt_date = models.DateField()

    # Financial
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    discount_given = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT, related_name='+'
    )
    exchange_rate = models.DecimalField(
        max_digits=18, decimal_places=8, default=Decimal('1.00000000')
    )

    # Method details
    payment_method = models.CharField(
        max_length=15, choices=METHOD_CHOICES, default='check'
    )
    check_number = models.CharField(max_length=20, blank=True)
    reference = models.CharField(max_length=100, blank=True)

    # GL linkage
    bank_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ar_receipts', help_text='Bank/cash account to deposit to'
    )
    ar_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ar_receipt_credits', help_text='AR control account'
    )
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ar_receipts'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, related_name='ar_receipts'
    )

    # Status
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft'
    )
    memo = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ar_receipts_created'
    )
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ar_receipts_voided'
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-receipt_date', '-receipt_number']
        unique_together = ('tenant', 'receipt_number')

    def __str__(self):
        return f"{self.receipt_number} - {self.customer.display_name}"

    @staticmethod
    def generate_receipt_number(tenant):
        year = timezone.now().year
        prefix = f"RCT-{year}-"
        last = Receipt.unscoped.filter(
            tenant=tenant, receipt_number__startswith=prefix
        ).order_by('-receipt_number').first()
        if last:
            last_num = int(last.receipt_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class ReceiptAllocation(models.Model):
    """Maps a receipt to specific invoices (supports partial payments)."""
    receipt = models.ForeignKey(
        Receipt, on_delete=models.CASCADE, related_name='allocations'
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name='receipt_allocations'
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    discount_given = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    class Meta:
        ordering = ['id']
        unique_together = ('receipt', 'invoice')

    def __str__(self):
        return f"{self.receipt.receipt_number} -> {self.invoice.invoice_number}: {self.amount}"


# =============================================================================
# 4. Recurring Invoicing
# =============================================================================

class RecurringInvoiceTemplate(TenantAwareModel):
    """Template for automatically generating invoices on a schedule."""
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semiannual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    template_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='recurring_templates'
    )

    # Schedule
    frequency = models.CharField(
        max_length=15, choices=FREQUENCY_CHOICES, default='monthly'
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_invoice_date = models.DateField()
    occurrences_limit = models.PositiveIntegerField(
        default=0, help_text='0 = unlimited'
    )
    occurrences_created = models.PositiveIntegerField(default=0)

    # Invoice defaults
    payment_term = models.ForeignKey(
        'accounts_payable.PaymentTerm', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ar_recurring_templates'
    )
    ar_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ar_recurring_templates'
    )
    currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT, related_name='+'
    )
    description = models.TextField(blank=True)
    subtotal = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    tax_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    auto_send = models.BooleanField(
        default=False, help_text='Automatically send after creation'
    )

    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='active'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ar_recurring_templates_created'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'template_number')

    def __str__(self):
        return f"{self.template_number} - {self.name}"

    @staticmethod
    def generate_template_number(tenant):
        year = timezone.now().year
        prefix = f"REC-{year}-"
        last = RecurringInvoiceTemplate.unscoped.filter(
            tenant=tenant, template_number__startswith=prefix
        ).order_by('-template_number').first()
        if last:
            last_num = int(last.template_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class RecurringInvoiceTemplateLine(models.Model):
    """Line items on a recurring invoice template."""
    template = models.ForeignKey(
        RecurringInvoiceTemplate, on_delete=models.CASCADE, related_name='lines'
    )
    account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ar_recurring_lines'
    )
    description = models.CharField(max_length=500, blank=True)
    quantity = models.DecimalField(
        max_digits=18, decimal_places=4, default=Decimal('1.0000')
    )
    unit_price = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    tax_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.account} - {self.amount}"


# =============================================================================
# 5. Credit Memo
# =============================================================================

class CreditMemo(TenantAwareModel):
    """Credit memo to reduce customer balance."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('applied', 'Applied'),
        ('void', 'Void'),
    ]

    memo_number = models.CharField(max_length=20, db_index=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='credit_memos'
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='credit_memos'
    )
    memo_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    reason = models.TextField()

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft'
    )

    # GL linkage
    ar_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ar_credit_memos'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        related_name='ar_credit_memos'
    )
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ar_credit_memos'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ar_credit_memos_created'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-memo_date']
        unique_together = ('tenant', 'memo_number')

    def __str__(self):
        return f"{self.memo_number} - {self.customer.display_name}"

    @staticmethod
    def generate_memo_number(tenant):
        year = timezone.now().year
        prefix = f"CM-{year}-"
        last = CreditMemo.unscoped.filter(
            tenant=tenant, memo_number__startswith=prefix
        ).order_by('-memo_number').first()
        if last:
            last_num = int(last.memo_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 6. Collections Management
# =============================================================================

class CollectionActivity(TenantAwareModel):
    """Activity log for collections workflow."""
    ACTIVITY_TYPE_CHOICES = [
        ('dunning_letter', 'Dunning Letter'),
        ('email', 'Email'),
        ('phone_call', 'Phone Call'),
        ('meeting', 'Meeting'),
        ('promise_to_pay', 'Promise to Pay'),
        ('dispute', 'Dispute'),
        ('write_off', 'Write Off'),
        ('note', 'Note'),
    ]
    DUNNING_LEVEL_CHOICES = [
        (1, 'Level 1 - Reminder'),
        (2, 'Level 2 - Past Due Notice'),
        (3, 'Level 3 - Urgent Collection'),
        (4, 'Level 4 - Final Notice'),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='collection_activities'
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='collection_activities'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    dunning_level = models.PositiveSmallIntegerField(
        choices=DUNNING_LEVEL_CHOICES, null=True, blank=True
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()
    contact_person = models.CharField(max_length=255, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    promise_date = models.DateField(null=True, blank=True)
    promise_amount = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )
    is_resolved = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='collection_activities_created'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Collection activities'

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.customer.display_name}"


# =============================================================================
# 7. Write-Offs
# =============================================================================

class WriteOff(TenantAwareModel):
    """Bad debt write-off for an invoice."""
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('reversed', 'Reversed'),
    ]

    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name='write_offs'
    )
    write_off_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    reason = models.TextField()

    bad_debt_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ar_write_offs', help_text='Bad debt expense account'
    )
    ar_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ar_write_off_credits'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        related_name='ar_write_offs'
    )
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ar_write_offs'
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ar_write_offs_created'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-write_off_date']

    def __str__(self):
        return f"Write-off {self.invoice.invoice_number} - {self.amount}"


# =============================================================================
# 8. Customer Portal
# =============================================================================

class CustomerPortalToken(TenantAwareModel):
    """Token-based access for customers (no Django user account needed)."""
    customer = models.OneToOneField(
        Customer, on_delete=models.CASCADE, related_name='portal_token'
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Portal token for {self.customer.display_name}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(48)

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at


class CustomerMessage(TenantAwareModel):
    """Simple messaging between customer portal and internal users."""
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='messages'
    )
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_from_customer = models.BooleanField(default=False)
    sender_name = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        direction = "from" if self.is_from_customer else "to"
        return f"Message {direction} {self.customer.display_name}: {self.subject}"
