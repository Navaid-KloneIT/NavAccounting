from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from apps.general_ledger.models import Account

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
# 1. Item Master Forms
# =============================================================================

class ItemCategoryForm(forms.ModelForm):
    class Meta:
        model = ItemCategory
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'gl_inventory_account': forms.Select(attrs={'class': 'form-select'}),
            'gl_cogs_account': forms.Select(attrs={'class': 'form-select'}),
            'gl_revenue_account': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            gl_qs = Account.unscoped.filter(tenant=tenant, is_active=True, is_header=False)
            self.fields['gl_inventory_account'].queryset = gl_qs
            self.fields['gl_cogs_account'].queryset = gl_qs
            self.fields['gl_revenue_account'].queryset = gl_qs
            self.fields['parent'].queryset = ItemCategory.unscoped.filter(
                tenant=tenant, is_active=True
            )


class UnitOfMeasureForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'abbreviation': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        exclude = ['tenant', 'created_at', 'updated_at', 'sku',
                    'quantity_on_hand', 'weighted_avg_cost']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'base_uom': forms.Select(attrs={'class': 'form-select'}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'costing_method': forms.Select(attrs={'class': 'form-select'}),
            'standard_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reorder_point': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reorder_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'safety_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'L x W x H'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = ItemCategory.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['base_uom'].queryset = UnitOfMeasure.unscoped.filter(
                tenant=tenant, is_active=True
            )


class ItemFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Search items...'
        })
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=ItemCategory.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Categories'
    )
    item_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + Item.ITEM_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('active', 'Active'), ('inactive', 'Inactive')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = ItemCategory.unscoped.filter(
                tenant=tenant, is_active=True
            )


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =============================================================================
# 3. Purchase Requisition Forms
# =============================================================================

class PurchaseRequisitionForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequisition
        exclude = ['tenant', 'created_at', 'updated_at', 'requisition_number',
                    'requested_by', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PurchaseRequisitionLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequisitionLine
        exclude = ['requisition']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'uom': forms.Select(attrs={'class': 'form-select'}),
            'estimated_unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


PurchaseRequisitionLineFormSet = inlineformset_factory(
    PurchaseRequisition, PurchaseRequisitionLine,
    form=PurchaseRequisitionLineForm,
    extra=3, can_delete=True,
)


# =============================================================================
# 4. Purchase Order Forms
# =============================================================================

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        exclude = ['tenant', 'created_at', 'updated_at', 'po_number',
                    'created_by', 'approved_by', 'status', 'total_amount']
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'requisition': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_delivery': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.accounts_payable.models import Vendor
            self.fields['vendor'].queryset = Vendor.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['requisition'].queryset = PurchaseRequisition.unscoped.filter(
                tenant=tenant, status='approved'
            )
            self.fields['requisition'].required = False


class PurchaseOrderLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderLine
        exclude = ['purchase_order', 'line_total', 'received_quantity']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'uom': forms.Select(attrs={'class': 'form-select'}),
        }


PurchaseOrderLineFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseOrderLine,
    form=PurchaseOrderLineForm,
    extra=3, can_delete=True,
)


# =============================================================================
# 5. Goods Receipt Forms
# =============================================================================

class GoodsReceiptForm(forms.ModelForm):
    class Meta:
        model = GoodsReceipt
        exclude = ['tenant', 'created_at', 'updated_at', 'receipt_number',
                    'received_by', 'status', 'journal_entry', 'purchase_order']
        widgets = {
            'receipt_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.unscoped.filter(
                tenant=tenant, is_active=True
            )


class GoodsReceiptLineForm(forms.ModelForm):
    class Meta:
        model = GoodsReceiptLine
        exclude = ['goods_receipt']
        widgets = {
            'po_line': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity_received': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


GoodsReceiptLineFormSet = inlineformset_factory(
    GoodsReceipt, GoodsReceiptLine,
    form=GoodsReceiptLineForm,
    extra=3, can_delete=True,
)


# =============================================================================
# 6. Inventory Transaction Forms
# =============================================================================

class InventoryAdjustmentForm(forms.ModelForm):
    class Meta:
        model = InventoryTransaction
        exclude = ['tenant', 'created_at', 'updated_at', 'transaction_number',
                    'posted_by', 'journal_entry', 'total_cost', 'transaction_type',
                    'reference']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.unscoped.filter(
                tenant=tenant, is_active=True, item_type='inventory'
            )
            self.fields['warehouse'].queryset = Warehouse.unscoped.filter(
                tenant=tenant, is_active=True
            )


class InventoryScrapForm(InventoryAdjustmentForm):
    """Same as adjustment but for scrap/write-off transactions."""
    pass


class TransactionFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Search transactions...'
        })
    )
    transaction_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + InventoryTransaction.TRANSACTION_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    item = forms.ModelChoiceField(
        required=False,
        queryset=Item.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Items'
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['item'].queryset = Item.unscoped.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# 7. Inventory Transfer Forms
# =============================================================================

class InventoryTransferForm(forms.ModelForm):
    class Meta:
        model = InventoryTransfer
        exclude = ['tenant', 'created_at', 'updated_at', 'transfer_number',
                    'created_by', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'from_warehouse': forms.Select(attrs={'class': 'form-select'}),
            'to_warehouse': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            wh_qs = Warehouse.unscoped.filter(tenant=tenant, is_active=True)
            self.fields['from_warehouse'].queryset = wh_qs
            self.fields['to_warehouse'].queryset = wh_qs


class InventoryTransferLineForm(forms.ModelForm):
    class Meta:
        model = InventoryTransferLine
        exclude = ['transfer']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
        }


InventoryTransferLineFormSet = inlineformset_factory(
    InventoryTransfer, InventoryTransferLine,
    form=InventoryTransferLineForm,
    extra=3, can_delete=True,
)


# =============================================================================
# 8. COGS Forms
# =============================================================================

class COGSCalculationForm(forms.ModelForm):
    class Meta:
        model = COGSCalculation
        exclude = ['tenant', 'created_at', 'updated_at', 'calculation_number',
                    'created_by', 'status', 'total_cogs', 'journal_entry']
        widgets = {
            'period': forms.Select(attrs={'class': 'form-select'}),
            'calculation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalPeriod
            self.fields['period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant
            ).order_by('-start_date')


# =============================================================================
# 9. Reorder Planning Forms
# =============================================================================

class ReorderFilterForm(forms.Form):
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + ReorderSuggestion.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=ItemCategory.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Categories'
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = ItemCategory.unscoped.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# 10. Cycle Counting Forms
# =============================================================================

class CycleCountPlanForm(forms.ModelForm):
    class Meta:
        model = CycleCountPlan
        exclude = ['tenant', 'created_at', 'updated_at', 'plan_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'item_selection_method': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'next_count_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['category'].queryset = ItemCategory.unscoped.filter(
                tenant=tenant, is_active=True
            )


class CycleCountSessionForm(forms.ModelForm):
    class Meta:
        model = CycleCountSession
        exclude = ['tenant', 'created_at', 'updated_at', 'session_number',
                    'counted_by', 'status', 'journal_entry']
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'count_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['plan'].queryset = CycleCountPlan.unscoped.filter(
                tenant=tenant, status='active'
            )
            self.fields['plan'].required = False
            self.fields['warehouse'].queryset = Warehouse.unscoped.filter(
                tenant=tenant, is_active=True
            )


class CycleCountItemForm(forms.ModelForm):
    class Meta:
        model = CycleCountItem
        fields = ['counted_quantity', 'resolution_notes']
        widgets = {
            'counted_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'resolution_notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


CycleCountItemFormSet = inlineformset_factory(
    CycleCountSession, CycleCountItem,
    form=CycleCountItemForm,
    extra=0, can_delete=False,
)


# =============================================================================
# 11. Landed Cost Forms
# =============================================================================

class LandedCostVoucherForm(forms.ModelForm):
    class Meta:
        model = LandedCostVoucher
        exclude = ['tenant', 'created_at', 'updated_at', 'voucher_number',
                    'created_by', 'status', 'total_additional_cost', 'journal_entry',
                    'goods_receipt']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class LandedCostLineForm(forms.ModelForm):
    class Meta:
        model = LandedCostLine
        exclude = ['voucher']
        widgets = {
            'cost_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vendor': forms.Select(attrs={'class': 'form-select'}),
        }


LandedCostLineFormSet = inlineformset_factory(
    LandedCostVoucher, LandedCostLine,
    form=LandedCostLineForm,
    extra=3, can_delete=True,
)


class LandedCostAllocationForm(forms.ModelForm):
    class Meta:
        model = LandedCostAllocation
        exclude = ['voucher']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'goods_receipt_line': forms.Select(attrs={'class': 'form-select'}),
            'allocated_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'allocation_method': forms.Select(attrs={'class': 'form-select'}),
        }
