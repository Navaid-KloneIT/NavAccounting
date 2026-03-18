from django.urls import path

from .views import security, workflows, notifications, data_operations, backups, health

app_name = 'system_admin'

urlpatterns = [
    # ── Security Settings ─────────────────────
    # MFA Configuration
    path('security/mfa/', security.mfa_config_list, name='mfa_config_list'),
    path('security/mfa/create/', security.mfa_config_create, name='mfa_config_create'),
    path('security/mfa/<int:pk>/', security.mfa_config_detail, name='mfa_config_detail'),
    path('security/mfa/<int:pk>/edit/', security.mfa_config_edit, name='mfa_config_edit'),
    # IP Restrictions
    path('security/ip/', security.ip_restriction_list, name='ip_restriction_list'),
    path('security/ip/create/', security.ip_restriction_create, name='ip_restriction_create'),
    path('security/ip/<int:pk>/', security.ip_restriction_detail, name='ip_restriction_detail'),
    path('security/ip/<int:pk>/edit/', security.ip_restriction_edit, name='ip_restriction_edit'),
    # Session Policies
    path('security/sessions/', security.session_policy_list, name='session_policy_list'),
    path('security/sessions/create/', security.session_policy_create, name='session_policy_create'),
    path('security/sessions/<int:pk>/', security.session_policy_detail, name='session_policy_detail'),
    path('security/sessions/<int:pk>/edit/', security.session_policy_edit, name='session_policy_edit'),

    # ── Workflow Designer ─────────────────────
    path('workflows/', workflows.workflow_list, name='workflow_list'),
    path('workflows/create/', workflows.workflow_create, name='workflow_create'),
    path('workflows/<int:pk>/', workflows.workflow_detail, name='workflow_detail'),
    path('workflows/<int:pk>/edit/', workflows.workflow_edit, name='workflow_edit'),
    path('workflows/<int:pk>/add-step/', workflows.workflow_step_create, name='workflow_step_create'),
    path('workflows/<int:pk>/steps/<int:step_pk>/edit/', workflows.workflow_step_edit, name='workflow_step_edit'),
    path('workflows/<int:pk>/steps/<int:step_pk>/delete/', workflows.workflow_step_delete, name='workflow_step_delete'),
    path('workflows/instances/', workflows.workflow_instance_list, name='workflow_instance_list'),
    path('workflows/instances/<int:pk>/', workflows.workflow_instance_detail, name='workflow_instance_detail'),

    # ── Notification Center ───────────────────
    path('notifications/channels/', notifications.channel_list, name='notification_channel_list'),
    path('notifications/channels/create/', notifications.channel_create, name='notification_channel_create'),
    path('notifications/channels/<int:pk>/', notifications.channel_detail, name='notification_channel_detail'),
    path('notifications/channels/<int:pk>/edit/', notifications.channel_edit, name='notification_channel_edit'),
    path('notifications/channels/<int:pk>/test/', notifications.channel_test, name='notification_channel_test'),
    path('notifications/rules/', notifications.rule_list, name='notification_rule_list'),
    path('notifications/rules/create/', notifications.rule_create, name='notification_rule_create'),
    path('notifications/rules/<int:pk>/', notifications.rule_detail, name='notification_rule_detail'),
    path('notifications/rules/<int:pk>/edit/', notifications.rule_edit, name='notification_rule_edit'),
    path('notifications/logs/', notifications.log_list, name='notification_log_list'),
    path('notifications/logs/<int:pk>/', notifications.log_detail, name='notification_log_detail'),

    # ── Data Import/Export ────────────────────
    path('data/imports/', data_operations.import_list, name='import_list'),
    path('data/imports/create/', data_operations.import_create, name='import_create'),
    path('data/imports/<int:pk>/', data_operations.import_detail, name='import_detail'),
    path('data/imports/<int:pk>/validate/', data_operations.import_validate, name='import_validate'),
    path('data/imports/<int:pk>/execute/', data_operations.import_execute, name='import_execute'),
    path('data/imports/<int:pk>/cancel/', data_operations.import_cancel, name='import_cancel'),
    path('data/exports/', data_operations.export_list, name='export_list'),
    path('data/exports/create/', data_operations.export_create, name='export_create'),
    path('data/exports/<int:pk>/', data_operations.export_detail, name='export_detail'),
    path('data/exports/<int:pk>/download/', data_operations.export_download, name='export_download'),
    path('data/templates/', data_operations.template_list, name='import_template_list'),
    path('data/templates/create/', data_operations.template_create, name='import_template_create'),
    path('data/templates/<int:pk>/edit/', data_operations.template_edit, name='import_template_edit'),
    path('data/templates/<int:pk>/download-sample/', data_operations.template_download_sample, name='import_template_download_sample'),

    # ── Backup & Recovery ─────────────────────
    path('backups/schedules/', backups.schedule_list, name='backup_schedule_list'),
    path('backups/schedules/create/', backups.schedule_create, name='backup_schedule_create'),
    path('backups/schedules/<int:pk>/', backups.schedule_detail, name='backup_schedule_detail'),
    path('backups/schedules/<int:pk>/edit/', backups.schedule_edit, name='backup_schedule_edit'),
    path('backups/jobs/', backups.job_list, name='backup_job_list'),
    path('backups/jobs/create/', backups.job_create_manual, name='backup_job_create'),
    path('backups/jobs/<int:pk>/', backups.job_detail, name='backup_job_detail'),
    path('backups/restore/<int:pk>/', backups.restore_create, name='restore_create'),
    path('backups/restores/', backups.restore_list, name='restore_list'),
    path('backups/restores/<int:pk>/', backups.restore_detail, name='restore_detail'),

    # ── System Health ─────────────────────────
    path('health/', health.health_dashboard, name='health_dashboard'),
    path('health/metrics/', health.metric_list, name='metric_list'),
    path('health/metrics/create/', health.metric_create, name='metric_create'),
    path('health/metrics/<int:pk>/', health.metric_detail, name='metric_detail'),
    path('health/metrics/<int:pk>/edit/', health.metric_edit, name='metric_edit'),
    path('health/checks/', health.health_check_list, name='health_check_list'),
    path('health/checks/create/', health.health_check_create, name='health_check_create'),
    path('health/checks/<int:pk>/', health.health_check_detail, name='health_check_detail'),
    path('health/checks/<int:pk>/edit/', health.health_check_edit, name='health_check_edit'),
    path('health/checks/<int:pk>/run/', health.health_check_run, name='health_check_run'),
    path('health/analytics/', health.analytics_list, name='analytics_list'),
    path('health/analytics/<int:pk>/', health.analytics_detail, name='analytics_detail'),
]
