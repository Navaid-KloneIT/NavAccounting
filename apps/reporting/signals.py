from apps.general_ledger.signals import AUDITED_MODELS

from .models import (
    FinancialStatement, ManagementReport, CustomReport,
    ReportSchedule, XBRLFiling, StatutoryReport,
    ConsolidationPackage, ReportDashboard,
)

RC_AUDITED_MODELS = [
    FinancialStatement,
    ManagementReport,
    CustomReport,
    ReportSchedule,
    XBRLFiling,
    StatutoryReport,
    ConsolidationPackage,
    ReportDashboard,
]

for model in RC_AUDITED_MODELS:
    if model not in AUDITED_MODELS:
        AUDITED_MODELS.append(model)
