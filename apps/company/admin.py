from django.contrib import admin

from .models import (
    AccountType,
    ChartOfAccountsTemplate,
    ChartOfAccountsTemplateItem,
    CompanySettings,
    Currency,
    FiscalPeriod,
    FiscalYear,
)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'tenant', 'base_currency', 'country')
    list_filter = ('tenant',)
    search_fields = ('company_name',)


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'start_date', 'end_date', 'is_current', 'is_closed')
    list_filter = ('is_current', 'is_closed', 'tenant')


@admin.register(FiscalPeriod)
class FiscalPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'fiscal_year', 'period_number', 'start_date', 'end_date', 'is_closed')
    list_filter = ('is_closed', 'fiscal_year')


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'normal_balance', 'display_order')


@admin.register(ChartOfAccountsTemplate)
class ChartOfAccountsTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'is_default')
    list_filter = ('is_default',)


@admin.register(ChartOfAccountsTemplateItem)
class ChartOfAccountsTemplateItemAdmin(admin.ModelAdmin):
    list_display = ('account_code', 'account_name', 'account_type', 'template', 'is_header')
    list_filter = ('template', 'account_type')
    search_fields = ('account_code', 'account_name')
