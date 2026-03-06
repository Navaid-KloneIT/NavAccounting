from django.contrib import admin

from .models import (
    Employee, PayrollJournal, PayrollJournalLine,
    TaxWithholding, TaxRemittance,
    BenefitPlan, EmployeeBenefit,
    Garnishment,
    WorkersCompClass, WorkersCompAssignment,
    PayrollReconciliation,
)


# =============================================================================
# Employee Master
# =============================================================================

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_number', 'last_name', 'first_name', 'department',
                    'pay_type', 'pay_frequency', 'is_active', 'tenant')
    list_filter = ('pay_type', 'pay_frequency', 'is_active', 'tenant')
    search_fields = ('employee_number', 'first_name', 'last_name', 'email')
    ordering = ['last_name', 'first_name']


# =============================================================================
# Payroll Journal
# =============================================================================

class PayrollJournalLineInline(admin.TabularInline):
    model = PayrollJournalLine
    extra = 0


@admin.register(PayrollJournal)
class PayrollJournalAdmin(admin.ModelAdmin):
    list_display = ('journal_number', 'pay_period_start', 'pay_period_end',
                    'pay_date', 'total_gross', 'total_net', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('journal_number',)
    inlines = [PayrollJournalLineInline]


# =============================================================================
# Tax Management
# =============================================================================

@admin.register(TaxWithholding)
class TaxWithholdingAdmin(admin.ModelAdmin):
    list_display = ('employee', 'tax_type', 'rate', 'ytd_amount',
                    'is_employer_paid', 'effective_date', 'tenant')
    list_filter = ('tax_type', 'is_employer_paid', 'tenant')
    search_fields = ('employee__first_name', 'employee__last_name')


@admin.register(TaxRemittance)
class TaxRemittanceAdmin(admin.ModelAdmin):
    list_display = ('remittance_number', 'tax_type', 'amount_due', 'amount_paid',
                    'due_date', 'status', 'tenant')
    list_filter = ('tax_type', 'status', 'tenant')
    search_fields = ('remittance_number',)


# =============================================================================
# Benefits
# =============================================================================

@admin.register(BenefitPlan)
class BenefitPlanAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'benefit_type', 'employer_contribution_type',
                    'employer_contribution_amount', 'is_active', 'tenant')
    list_filter = ('benefit_type', 'is_active', 'tenant')
    search_fields = ('code', 'name')
    ordering = ['code']


@admin.register(EmployeeBenefit)
class EmployeeBenefitAdmin(admin.ModelAdmin):
    list_display = ('employee', 'benefit_plan', 'employee_contribution',
                    'enrollment_date', 'is_active')
    list_filter = ('is_active', 'benefit_plan')
    search_fields = ('employee__first_name', 'employee__last_name')


# =============================================================================
# Garnishments
# =============================================================================

@admin.register(Garnishment)
class GarnishmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'garnishment_type', 'amount', 'total_required',
                    'total_paid', 'status', 'tenant')
    list_filter = ('garnishment_type', 'status', 'tenant')
    search_fields = ('employee__first_name', 'employee__last_name', 'case_number')


# =============================================================================
# Workers Comp
# =============================================================================

@admin.register(WorkersCompClass)
class WorkersCompClassAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'rate', 'effective_date', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('code', 'name')
    ordering = ['code']


@admin.register(WorkersCompAssignment)
class WorkersCompAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'comp_class', 'effective_date', 'end_date')
    search_fields = ('employee__first_name', 'employee__last_name')


# =============================================================================
# Reconciliation
# =============================================================================

@admin.register(PayrollReconciliation)
class PayrollReconciliationAdmin(admin.ModelAdmin):
    list_display = ('reconciliation_number', 'payroll_journal', 'reconciliation_date',
                    'total_gross', 'total_net', 'variance_amount', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('reconciliation_number',)
