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
# 1. Payment Terms
# =============================================================================

class PaymentTerm(TenantAwareModel):
    """Payment terms for vendor invoices (e.g., Net 30, 2/10 Net 30)."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, db_index=True)
    due_days = models.PositiveSmallIntegerField(default=30)
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    discount_days = models.PositiveSmallIntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['due_days']
        unique_together = ('tenant', 'code')

    def __str__(self):
        return self.name


# =============================================================================
# 2. Vendor Management
# =============================================================================

class Vendor(TenantAwareModel):
    """Vendor/supplier profile."""
    VENDOR_TYPE_CHOICES = [
        ('supplier', 'Supplier'),
        ('contractor', 'Contractor'),
        ('service', 'Service Provider'),
        ('utility', 'Utility'),
        ('government', 'Government'),
        ('other', 'Other'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('check', 'Check'),
        ('ach', 'ACH'),
        ('wire', 'Wire Transfer'),
        ('virtual_card', 'Virtual Card'),
    ]

    vendor_number = models.CharField(max_length=20, db_index=True)
    company_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    vendor_type = models.CharField(
        max_length=20, choices=VENDOR_TYPE_CHOICES, default='supplier'
    )

    # Tax / 1099 / W-9 tracking
    tax_id = models.CharField(max_length=50, blank=True)
    is_1099_eligible = models.BooleanField(default=False)
    w9_on_file = models.BooleanField(default=False)
    w9_received_date = models.DateField(null=True, blank=True)

    # Address
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='United States')

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Financial defaults
    default_payment_term = models.ForeignKey(
        PaymentTerm, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vendors'
    )
    default_expense_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vendor_defaults'
    )
    currency = models.ForeignKey(
        'company.Currency', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )
    credit_limit = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    # Payment preferences
    preferred_payment_method = models.CharField(
        max_length=15, choices=PAYMENT_METHOD_CHOICES, default='check'
    )
    bank_name = models.CharField(max_length=255, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_routing_number = models.CharField(max_length=50, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['company_name']
        unique_together = ('tenant', 'vendor_number')

    def __str__(self):
        return f"{self.vendor_number} - {self.display_name}"

    @staticmethod
    def generate_vendor_number(tenant):
        """Generate VND-NNNN for the tenant."""
        prefix = "VND-"
        last = Vendor.unscoped.filter(
            tenant=tenant, vendor_number__startswith=prefix
        ).order_by('-vendor_number').first()
        if last:
            last_num = int(last.vendor_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"

    @property
    def outstanding_balance(self):
        """Sum of unpaid bill amounts."""
        bills = self.bills.exclude(status__in=['draft', 'void'])
        total = bills.aggregate(bal=Sum(F('total_amount') - F('amount_paid')))
        return total['bal'] or Decimal('0.00')


class VendorContact(models.Model):
    """Multiple contacts per vendor."""
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name='contacts'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_primary', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# =============================================================================
# 3. Bill Processing
# =============================================================================

class Bill(TenantAwareModel):
    """Vendor bill/invoice — the central AP document."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('void', 'Void'),
    ]

    bill_number = models.CharField(max_length=20, db_index=True)
    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT, related_name='bills'
    )
    vendor_invoice_number = models.CharField(max_length=100, blank=True)

    # Dates
    bill_date = models.DateField()
    due_date = models.DateField()
    received_date = models.DateField(null=True, blank=True)

    # Financial
    payment_term = models.ForeignKey(
        PaymentTerm, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bills'
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
    ap_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ap_bills', help_text='AP control account (e.g., 2110)'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, related_name='ap_bills'
    )

    # Three-way matching references
    po_reference = models.CharField(
        max_length=100, blank=True, help_text='Purchase Order reference'
    )
    receipt_reference = models.CharField(
        max_length=100, blank=True, help_text='Goods receipt reference'
    )

    # Status & workflow
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ap_bills_created'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-bill_date', '-bill_number']
        unique_together = ('tenant', 'bill_number')

    def __str__(self):
        return f"{self.bill_number} - {self.vendor.display_name}"

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status not in ('paid', 'void')

    @property
    def discount_date(self):
        """Date by which early payment discount is available."""
        if self.payment_term and self.payment_term.discount_days > 0:
            return self.bill_date + timedelta(days=self.payment_term.discount_days)
        return None

    @property
    def discount_amount(self):
        """Potential early payment discount."""
        if self.payment_term and self.payment_term.discount_percentage > 0:
            return (self.total_amount * self.payment_term.discount_percentage / Decimal('100')).quantize(Decimal('0.01'))
        return Decimal('0.00')

    @property
    def discount_available(self):
        """Whether discount is still available."""
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
    def generate_bill_number(tenant):
        year = timezone.now().year
        prefix = f"BILL-{year}-"
        last = Bill.unscoped.filter(
            tenant=tenant, bill_number__startswith=prefix
        ).order_by('-bill_number').first()
        if last:
            last_num = int(last.bill_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class BillLine(models.Model):
    """Individual line item on a bill."""
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ap_bill_lines'
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


class BillApproval(TenantAwareModel):
    """Approval record for a bill."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE, related_name='approvals'
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='bill_approvals'
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
        return f"Approval for {self.bill.bill_number} by {self.approver}"


# =============================================================================
# 4. Bill Capture
# =============================================================================

class BillUpload(TenantAwareModel):
    """Uploaded invoice document for OCR processing."""
    OCR_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    upload_number = models.CharField(max_length=20, db_index=True)
    file = models.FileField(upload_to='ap/bill_uploads/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)

    # OCR fields
    ocr_status = models.CharField(
        max_length=15, choices=OCR_STATUS_CHOICES, default='pending'
    )
    ocr_processed_at = models.DateTimeField(null=True, blank=True)
    ocr_error_message = models.TextField(blank=True)
    extracted_data = models.JSONField(default=dict, blank=True)

    # Linkage
    bill = models.ForeignKey(
        Bill, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='uploads'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='bill_uploads'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'upload_number')

    def __str__(self):
        return f"{self.upload_number} - {self.original_filename}"

    @staticmethod
    def generate_upload_number(tenant):
        year = timezone.now().year
        prefix = f"UPL-{year}-"
        last = BillUpload.unscoped.filter(
            tenant=tenant, upload_number__startswith=prefix
        ).order_by('-upload_number').first()
        if last:
            last_num = int(last.upload_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 5. Payment Processing
# =============================================================================

class Payment(TenantAwareModel):
    """A payment to a vendor."""
    METHOD_CHOICES = [
        ('check', 'Check'),
        ('ach', 'ACH'),
        ('wire', 'Wire Transfer'),
        ('virtual_card', 'Virtual Card'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('void', 'Void'),
    ]

    payment_number = models.CharField(max_length=20, db_index=True)
    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT, related_name='payments'
    )
    payment_date = models.DateField()

    # Financial
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    discount_taken = models.DecimalField(
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
        related_name='ap_payments', help_text='Bank/cash account to pay from'
    )
    ap_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ap_payment_credits', help_text='AP control account'
    )
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ap_payments'
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT, related_name='ap_payments'
    )

    # Status
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft'
    )
    memo = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ap_payments_created'
    )
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ap_payments_voided'
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-payment_date', '-payment_number']
        unique_together = ('tenant', 'payment_number')

    def __str__(self):
        return f"{self.payment_number} - {self.vendor.display_name}"

    @staticmethod
    def generate_payment_number(tenant):
        year = timezone.now().year
        prefix = f"PAY-{year}-"
        last = Payment.unscoped.filter(
            tenant=tenant, payment_number__startswith=prefix
        ).order_by('-payment_number').first()
        if last:
            last_num = int(last.payment_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class PaymentAllocation(models.Model):
    """Maps a payment to specific bills (supports partial payments)."""
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name='allocations'
    )
    bill = models.ForeignKey(
        Bill, on_delete=models.PROTECT, related_name='payment_allocations'
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    discount_taken = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    class Meta:
        ordering = ['id']
        unique_together = ('payment', 'bill')

    def __str__(self):
        return f"{self.payment.payment_number} -> {self.bill.bill_number}: {self.amount}"


class PaymentBatch(TenantAwareModel):
    """Batch of payments processed together."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ready', 'Ready to Process'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    batch_number = models.CharField(max_length=20, db_index=True)
    description = models.CharField(max_length=255)
    payment_date = models.DateField()
    payment_method = models.CharField(
        max_length=15, choices=Payment.METHOD_CHOICES, default='check'
    )
    bank_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ap_batches'
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='draft'
    )
    total_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    payment_count = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ap_batches_created'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'batch_number')
        verbose_name_plural = 'Payment batches'

    def __str__(self):
        return f"{self.batch_number} - {self.description}"

    @staticmethod
    def generate_batch_number(tenant):
        year = timezone.now().year
        prefix = f"BATCH-{year}-"
        last = PaymentBatch.unscoped.filter(
            tenant=tenant, batch_number__startswith=prefix
        ).order_by('-batch_number').first()
        if last:
            last_num = int(last.batch_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 6. Payment Scheduling
# =============================================================================

class ScheduledPayment(TenantAwareModel):
    """Scheduled future payment."""
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('executed', 'Executed'),
        ('cancelled', 'Cancelled'),
    ]

    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE, related_name='scheduled_payments'
    )
    scheduled_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium'
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='scheduled'
    )
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='scheduled_source'
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='scheduled_payments'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['scheduled_date', 'priority']

    def __str__(self):
        return f"Scheduled: {self.bill.bill_number} on {self.scheduled_date}"


# =============================================================================
# 7. Vendor Portal
# =============================================================================

class VendorPortalToken(TenantAwareModel):
    """Token-based access for vendors (no Django user account needed)."""
    vendor = models.OneToOneField(
        Vendor, on_delete=models.CASCADE, related_name='portal_token'
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
        return f"Portal token for {self.vendor.display_name}"

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


class VendorMessage(TenantAwareModel):
    """Simple messaging between vendor portal and internal users."""
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name='messages'
    )
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_from_vendor = models.BooleanField(default=False)
    sender_name = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        direction = "from" if self.is_from_vendor else "to"
        return f"Message {direction} {self.vendor.display_name}: {self.subject}"
