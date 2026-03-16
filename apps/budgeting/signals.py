from apps.general_ledger.signals import AUDITED_MODELS

from .models import (
    Budget, BudgetVersion,
    PlanningDriver, RollingForecast,
    VarianceAnalysis, ScenarioModel,
    WorkforcePlan,
)

BP_AUDITED_MODELS = [
    Budget, BudgetVersion,
    PlanningDriver, RollingForecast,
    VarianceAnalysis, ScenarioModel,
    WorkforcePlan,
]

for model in BP_AUDITED_MODELS:
    if model not in AUDITED_MODELS:
        AUDITED_MODELS.append(model)
