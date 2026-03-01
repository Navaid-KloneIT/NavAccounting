from django.contrib import admin

from .models import (
    Account, JournalEntry, JournalEntryLine, JournalApproval,
    PeriodCloseChecklist, AccountReconciliation,
    AllocationRule, AllocationRuleLine,
    AuditTrail, ExchangeRate,
)


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 2


class AllocationRuleLineInline(admin.TabularInline):
    model = AllocationRuleLine
    extra = 1


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'name', 'account_type', 'tenant', 'is_active', 'is_header')
    list_filter = ('account_type', 'is_active', 'is_header', 'tenant')
    search_fields = ('account_number', 'name')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_number', 'date', 'description', 'status', 'source', 'tenant')
    list_filter = ('status', 'source', 'tenant')
    search_fields = ('entry_number', 'description')
    inlines = [JournalEntryLineInline]


@admin.register(JournalApproval)
class JournalApprovalAdmin(admin.ModelAdmin):
    list_display = ('journal_entry', 'approver', 'status', 'approved_at', 'tenant')
    list_filter = ('status', 'tenant')


@admin.register(PeriodCloseChecklist)
class PeriodCloseChecklistAdmin(admin.ModelAdmin):
    list_display = ('fiscal_period', 'step_name', 'step_order', 'is_completed', 'tenant')
    list_filter = ('is_completed', 'tenant')


@admin.register(AccountReconciliation)
class AccountReconciliationAdmin(admin.ModelAdmin):
    list_display = ('account', 'fiscal_period', 'expected_balance', 'actual_balance', 'difference', 'status', 'tenant')
    list_filter = ('status', 'tenant')


@admin.register(AllocationRule)
class AllocationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_account', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    inlines = [AllocationRuleLineInline]


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'record_id', 'action', 'field_name', 'user', 'timestamp', 'tenant')
    list_filter = ('action', 'table_name', 'tenant')
    search_fields = ('table_name', 'field_name')
    readonly_fields = ('table_name', 'record_id', 'action', 'field_name', 'old_value', 'new_value', 'user', 'ip_address', 'timestamp')


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('from_currency', 'to_currency', 'rate', 'effective_date', 'source', 'tenant')
    list_filter = ('from_currency', 'to_currency', 'tenant')
    search_fields = ('source',)
