from django.contrib import admin

from .models import (
    BankAccount, BankAccountSignatory, BankFeed, BankTransaction,
    BankReconciliation, ReconciliationItem, AutoMatchRule,
    CashForecast, CashForecastLine, IntercompanyTransfer, BankFee
)


class BankAccountSignatoryInline(admin.TabularInline):
    model = BankAccountSignatory
    extra = 1


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        'account_number_display', 'bank_name', 'account_type',
        'current_balance', 'is_active', 'tenant'
    )
    list_filter = ('account_type', 'is_active', 'tenant')
    search_fields = ('account_number_display', 'bank_name', 'account_number')
    inlines = [BankAccountSignatoryInline]


@admin.register(BankFeed)
class BankFeedAdmin(admin.ModelAdmin):
    list_display = ('bank_account', 'feed_source', 'status', 'last_sync_at', 'tenant')
    list_filter = ('feed_source', 'status', 'tenant')


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_number', 'bank_account', 'transaction_date',
        'amount', 'transaction_type', 'is_matched', 'tenant'
    )
    list_filter = ('transaction_type', 'is_matched', 'tenant')
    search_fields = ('transaction_number', 'description', 'reference')


class ReconciliationItemInline(admin.TabularInline):
    model = ReconciliationItem
    extra = 0


@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = (
        'bank_account', 'fiscal_period', 'statement_date',
        'statement_balance', 'status', 'tenant'
    )
    list_filter = ('status', 'tenant')
    inlines = [ReconciliationItemInline]


@admin.register(AutoMatchRule)
class AutoMatchRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'priority', 'is_active', 'tenant')
    list_filter = ('rule_type', 'is_active', 'tenant')


class CashForecastLineInline(admin.TabularInline):
    model = CashForecastLine
    extra = 3


@admin.register(CashForecast)
class CashForecastAdmin(admin.ModelAdmin):
    list_display = (
        'forecast_number', 'name', 'forecast_type',
        'start_date', 'end_date', 'status', 'tenant'
    )
    list_filter = ('forecast_type', 'status', 'tenant')
    search_fields = ('forecast_number', 'name')
    inlines = [CashForecastLineInline]


@admin.register(IntercompanyTransfer)
class IntercompanyTransferAdmin(admin.ModelAdmin):
    list_display = (
        'transfer_number', 'from_bank_account', 'to_bank_account',
        'amount', 'transfer_date', 'status', 'tenant'
    )
    list_filter = ('status', 'tenant')
    search_fields = ('transfer_number', 'reference')


@admin.register(BankFee)
class BankFeeAdmin(admin.ModelAdmin):
    list_display = (
        'bank_account', 'fee_date', 'fee_type',
        'amount', 'is_recurring', 'tenant'
    )
    list_filter = ('fee_type', 'is_recurring', 'tenant')
    search_fields = ('description',)
