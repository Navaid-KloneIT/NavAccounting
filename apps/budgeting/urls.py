from django.urls import path

from .views import (
    budgets, versions, drivers, forecasts,
    variance, scenarios, workforce,
)

app_name = 'budgeting'

urlpatterns = [
    # ── Budgets ───────────────────────────────
    path('budgets/', budgets.budget_list, name='budget_list'),
    path('budgets/create/', budgets.budget_create, name='budget_create'),
    path('budgets/<int:pk>/', budgets.budget_detail, name='budget_detail'),
    path('budgets/<int:pk>/edit/', budgets.budget_edit, name='budget_edit'),
    path('budgets/<int:pk>/submit/', budgets.budget_submit, name='budget_submit'),
    path('budgets/<int:pk>/approve/', budgets.budget_approve, name='budget_approve'),

    # ── Versions ──────────────────────────────
    path('versions/', versions.version_list, name='version_list'),
    path('versions/create/', versions.version_create, name='version_create'),
    path('versions/<int:pk>/', versions.version_detail, name='version_detail'),
    path('versions/<int:pk>/set-current/', versions.version_set_current, name='version_set_current'),

    # ── Planning Drivers ──────────────────────
    path('drivers/', drivers.driver_list, name='driver_list'),
    path('drivers/create/', drivers.driver_create, name='driver_create'),
    path('drivers/<int:pk>/', drivers.driver_detail, name='driver_detail'),
    path('drivers/<int:pk>/edit/', drivers.driver_edit, name='driver_edit'),
    path('drivers/<int:pk>/calculate/', drivers.driver_calculate, name='driver_calculate'),

    # ── Rolling Forecasts ─────────────────────
    path('forecasts/', forecasts.forecast_list, name='forecast_list'),
    path('forecasts/create/', forecasts.forecast_create, name='forecast_create'),
    path('forecasts/<int:pk>/', forecasts.forecast_detail, name='forecast_detail'),
    path('forecasts/<int:pk>/edit/', forecasts.forecast_edit, name='forecast_edit'),

    # ── Variance Analysis ─────────────────────
    path('variance/', variance.variance_list, name='variance_list'),
    path('variance/create/', variance.variance_create, name='variance_create'),
    path('variance/<int:pk>/', variance.variance_detail, name='variance_detail'),
    path('variance/<int:pk>/generate/', variance.variance_generate, name='variance_generate'),

    # ── What-if Scenarios ─────────────────────
    path('scenarios/', scenarios.scenario_list, name='scenario_list'),
    path('scenarios/create/', scenarios.scenario_create, name='scenario_create'),
    path('scenarios/<int:pk>/', scenarios.scenario_detail, name='scenario_detail'),
    path('scenarios/<int:pk>/edit/', scenarios.scenario_edit, name='scenario_edit'),
    path('scenarios/<int:pk>/calculate/', scenarios.scenario_calculate, name='scenario_calculate'),

    # ── Workforce Planning ────────────────────
    path('workforce/', workforce.workforce_list, name='workforce_list'),
    path('workforce/create/', workforce.workforce_create, name='workforce_create'),
    path('workforce/<int:pk>/', workforce.workforce_detail, name='workforce_detail'),
    path('workforce/<int:pk>/edit/', workforce.workforce_edit, name='workforce_edit'),
]
