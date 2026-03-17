from django.contrib import admin

from .models import (
    SOXControl, SOXControlTest,
    SoDRule, SoDViolation,
    AccessPolicy, AccessReview, AccessReviewItem,
    ChangeRequest, ChangeApproval,
    AuditEntry,
    ExceptionRule, AuditException,
    DocumentCategory, Document,
)


# ── SOX Controls ─────────────────────────────
class SOXControlTestInline(admin.TabularInline):
    model = SOXControlTest
    extra = 0


@admin.register(SOXControl)
class SOXControlAdmin(admin.ModelAdmin):
    list_display = ('control_number', 'name', 'control_type', 'risk_level',
                    'status', 'frequency', 'is_active', 'tenant')
    list_filter = ('status', 'control_type', 'risk_level', 'category', 'is_active', 'tenant')
    search_fields = ('control_number', 'name')
    inlines = [SOXControlTestInline]


@admin.register(SOXControlTest)
class SOXControlTestAdmin(admin.ModelAdmin):
    list_display = ('test_number', 'control', 'test_date', 'test_type',
                    'result', 'sample_size', 'exceptions_found', 'tenant')
    list_filter = ('result', 'test_type', 'tenant')
    search_fields = ('test_number',)


# ── Segregation of Duties ────────────────────
@admin.register(SoDRule)
class SoDRuleAdmin(admin.ModelAdmin):
    list_display = ('rule_number', 'name', 'enforcement', 'risk_level',
                    'status', 'tenant')
    list_filter = ('status', 'enforcement', 'risk_level', 'tenant')
    search_fields = ('rule_number', 'name')


@admin.register(SoDViolation)
class SoDViolationAdmin(admin.ModelAdmin):
    list_display = ('violation_number', 'rule', 'user', 'status',
                    'detected_at', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('violation_number',)


# ── Access Controls ──────────────────────────
@admin.register(AccessPolicy)
class AccessPolicyAdmin(admin.ModelAdmin):
    list_display = ('policy_number', 'name', 'policy_type', 'access_level',
                    'role', 'status', 'is_active', 'tenant')
    list_filter = ('policy_type', 'access_level', 'status', 'is_active', 'tenant')
    search_fields = ('policy_number', 'name')


class AccessReviewItemInline(admin.TabularInline):
    model = AccessReviewItem
    extra = 0


@admin.register(AccessReview)
class AccessReviewAdmin(admin.ModelAdmin):
    list_display = ('review_number', 'name', 'review_date', 'scope',
                    'status', 'findings_count', 'tenant')
    list_filter = ('status', 'scope', 'tenant')
    search_fields = ('review_number', 'name')
    inlines = [AccessReviewItemInline]


@admin.register(AccessReviewItem)
class AccessReviewItemAdmin(admin.ModelAdmin):
    list_display = ('item_number', 'review', 'policy', 'user',
                    'recommended_action', 'reviewer_decision', 'tenant')
    list_filter = ('recommended_action', 'reviewer_decision', 'tenant')
    search_fields = ('item_number',)


# ── Change Management ────────────────────────
class ChangeApprovalInline(admin.TabularInline):
    model = ChangeApproval
    extra = 0


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('request_number', 'title', 'change_type', 'priority',
                    'status', 'requested_by', 'tenant')
    list_filter = ('status', 'change_type', 'priority', 'tenant')
    search_fields = ('request_number', 'title')
    inlines = [ChangeApprovalInline]


@admin.register(ChangeApproval)
class ChangeApprovalAdmin(admin.ModelAdmin):
    list_display = ('approval_number', 'change_request', 'approver',
                    'decision', 'decided_at', 'tenant')
    list_filter = ('decision', 'tenant')
    search_fields = ('approval_number',)


# ── Audit Trail ──────────────────────────────
@admin.register(AuditEntry)
class AuditEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_number', 'action', 'model_name', 'record_id',
                    'user', 'timestamp', 'tenant')
    list_filter = ('action', 'model_name', 'tenant')
    search_fields = ('entry_number', 'model_name', 'changes_summary')
    readonly_fields = ('entry_number', 'action', 'model_name', 'record_id',
                       'user', 'timestamp', 'ip_address', 'old_values',
                       'new_values', 'changes_summary', 'session_id')


# ── Exception Reporting ──────────────────────
@admin.register(ExceptionRule)
class ExceptionRuleAdmin(admin.ModelAdmin):
    list_display = ('rule_number', 'name', 'rule_type', 'severity',
                    'is_active', 'tenant')
    list_filter = ('rule_type', 'severity', 'is_active', 'tenant')
    search_fields = ('rule_number', 'name')


@admin.register(AuditException)
class AuditExceptionAdmin(admin.ModelAdmin):
    list_display = ('exception_number', 'rule', 'severity', 'status',
                    'detected_at', 'assigned_to', 'tenant')
    list_filter = ('severity', 'status', 'tenant')
    search_fields = ('exception_number',)


# ── Document Management ─────────────────────
@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_number', 'name', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('category_number', 'name')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'title', 'category', 'file_type',
                    'status', 'uploaded_by', 'tenant')
    list_filter = ('status', 'category', 'tenant')
    search_fields = ('document_number', 'title')
