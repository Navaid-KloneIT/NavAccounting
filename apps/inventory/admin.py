from django.contrib import admin

from .models import (
    ItemCategory, UnitOfMeasure, Item, CostLayer, Warehouse,
    PurchaseRequisition, PurchaseRequisitionLine,
    PurchaseOrder, PurchaseOrderLine,
    GoodsReceipt, GoodsReceiptLine,
    InventoryTransaction, InventoryTransfer, InventoryTransferLine,
    COGSCalculation, COGSEntry,
    ReorderSuggestion,
    CycleCountPlan, CycleCountSession, CycleCountItem,
    LandedCostVoucher, LandedCostLine, LandedCostAllocation,
)


# =============================================================================
# Item Master
# =============================================================================

@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('code', 'name')
    ordering = ['code']


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'abbreviation', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('code', 'name')
    ordering = ['code']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'item_type', 'costing_method',
                    'quantity_on_hand', 'is_active', 'tenant')
    list_filter = ('item_type', 'costing_method', 'is_active', 'tenant')
    search_fields = ('sku', 'name')
    ordering = ['sku']


@admin.register(CostLayer)
class CostLayerAdmin(admin.ModelAdmin):
    list_display = ('item', 'receipt_date', 'quantity_on_hand', 'original_quantity',
                    'unit_cost', 'source_type', 'is_depleted', 'tenant')
    list_filter = ('source_type', 'is_depleted', 'tenant')
    search_fields = ('item__sku', 'source_reference')


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('code', 'name')
    ordering = ['code']


# =============================================================================
# Purchasing
# =============================================================================

class PurchaseRequisitionLineInline(admin.TabularInline):
    model = PurchaseRequisitionLine
    extra = 0


@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(admin.ModelAdmin):
    list_display = ('requisition_number', 'date', 'requested_by', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('requisition_number',)
    inlines = [PurchaseRequisitionLineInline]


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'vendor', 'date', 'total_amount', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('po_number', 'vendor__name')
    inlines = [PurchaseOrderLineInline]


class GoodsReceiptLineInline(admin.TabularInline):
    model = GoodsReceiptLine
    extra = 0


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'purchase_order', 'receipt_date', 'warehouse',
                    'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('receipt_number',)
    inlines = [GoodsReceiptLineInline]


# =============================================================================
# Transactions & Transfers
# =============================================================================

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_number', 'date', 'item', 'transaction_type',
                    'quantity', 'unit_cost', 'total_cost', 'tenant')
    list_filter = ('transaction_type', 'tenant')
    search_fields = ('transaction_number', 'item__sku')


class InventoryTransferLineInline(admin.TabularInline):
    model = InventoryTransferLine
    extra = 0


@admin.register(InventoryTransfer)
class InventoryTransferAdmin(admin.ModelAdmin):
    list_display = ('transfer_number', 'date', 'from_warehouse', 'to_warehouse',
                    'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('transfer_number',)
    inlines = [InventoryTransferLineInline]


# =============================================================================
# COGS
# =============================================================================

class COGSEntryInline(admin.TabularInline):
    model = COGSEntry
    extra = 0


@admin.register(COGSCalculation)
class COGSCalculationAdmin(admin.ModelAdmin):
    list_display = ('calculation_number', 'period', 'calculation_date', 'method',
                    'total_cogs', 'status', 'tenant')
    list_filter = ('status', 'method', 'tenant')
    search_fields = ('calculation_number',)
    inlines = [COGSEntryInline]


# =============================================================================
# Reorder Planning
# =============================================================================

@admin.register(ReorderSuggestion)
class ReorderSuggestionAdmin(admin.ModelAdmin):
    list_display = ('item', 'current_stock', 'reorder_point', 'suggested_quantity',
                    'status', 'vendor', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('item__sku', 'item__name')


# =============================================================================
# Cycle Counting
# =============================================================================

@admin.register(CycleCountPlan)
class CycleCountPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_number', 'name', 'frequency', 'item_selection_method',
                    'status', 'next_count_date', 'tenant')
    list_filter = ('status', 'frequency', 'tenant')
    search_fields = ('plan_number', 'name')


class CycleCountItemInline(admin.TabularInline):
    model = CycleCountItem
    extra = 0


@admin.register(CycleCountSession)
class CycleCountSessionAdmin(admin.ModelAdmin):
    list_display = ('session_number', 'plan', 'count_date', 'counted_by',
                    'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('session_number',)
    inlines = [CycleCountItemInline]


# =============================================================================
# Landed Cost
# =============================================================================

class LandedCostLineInline(admin.TabularInline):
    model = LandedCostLine
    extra = 0


class LandedCostAllocationInline(admin.TabularInline):
    model = LandedCostAllocation
    extra = 0


@admin.register(LandedCostVoucher)
class LandedCostVoucherAdmin(admin.ModelAdmin):
    list_display = ('voucher_number', 'goods_receipt', 'date', 'total_additional_cost',
                    'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('voucher_number',)
    inlines = [LandedCostLineInline, LandedCostAllocationInline]
