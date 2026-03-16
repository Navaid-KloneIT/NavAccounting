from django.contrib import admin

from .models import (
    Budget, BudgetLineItem, BudgetVersion,
    PlanningDriver, PlanningDriverPeriod,
    RollingForecast, ForecastLineItem,
    VarianceAnalysis, VarianceLineItem,
    ScenarioModel, ScenarioAdjustment,
    WorkforcePlan, WorkforcePlanPosition,
)


# ── Budget ────────────────────────────────────
class BudgetLineItemInline(admin.TabularInline):
    model = BudgetLineItem
    extra = 0


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('budget_number', 'name', 'budget_type', 'fiscal_year',
                    'status', 'total_amount', 'is_active', 'tenant')
    list_filter = ('status', 'budget_type', 'approach', 'is_active', 'tenant')
    search_fields = ('budget_number', 'name')
    inlines = [BudgetLineItemInline]


@admin.register(BudgetLineItem)
class BudgetLineItemAdmin(admin.ModelAdmin):
    list_display = ('budget', 'gl_account', 'fiscal_period', 'department', 'amount', 'tenant')
    list_filter = ('tenant',)
    search_fields = ('budget__budget_number', 'gl_account__account_number')


# ── Versions ──────────────────────────────────
@admin.register(BudgetVersion)
class BudgetVersionAdmin(admin.ModelAdmin):
    list_display = ('version_number', 'budget', 'name', 'version_type',
                    'is_current', 'total_amount', 'tenant')
    list_filter = ('version_type', 'is_current', 'tenant')
    search_fields = ('version_number', 'name')


# ── Planning Drivers ──────────────────────────
class PlanningDriverPeriodInline(admin.TabularInline):
    model = PlanningDriverPeriod
    extra = 0


@admin.register(PlanningDriver)
class PlanningDriverAdmin(admin.ModelAdmin):
    list_display = ('driver_number', 'name', 'driver_type', 'base_value',
                    'growth_rate', 'is_active', 'tenant')
    list_filter = ('driver_type', 'is_active', 'tenant')
    search_fields = ('driver_number', 'name')
    inlines = [PlanningDriverPeriodInline]


@admin.register(PlanningDriverPeriod)
class PlanningDriverPeriodAdmin(admin.ModelAdmin):
    list_display = ('driver', 'fiscal_period', 'quantity', 'rate', 'calculated_amount', 'tenant')
    list_filter = ('tenant',)


# ── Rolling Forecasts ─────────────────────────
class ForecastLineItemInline(admin.TabularInline):
    model = ForecastLineItem
    extra = 0


@admin.register(RollingForecast)
class RollingForecastAdmin(admin.ModelAdmin):
    list_display = ('forecast_number', 'name', 'forecast_type', 'status',
                    'as_of_date', 'horizon_periods', 'tenant')
    list_filter = ('status', 'forecast_type', 'tenant')
    search_fields = ('forecast_number', 'name')
    inlines = [ForecastLineItemInline]


@admin.register(ForecastLineItem)
class ForecastLineItemAdmin(admin.ModelAdmin):
    list_display = ('forecast', 'gl_account', 'fiscal_period',
                    'forecast_amount', 'actual_amount', 'variance_amount', 'tenant')
    list_filter = ('tenant',)


# ── Variance Analysis ─────────────────────────
class VarianceLineItemInline(admin.TabularInline):
    model = VarianceLineItem
    extra = 0


@admin.register(VarianceAnalysis)
class VarianceAnalysisAdmin(admin.ModelAdmin):
    list_display = ('analysis_number', 'name', 'budget', 'fiscal_period',
                    'status', 'total_variance', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('analysis_number', 'name')
    inlines = [VarianceLineItemInline]


@admin.register(VarianceLineItem)
class VarianceLineItemAdmin(admin.ModelAdmin):
    list_display = ('analysis', 'gl_account', 'budget_amount', 'actual_amount',
                    'variance_amount', 'is_favorable', 'tenant')
    list_filter = ('is_favorable', 'tenant')


# ── Scenarios ─────────────────────────────────
class ScenarioAdjustmentInline(admin.TabularInline):
    model = ScenarioAdjustment
    extra = 0


@admin.register(ScenarioModel)
class ScenarioModelAdmin(admin.ModelAdmin):
    list_display = ('scenario_number', 'name', 'budget', 'scenario_type',
                    'status', 'tenant')
    list_filter = ('scenario_type', 'status', 'tenant')
    search_fields = ('scenario_number', 'name')
    inlines = [ScenarioAdjustmentInline]


@admin.register(ScenarioAdjustment)
class ScenarioAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('scenario', 'gl_account', 'adjustment_type',
                    'adjustment_value', 'original_amount', 'adjusted_amount', 'tenant')
    list_filter = ('adjustment_type', 'tenant')


# ── Workforce Planning ────────────────────────
class WorkforcePlanPositionInline(admin.TabularInline):
    model = WorkforcePlanPosition
    extra = 0


@admin.register(WorkforcePlan)
class WorkforcePlanAdmin(admin.ModelAdmin):
    list_display = ('plan_number', 'name', 'budget', 'department', 'status',
                    'total_headcount', 'total_cost', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('plan_number', 'name')
    inlines = [WorkforcePlanPositionInline]


@admin.register(WorkforcePlanPosition)
class WorkforcePlanPositionAdmin(admin.ModelAdmin):
    list_display = ('workforce_plan', 'position_title', 'department', 'headcount',
                    'annual_salary', 'total_cost', 'is_new_position', 'tenant')
    list_filter = ('is_new_position', 'tenant')
    search_fields = ('position_title', 'department')
