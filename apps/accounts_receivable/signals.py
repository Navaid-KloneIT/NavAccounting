"""Extend audit trail to cover Accounts Receivable models."""
from apps.general_ledger.signals import AUDITED_MODELS

from .models import Invoice, InvoiceApproval, Receipt, Customer


AR_AUDITED_MODELS = [Invoice, InvoiceApproval, Receipt, Customer]

# Register AR models into the shared AUDITED_MODELS list
for model in AR_AUDITED_MODELS:
    if model not in AUDITED_MODELS:
        AUDITED_MODELS.append(model)
