from apps.general_ledger.signals import AUDITED_MODELS

from .models import (
    Project, ProjectInvoice, RevenueRecognition,
    TimeEntry, ExpenseEntry, ProfitabilitySnapshot,
)

PJ_AUDITED_MODELS = [
    Project, ProjectInvoice, RevenueRecognition,
    TimeEntry, ExpenseEntry, ProfitabilitySnapshot,
]

for model in PJ_AUDITED_MODELS:
    if model not in AUDITED_MODELS:
        AUDITED_MODELS.append(model)
