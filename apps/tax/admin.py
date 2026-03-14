from django.contrib import admin

from .models import (
    TaxJurisdiction, TaxRate, TaxRule, TaxGroup, TaxGroupMember,
    TaxReturn, TaxReturnLine, TaxReturnPayment,
    UseTaxAssessment, UseTaxAccrual,
    IncomeTaxProvision, DeferredTaxItem, ETRReconciliation,
    TaxDeadline, TaxDeadlineReminder,
    TaxAudit, AuditFinding, AuditDocument,
    NexusJurisdiction, NexusActivity,
)


# =============================================================================
# Sales Tax Engine
# =============================================================================

@admin.register(TaxJurisdiction)
class TaxJurisdictionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'jurisdiction_level', 'country',
                    'state_code', 'is_active', 'tenant')
    list_filter = ('jurisdiction_level', 'is_active', 'tenant')
    search_fields = ('code', 'name', 'state_code')
    ordering = ['code']


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ('jurisdiction', 'rate_name', 'rate', 'effective_date',
                    'end_date', 'is_compound', 'is_active', 'tenant')
    list_filter = ('is_active', 'is_compound', 'tenant')
    search_fields = ('rate_name', 'jurisdiction__code', 'jurisdiction__name')
    ordering = ['-effective_date']


@admin.register(TaxRule)
class TaxRuleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'jurisdiction', 'rule_type',
                    'product_category', 'is_active', 'tenant')
    list_filter = ('rule_type', 'is_active', 'tenant')
    search_fields = ('code', 'name', 'product_category')
    ordering = ['code']


class TaxGroupMemberInline(admin.TabularInline):
    model = TaxGroupMember
    extra = 0


@admin.register(TaxGroup)
class TaxGroupAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('code', 'name')
    ordering = ['code']
    inlines = [TaxGroupMemberInline]


# =============================================================================
# Tax Returns
# =============================================================================

class TaxReturnLineInline(admin.TabularInline):
    model = TaxReturnLine
    extra = 0


@admin.register(TaxReturn)
class TaxReturnAdmin(admin.ModelAdmin):
    list_display = ('return_number', 'return_type', 'jurisdiction', 'period_start',
                    'period_end', 'net_tax_due', 'status', 'tenant')
    list_filter = ('return_type', 'status', 'tenant')
    search_fields = ('return_number', 'confirmation_number')
    ordering = ['-period_end']
    inlines = [TaxReturnLineInline]


@admin.register(TaxReturnPayment)
class TaxReturnPaymentAdmin(admin.ModelAdmin):
    list_display = ('tax_return', 'payment_date', 'amount',
                    'payment_method', 'reference', 'tenant')
    list_filter = ('payment_method', 'tenant')
    search_fields = ('reference', 'tax_return__return_number')


# =============================================================================
# Use Tax Tracking
# =============================================================================

@admin.register(UseTaxAssessment)
class UseTaxAssessmentAdmin(admin.ModelAdmin):
    list_display = ('assessment_number', 'vendor', 'jurisdiction', 'purchase_date',
                    'purchase_amount', 'tax_amount', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('assessment_number', 'vendor__company_name')
    ordering = ['-purchase_date']


@admin.register(UseTaxAccrual)
class UseTaxAccrualAdmin(admin.ModelAdmin):
    list_display = ('accrual_number', 'period_start', 'period_end',
                    'total_purchases', 'total_tax_accrued', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('accrual_number',)


# =============================================================================
# Income Tax Provision
# =============================================================================

class DeferredTaxItemInline(admin.TabularInline):
    model = DeferredTaxItem
    extra = 0


class ETRReconciliationInline(admin.TabularInline):
    model = ETRReconciliation
    extra = 0


@admin.register(IncomeTaxProvision)
class IncomeTaxProvisionAdmin(admin.ModelAdmin):
    list_display = ('provision_number', 'fiscal_year', 'provision_type',
                    'pretax_income', 'total_tax_expense', 'effective_tax_rate',
                    'status', 'tenant')
    list_filter = ('provision_type', 'status', 'tenant')
    search_fields = ('provision_number',)
    inlines = [DeferredTaxItemInline, ETRReconciliationInline]


# =============================================================================
# Tax Calendar
# =============================================================================

class TaxDeadlineReminderInline(admin.TabularInline):
    model = TaxDeadlineReminder
    extra = 0


@admin.register(TaxDeadline)
class TaxDeadlineAdmin(admin.ModelAdmin):
    list_display = ('deadline_number', 'name', 'tax_type', 'jurisdiction',
                    'due_date', 'status', 'is_recurring', 'tenant')
    list_filter = ('tax_type', 'status', 'is_recurring', 'tenant')
    search_fields = ('deadline_number', 'name')
    ordering = ['due_date']
    inlines = [TaxDeadlineReminderInline]


# =============================================================================
# Audit Support
# =============================================================================

class AuditFindingInline(admin.TabularInline):
    model = AuditFinding
    extra = 0


class AuditDocumentInline(admin.TabularInline):
    model = AuditDocument
    extra = 0


@admin.register(TaxAudit)
class TaxAuditAdmin(admin.ModelAdmin):
    list_display = ('audit_number', 'name', 'tax_type', 'jurisdiction',
                    'audit_period_start', 'audit_period_end', 'status', 'tenant')
    list_filter = ('tax_type', 'status', 'tenant')
    search_fields = ('audit_number', 'name', 'auditing_authority')
    ordering = ['-audit_period_end']
    inlines = [AuditFindingInline, AuditDocumentInline]


# =============================================================================
# Nexus Tracking
# =============================================================================

class NexusActivityInline(admin.TabularInline):
    model = NexusActivity
    extra = 0


@admin.register(NexusJurisdiction)
class NexusJurisdictionAdmin(admin.ModelAdmin):
    list_display = ('jurisdiction', 'nexus_type', 'has_nexus', 'registration_status',
                    'current_period_sales', 'threshold_percentage', 'is_active', 'tenant')
    list_filter = ('nexus_type', 'has_nexus', 'registration_status', 'is_active', 'tenant')
    search_fields = ('jurisdiction__code', 'jurisdiction__name', 'registration_number')
    inlines = [NexusActivityInline]
