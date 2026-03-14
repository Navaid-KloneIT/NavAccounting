from apps.general_ledger.signals import AUDITED_MODELS

from .models import (
    TaxJurisdiction, TaxReturn, UseTaxAssessment,
    IncomeTaxProvision, TaxDeadline, TaxAudit, NexusJurisdiction,
)

TX_AUDITED_MODELS = [
    TaxJurisdiction,
    TaxReturn,
    UseTaxAssessment,
    IncomeTaxProvision,
    TaxDeadline,
    TaxAudit,
    NexusJurisdiction,
]

for model in TX_AUDITED_MODELS:
    if model not in AUDITED_MODELS:
        AUDITED_MODELS.append(model)
