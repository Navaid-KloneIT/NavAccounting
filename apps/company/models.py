from django.conf import settings
from django.db import models

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


class Currency(models.Model):
    """System-wide currency definitions (ISO 4217)."""
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=5)
    decimal_places = models.PositiveSmallIntegerField(default=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Currencies'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class CompanySettings(TenantAwareModel):
    """One-to-one with Tenant. Core company configuration."""
    company_name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)

    # Address
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Financial settings
    base_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='+'
    )
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    financial_year_start_month = models.PositiveSmallIntegerField(default=1)

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        verbose_name_plural = 'Company Settings'

    def __str__(self):
        return self.company_name


class FiscalYear(TenantAwareModel):
    """Fiscal year periods for the tenant."""
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    is_current = models.BooleanField(default=False)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    closed_at = models.DateTimeField(null=True, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-start_date']
        unique_together = ('name', 'tenant')

    def __str__(self):
        return self.name


class FiscalPeriod(TenantAwareModel):
    """Monthly periods within a fiscal year."""
    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.CASCADE,
        related_name='periods'
    )
    name = models.CharField(max_length=50)
    period_number = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    is_adjustment_period = models.BooleanField(default=False)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['period_number']

    def __str__(self):
        return self.name


class AccountType(models.Model):
    """Standard account types (system-wide)."""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    normal_balance = models.CharField(
        max_length=6,
        choices=[('debit', 'Debit'), ('credit', 'Credit')]
    )
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.name


class ChartOfAccountsTemplate(models.Model):
    """Pre-built COA templates (system-level)."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ChartOfAccountsTemplateItem(models.Model):
    """Individual accounts within a COA template."""
    template = models.ForeignKey(
        ChartOfAccountsTemplate,
        on_delete=models.CASCADE,
        related_name='items'
    )
    account_code = models.CharField(max_length=20)
    account_name = models.CharField(max_length=255)
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    is_header = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'account_code']
        unique_together = ('template', 'account_code')

    def __str__(self):
        return f"{self.account_code} - {self.account_name}"
