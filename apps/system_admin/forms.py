from django import forms

from .models import (
    MFAConfiguration, IPRestriction, SessionPolicy,
    WorkflowDefinition, WorkflowStep,
    NotificationChannel, NotificationRule,
    DataImportJob, DataExportJob, DataImportTemplate,
    BackupSchedule, BackupJob, RestoreJob,
    SystemMetric, SystemHealthCheck,
)


# ══════════════════════════════════════════════
# SECURITY SETTINGS FORMS
# ══════════════════════════════════════════════

class MFAConfigurationForm(forms.ModelForm):
    class Meta:
        model = MFAConfiguration
        exclude = ['tenant', 'created_at', 'updated_at', 'config_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'mfa_method': forms.Select(attrs={'class': 'form-select'}),
            'is_enforced': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enforcement_scope': forms.Select(attrs={'class': 'form-select'}),
            'enforced_roles': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'grace_period_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class IPRestrictionForm(forms.ModelForm):
    class Meta:
        model = IPRestriction
        exclude = ['tenant', 'created_at', 'updated_at', 'restriction_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '192.168.1.1'}),
            'cidr_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '192.168.1.0/24'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'applies_to': forms.Select(attrs={'class': 'form-select'}),
            'target_roles': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'target_users': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SessionPolicyForm(forms.ModelForm):
    class Meta:
        model = SessionPolicy
        exclude = ['tenant', 'created_at', 'updated_at', 'policy_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'max_session_duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'idle_timeout_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_concurrent_sessions': forms.NumberInput(attrs={'class': 'form-control'}),
            'enforce_single_session': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_re_auth_for_sensitive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'password_expiry_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_password_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'require_special_chars': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ══════════════════════════════════════════════
# WORKFLOW DESIGNER FORMS
# ══════════════════════════════════════════════

class WorkflowDefinitionForm(forms.ModelForm):
    class Meta:
        model = WorkflowDefinition
        exclude = ['tenant', 'created_at', 'updated_at', 'workflow_number', 'version', 'created_by']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'target_model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. JournalEntry'}),
            'trigger_event': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class WorkflowStepForm(forms.ModelForm):
    class Meta:
        model = WorkflowStep
        exclude = ['tenant', 'created_at', 'updated_at', 'step_number', 'workflow']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'step_type': forms.Select(attrs={'class': 'form-select'}),
            'assignee_type': forms.Select(attrs={'class': 'form-select'}),
            'assigned_user': forms.Select(attrs={'class': 'form-select'}),
            'assigned_role': forms.Select(attrs={'class': 'form-select'}),
            'condition_field': forms.TextInput(attrs={'class': 'form-control'}),
            'condition_operator': forms.Select(attrs={'class': 'form-select'}),
            'condition_value': forms.TextInput(attrs={'class': 'form-control'}),
            'timeout_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'on_timeout': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ══════════════════════════════════════════════
# NOTIFICATION CENTER FORMS
# ══════════════════════════════════════════════

class NotificationChannelForm(forms.ModelForm):
    class Meta:
        model = NotificationChannel
        exclude = ['tenant', 'created_at', 'updated_at', 'channel_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'channel_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class NotificationRuleForm(forms.ModelForm):
    class Meta:
        model = NotificationRule
        exclude = ['tenant', 'created_at', 'updated_at', 'rule_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'target_model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. JournalEntry'}),
            'channel': forms.Select(attrs={'class': 'form-select'}),
            'recipient_type': forms.Select(attrs={'class': 'form-select'}),
            'recipient_users': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'recipient_roles': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'subject_template': forms.TextInput(attrs={'class': 'form-control'}),
            'body_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ══════════════════════════════════════════════
# DATA IMPORT/EXPORT FORMS
# ══════════════════════════════════════════════

class DataImportJobForm(forms.ModelForm):
    class Meta:
        model = DataImportJob
        exclude = [
            'tenant', 'created_at', 'updated_at', 'job_number',
            'processed_rows', 'success_rows', 'error_rows', 'error_log',
            'started_at', 'completed_at', 'started_by', 'total_rows',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file_format': forms.Select(attrs={'class': 'form-select'}),
            'target_model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Vendor'}),
            'source_file': forms.FileInput(attrs={'class': 'form-control'}),
            'source_file_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DataExportJobForm(forms.ModelForm):
    class Meta:
        model = DataExportJob
        exclude = [
            'tenant', 'created_at', 'updated_at', 'job_number',
            'total_records', 'output_file', 'output_file_name',
            'started_at', 'completed_at', 'started_by', 'error_message', 'status',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file_format': forms.Select(attrs={'class': 'form-select'}),
            'source_model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Vendor'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DataImportTemplateForm(forms.ModelForm):
    class Meta:
        model = DataImportTemplate
        exclude = ['tenant', 'created_at', 'updated_at', 'template_number', 'created_by']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'target_model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Vendor'}),
            'file_format': forms.Select(attrs={'class': 'form-select'}),
            'sample_file': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ══════════════════════════════════════════════
# BACKUP & RECOVERY FORMS
# ══════════════════════════════════════════════

class BackupScheduleForm(forms.ModelForm):
    class Meta:
        model = BackupSchedule
        exclude = [
            'tenant', 'created_at', 'updated_at', 'schedule_number',
            'last_run_at', 'next_run_at', 'created_by',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'backup_type': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'day_of_week': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 6}),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'retention_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'storage_location': forms.TextInput(attrs={'class': 'form-control'}),
            'include_media': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BackupJobManualForm(forms.ModelForm):
    class Meta:
        model = BackupJob
        fields = ['backup_type', 'notes']
        widgets = {
            'backup_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class RestoreJobForm(forms.ModelForm):
    class Meta:
        model = RestoreJob
        exclude = [
            'tenant', 'created_at', 'updated_at', 'job_number',
            'status', 'started_at', 'completed_at', 'initiated_by', 'error_message',
        ]
        widgets = {
            'backup': forms.Select(attrs={'class': 'form-select'}),
            'restore_type': forms.Select(attrs={'class': 'form-select'}),
            'point_in_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ══════════════════════════════════════════════
# SYSTEM HEALTH FORMS
# ══════════════════════════════════════════════

class SystemMetricForm(forms.ModelForm):
    class Meta:
        model = SystemMetric
        exclude = ['tenant', 'created_at', 'updated_at', 'metric_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'metric_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ms, MB, %'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'warning_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'critical_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'collection_interval_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SystemHealthCheckForm(forms.ModelForm):
    class Meta:
        model = SystemHealthCheck
        exclude = [
            'tenant', 'created_at', 'updated_at', 'check_number',
            'last_status', 'last_checked_at', 'last_response_time_ms', 'last_error',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'check_type': forms.Select(attrs={'class': 'form-select'}),
            'endpoint': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. https://api.example.com/health'}),
            'check_interval_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
