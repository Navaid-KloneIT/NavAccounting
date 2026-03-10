from django.contrib import admin

from .models import (
    ConsolidationGroup,
    ConsolidationRun,
    CurrencyTranslationRule,
    EliminationEntry,
    EliminationRule,
    Entity,
    IntercompanyBalance,
    IntercompanyTransaction,
    LocalGAAPAdjustment,
    MinorityInterest,
    RegulatoryReport,
    TransferPricingPolicy,
    TransferPricingTransaction,
    TranslationAdjustment,
)


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'entity_type', 'parent', 'functional_currency',
                    'ownership_percentage', 'consolidation_method', 'status', 'tenant')
    list_filter = ('entity_type', 'consolidation_method', 'status', 'tenant')
    search_fields = ('code', 'name', 'legal_name')
    ordering = ['code']


@admin.register(IntercompanyTransaction)
class IntercompanyTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_number', 'from_entity', 'to_entity', 'transaction_type',
                    'amount', 'date', 'status', 'tenant')
    list_filter = ('transaction_type', 'status', 'tenant')
    search_fields = ('transaction_number',)


@admin.register(IntercompanyBalance)
class IntercompanyBalanceAdmin(admin.ModelAdmin):
    list_display = ('from_entity', 'to_entity', 'fiscal_period', 'balance',
                    'is_reconciled', 'tenant')
    list_filter = ('is_reconciled', 'tenant')


@admin.register(CurrencyTranslationRule)
class CurrencyTranslationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_scope', 'rate_type', 'is_active', 'tenant')
    list_filter = ('rate_type', 'account_scope', 'is_active', 'tenant')


@admin.register(TranslationAdjustment)
class TranslationAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('entity', 'fiscal_period', 'cta_amount', 'cta_cumulative', 'tenant')
    list_filter = ('tenant',)


@admin.register(ConsolidationGroup)
class ConsolidationGroupAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent_entity', 'reporting_currency', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('code', 'name')
    filter_horizontal = ('entities',)


@admin.register(ConsolidationRun)
class ConsolidationRunAdmin(admin.ModelAdmin):
    list_display = ('run_number', 'consolidation_group', 'fiscal_period', 'status',
                    'total_eliminations', 'total_minority_interest', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('run_number',)


@admin.register(EliminationRule)
class EliminationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'consolidation_group', 'is_auto', 'is_active',
                    'priority', 'tenant')
    list_filter = ('rule_type', 'is_auto', 'is_active', 'tenant')
    ordering = ['priority', 'name']


@admin.register(EliminationEntry)
class EliminationEntryAdmin(admin.ModelAdmin):
    list_display = ('consolidation_run', 'from_entity', 'to_entity', 'amount', 'tenant')
    list_filter = ('tenant',)


@admin.register(MinorityInterest)
class MinorityInterestAdmin(admin.ModelAdmin):
    list_display = ('entity', 'fiscal_period', 'minority_percentage', 'minority_share',
                    'minority_equity', 'tenant')
    list_filter = ('tenant',)


@admin.register(TransferPricingPolicy)
class TransferPricingPolicyAdmin(admin.ModelAdmin):
    list_display = ('policy_number', 'name', 'from_entity', 'to_entity', 'pricing_method',
                    'markup_percentage', 'status', 'tenant')
    list_filter = ('pricing_method', 'status', 'tenant')
    search_fields = ('policy_number', 'name')


@admin.register(TransferPricingTransaction)
class TransferPricingTransactionAdmin(admin.ModelAdmin):
    list_display = ('intercompany_transaction', 'transfer_price', 'arms_length_price',
                    'variance', 'status', 'tenant')
    list_filter = ('status', 'tenant')


@admin.register(LocalGAAPAdjustment)
class LocalGAAPAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('adjustment_number', 'entity', 'fiscal_period', 'adjustment_type',
                    'amount', 'status', 'tenant')
    list_filter = ('adjustment_type', 'status', 'tenant')
    search_fields = ('adjustment_number',)


@admin.register(RegulatoryReport)
class RegulatoryReportAdmin(admin.ModelAdmin):
    list_display = ('report_number', 'entity', 'fiscal_period', 'report_type', 'name',
                    'status', 'tenant')
    list_filter = ('report_type', 'status', 'tenant')
    search_fields = ('report_number', 'name')
