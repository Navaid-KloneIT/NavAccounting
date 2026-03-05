from django.urls import path

from .views import (
    item_master, purchasing, transactions, costing,
    planning, cycle_count, landed_cost,
)

app_name = 'inventory'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Item Master
    # -------------------------------------------------------------------------
    path('categories/', item_master.category_list, name='category_list'),
    path('categories/create/', item_master.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', item_master.category_edit, name='category_edit'),

    path('uom/', item_master.uom_list, name='uom_list'),
    path('uom/create/', item_master.uom_create, name='uom_create'),
    path('uom/<int:pk>/edit/', item_master.uom_edit, name='uom_edit'),

    path('items/', item_master.item_list, name='item_list'),
    path('items/create/', item_master.item_create, name='item_create'),
    path('items/<int:pk>/', item_master.item_detail, name='item_detail'),
    path('items/<int:pk>/edit/', item_master.item_edit, name='item_edit'),

    path('warehouses/', item_master.warehouse_list, name='warehouse_list'),
    path('warehouses/create/', item_master.warehouse_create, name='warehouse_create'),
    path('warehouses/<int:pk>/edit/', item_master.warehouse_edit, name='warehouse_edit'),

    # -------------------------------------------------------------------------
    # Purchase Requisitions
    # -------------------------------------------------------------------------
    path('requisitions/', purchasing.requisition_list, name='requisition_list'),
    path('requisitions/create/', purchasing.requisition_create, name='requisition_create'),
    path('requisitions/<int:pk>/', purchasing.requisition_detail, name='requisition_detail'),
    path('requisitions/<int:pk>/approve/', purchasing.requisition_approve, name='requisition_approve'),
    path('requisitions/<int:pk>/convert/', purchasing.requisition_convert, name='requisition_convert'),

    # -------------------------------------------------------------------------
    # Purchase Orders
    # -------------------------------------------------------------------------
    path('purchase-orders/', purchasing.po_list, name='po_list'),
    path('purchase-orders/create/', purchasing.po_create, name='po_create'),
    path('purchase-orders/<int:pk>/', purchasing.po_detail, name='po_detail'),
    path('purchase-orders/<int:pk>/edit/', purchasing.po_edit, name='po_edit'),
    path('purchase-orders/<int:pk>/approve/', purchasing.po_approve, name='po_approve'),

    # -------------------------------------------------------------------------
    # Goods Receipts
    # -------------------------------------------------------------------------
    path('goods-receipts/', purchasing.receipt_list, name='receipt_list'),
    path('goods-receipts/create/<int:po_pk>/', purchasing.receipt_create, name='receipt_create'),
    path('goods-receipts/<int:pk>/', purchasing.receipt_detail, name='receipt_detail'),
    path('goods-receipts/<int:pk>/post/', purchasing.receipt_post, name='receipt_post'),

    # -------------------------------------------------------------------------
    # Inventory Transactions
    # -------------------------------------------------------------------------
    path('transactions/', transactions.transaction_list, name='transaction_list'),
    path('transactions/adjustment/', transactions.transaction_adjustment, name='transaction_adjustment'),
    path('transactions/scrap/', transactions.transaction_scrap, name='transaction_scrap'),

    # -------------------------------------------------------------------------
    # Inventory Transfers
    # -------------------------------------------------------------------------
    path('transfers/', transactions.transfer_list, name='transfer_list'),
    path('transfers/create/', transactions.transfer_create, name='transfer_create'),
    path('transfers/<int:pk>/', transactions.transfer_detail, name='transfer_detail'),
    path('transfers/<int:pk>/complete/', transactions.transfer_complete, name='transfer_complete'),

    # -------------------------------------------------------------------------
    # COGS & Valuation
    # -------------------------------------------------------------------------
    path('cogs/', costing.cogs_dashboard, name='cogs_dashboard'),
    path('cogs/calculate/', costing.cogs_calculate, name='cogs_calculate'),
    path('cogs/<int:pk>/', costing.cogs_detail, name='cogs_detail'),
    path('cogs/<int:pk>/post/', costing.cogs_post, name='cogs_post'),
    path('valuation/', costing.valuation_report, name='valuation_report'),

    # -------------------------------------------------------------------------
    # Reorder Planning
    # -------------------------------------------------------------------------
    path('reorder/', planning.reorder_dashboard, name='reorder_dashboard'),
    path('reorder/generate/', planning.reorder_generate, name='reorder_generate'),
    path('reorder/<int:pk>/approve/', planning.reorder_approve, name='reorder_approve'),
    path('reorder/<int:pk>/dismiss/', planning.reorder_dismiss, name='reorder_dismiss'),
    path('reorder/<int:pk>/create-po/', planning.reorder_create_po, name='reorder_create_po'),

    # -------------------------------------------------------------------------
    # Cycle Counting
    # -------------------------------------------------------------------------
    path('cycle-counts/plans/', cycle_count.cycle_count_plan_list, name='cycle_count_plan_list'),
    path('cycle-counts/plans/create/', cycle_count.cycle_count_plan_create, name='cycle_count_plan_create'),
    path('cycle-counts/sessions/', cycle_count.cycle_count_session_list, name='cycle_count_session_list'),
    path('cycle-counts/sessions/create/', cycle_count.cycle_count_session_create, name='cycle_count_session_create'),
    path('cycle-counts/sessions/<int:pk>/', cycle_count.cycle_count_session_detail, name='cycle_count_session_detail'),
    path('cycle-counts/sessions/<int:pk>/count/', cycle_count.cycle_count_enter, name='cycle_count_enter'),
    path('cycle-counts/sessions/<int:pk>/approve/', cycle_count.cycle_count_approve, name='cycle_count_approve'),

    # -------------------------------------------------------------------------
    # Landed Cost
    # -------------------------------------------------------------------------
    path('landed-cost/', landed_cost.landed_cost_list, name='landed_cost_list'),
    path('landed-cost/create/<int:receipt_pk>/', landed_cost.landed_cost_create, name='landed_cost_create'),
    path('landed-cost/<int:pk>/', landed_cost.landed_cost_detail, name='landed_cost_detail'),
    path('landed-cost/<int:pk>/post/', landed_cost.landed_cost_post, name='landed_cost_post'),
]
