from apps.general_ledger.signals import AUDITED_MODELS

from .models import (
    Employee, PayrollJournal, TaxRemittance,
    Garnishment, PayrollReconciliation,
)

PR_AUDITED_MODELS = [
    Employee, PayrollJournal, TaxRemittance,
    Garnishment, PayrollReconciliation,
]

for model in PR_AUDITED_MODELS:
    if model not in AUDITED_MODELS:
        AUDITED_MODELS.append(model)
