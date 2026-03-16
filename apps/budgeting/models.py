from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# ──────────────────────────────────────────────
# 1. Budget
# ──────────────────────────────────────────────
class Budget(TenantAwareModel):
    """Core budget record — top-down, bottom-up, or hybrid."""

    BUDGET_TYPE_CHOICES = [
        ('top_down', 'Top-Down'),
        ('bottom_up', 'Bottom-Up'),
        ('hybrid', 'Hybrid'),
    ]
    APPROACH_CHOICES = [
        ('incremental', 'Incremental'),
        ('zero_based', 'Zero-Based'),
        ('activity_based', 'Activity-Based'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    budget_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPE_CHOICES, default='top_down')
    approach = models.CharField(max_length=20, choices=APPROACH_CHOICES, default='incremental')
    fiscal_year = models.ForeignKey(
        'company.FiscalYear', on_delete=models.PROTECT,
        related_name='bp_budgets',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField()
    end_date = models.DateField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='bp_budgets_created',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bp_budgets_approved',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'budget_number')

    def __str__(self):
        return f"{self.budget_number} — {self.name}"

    @staticmethod
    def generate_budget_number(tenant):
        prefix = "BUD-"
        last = Budget.unscoped.filter(
            tenant=tenant, budget_number__startswith=prefix
        ).order_by('-budget_number').first()
        if last:
            last_num = int(last.budget_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 2. BudgetLineItem
# ──────────────────────────────────────────────
class BudgetLineItem(TenantAwareModel):
    """Individual line item per GL account / fiscal period."""

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='line_items')
    gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='bp_budget_lines',
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        related_name='bp_budget_lines',
    )
    department = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['gl_account__account_number', 'fiscal_period__period_number']

    def __str__(self):
        return f"{self.budget} | {self.gl_account} | {self.fiscal_period}"


# ──────────────────────────────────────────────
# 3. BudgetVersion
# ──────────────────────────────────────────────
class BudgetVersion(TenantAwareModel):
    """Multiple budget scenarios / revisions."""

    VERSION_TYPE_CHOICES = [
        ('original', 'Original'),
        ('revision', 'Revision'),
        ('scenario', 'Scenario'),
    ]

    version_number = models.CharField(max_length=20, db_index=True)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='versions')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    version_type = models.CharField(max_length=20, choices=VERSION_TYPE_CHOICES, default='original')
    is_current = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='bp_versions_created',
    )
    snapshot_data = models.JSONField(default=dict, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'version_number')

    def __str__(self):
        return f"{self.version_number} — {self.name}"

    @staticmethod
    def generate_version_number(tenant):
        prefix = "VER-"
        last = BudgetVersion.unscoped.filter(
            tenant=tenant, version_number__startswith=prefix
        ).order_by('-version_number').first()
        if last:
            last_num = int(last.version_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 4. PlanningDriver
# ──────────────────────────────────────────────
class PlanningDriver(TenantAwareModel):
    """Revenue / cost / headcount drivers for driver-based planning."""

    DRIVER_TYPE_CHOICES = [
        ('revenue', 'Revenue'),
        ('cost', 'Cost'),
        ('headcount', 'Headcount'),
        ('volume', 'Volume'),
        ('custom', 'Custom'),
    ]

    driver_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    driver_type = models.CharField(max_length=20, choices=DRIVER_TYPE_CHOICES, default='revenue')
    unit = models.CharField(max_length=50, blank=True)
    base_value = models.DecimalField(max_digits=15, decimal_places=4, default=Decimal('0.0000'))
    growth_rate = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal('0.0000'))
    gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='bp_drivers',
    )
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='drivers')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['name']
        unique_together = ('tenant', 'driver_number')

    def __str__(self):
        return f"{self.driver_number} — {self.name}"

    @staticmethod
    def generate_driver_number(tenant):
        prefix = "DRV-"
        last = PlanningDriver.unscoped.filter(
            tenant=tenant, driver_number__startswith=prefix
        ).order_by('-driver_number').first()
        if last:
            last_num = int(last.driver_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 5. PlanningDriverPeriod
# ──────────────────────────────────────────────
class PlanningDriverPeriod(TenantAwareModel):
    """Per-period driver values (quantity × rate)."""

    driver = models.ForeignKey(PlanningDriver, on_delete=models.CASCADE, related_name='periods')
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        related_name='bp_driver_periods',
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default=Decimal('0.0000'))
    rate = models.DecimalField(max_digits=15, decimal_places=4, default=Decimal('0.0000'))
    calculated_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['fiscal_period__period_number']

    def __str__(self):
        return f"{self.driver} | {self.fiscal_period}"


# ──────────────────────────────────────────────
# 6. RollingForecast
# ──────────────────────────────────────────────
class RollingForecast(TenantAwareModel):
    """Continuous planning cycles — monthly or quarterly."""

    FORECAST_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    forecast_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    budget = models.ForeignKey(
        Budget, on_delete=models.CASCADE,
        null=True, blank=True, related_name='forecasts',
    )
    forecast_type = models.CharField(max_length=20, choices=FORECAST_TYPE_CHOICES, default='monthly')
    horizon_periods = models.IntegerField(default=12)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    as_of_date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='bp_forecasts_created',
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-as_of_date']
        unique_together = ('tenant', 'forecast_number')

    def __str__(self):
        return f"{self.forecast_number} — {self.name}"

    @staticmethod
    def generate_forecast_number(tenant):
        prefix = "RFC-"
        last = RollingForecast.unscoped.filter(
            tenant=tenant, forecast_number__startswith=prefix
        ).order_by('-forecast_number').first()
        if last:
            last_num = int(last.forecast_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 7. ForecastLineItem
# ──────────────────────────────────────────────
class ForecastLineItem(TenantAwareModel):
    """Forecast details per GL account and period."""

    forecast = models.ForeignKey(RollingForecast, on_delete=models.CASCADE, related_name='line_items')
    gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='bp_forecast_lines',
    )
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        related_name='bp_forecast_lines',
    )
    forecast_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    variance_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    variance_pct = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['gl_account__account_number', 'fiscal_period__period_number']

    def __str__(self):
        return f"{self.forecast} | {self.gl_account} | {self.fiscal_period}"


# ──────────────────────────────────────────────
# 8. VarianceAnalysis
# ──────────────────────────────────────────────
class VarianceAnalysis(TenantAwareModel):
    """Budget vs actual analysis with drill-down."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]

    analysis_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='variance_analyses')
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        related_name='bp_variance_analyses',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    generated_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bp_variances_generated',
    )
    total_budget = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_actual = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_variance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'analysis_number')
        verbose_name_plural = 'Variance analyses'

    def __str__(self):
        return f"{self.analysis_number} — {self.name}"

    @staticmethod
    def generate_analysis_number(tenant):
        prefix = "VAR-"
        last = VarianceAnalysis.unscoped.filter(
            tenant=tenant, analysis_number__startswith=prefix
        ).order_by('-analysis_number').first()
        if last:
            last_num = int(last.analysis_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 9. VarianceLineItem
# ──────────────────────────────────────────────
class VarianceLineItem(TenantAwareModel):
    """Per-account variance detail."""

    analysis = models.ForeignKey(VarianceAnalysis, on_delete=models.CASCADE, related_name='line_items')
    gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='bp_variance_lines',
    )
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    variance_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    variance_pct = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))
    explanation = models.TextField(blank=True)
    is_favorable = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['gl_account__account_number']

    def __str__(self):
        return f"{self.analysis} | {self.gl_account}"


# ──────────────────────────────────────────────
# 10. ScenarioModel
# ──────────────────────────────────────────────
class ScenarioModel(TenantAwareModel):
    """What-if analysis / scenario modeling."""

    SCENARIO_TYPE_CHOICES = [
        ('best_case', 'Best Case'),
        ('worst_case', 'Worst Case'),
        ('most_likely', 'Most Likely'),
        ('custom', 'Custom'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('reviewed', 'Reviewed'),
    ]

    scenario_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='scenarios')
    scenario_type = models.CharField(max_length=20, choices=SCENARIO_TYPE_CHOICES, default='custom')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='bp_scenarios_created',
    )
    assumptions = models.JSONField(default=dict, blank=True)
    result_summary = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'scenario_number')

    def __str__(self):
        return f"{self.scenario_number} — {self.name}"

    @staticmethod
    def generate_scenario_number(tenant):
        prefix = "SCN-"
        last = ScenarioModel.unscoped.filter(
            tenant=tenant, scenario_number__startswith=prefix
        ).order_by('-scenario_number').first()
        if last:
            last_num = int(last.scenario_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 11. ScenarioAdjustment
# ──────────────────────────────────────────────
class ScenarioAdjustment(TenantAwareModel):
    """Individual what-if adjustments within a scenario."""

    ADJUSTMENT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('override', 'Override'),
    ]

    scenario = models.ForeignKey(ScenarioModel, on_delete=models.CASCADE, related_name='adjustments')
    gl_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='bp_scenario_adjustments',
    )
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE_CHOICES, default='percentage')
    adjustment_value = models.DecimalField(max_digits=15, decimal_places=4, default=Decimal('0.0000'))
    original_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    adjusted_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    fiscal_period = models.ForeignKey(
        'company.FiscalPeriod', on_delete=models.PROTECT,
        null=True, blank=True, related_name='bp_scenario_adjustments',
    )

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['gl_account__account_number']

    def __str__(self):
        return f"{self.scenario} | {self.gl_account} | {self.get_adjustment_type_display()}"


# ──────────────────────────────────────────────
# 12. WorkforcePlan
# ──────────────────────────────────────────────
class WorkforcePlan(TenantAwareModel):
    """Salary and benefits forecasting."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('approved', 'Approved'),
    ]

    plan_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='workforce_plans')
    department = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    total_headcount = models.IntegerField(default=0)
    total_salary_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_benefit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='bp_workforce_plans_created',
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'plan_number')

    def __str__(self):
        return f"{self.plan_number} — {self.name}"

    @staticmethod
    def generate_plan_number(tenant):
        prefix = "WFP-"
        last = WorkforcePlan.unscoped.filter(
            tenant=tenant, plan_number__startswith=prefix
        ).order_by('-plan_number').first()
        if last:
            last_num = int(last.plan_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 13. WorkforcePlanPosition
# ──────────────────────────────────────────────
class WorkforcePlanPosition(TenantAwareModel):
    """Individual positions within a workforce plan."""

    workforce_plan = models.ForeignKey(WorkforcePlan, on_delete=models.CASCADE, related_name='positions')
    position_title = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    headcount = models.IntegerField(default=1)
    annual_salary = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    benefit_rate = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal('0.0000'))
    benefit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    gl_salary_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='bp_workforce_salary',
    )
    gl_benefit_account = models.ForeignKey(
        'general_ledger.Account', on_delete=models.PROTECT,
        related_name='bp_workforce_benefit',
    )
    is_new_position = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['department', 'position_title']

    def __str__(self):
        return f"{self.position_title} ({self.department})"
