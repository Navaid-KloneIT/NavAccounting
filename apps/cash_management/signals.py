"""Extend audit trail to cover Cash Management models."""
from apps.general_ledger.signals import AUDITED_MODELS

from .models import BankAccount, BankReconciliation, IntercompanyTransfer


CM_AUDITED_MODELS = [BankAccount, BankReconciliation, IntercompanyTransfer]

# Register CM models into the shared AUDITED_MODELS list
for model in CM_AUDITED_MODELS:
    if model not in AUDITED_MODELS:
        AUDITED_MODELS.append(model)
