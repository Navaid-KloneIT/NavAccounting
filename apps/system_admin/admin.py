from django.contrib import admin

from .models import (
    MFAConfiguration, IPRestriction, SessionPolicy,
    WorkflowDefinition, WorkflowStep, WorkflowInstance, WorkflowStepLog,
    NotificationChannel, NotificationRule, NotificationLog,
    DataImportJob, DataExportJob, DataImportTemplate,
    BackupSchedule, BackupJob, RestoreJob,
    SystemMetric, MetricDataPoint, SystemHealthCheck, UsageAnalytics,
)


# ── Security Settings ────────────────────────
@admin.register(MFAConfiguration)
class MFAConfigurationAdmin(admin.ModelAdmin):
    list_display = ('config_number', 'name', 'mfa_method', 'is_enforced',
                    'enforcement_scope', 'status', 'tenant')
    list_filter = ('status', 'mfa_method', 'is_enforced', 'tenant')
    search_fields = ('config_number', 'name')


@admin.register(IPRestriction)
class IPRestrictionAdmin(admin.ModelAdmin):
    list_display = ('restriction_number', 'name', 'rule_type', 'ip_address',
                    'cidr_range', 'applies_to', 'priority', 'is_active', 'tenant')
    list_filter = ('rule_type', 'applies_to', 'is_active', 'tenant')
    search_fields = ('restriction_number', 'name', 'ip_address')


@admin.register(SessionPolicy)
class SessionPolicyAdmin(admin.ModelAdmin):
    list_display = ('policy_number', 'name', 'max_session_duration_minutes',
                    'idle_timeout_minutes', 'status', 'is_active', 'tenant')
    list_filter = ('status', 'is_active', 'tenant')
    search_fields = ('policy_number', 'name')


# ── Workflow Designer ────────────────────────
class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 0


@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    list_display = ('workflow_number', 'name', 'target_model', 'trigger_event',
                    'version', 'status', 'is_active', 'tenant')
    list_filter = ('status', 'trigger_event', 'is_active', 'tenant')
    search_fields = ('workflow_number', 'name')
    inlines = [WorkflowStepInline]


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ('step_number', 'name', 'workflow', 'order',
                    'step_type', 'assignee_type', 'tenant')
    list_filter = ('step_type', 'assignee_type', 'tenant')
    search_fields = ('step_number', 'name')


class WorkflowStepLogInline(admin.TabularInline):
    model = WorkflowStepLog
    extra = 0


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = ('instance_number', 'workflow', 'target_model',
                    'target_record_id', 'status', 'initiated_by', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('instance_number',)
    inlines = [WorkflowStepLogInline]


@admin.register(WorkflowStepLog)
class WorkflowStepLogAdmin(admin.ModelAdmin):
    list_display = ('log_number', 'instance', 'step', 'action_taken',
                    'performed_by', 'performed_at', 'tenant')
    list_filter = ('action_taken', 'tenant')
    search_fields = ('log_number',)


# ── Notification Center ──────────────────────
@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ('channel_number', 'name', 'channel_type',
                    'is_active', 'status', 'tenant')
    list_filter = ('channel_type', 'status', 'is_active', 'tenant')
    search_fields = ('channel_number', 'name')


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = ('rule_number', 'name', 'event_type', 'channel',
                    'recipient_type', 'is_active', 'status', 'tenant')
    list_filter = ('event_type', 'status', 'is_active', 'tenant')
    search_fields = ('rule_number', 'name')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('log_number', 'subject', 'rule', 'channel',
                    'recipient', 'status', 'sent_at', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('log_number', 'subject')


# ── Data Import/Export ───────────────────────
@admin.register(DataImportJob)
class DataImportJobAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'name', 'file_format', 'target_model',
                    'total_rows', 'success_rows', 'error_rows', 'status', 'tenant')
    list_filter = ('status', 'file_format', 'tenant')
    search_fields = ('job_number', 'name')


@admin.register(DataExportJob)
class DataExportJobAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'name', 'file_format', 'source_model',
                    'total_records', 'status', 'tenant')
    list_filter = ('status', 'file_format', 'tenant')
    search_fields = ('job_number', 'name')


@admin.register(DataImportTemplate)
class DataImportTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_number', 'name', 'target_model',
                    'file_format', 'is_active', 'tenant')
    list_filter = ('file_format', 'is_active', 'tenant')
    search_fields = ('template_number', 'name')


# ── Backup & Recovery ────────────────────────
@admin.register(BackupSchedule)
class BackupScheduleAdmin(admin.ModelAdmin):
    list_display = ('schedule_number', 'name', 'backup_type', 'frequency',
                    'status', 'is_active', 'last_run_at', 'tenant')
    list_filter = ('status', 'backup_type', 'frequency', 'is_active', 'tenant')
    search_fields = ('schedule_number', 'name')


@admin.register(BackupJob)
class BackupJobAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'backup_type', 'trigger', 'status',
                    'file_size_bytes', 'started_at', 'completed_at', 'tenant')
    list_filter = ('status', 'backup_type', 'trigger', 'tenant')
    search_fields = ('job_number',)


@admin.register(RestoreJob)
class RestoreJobAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'backup', 'restore_type', 'status',
                    'initiated_by', 'started_at', 'tenant')
    list_filter = ('status', 'restore_type', 'tenant')
    search_fields = ('job_number',)


# ── System Health ────────────────────────────
@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ('metric_number', 'name', 'metric_type', 'category',
                    'unit', 'is_active', 'tenant')
    list_filter = ('category', 'metric_type', 'is_active', 'tenant')
    search_fields = ('metric_number', 'name')


@admin.register(MetricDataPoint)
class MetricDataPointAdmin(admin.ModelAdmin):
    list_display = ('metric', 'value', 'recorded_at', 'tenant')
    list_filter = ('metric', 'tenant')


@admin.register(SystemHealthCheck)
class SystemHealthCheckAdmin(admin.ModelAdmin):
    list_display = ('check_number', 'name', 'check_type', 'last_status',
                    'last_checked_at', 'last_response_time_ms', 'is_active', 'tenant')
    list_filter = ('check_type', 'last_status', 'is_active', 'tenant')
    search_fields = ('check_number', 'name')


@admin.register(UsageAnalytics)
class UsageAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('analytics_number', 'period_type', 'period_start',
                    'period_end', 'active_users', 'total_logins', 'tenant')
    list_filter = ('period_type', 'tenant')
    search_fields = ('analytics_number',)
