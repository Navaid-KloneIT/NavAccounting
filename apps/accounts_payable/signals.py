"""Extend audit trail to cover Accounts Payable models."""
from apps.general_ledger.signals import AUDITED_MODELS

from .models import Bill, BillApproval, Payment, Vendor


AP_AUDITED_MODELS = [Bill, BillApproval, Payment, Vendor]

# Register AP models into the shared AUDITED_MODELS list
for model in AP_AUDITED_MODELS:
    if model not in AUDITED_MODELS:
        AUDITED_MODELS.append(model)
