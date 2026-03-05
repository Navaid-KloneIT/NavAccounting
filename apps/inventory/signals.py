from apps.general_ledger.signals import AUDITED_MODELS

from .models import (
    Item, PurchaseOrder, GoodsReceipt, InventoryTransaction,
    InventoryTransfer, COGSCalculation, LandedCostVoucher, CycleCountSession,
)

IC_AUDITED_MODELS = [
    Item, PurchaseOrder, GoodsReceipt, InventoryTransaction,
    InventoryTransfer, COGSCalculation, LandedCostVoucher, CycleCountSession,
]

for model in IC_AUDITED_MODELS:
    if model not in AUDITED_MODELS:
        AUDITED_MODELS.append(model)
