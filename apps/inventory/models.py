from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum, F
from django.utils import timezone

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# =============================================================================
# 1. Item Master
# =============================================================================

class ItemCategory(TenantAwareModel):
    """Category for grouping inventory items with GL account mappings."""
    code = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children'
    )
    description = models.TextField(blank=True)
    gl_inventory_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ic_inventory_categories',
        help_text='GL account for inventory asset'
    )
    gl_cogs_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ic_cogs_categories',
        help_text='GL account for cost of goods sold'
    )
    gl_revenue_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='ic_revenue_categories',
        help_text='GL account for sales revenue'
    )
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')
        verbose_name_plural = 'Item categories'

    def __str__(self):
        return f"{self.code} - {self.name}"


class UnitOfMeasure(TenantAwareModel):
    """Unit of measure for inventory items."""
    code = models.CharField(max_length=10, db_index=True)
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')
        verbose_name_plural = 'Units of measure'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Item(TenantAwareModel):
    """Master record for an inventory item / SKU."""
    ITEM_TYPE_CHOICES = [
        ('inventory', 'Inventory'),
        ('service', 'Service'),
        ('non_inventory', 'Non-Inventory'),
    ]
    COSTING_METHOD_CHOICES = [
        ('fifo', 'FIFO'),
        ('lifo', 'LIFO'),
        ('weighted_avg', 'Weighted Average'),
        ('standard', 'Standard Cost'),
    ]

    sku = models.CharField(max_length=50, db_index=True, verbose_name='SKU')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        ItemCategory, on_delete=models.PROTECT, related_name='items'
    )
    base_uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT, related_name='items',
        verbose_name='Base UOM'
    )
    item_type = models.CharField(
        max_length=15, choices=ITEM_TYPE_CHOICES, default='inventory'
    )
    costing_method = models.CharField(
        max_length=15, choices=COSTING_METHOD_CHOICES, default='weighted_avg'
    )
    standard_cost = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    purchase_price = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    selling_price = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    reorder_point = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    reorder_quantity = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    safety_stock = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    lead_time_days = models.PositiveIntegerField(default=0)
    quantity_on_hand = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    weighted_avg_cost = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    is_active = models.BooleanField(default=True)
    weight = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    dimensions = models.CharField(
        max_length=100, blank=True, help_text='L x W x H'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['sku']
        unique_together = ('tenant', 'sku')

    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def inventory_value(self):
        if self.costing_method == 'standard':
            return self.quantity_on_hand * self.standard_cost
        elif self.costing_method == 'weighted_avg':
            return self.quantity_on_hand * self.weighted_avg_cost
        return self.cost_layers.filter(is_depleted=False).aggregate(
            total=Sum(F('quantity_on_hand') * F('unit_cost'))
        )['total'] or Decimal('0.00')

    @staticmethod
    def generate_sku(tenant):
        prefix = "ITM-"
        last = Item.unscoped.filter(
            tenant=tenant, sku__startswith=prefix
        ).order_by('-sku').first()
        if last:
            last_num = int(last.sku.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:05d}"


# =============================================================================
# 2. Inventory Valuation & Cost Layers
# =============================================================================

class CostLayer(TenantAwareModel):
    """Tracks individual cost lots for FIFO/LIFO valuation."""
    SOURCE_TYPE_CHOICES = [
        ('purchase', 'Purchase Order'),
        ('adjustment', 'Adjustment'),
        ('transfer', 'Transfer'),
        ('opening', 'Opening Balance'),
    ]

    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='cost_layers'
    )
    receipt_date = models.DateField()
    quantity_on_hand = models.DecimalField(max_digits=18, decimal_places=2)
    original_quantity = models.DecimalField(max_digits=18, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4)
    source_type = models.CharField(
        max_length=15, choices=SOURCE_TYPE_CHOICES, default='purchase'
    )
    source_reference = models.CharField(max_length=50, blank=True)
    is_depleted = models.BooleanField(default=False)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['receipt_date', 'pk']

    def __str__(self):
        return f"{self.item.sku} - {self.receipt_date} - Qty:{self.quantity_on_hand}"

    @property
    def total_value(self):
        return self.quantity_on_hand * self.unit_cost


# =============================================================================
# 2b. Warehouse / Location
# =============================================================================

class Warehouse(TenantAwareModel):
    """Inventory storage location."""
    code = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['code']
        unique_together = ('tenant', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


# =============================================================================
# 3. Purchase Orders
# =============================================================================

class PurchaseRequisition(TenantAwareModel):
    """Request for purchasing items."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('converted', 'Converted to PO'),
    ]

    requisition_number = models.CharField(max_length=20, db_index=True)
    date = models.DateField()
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ic_requisitions'
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='draft'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-date']
        unique_together = ('tenant', 'requisition_number')

    def __str__(self):
        return self.requisition_number

    @staticmethod
    def generate_requisition_number(tenant):
        year = timezone.now().year
        prefix = f"REQ-{year}-"
        last = PurchaseRequisition.unscoped.filter(
            tenant=tenant, requisition_number__startswith=prefix
        ).order_by('-requisition_number').first()
        if last:
            last_num = int(last.requisition_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class PurchaseRequisitionLine(models.Model):
    """Line item in a purchase requisition."""
    requisition = models.ForeignKey(
        PurchaseRequisition, on_delete=models.CASCADE, related_name='lines'
    )
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, related_name='requisition_lines'
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=2)
    uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT, related_name='+'
    )
    estimated_unit_price = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{self.requisition.requisition_number} - {self.item.sku}"

    @property
    def line_total(self):
        return self.quantity * self.estimated_unit_price


class PurchaseOrder(TenantAwareModel):
    """Purchase order to a vendor."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('partially_received', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=20, db_index=True)
    vendor = models.ForeignKey(
        'accounts_payable.Vendor', on_delete=models.PROTECT,
        related_name='ic_purchase_orders'
    )
    requisition = models.ForeignKey(
        PurchaseRequisition, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='purchase_orders'
    )
    date = models.DateField()
    expected_delivery = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    terms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ic_purchase_orders_created'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ic_purchase_orders_approved'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-date']
        unique_together = ('tenant', 'po_number')

    def __str__(self):
        return f"{self.po_number} - {self.vendor}"

    def update_total(self):
        self.total_amount = self.lines.aggregate(
            total=Sum('line_total')
        )['total'] or Decimal('0.00')
        self.save(update_fields=['total_amount', 'updated_at'])

    @staticmethod
    def generate_po_number(tenant):
        year = timezone.now().year
        prefix = f"PO-{year}-"
        last = PurchaseOrder.unscoped.filter(
            tenant=tenant, po_number__startswith=prefix
        ).order_by('-po_number').first()
        if last:
            last_num = int(last.po_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class PurchaseOrderLine(models.Model):
    """Line item in a purchase order."""
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name='lines'
    )
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, related_name='po_lines'
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=2)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT, related_name='+'
    )
    line_total = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    received_quantity = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.item.sku}"

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    @property
    def remaining_quantity(self):
        return self.quantity - self.received_quantity


class GoodsReceipt(TenantAwareModel):
    """Record of goods received against a purchase order."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]

    receipt_number = models.CharField(max_length=20, db_index=True)
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.PROTECT, related_name='goods_receipts'
    )
    receipt_date = models.DateField()
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ic_goods_receipts'
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='goods_receipts'
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='draft'
    )
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='ic_goods_receipts'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-receipt_date']
        unique_together = ('tenant', 'receipt_number')

    def __str__(self):
        return self.receipt_number

    @staticmethod
    def generate_receipt_number(tenant):
        year = timezone.now().year
        prefix = f"GRN-{year}-"
        last = GoodsReceipt.unscoped.filter(
            tenant=tenant, receipt_number__startswith=prefix
        ).order_by('-receipt_number').first()
        if last:
            last_num = int(last.receipt_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class GoodsReceiptLine(models.Model):
    """Line item in a goods receipt."""
    goods_receipt = models.ForeignKey(
        GoodsReceipt, on_delete=models.CASCADE, related_name='lines'
    )
    po_line = models.ForeignKey(
        PurchaseOrderLine, on_delete=models.PROTECT, related_name='receipt_lines'
    )
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, related_name='receipt_lines'
    )
    quantity_received = models.DecimalField(max_digits=18, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{self.goods_receipt.receipt_number} - {self.item.sku}"

    @property
    def line_total(self):
        return self.quantity_received * self.unit_cost


# =============================================================================
# 4. Inventory Transactions
# =============================================================================

class InventoryTransaction(TenantAwareModel):
    """Individual inventory movement record."""
    TRANSACTION_TYPE_CHOICES = [
        ('receipt', 'Receipt'),
        ('issue', 'Issue'),
        ('adjustment', 'Adjustment'),
        ('scrap', 'Scrap'),
        ('write_off', 'Write Off'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
    ]

    transaction_number = models.CharField(max_length=20, db_index=True)
    date = models.DateField()
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=15, choices=TRANSACTION_TYPE_CHOICES
    )
    quantity = models.DecimalField(
        max_digits=18, decimal_places=2,
        help_text='Positive = in, Negative = out'
    )
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4)
    total_cost = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='transactions',
        null=True, blank=True
    )
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ic_transactions_posted'
    )
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='ic_transactions'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-date', '-pk']
        unique_together = ('tenant', 'transaction_number')

    def __str__(self):
        return f"{self.transaction_number} - {self.item.sku}"

    def save(self, *args, **kwargs):
        self.total_cost = abs(self.quantity) * self.unit_cost
        super().save(*args, **kwargs)

    @staticmethod
    def generate_transaction_number(tenant):
        year = timezone.now().year
        prefix = f"TXN-{year}-"
        last = InventoryTransaction.unscoped.filter(
            tenant=tenant, transaction_number__startswith=prefix
        ).order_by('-transaction_number').first()
        if last:
            last_num = int(last.transaction_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class InventoryTransfer(TenantAwareModel):
    """Transfer of items between warehouses."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    transfer_number = models.CharField(max_length=20, db_index=True)
    date = models.DateField()
    from_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='transfers_out'
    )
    to_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='transfers_in'
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='draft'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ic_transfers_created'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-date']
        unique_together = ('tenant', 'transfer_number')

    def __str__(self):
        return self.transfer_number

    @staticmethod
    def generate_transfer_number(tenant):
        year = timezone.now().year
        prefix = f"ITR-{year}-"
        last = InventoryTransfer.unscoped.filter(
            tenant=tenant, transfer_number__startswith=prefix
        ).order_by('-transfer_number').first()
        if last:
            last_num = int(last.transfer_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class InventoryTransferLine(models.Model):
    """Line item in an inventory transfer."""
    transfer = models.ForeignKey(
        InventoryTransfer, on_delete=models.CASCADE, related_name='lines'
    )
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, related_name='transfer_lines'
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{self.transfer.transfer_number} - {self.item.sku}"


# =============================================================================
# 5. Cost of Goods Sold
# =============================================================================

class COGSCalculation(TenantAwareModel):
    """Period-end COGS calculation run."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ]
    METHOD_CHOICES = [
        ('fifo', 'FIFO'),
        ('lifo', 'LIFO'),
        ('weighted_avg', 'Weighted Average'),
        ('standard', 'Standard Cost'),
    ]

    calculation_number = models.CharField(max_length=20, db_index=True)
    period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        related_name='ic_cogs_calculations'
    )
    calculation_date = models.DateField()
    method = models.CharField(max_length=15, choices=METHOD_CHOICES)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft'
    )
    total_cogs = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ic_cogs_calculations'
    )
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='ic_cogs_calculations'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-calculation_date']
        unique_together = ('tenant', 'calculation_number')
        verbose_name = 'COGS calculation'
        verbose_name_plural = 'COGS calculations'

    def __str__(self):
        return self.calculation_number

    @staticmethod
    def generate_calculation_number(tenant):
        year = timezone.now().year
        prefix = f"COGS-{year}-"
        last = COGSCalculation.unscoped.filter(
            tenant=tenant, calculation_number__startswith=prefix
        ).order_by('-calculation_number').first()
        if last:
            last_num = int(last.calculation_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class COGSEntry(models.Model):
    """Individual item entry within a COGS calculation."""
    calculation = models.ForeignKey(
        COGSCalculation, on_delete=models.CASCADE, related_name='entries'
    )
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, related_name='cogs_entries'
    )
    quantity_sold = models.DecimalField(max_digits=18, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4)
    total_cost = models.DecimalField(max_digits=18, decimal_places=2)
    cost_layers_used = models.JSONField(
        default=list, blank=True,
        help_text='JSON array of cost layer IDs and amounts consumed'
    )

    class Meta:
        ordering = ['item__sku']
        verbose_name = 'COGS entry'
        verbose_name_plural = 'COGS entries'

    def __str__(self):
        return f"{self.calculation.calculation_number} - {self.item.sku}"


# =============================================================================
# 6. Reorder Point Planning
# =============================================================================

class ReorderSuggestion(TenantAwareModel):
    """Automated replenishment suggestion."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('ordered', 'Ordered'),
        ('dismissed', 'Dismissed'),
    ]

    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='reorder_suggestions'
    )
    current_stock = models.DecimalField(max_digits=18, decimal_places=2)
    reorder_point = models.DecimalField(max_digits=18, decimal_places=2)
    suggested_quantity = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='pending'
    )
    vendor = models.ForeignKey(
        'accounts_payable.Vendor', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ic_reorder_suggestions'
    )
    created_date = models.DateField(auto_now_add=True)
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reorder_suggestions'
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"Reorder: {self.item.sku} - Qty: {self.suggested_quantity}"


# =============================================================================
# 7. Cycle Counting
# =============================================================================

class CycleCountPlan(TenantAwareModel):
    """Schedule for periodic physical inventory counts."""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    SELECTION_METHOD_CHOICES = [
        ('abc', 'ABC Classification'),
        ('random', 'Random'),
        ('category', 'By Category'),
        ('all', 'All Items'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]

    plan_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    frequency = models.CharField(
        max_length=10, choices=FREQUENCY_CHOICES, default='monthly'
    )
    item_selection_method = models.CharField(
        max_length=10, choices=SELECTION_METHOD_CHOICES, default='abc'
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT,
        related_name='cycle_count_plans', null=True, blank=True
    )
    category = models.ForeignKey(
        ItemCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cycle_count_plans'
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='active'
    )
    next_count_date = models.DateField()

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['next_count_date']
        unique_together = ('tenant', 'plan_number')

    def __str__(self):
        return f"{self.plan_number} - {self.name}"

    @staticmethod
    def generate_plan_number(tenant):
        prefix = "CCP-"
        last = CycleCountPlan.unscoped.filter(
            tenant=tenant, plan_number__startswith=prefix
        ).order_by('-plan_number').first()
        if last:
            last_num = int(last.plan_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class CycleCountSession(TenantAwareModel):
    """Individual count session for a cycle count plan."""
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
    ]

    session_number = models.CharField(max_length=20, db_index=True)
    plan = models.ForeignKey(
        CycleCountPlan, on_delete=models.CASCADE,
        related_name='sessions', null=True, blank=True
    )
    count_date = models.DateField()
    counted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ic_cycle_count_sessions'
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT,
        related_name='cycle_count_sessions', null=True, blank=True
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='planned'
    )
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='ic_cycle_count_sessions'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-count_date']
        unique_together = ('tenant', 'session_number')

    def __str__(self):
        return self.session_number

    @staticmethod
    def generate_session_number(tenant):
        year = timezone.now().year
        prefix = f"CCS-{year}-"
        last = CycleCountSession.unscoped.filter(
            tenant=tenant, session_number__startswith=prefix
        ).order_by('-session_number').first()
        if last:
            last_num = int(last.session_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"

    @property
    def total_items(self):
        return self.items.count()

    @property
    def variance_count(self):
        return self.items.exclude(variance_quantity=Decimal('0.00')).count()


class CycleCountItem(models.Model):
    """Individual item to be counted in a cycle count session."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('counted', 'Counted'),
        ('resolved', 'Resolved'),
    ]

    session = models.ForeignKey(
        CycleCountSession, on_delete=models.CASCADE, related_name='items'
    )
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, related_name='cycle_count_items'
    )
    system_quantity = models.DecimalField(max_digits=18, decimal_places=2)
    counted_quantity = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )
    variance_quantity = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    variance_value = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    resolution_notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending'
    )

    class Meta:
        ordering = ['item__sku']

    def __str__(self):
        return f"{self.session.session_number} - {self.item.sku}"

    def save(self, *args, **kwargs):
        if self.counted_quantity is not None:
            self.variance_quantity = self.counted_quantity - self.system_quantity
            self.variance_value = self.variance_quantity * (
                self.item.weighted_avg_cost or self.item.standard_cost
            )
        super().save(*args, **kwargs)


# =============================================================================
# 8. Landed Cost
# =============================================================================

class LandedCostVoucher(TenantAwareModel):
    """Voucher for allocating additional costs to received goods."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]

    voucher_number = models.CharField(max_length=20, db_index=True)
    goods_receipt = models.ForeignKey(
        GoodsReceipt, on_delete=models.PROTECT,
        related_name='landed_cost_vouchers'
    )
    date = models.DateField()
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='draft'
    )
    total_additional_cost = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0.00')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ic_landed_cost_vouchers'
    )
    journal_entry = models.ForeignKey(
        'general_ledger.JournalEntry', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='ic_landed_cost_vouchers'
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-date']
        unique_together = ('tenant', 'voucher_number')

    def __str__(self):
        return self.voucher_number

    def update_total(self):
        self.total_additional_cost = self.cost_lines.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        self.save(update_fields=['total_additional_cost', 'updated_at'])

    @staticmethod
    def generate_voucher_number(tenant):
        year = timezone.now().year
        prefix = f"LCV-{year}-"
        last = LandedCostVoucher.unscoped.filter(
            tenant=tenant, voucher_number__startswith=prefix
        ).order_by('-voucher_number').first()
        if last:
            last_num = int(last.voucher_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"


class LandedCostLine(models.Model):
    """Individual cost component in a landed cost voucher."""
    COST_TYPE_CHOICES = [
        ('freight', 'Freight'),
        ('duty', 'Customs Duty'),
        ('insurance', 'Insurance'),
        ('handling', 'Handling'),
        ('other', 'Other'),
    ]

    voucher = models.ForeignKey(
        LandedCostVoucher, on_delete=models.CASCADE, related_name='cost_lines'
    )
    cost_type = models.CharField(max_length=15, choices=COST_TYPE_CHOICES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    vendor = models.ForeignKey(
        'accounts_payable.Vendor', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{self.voucher.voucher_number} - {self.get_cost_type_display()}"


class LandedCostAllocation(models.Model):
    """Allocation of landed costs to individual receipt line items."""
    ALLOCATION_METHOD_CHOICES = [
        ('by_value', 'By Value'),
        ('by_quantity', 'By Quantity'),
        ('by_weight', 'By Weight'),
    ]

    voucher = models.ForeignKey(
        LandedCostVoucher, on_delete=models.CASCADE, related_name='allocations'
    )
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, related_name='landed_cost_allocations'
    )
    goods_receipt_line = models.ForeignKey(
        GoodsReceiptLine, on_delete=models.PROTECT,
        related_name='landed_cost_allocations'
    )
    allocated_amount = models.DecimalField(max_digits=18, decimal_places=2)
    allocation_method = models.CharField(
        max_length=15, choices=ALLOCATION_METHOD_CHOICES, default='by_value'
    )

    class Meta:
        ordering = ['item__sku']

    def __str__(self):
        return f"{self.voucher.voucher_number} - {self.item.sku} - ${self.allocated_amount}"
