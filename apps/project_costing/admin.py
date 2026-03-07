from django.contrib import admin

from .models import (
    Project, WBSElement, ProjectBudget, BillingRule,
    TimeEntry, ExpenseEntry,
    RevenueRecognition, ProjectMilestone,
    ProjectInvoice, ProjectInvoiceLine,
    ProfitabilitySnapshot, ResourceAssignment,
)


# =============================================================================
# Project Setup
# =============================================================================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_number', 'name', 'client_name', 'status',
                    'billing_type', 'contract_amount', 'is_active', 'tenant')
    list_filter = ('status', 'billing_type', 'is_active', 'tenant')
    search_fields = ('project_number', 'name', 'client_name')
    ordering = ['project_number']


@admin.register(WBSElement)
class WBSElementAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'project', 'level', 'budget_hours',
                    'budget_amount', 'is_billable', 'is_active', 'tenant')
    list_filter = ('is_billable', 'is_active', 'tenant')
    search_fields = ('code', 'name')
    ordering = ['project', 'display_order', 'code']


@admin.register(ProjectBudget)
class ProjectBudgetAdmin(admin.ModelAdmin):
    list_display = ('project', 'description', 'gl_account', 'budget_hours',
                    'budget_amount', 'revised_amount', 'tenant')
    list_filter = ('tenant',)
    search_fields = ('description', 'project__project_number')


@admin.register(BillingRule)
class BillingRuleAdmin(admin.ModelAdmin):
    list_display = ('project', 'description', 'rate_type', 'rate',
                    'markup_percentage', 'effective_date', 'is_active', 'tenant')
    list_filter = ('rate_type', 'is_active', 'tenant')
    search_fields = ('description', 'project__project_number')


# =============================================================================
# Time & Expense
# =============================================================================

@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('project', 'employee', 'entry_date', 'hours',
                    'hourly_rate', 'total_amount', 'billing_status', 'tenant')
    list_filter = ('billing_status', 'is_billable', 'tenant')
    search_fields = ('employee__first_name', 'employee__last_name',
                     'project__project_number', 'description')


@admin.register(ExpenseEntry)
class ExpenseEntryAdmin(admin.ModelAdmin):
    list_display = ('project', 'entry_date', 'description', 'amount',
                    'vendor_name', 'billing_status', 'tenant')
    list_filter = ('billing_status', 'is_billable', 'tenant')
    search_fields = ('description', 'vendor_name', 'project__project_number')


# =============================================================================
# Revenue Recognition
# =============================================================================

@admin.register(RevenueRecognition)
class RevenueRecognitionAdmin(admin.ModelAdmin):
    list_display = ('project', 'recognition_date', 'method',
                    'completion_percentage', 'recognized_this_period',
                    'cumulative_recognized', 'status', 'tenant')
    list_filter = ('method', 'status', 'tenant')
    search_fields = ('project__project_number',)


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = ('project', 'name', 'amount', 'target_date',
                    'actual_date', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('name', 'project__project_number')


# =============================================================================
# Project Billing
# =============================================================================

class ProjectInvoiceLineInline(admin.TabularInline):
    model = ProjectInvoiceLine
    extra = 0


@admin.register(ProjectInvoice)
class ProjectInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'project', 'invoice_date', 'due_date',
                    'subtotal', 'retention_amount', 'total_amount', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('invoice_number', 'project__project_number')
    inlines = [ProjectInvoiceLineInline]


# =============================================================================
# Profitability
# =============================================================================

@admin.register(ProfitabilitySnapshot)
class ProfitabilitySnapshotAdmin(admin.ModelAdmin):
    list_display = ('project', 'snapshot_date', 'budget_amount', 'actual_cost',
                    'actual_revenue', 'cost_variance', 'cost_performance_index', 'tenant')
    list_filter = ('tenant',)
    search_fields = ('project__project_number',)


# =============================================================================
# Resource Planning
# =============================================================================

@admin.register(ResourceAssignment)
class ResourceAssignmentAdmin(admin.ModelAdmin):
    list_display = ('project', 'employee', 'role', 'allocation_percentage',
                    'start_date', 'end_date', 'planned_hours', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('employee__first_name', 'employee__last_name',
                     'project__project_number', 'role')
