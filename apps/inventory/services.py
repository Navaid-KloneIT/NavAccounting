from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum, F
from django.utils import timezone

from apps.general_ledger.models import JournalEntry, JournalEntryLine


def _get_default_currency_id(tenant):
    """Get the default currency for a tenant."""
    from apps.company.models import CompanySettings
    try:
        settings = CompanySettings.unscoped.filter(tenant=tenant).first()
        if settings and settings.default_currency_id:
            return settings.default_currency_id
    except Exception:
        pass
    from apps.company.models import Currency
    currency = Currency.objects.first()
    return currency.id if currency else None


# =============================================================================
# Goods Receipt Posting
# =============================================================================

def post_goods_receipt(receipt, tenant, user):
    """
    Post a goods receipt: update PO received quantities, create cost layers,
    update item quantities, and create GL journal entry.
    Debit: Inventory Asset, Credit: Goods Received Not Invoiced
    """
    from .models import CostLayer, InventoryTransaction

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=receipt.receipt_date,
        description=f"Goods Receipt: {receipt.receipt_number}",
        reference=receipt.receipt_number,
        status='posted',
        source='ic_receipt',
        currency_id=_get_default_currency_id(tenant),
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    for line in receipt.lines.select_related('item', 'item__category', 'po_line'):
        item = line.item
        category = item.category
        line_total = line.quantity_received * line.unit_cost

        # Update PO line received quantity
        po_line = line.po_line
        po_line.received_quantity += line.quantity_received
        po_line.save(update_fields=['received_quantity'])

        # Create cost layer
        CostLayer.objects.create(
            tenant=tenant,
            item=item,
            receipt_date=receipt.receipt_date,
            quantity_on_hand=line.quantity_received,
            original_quantity=line.quantity_received,
            unit_cost=line.unit_cost,
            source_type='purchase',
            source_reference=receipt.receipt_number,
        )

        # Update item quantity and weighted average cost
        _update_item_after_receipt(item, line.quantity_received, line.unit_cost)

        # Create inventory transaction
        InventoryTransaction.objects.create(
            tenant=tenant,
            transaction_number=InventoryTransaction.generate_transaction_number(tenant),
            date=receipt.receipt_date,
            item=item,
            transaction_type='receipt',
            quantity=line.quantity_received,
            unit_cost=line.unit_cost,
            warehouse=receipt.warehouse,
            reference=receipt.receipt_number,
            posted_by=user,
            journal_entry=je,
        )

        # GL: Debit Inventory Asset
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.gl_inventory_account,
            description=f"Inventory receipt - {item.sku}",
            debit=line_total,
            credit=Decimal('0.00'),
        )

        # GL: Credit Goods Received Not Invoiced (using same inventory account as offset)
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.gl_inventory_account,
            description=f"GR offset - {item.sku}",
            debit=Decimal('0.00'),
            credit=line_total,
        )

    # Update PO status
    po = receipt.purchase_order
    all_received = all(
        line.received_quantity >= line.quantity
        for line in po.lines.all()
    )
    if all_received:
        po.status = 'received'
    else:
        po.status = 'partially_received'
    po.save(update_fields=['status', 'updated_at'])

    receipt.status = 'posted'
    receipt.journal_entry = je
    receipt.save(update_fields=['status', 'journal_entry', 'updated_at'])

    return je


def _update_item_after_receipt(item, quantity, unit_cost):
    """Update item quantity_on_hand and weighted_avg_cost after receipt."""
    old_qty = item.quantity_on_hand
    old_avg = item.weighted_avg_cost
    new_qty = old_qty + quantity

    if new_qty > 0 and item.costing_method == 'weighted_avg':
        total_value = (old_qty * old_avg) + (quantity * unit_cost)
        item.weighted_avg_cost = (total_value / new_qty).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

    item.quantity_on_hand = new_qty
    item.save(update_fields=['quantity_on_hand', 'weighted_avg_cost', 'updated_at'])


# =============================================================================
# Inventory Transaction Processing
# =============================================================================

def process_inventory_transaction(txn, tenant, user):
    """Process an inventory adjustment/scrap transaction and update item quantity."""
    item = txn.item

    # Update item quantity
    item.quantity_on_hand += txn.quantity
    item.save(update_fields=['quantity_on_hand', 'updated_at'])

    # Create GL journal entry
    category = item.category
    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=txn.date,
        description=f"Inventory {txn.get_transaction_type_display()}: {txn.transaction_number}",
        reference=txn.transaction_number,
        status='posted',
        source='ic_adjustment',
        currency_id=_get_default_currency_id(tenant),
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    if txn.quantity > 0:
        # Positive adjustment: Debit Inventory, Credit Adjustment Expense
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.gl_inventory_account,
            description=f"Inventory adjustment - {item.sku}",
            debit=txn.total_cost,
            credit=Decimal('0.00'),
        )
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.gl_cogs_account,
            description=f"Adjustment offset - {item.sku}",
            debit=Decimal('0.00'),
            credit=txn.total_cost,
        )
    else:
        # Negative adjustment/scrap: Debit Adjustment Expense, Credit Inventory
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.gl_cogs_account,
            description=f"Inventory {txn.get_transaction_type_display()} - {item.sku}",
            debit=txn.total_cost,
            credit=Decimal('0.00'),
        )
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.gl_inventory_account,
            description=f"Inventory reduction - {item.sku}",
            debit=Decimal('0.00'),
            credit=txn.total_cost,
        )

    txn.journal_entry = je
    txn.save(update_fields=['journal_entry', 'updated_at'])

    return je


# =============================================================================
# Inventory Transfer
# =============================================================================

def complete_inventory_transfer(transfer, tenant, user):
    """Complete an inventory transfer between warehouses."""
    from .models import InventoryTransaction

    for line in transfer.lines.select_related('item'):
        # Create transfer out transaction
        InventoryTransaction.objects.create(
            tenant=tenant,
            transaction_number=InventoryTransaction.generate_transaction_number(tenant),
            date=transfer.date,
            item=line.item,
            transaction_type='transfer_out',
            quantity=-line.quantity,
            unit_cost=line.unit_cost,
            warehouse=transfer.from_warehouse,
            reference=transfer.transfer_number,
            posted_by=user,
        )

        # Create transfer in transaction
        InventoryTransaction.objects.create(
            tenant=tenant,
            transaction_number=InventoryTransaction.generate_transaction_number(tenant),
            date=transfer.date,
            item=line.item,
            transaction_type='transfer_in',
            quantity=line.quantity,
            unit_cost=line.unit_cost,
            warehouse=transfer.to_warehouse,
            reference=transfer.transfer_number,
            posted_by=user,
        )

    transfer.status = 'completed'
    transfer.save(update_fields=['status', 'updated_at'])


# =============================================================================
# COGS Calculation
# =============================================================================

def run_cogs_calculation(calculation, tenant):
    """Run COGS calculation for a period using the specified method."""
    from .models import COGSEntry, Item, InventoryTransaction

    items = Item.objects.filter(
        tenant=tenant, is_active=True, item_type='inventory'
    )

    total_cogs = Decimal('0.00')

    for item in items:
        # Get issue transactions for the period
        issues = InventoryTransaction.objects.filter(
            tenant=tenant,
            item=item,
            transaction_type__in=['issue', 'scrap', 'write_off'],
            date__gte=calculation.period.start_date,
            date__lte=calculation.period.end_date,
        )

        qty_sold = issues.aggregate(
            total=Sum('quantity')
        )['total'] or Decimal('0.00')
        qty_sold = abs(qty_sold)

        if qty_sold <= 0:
            continue

        # Calculate cost based on method
        if calculation.method == 'weighted_avg':
            unit_cost = item.weighted_avg_cost
            item_cogs = (qty_sold * unit_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            layers_used = []
        elif calculation.method == 'standard':
            unit_cost = item.standard_cost
            item_cogs = (qty_sold * unit_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            layers_used = []
        elif calculation.method == 'fifo':
            item_cogs, layers_used, unit_cost = consume_cost_layers_fifo(item, qty_sold, tenant)
        elif calculation.method == 'lifo':
            item_cogs, layers_used, unit_cost = consume_cost_layers_lifo(item, qty_sold, tenant)
        else:
            continue

        COGSEntry.objects.create(
            calculation=calculation,
            item=item,
            quantity_sold=qty_sold,
            unit_cost=unit_cost,
            total_cost=item_cogs,
            cost_layers_used=layers_used,
        )

        total_cogs += item_cogs

    calculation.total_cogs = total_cogs
    calculation.save(update_fields=['total_cogs', 'updated_at'])


def post_cogs_calculation(calculation, tenant, user):
    """Post COGS calculation and create GL journal entry."""
    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=calculation.calculation_date,
        description=f"COGS: {calculation.calculation_number}",
        reference=calculation.calculation_number,
        status='posted',
        source='ic_cogs',
        currency_id=_get_default_currency_id(tenant),
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    for entry in calculation.entries.select_related('item', 'item__category'):
        category = entry.item.category

        # Debit: COGS
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.gl_cogs_account,
            description=f"COGS - {entry.item.sku}",
            debit=entry.total_cost,
            credit=Decimal('0.00'),
        )

        # Credit: Inventory
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.gl_inventory_account,
            description=f"Inventory reduction - {entry.item.sku}",
            debit=Decimal('0.00'),
            credit=entry.total_cost,
        )

    calculation.status = 'posted'
    calculation.journal_entry = je
    calculation.save(update_fields=['status', 'journal_entry', 'updated_at'])

    return je


# =============================================================================
# Cost Layer Consumption (FIFO / LIFO)
# =============================================================================

def consume_cost_layers_fifo(item, quantity, tenant):
    """Consume cost layers in FIFO order. Returns (total_cost, layers_used, avg_unit_cost)."""
    from .models import CostLayer

    layers = CostLayer.unscoped.filter(
        tenant=tenant, item=item, is_depleted=False
    ).order_by('receipt_date', 'pk')

    return _consume_layers(layers, quantity)


def consume_cost_layers_lifo(item, quantity, tenant):
    """Consume cost layers in LIFO order. Returns (total_cost, layers_used, avg_unit_cost)."""
    from .models import CostLayer

    layers = CostLayer.unscoped.filter(
        tenant=tenant, item=item, is_depleted=False
    ).order_by('-receipt_date', '-pk')

    return _consume_layers(layers, quantity)


def _consume_layers(layers, quantity):
    """Consume from ordered cost layers. Returns (total_cost, layers_used, avg_unit_cost)."""
    remaining = quantity
    total_cost = Decimal('0.00')
    layers_used = []

    for layer in layers:
        if remaining <= 0:
            break

        available = layer.quantity_on_hand
        consume = min(available, remaining)

        cost = (consume * layer.unit_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_cost += cost
        remaining -= consume

        layers_used.append({'layer_id': layer.pk, 'quantity': str(consume), 'cost': str(cost)})

        layer.quantity_on_hand -= consume
        if layer.quantity_on_hand <= 0:
            layer.is_depleted = True
        layer.save(update_fields=['quantity_on_hand', 'is_depleted', 'updated_at'])

    avg_unit_cost = (total_cost / quantity).quantize(
        Decimal('0.0001'), rounding=ROUND_HALF_UP
    ) if quantity > 0 else Decimal('0.00')

    return total_cost, layers_used, avg_unit_cost


# =============================================================================
# Reorder Planning
# =============================================================================

def generate_reorder_suggestions(tenant):
    """Scan items below reorder point and create suggestions."""
    from .models import Item, ReorderSuggestion

    items = Item.objects.filter(
        tenant=tenant, is_active=True, item_type='inventory'
    )

    count = 0
    for item in items:
        if item.quantity_on_hand <= item.reorder_point and item.reorder_quantity > 0:
            # Check if pending suggestion already exists
            existing = ReorderSuggestion.objects.filter(
                tenant=tenant, item=item, status='pending'
            ).exists()
            if not existing:
                ReorderSuggestion.objects.create(
                    tenant=tenant,
                    item=item,
                    current_stock=item.quantity_on_hand,
                    reorder_point=item.reorder_point,
                    suggested_quantity=item.reorder_quantity,
                )
                count += 1

    return count


def create_po_from_reorder(suggestion, tenant, user):
    """Create a purchase order from a reorder suggestion."""
    from .models import PurchaseOrder, PurchaseOrderLine

    po = PurchaseOrder.objects.create(
        tenant=tenant,
        po_number=PurchaseOrder.generate_po_number(tenant),
        vendor=suggestion.vendor,
        date=timezone.now().date(),
        created_by=user,
    )

    PurchaseOrderLine.objects.create(
        purchase_order=po,
        item=suggestion.item,
        quantity=suggestion.suggested_quantity,
        unit_price=suggestion.item.purchase_price,
        uom=suggestion.item.base_uom,
    )

    po.update_total()
    return po


# =============================================================================
# Cycle Count Approval
# =============================================================================

def approve_cycle_count(session, tenant, user):
    """Approve a cycle count session and post inventory adjustments."""
    from .models import InventoryTransaction

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=session.count_date,
        description=f"Cycle Count Adjustment: {session.session_number}",
        reference=session.session_number,
        status='posted',
        source='ic_adjustment',
        currency_id=_get_default_currency_id(tenant),
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    for ci in session.items.select_related('item', 'item__category').exclude(
        variance_quantity=Decimal('0.00')
    ):
        item = ci.item
        category = item.category

        # Update item quantity
        item.quantity_on_hand = ci.counted_quantity
        item.save(update_fields=['quantity_on_hand', 'updated_at'])

        # Create adjustment transaction
        InventoryTransaction.objects.create(
            tenant=tenant,
            transaction_number=InventoryTransaction.generate_transaction_number(tenant),
            date=session.count_date,
            item=item,
            transaction_type='adjustment',
            quantity=ci.variance_quantity,
            unit_cost=item.weighted_avg_cost or item.standard_cost,
            reference=session.session_number,
            notes=ci.resolution_notes,
            posted_by=user,
            journal_entry=je,
        )

        abs_value = abs(ci.variance_value)

        if ci.variance_quantity > 0:
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=category.gl_inventory_account,
                description=f"Count adjustment + {item.sku}",
                debit=abs_value,
                credit=Decimal('0.00'),
            )
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=category.gl_cogs_account,
                description=f"Count adjustment offset - {item.sku}",
                debit=Decimal('0.00'),
                credit=abs_value,
            )
        else:
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=category.gl_cogs_account,
                description=f"Count adjustment - {item.sku}",
                debit=abs_value,
                credit=Decimal('0.00'),
            )
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=category.gl_inventory_account,
                description=f"Count adjustment offset - {item.sku}",
                debit=Decimal('0.00'),
                credit=abs_value,
            )

        ci.status = 'resolved'
        ci.save(update_fields=['status'])

    session.status = 'approved'
    session.journal_entry = je
    session.save(update_fields=['status', 'journal_entry', 'updated_at'])

    return je


# =============================================================================
# Landed Cost
# =============================================================================

def post_landed_cost(voucher, tenant, user):
    """Post a landed cost voucher: allocate costs and create GL entry."""
    from .models import LandedCostAllocation

    # Auto-allocate if no allocations exist
    if not voucher.allocations.exists():
        allocate_landed_costs(voucher)

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=voucher.date,
        description=f"Landed Cost: {voucher.voucher_number}",
        reference=voucher.voucher_number,
        status='posted',
        source='ic_landed_cost',
        currency_id=_get_default_currency_id(tenant),
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    for alloc in voucher.allocations.select_related('item', 'item__category'):
        category = alloc.item.category

        # Debit: Inventory Asset (increase cost basis)
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.gl_inventory_account,
            description=f"Landed cost - {alloc.item.sku}",
            debit=alloc.allocated_amount,
            credit=Decimal('0.00'),
        )

    # Credit: total additional cost (offset)
    if voucher.total_additional_cost > 0:
        first_alloc = voucher.allocations.select_related('item__category').first()
        if first_alloc:
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=first_alloc.item.category.gl_inventory_account,
                description=f"Landed cost offset - {voucher.voucher_number}",
                debit=Decimal('0.00'),
                credit=voucher.total_additional_cost,
            )

    voucher.status = 'posted'
    voucher.journal_entry = je
    voucher.save(update_fields=['status', 'journal_entry', 'updated_at'])

    return je


def allocate_landed_costs(voucher):
    """Distribute additional costs across goods receipt lines by value."""
    from .models import LandedCostAllocation

    receipt = voucher.goods_receipt
    lines = receipt.lines.select_related('item')

    # Calculate total receipt value
    total_value = sum(line.quantity_received * line.unit_cost for line in lines)
    if total_value <= 0:
        return

    total_cost = voucher.total_additional_cost

    for line in lines:
        line_value = line.quantity_received * line.unit_cost
        proportion = line_value / total_value
        allocated = (total_cost * proportion).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        LandedCostAllocation.objects.create(
            voucher=voucher,
            item=line.item,
            goods_receipt_line=line,
            allocated_amount=allocated,
            allocation_method='by_value',
        )
