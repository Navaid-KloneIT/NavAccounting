from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# =============================================================================
# 1. Asset Register
# =============================================================================

class AssetCategory(TenantAwareModel):
    """Category/class for grouping assets with default depreciation settings."""
    DEPRECIATION_METHOD_CHOICES = [
        ('straight_line', 'Straight Line'),
        ('declining_balance', 'Declining Balance'),
        ('units_of_production', 'Units of Production'),
    ]

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, db_index=True)
    description = models.TextField(blank=True)
    depreciation_method = models.CharField(
        max_length=25, choices=DEPRECIATION_METHOD_CHOICES, default='straight_line'
    )
    default_useful_life_months = models.PositiveIntegerField(default=60)
    default_salvage_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        help_text='Default salvage value as percentage of acquisition cost'
    )
    asset_gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='fa_asset_categories',
        help_text='GL account for asset cost'
    )
    depreciation_gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='fa_depreciation_categories',
        help_text='GL account for depreciation expense'
    )
    accumulated_depreciation_gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='fa_accumulated_dep_categories',
        help_text='GL account for accumulated depreciation (contra-asset)'
    )
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')
        verbose_name_plural = 'Asset categories'

    def __str__(self):
        return f"{self.code} - {self.name}"


class AssetLocation(TenantAwareModel):
    """Physical location where assets are housed."""
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, db_index=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class Asset(TenantAwareModel):
    """Master record for a fixed asset."""
    STATUS_CHOICES = [
        ('in_service', 'In Service'),
        ('under_maintenance', 'Under Maintenance'),
        ('disposed', 'Disposed'),
        ('written_off', 'Written Off'),
        ('construction_in_progress', 'Construction in Progress'),
    ]
    DEPRECIATION_METHOD_CHOICES = [
        ('straight_line', 'Straight Line'),
        ('declining_balance', 'Declining Balance'),
        ('units_of_production', 'Units of Production'),
    ]

    asset_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        AssetCategory, on_delete=models.PROTECT, related_name='assets'
    )
    location = models.ForeignKey(
        AssetLocation, on_delete=models.PROTECT,
        related_name='assets', null=True, blank=True
    )
    custodian = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='custodian_assets'
    )
    serial_number = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    tag_number = models.CharField(max_length=50, blank=True)
    acquisition_date = models.DateField()
    acquisition_cost = models.DecimalField(max_digits=18, decimal_places=2)
    salvage_value = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    useful_life_months = models.PositiveIntegerField(default=60)
    depreciation_method = models.CharField(
        max_length=25, choices=DEPRECIATION_METHOD_CHOICES, default='straight_line'
    )
    accumulated_depreciation = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default='in_service'
    )
    warranty_expiry = models.DateField(null=True, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['asset_number']
        unique_together = ('tenant', 'asset_number')

    def __str__(self):
        return f"{self.asset_number} - {self.name}"

    @property
    def net_book_value(self):
        return self.acquisition_cost - self.accumulated_depreciation

    @property
    def depreciation_remaining(self):
        return self.net_book_value - self.salvage_value

    @staticmethod
    def generate_asset_number(tenant):
        year = timezone.now().year
        prefix = f"AST-{year}-"
        last = Asset.unscoped.filter(
            tenant=tenant, asset_number__startswith=prefix
        ).order_by('-asset_number').first()
        if last:
            last_num = int(last.asset_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 2. Acquisition
# =============================================================================

class AssetAcquisition(TenantAwareModel):
    """Records how an asset was acquired and its capitalization."""
    ACQUISITION_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('lease', 'Lease'),
        ('donation', 'Donation'),
        ('construction', 'Construction'),
        ('transfer_in', 'Transfer In'),
    ]

    acquisition_number = models.CharField(max_length=20, db_index=True)
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name='acquisitions'
    )
    acquisition_type = models.CharField(
        max_length=20, choices=ACQUISITION_TYPE_CHOICES, default='purchase'
    )
    vendor_name = models.CharField(max_length=255, blank=True)
    invoice_reference = models.CharField(max_length=100, blank=True)
    purchase_order = models.CharField(max_length=100, blank=True)
    acquisition_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.ForeignKey(
        'company.Currency', on_delete=models.PROTECT, related_name='+'
    )
    capitalization_date = models.DateField(null=True, blank=True)
    is_capitalized = models.BooleanField(default=False)
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='fa_acquisitions'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-acquisition_date']
        unique_together = ('tenant', 'acquisition_number')

    def __str__(self):
        return f"{self.acquisition_number} - {self.asset.name}"

    @staticmethod
    def generate_acquisition_number(tenant):
        year = timezone.now().year
        prefix = f"ACQ-{year}-"
        last = AssetAcquisition.unscoped.filter(
            tenant=tenant, acquisition_number__startswith=prefix
        ).order_by('-acquisition_number').first()
        if last:
            last_num = int(last.acquisition_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 3. Depreciation Engine
# =============================================================================

class DepreciationProfile(TenantAwareModel):
    """Depreciation configuration for a specific asset."""
    METHOD_CHOICES = [
        ('straight_line', 'Straight Line'),
        ('declining_balance', 'Declining Balance'),
        ('units_of_production', 'Units of Production'),
    ]

    asset = models.OneToOneField(
        Asset, on_delete=models.CASCADE, related_name='depreciation_profile'
    )
    method = models.CharField(
        max_length=25, choices=METHOD_CHOICES, default='straight_line'
    )
    useful_life_months = models.PositiveIntegerField(default=60)
    start_date = models.DateField()
    end_date = models.DateField()
    salvage_value = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    total_units = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Total production units (for Units of Production method)'
    )
    declining_balance_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        help_text='Rate as percentage (e.g., 200 for double declining)'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['asset__asset_number']

    def __str__(self):
        return f"Depreciation: {self.asset.asset_number} ({self.get_method_display()})"


class DepreciationSchedule(TenantAwareModel):
    """Pre-computed depreciation schedule line for an asset."""
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name='depreciation_schedules'
    )
    period_number = models.PositiveIntegerField()
    period_start = models.DateField()
    period_end = models.DateField()
    depreciation_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    accumulated_depreciation = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    net_book_value = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    is_posted = models.BooleanField(default=False)
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='fa_depreciation_schedules'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['asset__asset_number', 'period_number']
        unique_together = ('tenant', 'asset', 'period_number')

    def __str__(self):
        return f"{self.asset.asset_number} - Period {self.period_number}"


class DepreciationEntry(TenantAwareModel):
    """Batch depreciation run for a fiscal period."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ]

    entry_number = models.CharField(max_length=20, db_index=True)
    run_date = models.DateField()
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        related_name='fa_depreciation_entries'
    )
    total_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    asset_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='fa_depreciation_entries_created'
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='fa_depreciation_entries_posted'
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='fa_depreciation_entries'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-run_date']
        unique_together = ('tenant', 'entry_number')
        verbose_name_plural = 'Depreciation entries'

    def __str__(self):
        return f"{self.entry_number} - {self.run_date}"

    @staticmethod
    def generate_entry_number(tenant):
        year = timezone.now().year
        prefix = f"DEP-{year}-"
        last = DepreciationEntry.unscoped.filter(
            tenant=tenant, entry_number__startswith=prefix
        ).order_by('-entry_number').first()
        if last:
            last_num = int(last.entry_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 4. Asset Transfers
# =============================================================================

class AssetTransfer(TenantAwareModel):
    """Record of an asset being moved between locations/departments/custodians."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    transfer_number = models.CharField(max_length=20, db_index=True)
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name='transfers'
    )
    from_location = models.ForeignKey(
        AssetLocation, on_delete=models.PROTECT,
        related_name='transfers_from', null=True, blank=True
    )
    to_location = models.ForeignKey(
        AssetLocation, on_delete=models.PROTECT,
        related_name='transfers_to', null=True, blank=True
    )
    from_department = models.CharField(max_length=255, blank=True)
    to_department = models.CharField(max_length=255, blank=True)
    from_custodian = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='fa_transfers_from'
    )
    to_custodian = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='fa_transfers_to'
    )
    transfer_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='fa_transfers_created'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='fa_transfers_approved'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-transfer_date']
        unique_together = ('tenant', 'transfer_number')

    def __str__(self):
        return f"{self.transfer_number} - {self.asset.name}"

    @staticmethod
    def generate_transfer_number(tenant):
        year = timezone.now().year
        prefix = f"ATR-{year}-"
        last = AssetTransfer.unscoped.filter(
            tenant=tenant, transfer_number__startswith=prefix
        ).order_by('-transfer_number').first()
        if last:
            last_num = int(last.transfer_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 5. Disposals & Retirements
# =============================================================================

class AssetDisposal(TenantAwareModel):
    """Record of an asset being disposed, sold, scrapped, or written off."""
    DISPOSAL_TYPE_CHOICES = [
        ('sale', 'Sale'),
        ('scrap', 'Scrap'),
        ('write_off', 'Write Off'),
        ('donation', 'Donation'),
        ('trade_in', 'Trade In'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    disposal_number = models.CharField(max_length=20, db_index=True)
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name='disposals'
    )
    disposal_type = models.CharField(
        max_length=20, choices=DISPOSAL_TYPE_CHOICES, default='sale'
    )
    disposal_date = models.DateField()
    proceeds = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    net_book_value_at_disposal = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    gain_loss = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    buyer_name = models.CharField(max_length=255, blank=True)
    invoice_reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='fa_disposals_created'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='fa_disposals_approved'
    )
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='fa_disposals'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-disposal_date']
        unique_together = ('tenant', 'disposal_number')

    def __str__(self):
        return f"{self.disposal_number} - {self.asset.name}"

    def save(self, *args, **kwargs):
        self.gain_loss = self.proceeds - self.net_book_value_at_disposal
        super().save(*args, **kwargs)

    @staticmethod
    def generate_disposal_number(tenant):
        year = timezone.now().year
        prefix = f"DSP-{year}-"
        last = AssetDisposal.unscoped.filter(
            tenant=tenant, disposal_number__startswith=prefix
        ).order_by('-disposal_number').first()
        if last:
            last_num = int(last.disposal_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


# =============================================================================
# 6. Impairment Testing
# =============================================================================

class ImpairmentTest(TenantAwareModel):
    """Impairment test to determine if asset carrying amount exceeds recoverable amount."""
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name='impairment_tests'
    )
    test_date = models.DateField()
    carrying_amount = models.DecimalField(max_digits=18, decimal_places=2)
    recoverable_amount = models.DecimalField(max_digits=18, decimal_places=2)
    value_in_use = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    fair_value_less_costs = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    impairment_loss = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    is_impaired = models.BooleanField(default=False)
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='fa_impairments'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='fa_impairment_tests'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-test_date']

    def __str__(self):
        return f"Impairment: {self.asset.asset_number} - {self.test_date}"

    def save(self, *args, **kwargs):
        self.recoverable_amount = max(self.value_in_use, self.fair_value_less_costs)
        if self.carrying_amount > self.recoverable_amount:
            self.impairment_loss = self.carrying_amount - self.recoverable_amount
            self.is_impaired = True
        else:
            self.impairment_loss = Decimal('0.00')
            self.is_impaired = False
        super().save(*args, **kwargs)


# =============================================================================
# 7. Physical Inventory
# =============================================================================

class PhysicalInventory(TenantAwareModel):
    """Physical inventory count session for fixed assets."""
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reconciled', 'Reconciled'),
    ]

    inventory_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    location = models.ForeignKey(
        AssetLocation, on_delete=models.PROTECT,
        related_name='physical_inventories', null=True, blank=True
    )
    count_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='planned'
    )
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='fa_inventories_conducted'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-count_date']
        unique_together = ('tenant', 'inventory_number')
        verbose_name_plural = 'Physical inventories'

    def __str__(self):
        return f"{self.inventory_number} - {self.name}"

    @property
    def total_items(self):
        return self.items.count()

    @property
    def found_count(self):
        return self.items.filter(is_found=True).count()

    @property
    def missing_count(self):
        return self.items.filter(is_found=False).count()

    @staticmethod
    def generate_inventory_number(tenant):
        year = timezone.now().year
        prefix = f"INV-{year}-"
        last = PhysicalInventory.unscoped.filter(
            tenant=tenant, inventory_number__startswith=prefix
        ).order_by('-inventory_number').first()
        if last:
            last_num = int(last.inventory_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class PhysicalInventoryItem(models.Model):
    """Individual item line in a physical inventory count."""
    CONDITION_CHOICES = [
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    ]

    inventory = models.ForeignKey(
        PhysicalInventory, on_delete=models.CASCADE, related_name='items'
    )
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name='inventory_items'
    )
    expected_location = models.ForeignKey(
        AssetLocation, on_delete=models.PROTECT,
        related_name='+', null=True, blank=True
    )
    found_location = models.ForeignKey(
        AssetLocation, on_delete=models.PROTECT,
        related_name='+', null=True, blank=True
    )
    is_found = models.BooleanField(default=False)
    condition = models.CharField(
        max_length=10, choices=CONDITION_CHOICES, default='good'
    )
    scanned_barcode = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['asset__asset_number']

    def __str__(self):
        status = 'Found' if self.is_found else 'Missing'
        return f"{self.asset.asset_number} - {status}"


# =============================================================================
# 8. Tax Depreciation
# =============================================================================

class TaxDepreciationBook(TenantAwareModel):
    """Parallel tax depreciation book (e.g., MACRS, Section 179)."""
    TAX_METHOD_CHOICES = [
        ('macrs', 'MACRS'),
        ('bonus', 'Bonus Depreciation'),
        ('section_179', 'Section 179'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, db_index=True)
    tax_method = models.CharField(
        max_length=20, choices=TAX_METHOD_CHOICES, default='macrs'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class TaxDepreciationEntry(TenantAwareModel):
    """Tax depreciation record for an asset in a specific tax book."""
    CONVENTION_CHOICES = [
        ('half_year', 'Half-Year'),
        ('mid_quarter', 'Mid-Quarter'),
        ('mid_month', 'Mid-Month'),
    ]

    tax_book = models.ForeignKey(
        TaxDepreciationBook, on_delete=models.CASCADE,
        related_name='entries'
    )
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE,
        related_name='tax_depreciation_entries'
    )
    fiscal_year = models.PositiveIntegerField()
    depreciation_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    accumulated_depreciation = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    recovery_period_years = models.PositiveIntegerField(default=5)
    convention = models.CharField(
        max_length=15, choices=CONVENTION_CHOICES, default='half_year'
    )
    property_class = models.CharField(max_length=50, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['asset__asset_number', 'fiscal_year']
        unique_together = ('tenant', 'tax_book', 'asset', 'fiscal_year')
        verbose_name_plural = 'Tax depreciation entries'

    def __str__(self):
        return f"{self.asset.asset_number} - {self.tax_book.code} - FY{self.fiscal_year}"
