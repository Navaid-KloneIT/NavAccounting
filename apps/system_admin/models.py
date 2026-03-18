from django.conf import settings
from django.db import models

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# ══════════════════════════════════════════════
# SUBMODULE 3: SECURITY SETTINGS
# ══════════════════════════════════════════════

# ──────────────────────────────────────────────
# 1. MFAConfiguration
# ──────────────────────────────────────────────
class MFAConfiguration(TenantAwareModel):
    """Multi-factor authentication configuration."""

    MFA_METHOD_CHOICES = [
        ('totp', 'TOTP Authenticator'),
        ('email', 'Email OTP'),
        ('sms', 'SMS OTP'),
    ]
    ENFORCEMENT_SCOPE_CHOICES = [
        ('all', 'All Users'),
        ('admin', 'Admins Only'),
        ('role_based', 'Role-Based'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    config_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    mfa_method = models.CharField(max_length=20, choices=MFA_METHOD_CHOICES, default='totp')
    is_enforced = models.BooleanField(default=False)
    enforcement_scope = models.CharField(max_length=20, choices=ENFORCEMENT_SCOPE_CHOICES, default='all')
    enforced_roles = models.ManyToManyField(
        'roles.Role', blank=True, related_name='sa_mfa_configs',
    )
    grace_period_days = models.IntegerField(default=7)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'config_number')

    def __str__(self):
        return f"{self.config_number} — {self.name}"

    @staticmethod
    def generate_config_number(tenant):
        prefix = "MFA-"
        last = MFAConfiguration.unscoped.filter(
            tenant=tenant, config_number__startswith=prefix
        ).order_by('-config_number').first()
        if last:
            last_num = int(last.config_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 2. IPRestriction
# ──────────────────────────────────────────────
class IPRestriction(TenantAwareModel):
    """IP-based access restriction rules."""

    RULE_TYPE_CHOICES = [
        ('allow', 'Allow'),
        ('deny', 'Deny'),
    ]
    APPLIES_TO_CHOICES = [
        ('all', 'All Users'),
        ('role', 'Specific Roles'),
        ('user', 'Specific Users'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    restriction_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=10, choices=RULE_TYPE_CHOICES, default='allow')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    cidr_range = models.CharField(max_length=43, blank=True)
    description = models.TextField(blank=True)
    applies_to = models.CharField(max_length=10, choices=APPLIES_TO_CHOICES, default='all')
    target_roles = models.ManyToManyField(
        'roles.Role', blank=True, related_name='sa_ip_restrictions',
    )
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='sa_ip_restrictions',
    )
    priority = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['priority', '-created_at']
        unique_together = ('tenant', 'restriction_number')

    def __str__(self):
        return f"{self.restriction_number} — {self.name}"

    @staticmethod
    def generate_restriction_number(tenant):
        prefix = "IPR-"
        last = IPRestriction.unscoped.filter(
            tenant=tenant, restriction_number__startswith=prefix
        ).order_by('-restriction_number').first()
        if last:
            last_num = int(last.restriction_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 3. SessionPolicy
# ──────────────────────────────────────────────
class SessionPolicy(TenantAwareModel):
    """Session management and password policy configuration."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    policy_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    max_session_duration_minutes = models.IntegerField(default=480)
    idle_timeout_minutes = models.IntegerField(default=30)
    max_concurrent_sessions = models.IntegerField(default=3)
    enforce_single_session = models.BooleanField(default=False)
    require_re_auth_for_sensitive = models.BooleanField(default=False)
    password_expiry_days = models.IntegerField(default=90, help_text="0 = never expires")
    min_password_length = models.IntegerField(default=8)
    require_special_chars = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'policy_number')
        verbose_name_plural = 'Session policies'

    def __str__(self):
        return f"{self.policy_number} — {self.name}"

    @staticmethod
    def generate_policy_number(tenant):
        prefix = "SSP-"
        last = SessionPolicy.unscoped.filter(
            tenant=tenant, policy_number__startswith=prefix
        ).order_by('-policy_number').first()
        if last:
            last_num = int(last.policy_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ══════════════════════════════════════════════
# SUBMODULE 4: WORKFLOW DESIGNER
# ══════════════════════════════════════════════

# ──────────────────────────────────────────────
# 4. WorkflowDefinition
# ──────────────────────────────────────────────
class WorkflowDefinition(TenantAwareModel):
    """Workflow process definition."""

    TRIGGER_CHOICES = [
        ('on_create', 'On Create'),
        ('on_update', 'On Update'),
        ('on_status_change', 'On Status Change'),
        ('manual', 'Manual'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]

    workflow_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_model = models.CharField(max_length=100, blank=True)
    trigger_event = models.CharField(max_length=20, choices=TRIGGER_CHOICES, default='manual')
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='sa_workflows_created',
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'workflow_number')

    def __str__(self):
        return f"{self.workflow_number} — {self.name}"

    @staticmethod
    def generate_workflow_number(tenant):
        prefix = "WFD-"
        last = WorkflowDefinition.unscoped.filter(
            tenant=tenant, workflow_number__startswith=prefix
        ).order_by('-workflow_number').first()
        if last:
            last_num = int(last.workflow_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 5. WorkflowStep
# ──────────────────────────────────────────────
class WorkflowStep(TenantAwareModel):
    """Individual step within a workflow definition."""

    STEP_TYPE_CHOICES = [
        ('approval', 'Approval'),
        ('notification', 'Notification'),
        ('condition', 'Condition'),
        ('action', 'Action'),
    ]
    ASSIGNEE_TYPE_CHOICES = [
        ('user', 'Specific User'),
        ('role', 'Role'),
        ('manager', 'Manager'),
        ('creator', 'Creator'),
    ]
    CONDITION_OPERATOR_CHOICES = [
        ('eq', 'Equals'),
        ('neq', 'Not Equals'),
        ('gt', 'Greater Than'),
        ('lt', 'Less Than'),
        ('gte', 'Greater Than or Equal'),
        ('lte', 'Less Than or Equal'),
    ]
    ON_TIMEOUT_CHOICES = [
        ('skip', 'Skip'),
        ('escalate', 'Escalate'),
        ('reject', 'Reject'),
    ]

    step_number = models.CharField(max_length=20, db_index=True)
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    step_type = models.CharField(max_length=20, choices=STEP_TYPE_CHOICES, default='approval')
    assignee_type = models.CharField(max_length=20, choices=ASSIGNEE_TYPE_CHOICES, default='role')
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='sa_workflow_steps_assigned',
    )
    assigned_role = models.ForeignKey(
        'roles.Role', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='sa_workflow_steps',
    )
    condition_field = models.CharField(max_length=100, blank=True)
    condition_operator = models.CharField(
        max_length=20, blank=True, choices=CONDITION_OPERATOR_CHOICES,
    )
    condition_value = models.CharField(max_length=200, blank=True)
    action_config = models.JSONField(default=dict, blank=True)
    timeout_hours = models.IntegerField(default=0)
    on_timeout = models.CharField(max_length=20, choices=ON_TIMEOUT_CHOICES, default='skip')
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['order']
        unique_together = ('tenant', 'step_number')

    def __str__(self):
        return f"{self.step_number} — {self.name}"

    @staticmethod
    def generate_step_number(tenant):
        prefix = "WFS-"
        last = WorkflowStep.unscoped.filter(
            tenant=tenant, step_number__startswith=prefix
        ).order_by('-step_number').first()
        if last:
            last_num = int(last.step_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 6. WorkflowInstance
# ──────────────────────────────────────────────
class WorkflowInstance(TenantAwareModel):
    """Running instance of a workflow."""

    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    instance_number = models.CharField(max_length=20, db_index=True)
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.PROTECT, related_name='instances')
    target_model = models.CharField(max_length=100)
    target_record_id = models.PositiveIntegerField()
    current_step = models.ForeignKey(
        WorkflowStep, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='current_instances',
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='sa_workflow_instances_initiated',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-started_at']
        unique_together = ('tenant', 'instance_number')

    def __str__(self):
        return f"{self.instance_number} — {self.workflow.name}"

    @staticmethod
    def generate_instance_number(tenant):
        prefix = "WFI-"
        last = WorkflowInstance.unscoped.filter(
            tenant=tenant, instance_number__startswith=prefix
        ).order_by('-instance_number').first()
        if last:
            last_num = int(last.instance_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 7. WorkflowStepLog
# ──────────────────────────────────────────────
class WorkflowStepLog(TenantAwareModel):
    """Log entry for a workflow step execution."""

    ACTION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped'),
        ('escalated', 'Escalated'),
        ('completed', 'Completed'),
    ]

    log_number = models.CharField(max_length=20, db_index=True)
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='step_logs')
    step = models.ForeignKey(WorkflowStep, on_delete=models.PROTECT, related_name='logs')
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='sa_workflow_step_logs',
    )
    performed_at = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['performed_at']
        unique_together = ('tenant', 'log_number')

    def __str__(self):
        return f"{self.log_number} — {self.get_action_taken_display()}"

    @staticmethod
    def generate_log_number(tenant):
        prefix = "WFL-"
        last = WorkflowStepLog.unscoped.filter(
            tenant=tenant, log_number__startswith=prefix
        ).order_by('-log_number').first()
        if last:
            last_num = int(last.log_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ══════════════════════════════════════════════
# SUBMODULE 5: NOTIFICATION CENTER
# ══════════════════════════════════════════════

# ──────────────────────────────────────────────
# 8. NotificationChannel
# ──────────────────────────────────────────────
class NotificationChannel(TenantAwareModel):
    """Notification delivery channel configuration."""

    CHANNEL_TYPE_CHOICES = [
        ('email', 'Email'),
        ('in_app', 'In-App'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    channel_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPE_CHOICES, default='email')
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'channel_number')

    def __str__(self):
        return f"{self.channel_number} — {self.name}"

    @staticmethod
    def generate_channel_number(tenant):
        prefix = "NCH-"
        last = NotificationChannel.unscoped.filter(
            tenant=tenant, channel_number__startswith=prefix
        ).order_by('-channel_number').first()
        if last:
            last_num = int(last.channel_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 9. NotificationRule
# ──────────────────────────────────────────────
class NotificationRule(TenantAwareModel):
    """Rules that trigger notifications based on events."""

    EVENT_TYPE_CHOICES = [
        ('record_created', 'Record Created'),
        ('record_updated', 'Record Updated'),
        ('status_changed', 'Status Changed'),
        ('approval_needed', 'Approval Needed'),
        ('threshold_exceeded', 'Threshold Exceeded'),
        ('system_alert', 'System Alert'),
        ('scheduled', 'Scheduled'),
    ]
    RECIPIENT_TYPE_CHOICES = [
        ('user', 'Specific Users'),
        ('role', 'Role Members'),
        ('creator', 'Record Creator'),
        ('all', 'All Users'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    rule_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='status_changed')
    target_model = models.CharField(max_length=100, blank=True)
    condition = models.JSONField(default=dict, blank=True)
    channel = models.ForeignKey(
        NotificationChannel, on_delete=models.PROTECT, related_name='rules',
    )
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_TYPE_CHOICES, default='role')
    recipient_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='sa_notification_rules',
    )
    recipient_roles = models.ManyToManyField(
        'roles.Role', blank=True, related_name='sa_notification_rules',
    )
    subject_template = models.CharField(max_length=500, blank=True)
    body_template = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'rule_number')

    def __str__(self):
        return f"{self.rule_number} — {self.name}"

    @staticmethod
    def generate_rule_number(tenant):
        prefix = "NRL-"
        last = NotificationRule.unscoped.filter(
            tenant=tenant, rule_number__startswith=prefix
        ).order_by('-rule_number').first()
        if last:
            last_num = int(last.rule_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 10. NotificationLog
# ──────────────────────────────────────────────
class NotificationLog(TenantAwareModel):
    """Log of sent/attempted notifications."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ]

    log_number = models.CharField(max_length=20, db_index=True)
    rule = models.ForeignKey(
        NotificationRule, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='logs',
    )
    channel = models.ForeignKey(
        NotificationChannel, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='logs',
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='sa_notification_logs',
    )
    subject = models.CharField(max_length=500)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'log_number')

    def __str__(self):
        return f"{self.log_number} — {self.subject[:50]}"

    @staticmethod
    def generate_log_number(tenant):
        prefix = "NLG-"
        last = NotificationLog.unscoped.filter(
            tenant=tenant, log_number__startswith=prefix
        ).order_by('-log_number').first()
        if last:
            last_num = int(last.log_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ══════════════════════════════════════════════
# SUBMODULE 6: DATA IMPORT/EXPORT
# ══════════════════════════════════════════════

# ──────────────────────────────────────────────
# 11. DataImportJob
# ──────────────────────────────────────────────
class DataImportJob(TenantAwareModel):
    """Tracks a data import operation."""

    FILE_FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('json', 'JSON'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('validating', 'Validating'),
        ('validated', 'Validated'),
        ('importing', 'Importing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    job_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    file_format = models.CharField(max_length=10, choices=FILE_FORMAT_CHOICES, default='csv')
    target_model = models.CharField(max_length=100)
    source_file = models.FileField(upload_to='system_admin/imports/%Y/%m/')
    source_file_name = models.CharField(max_length=255, blank=True)
    column_mapping = models.JSONField(default=dict, blank=True)
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    success_rows = models.IntegerField(default=0)
    error_rows = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    error_log = models.JSONField(default=list, blank=True)
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='sa_import_jobs',
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'job_number')

    def __str__(self):
        return f"{self.job_number} — {self.name}"

    @staticmethod
    def generate_job_number(tenant):
        prefix = "IMP-"
        last = DataImportJob.unscoped.filter(
            tenant=tenant, job_number__startswith=prefix
        ).order_by('-job_number').first()
        if last:
            last_num = int(last.job_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 12. DataExportJob
# ──────────────────────────────────────────────
class DataExportJob(TenantAwareModel):
    """Tracks a data export operation."""

    FILE_FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('json', 'JSON'),
        ('pdf', 'PDF'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    job_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    file_format = models.CharField(max_length=10, choices=FILE_FORMAT_CHOICES, default='csv')
    source_model = models.CharField(max_length=100)
    filters = models.JSONField(default=dict, blank=True)
    columns = models.JSONField(default=list, blank=True)
    total_records = models.IntegerField(default=0)
    output_file = models.FileField(
        upload_to='system_admin/exports/%Y/%m/', null=True, blank=True,
    )
    output_file_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='sa_export_jobs',
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'job_number')

    def __str__(self):
        return f"{self.job_number} — {self.name}"

    @staticmethod
    def generate_job_number(tenant):
        prefix = "EXP-"
        last = DataExportJob.unscoped.filter(
            tenant=tenant, job_number__startswith=prefix
        ).order_by('-job_number').first()
        if last:
            last_num = int(last.job_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 13. DataImportTemplate
# ──────────────────────────────────────────────
class DataImportTemplate(TenantAwareModel):
    """Reusable import mapping template."""

    FILE_FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('json', 'JSON'),
    ]

    template_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_model = models.CharField(max_length=100)
    file_format = models.CharField(max_length=10, choices=FILE_FORMAT_CHOICES, default='csv')
    column_mapping = models.JSONField(default=dict, blank=True)
    sample_file = models.FileField(
        upload_to='system_admin/templates/', null=True, blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='sa_import_templates',
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'template_number')

    def __str__(self):
        return f"{self.template_number} — {self.name}"

    @staticmethod
    def generate_template_number(tenant):
        prefix = "IMT-"
        last = DataImportTemplate.unscoped.filter(
            tenant=tenant, template_number__startswith=prefix
        ).order_by('-template_number').first()
        if last:
            last_num = int(last.template_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ══════════════════════════════════════════════
# SUBMODULE 7: BACKUP & RECOVERY
# ══════════════════════════════════════════════

# ──────────────────────────────────────────────
# 14. BackupSchedule
# ──────────────────────────────────────────────
class BackupSchedule(TenantAwareModel):
    """Scheduled backup configuration."""

    BACKUP_TYPE_CHOICES = [
        ('full', 'Full'),
        ('incremental', 'Incremental'),
        ('differential', 'Differential'),
    ]
    FREQUENCY_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('paused', 'Paused'),
    ]

    schedule_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPE_CHOICES, default='full')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    scheduled_time = models.TimeField()
    day_of_week = models.IntegerField(null=True, blank=True, help_text="0=Monday, 6=Sunday")
    day_of_month = models.IntegerField(null=True, blank=True)
    retention_days = models.IntegerField(default=30)
    storage_location = models.CharField(max_length=500, blank=True)
    include_media = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='sa_backup_schedules',
    )
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'schedule_number')

    def __str__(self):
        return f"{self.schedule_number} — {self.name}"

    @staticmethod
    def generate_schedule_number(tenant):
        prefix = "BKS-"
        last = BackupSchedule.unscoped.filter(
            tenant=tenant, schedule_number__startswith=prefix
        ).order_by('-schedule_number').first()
        if last:
            last_num = int(last.schedule_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 15. BackupJob
# ──────────────────────────────────────────────
class BackupJob(TenantAwareModel):
    """Individual backup execution record."""

    BACKUP_TYPE_CHOICES = [
        ('full', 'Full'),
        ('incremental', 'Incremental'),
        ('differential', 'Differential'),
    ]
    TRIGGER_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('manual', 'Manual'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    job_number = models.CharField(max_length=20, db_index=True)
    schedule = models.ForeignKey(
        BackupSchedule, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='jobs',
    )
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPE_CHOICES, default='full')
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES, default='manual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    file_size_bytes = models.BigIntegerField(default=0)
    tables_included = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='sa_backup_jobs',
    )
    error_message = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'job_number')

    def __str__(self):
        return f"{self.job_number} — {self.get_backup_type_display()}"

    @staticmethod
    def generate_job_number(tenant):
        prefix = "BKJ-"
        last = BackupJob.unscoped.filter(
            tenant=tenant, job_number__startswith=prefix
        ).order_by('-job_number').first()
        if last:
            last_num = int(last.job_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 16. RestoreJob
# ──────────────────────────────────────────────
class RestoreJob(TenantAwareModel):
    """Restore operation from a backup."""

    RESTORE_TYPE_CHOICES = [
        ('full', 'Full Restore'),
        ('partial', 'Partial Restore'),
        ('point_in_time', 'Point-in-Time'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rolled_back', 'Rolled Back'),
    ]

    job_number = models.CharField(max_length=20, db_index=True)
    backup = models.ForeignKey(BackupJob, on_delete=models.PROTECT, related_name='restores')
    restore_type = models.CharField(max_length=20, choices=RESTORE_TYPE_CHOICES, default='full')
    target_tables = models.JSONField(default=list, blank=True)
    point_in_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='sa_restore_jobs',
    )
    error_message = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'job_number')

    def __str__(self):
        return f"{self.job_number} — {self.get_restore_type_display()}"

    @staticmethod
    def generate_job_number(tenant):
        prefix = "RST-"
        last = RestoreJob.unscoped.filter(
            tenant=tenant, job_number__startswith=prefix
        ).order_by('-job_number').first()
        if last:
            last_num = int(last.job_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ══════════════════════════════════════════════
# SUBMODULE 8: SYSTEM HEALTH
# ══════════════════════════════════════════════

# ──────────────────────────────────────────────
# 17. SystemMetric
# ──────────────────────────────────────────────
class SystemMetric(TenantAwareModel):
    """System performance metric definition."""

    METRIC_TYPE_CHOICES = [
        ('gauge', 'Gauge'),
        ('counter', 'Counter'),
        ('histogram', 'Histogram'),
    ]
    CATEGORY_CHOICES = [
        ('performance', 'Performance'),
        ('usage', 'Usage'),
        ('storage', 'Storage'),
        ('error', 'Error Rate'),
    ]

    metric_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES, default='gauge')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='performance')
    unit = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    warning_threshold = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    critical_threshold = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    is_active = models.BooleanField(default=True)
    collection_interval_minutes = models.IntegerField(default=5)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'metric_number')

    def __str__(self):
        return f"{self.metric_number} — {self.name}"

    @staticmethod
    def generate_metric_number(tenant):
        prefix = "SMT-"
        last = SystemMetric.unscoped.filter(
            tenant=tenant, metric_number__startswith=prefix
        ).order_by('-metric_number').first()
        if last:
            last_num = int(last.metric_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 18. MetricDataPoint
# ──────────────────────────────────────────────
class MetricDataPoint(TenantAwareModel):
    """High-volume time-series metric data point."""

    metric = models.ForeignKey(SystemMetric, on_delete=models.CASCADE, related_name='data_points')
    value = models.DecimalField(max_digits=12, decimal_places=4)
    recorded_at = models.DateTimeField(db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric', 'recorded_at']),
        ]

    def __str__(self):
        return f"{self.metric.name} = {self.value} @ {self.recorded_at}"


# ──────────────────────────────────────────────
# 19. SystemHealthCheck
# ──────────────────────────────────────────────
class SystemHealthCheck(TenantAwareModel):
    """Service health check configuration and status."""

    CHECK_TYPE_CHOICES = [
        ('database', 'Database'),
        ('storage', 'Storage'),
        ('email', 'Email Service'),
        ('cache', 'Cache'),
        ('external_api', 'External API'),
        ('queue', 'Task Queue'),
    ]
    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('degraded', 'Degraded'),
        ('unhealthy', 'Unhealthy'),
        ('unknown', 'Unknown'),
    ]

    check_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    check_type = models.CharField(max_length=20, choices=CHECK_TYPE_CHOICES, default='database')
    endpoint = models.CharField(max_length=500, blank=True)
    last_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown')
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_response_time_ms = models.IntegerField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    check_interval_minutes = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'check_number')

    def __str__(self):
        return f"{self.check_number} — {self.name}"

    @staticmethod
    def generate_check_number(tenant):
        prefix = "SHC-"
        last = SystemHealthCheck.unscoped.filter(
            tenant=tenant, check_number__startswith=prefix
        ).order_by('-check_number').first()
        if last:
            last_num = int(last.check_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 20. UsageAnalytics
# ──────────────────────────────────────────────
class UsageAnalytics(TenantAwareModel):
    """Period-based usage statistics."""

    PERIOD_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    analytics_number = models.CharField(max_length=20, db_index=True)
    period_start = models.DateField()
    period_end = models.DateField()
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES, default='daily')
    active_users = models.IntegerField(default=0)
    total_logins = models.IntegerField(default=0)
    total_transactions = models.IntegerField(default=0)
    storage_used_mb = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    api_calls = models.IntegerField(default=0)
    top_modules = models.JSONField(default=dict, blank=True)
    top_users = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-period_start']
        unique_together = ('tenant', 'analytics_number')
        verbose_name_plural = 'Usage analytics'

    def __str__(self):
        return f"{self.analytics_number} — {self.period_start} to {self.period_end}"

    @staticmethod
    def generate_analytics_number(tenant):
        prefix = "UAN-"
        last = UsageAnalytics.unscoped.filter(
            tenant=tenant, analytics_number__startswith=prefix
        ).order_by('-analytics_number').first()
        if last:
            last_num = int(last.analytics_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"
