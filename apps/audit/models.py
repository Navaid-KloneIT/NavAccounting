from django.conf import settings
from django.db import models

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


# ──────────────────────────────────────────────
# 1. SOXControl
# ──────────────────────────────────────────────
class SOXControl(TenantAwareModel):
    """SOX control documentation and testing."""

    CONTROL_TYPE_CHOICES = [
        ('preventive', 'Preventive'),
        ('detective', 'Detective'),
        ('corrective', 'Corrective'),
    ]
    CATEGORY_CHOICES = [
        ('financial_reporting', 'Financial Reporting'),
        ('operations', 'Operations'),
        ('compliance', 'Compliance'),
        ('it_general', 'IT General'),
    ]
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]
    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('testing', 'Testing'),
        ('deficient', 'Deficient'),
        ('remediated', 'Remediated'),
    ]

    control_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    control_type = models.CharField(max_length=20, choices=CONTROL_TYPE_CHOICES, default='preventive')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='financial_reporting')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ac_sox_controls_owned',
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    effective_date = models.DateField(null=True, blank=True)
    last_tested_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'control_number')

    def __str__(self):
        return f"{self.control_number} — {self.name}"

    @staticmethod
    def generate_control_number(tenant):
        prefix = "SOX-"
        last = SOXControl.unscoped.filter(
            tenant=tenant, control_number__startswith=prefix
        ).order_by('-control_number').first()
        if last:
            last_num = int(last.control_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 2. SOXControlTest
# ──────────────────────────────────────────────
class SOXControlTest(TenantAwareModel):
    """Test execution records for SOX controls."""

    TEST_TYPE_CHOICES = [
        ('walkthrough', 'Walkthrough'),
        ('sample', 'Sample'),
        ('full', 'Full'),
    ]
    RESULT_CHOICES = [
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('inconclusive', 'Inconclusive'),
    ]

    test_number = models.CharField(max_length=20, db_index=True)
    control = models.ForeignKey(SOXControl, on_delete=models.CASCADE, related_name='tests')
    test_date = models.DateField()
    tested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ac_sox_tests_performed',
    )
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES, default='walkthrough')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='inconclusive')
    sample_size = models.IntegerField(default=0)
    exceptions_found = models.IntegerField(default=0)
    conclusion = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-test_date']
        unique_together = ('tenant', 'test_number')

    def __str__(self):
        return f"{self.test_number} — {self.control.name}"

    @staticmethod
    def generate_test_number(tenant):
        prefix = "STT-"
        last = SOXControlTest.unscoped.filter(
            tenant=tenant, test_number__startswith=prefix
        ).order_by('-test_number').first()
        if last:
            last_num = int(last.test_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 3. SoDRule
# ──────────────────────────────────────────────
class SoDRule(TenantAwareModel):
    """Segregation of duties conflict rules."""

    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    ENFORCEMENT_CHOICES = [
        ('hard', 'Hard'),
        ('soft', 'Soft'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('under_review', 'Under Review'),
    ]

    rule_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    conflicting_role_1 = models.CharField(max_length=200)
    conflicting_role_2 = models.CharField(max_length=200)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='medium')
    enforcement = models.CharField(max_length=10, choices=ENFORCEMENT_CHOICES, default='soft')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['name']
        unique_together = ('tenant', 'rule_number')

    def __str__(self):
        return f"{self.rule_number} — {self.name}"

    @staticmethod
    def generate_rule_number(tenant):
        prefix = "SOD-"
        last = SoDRule.unscoped.filter(
            tenant=tenant, rule_number__startswith=prefix
        ).order_by('-rule_number').first()
        if last:
            last_num = int(last.rule_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 4. SoDViolation
# ──────────────────────────────────────────────
class SoDViolation(TenantAwareModel):
    """Detected segregation of duties violations."""

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('mitigated', 'Mitigated'),
        ('accepted', 'Accepted'),
    ]

    violation_number = models.CharField(max_length=20, db_index=True)
    rule = models.ForeignKey(SoDRule, on_delete=models.CASCADE, related_name='violations')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ac_sod_violations',
    )
    role_1_name = models.CharField(max_length=200)
    role_2_name = models.CharField(max_length=200)
    detected_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    mitigating_control = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ac_sod_violations_resolved',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-detected_at']
        unique_together = ('tenant', 'violation_number')

    def __str__(self):
        return f"{self.violation_number} — {self.rule.name}"

    @staticmethod
    def generate_violation_number(tenant):
        prefix = "SDV-"
        last = SoDViolation.unscoped.filter(
            tenant=tenant, violation_number__startswith=prefix
        ).order_by('-violation_number').first()
        if last:
            last_num = int(last.violation_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 5. AccessPolicy
# ──────────────────────────────────────────────
class AccessPolicy(TenantAwareModel):
    """Role-based and field-level access policies."""

    POLICY_TYPE_CHOICES = [
        ('role_based', 'Role-Based'),
        ('field_level', 'Field-Level'),
        ('data_level', 'Data-Level'),
    ]
    ACCESS_LEVEL_CHOICES = [
        ('none', 'None'),
        ('read', 'Read'),
        ('write', 'Write'),
        ('full', 'Full'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    policy_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES, default='role_based')
    target_model = models.CharField(max_length=100, blank=True)
    target_field = models.CharField(max_length=100, blank=True)
    access_level = models.CharField(max_length=10, choices=ACCESS_LEVEL_CHOICES, default='read')
    role = models.ForeignKey(
        'roles.Role', on_delete=models.PROTECT,
        related_name='ac_access_policies',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['name']
        unique_together = ('tenant', 'policy_number')
        verbose_name_plural = 'Access policies'

    def __str__(self):
        return f"{self.policy_number} — {self.name}"

    @staticmethod
    def generate_policy_number(tenant):
        prefix = "ACP-"
        last = AccessPolicy.unscoped.filter(
            tenant=tenant, policy_number__startswith=prefix
        ).order_by('-policy_number').first()
        if last:
            last_num = int(last.policy_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 6. AccessReview
# ──────────────────────────────────────────────
class AccessReview(TenantAwareModel):
    """Periodic access review campaigns."""

    SCOPE_CHOICES = [
        ('full', 'Full'),
        ('department', 'Department'),
        ('role', 'Role'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    ]

    review_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    review_date = models.DateField()
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ac_access_reviews_conducted',
    )
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='full')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    findings_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-review_date']
        unique_together = ('tenant', 'review_number')

    def __str__(self):
        return f"{self.review_number} — {self.name}"

    @staticmethod
    def generate_review_number(tenant):
        prefix = "ACR-"
        last = AccessReview.unscoped.filter(
            tenant=tenant, review_number__startswith=prefix
        ).order_by('-review_number').first()
        if last:
            last_num = int(last.review_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 7. AccessReviewItem
# ──────────────────────────────────────────────
class AccessReviewItem(TenantAwareModel):
    """Individual items within an access review."""

    RECOMMENDED_ACTION_CHOICES = [
        ('retain', 'Retain'),
        ('revoke', 'Revoke'),
        ('modify', 'Modify'),
    ]
    REVIEWER_DECISION_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('revoked', 'Revoked'),
        ('modified', 'Modified'),
    ]

    item_number = models.CharField(max_length=20, db_index=True)
    review = models.ForeignKey(AccessReview, on_delete=models.CASCADE, related_name='items')
    policy = models.ForeignKey(AccessPolicy, on_delete=models.CASCADE, related_name='ac_review_items')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ac_access_review_items',
    )
    current_access = models.CharField(max_length=200, blank=True)
    recommended_action = models.CharField(max_length=20, choices=RECOMMENDED_ACTION_CHOICES, default='retain')
    reviewer_decision = models.CharField(max_length=20, choices=REVIEWER_DECISION_CHOICES, default='pending')
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['review', 'user__username']
        unique_together = ('tenant', 'item_number')

    def __str__(self):
        return f"{self.item_number} — {self.review.name}"

    @staticmethod
    def generate_item_number(tenant):
        prefix = "ARI-"
        last = AccessReviewItem.unscoped.filter(
            tenant=tenant, item_number__startswith=prefix
        ).order_by('-item_number').first()
        if last:
            last_num = int(last.item_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 8. ChangeRequest
# ──────────────────────────────────────────────
class ChangeRequest(TenantAwareModel):
    """Approval workflows for master data changes."""

    CHANGE_TYPE_CHOICES = [
        ('master_data', 'Master Data'),
        ('configuration', 'Configuration'),
        ('process', 'Process'),
        ('system', 'System'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
    ]

    request_number = models.CharField(max_length=20, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES, default='master_data')
    target_model = models.CharField(max_length=100, blank=True)
    target_record_id = models.PositiveIntegerField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ac_change_requests_created',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ac_change_requests_approved',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    implemented_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ac_change_requests_implemented',
    )
    implemented_at = models.DateTimeField(null=True, blank=True)
    change_data = models.JSONField(default=dict, blank=True)
    rollback_data = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'request_number')

    def __str__(self):
        return f"{self.request_number} — {self.title}"

    @staticmethod
    def generate_request_number(tenant):
        prefix = "CHR-"
        last = ChangeRequest.unscoped.filter(
            tenant=tenant, request_number__startswith=prefix
        ).order_by('-request_number').first()
        if last:
            last_num = int(last.request_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 9. ChangeApproval
# ──────────────────────────────────────────────
class ChangeApproval(TenantAwareModel):
    """Individual approval decisions on a change request."""

    DECISION_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('deferred', 'Deferred'),
    ]

    approval_number = models.CharField(max_length=20, db_index=True)
    change_request = models.ForeignKey(ChangeRequest, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ac_change_approvals',
    )
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'approval_number')

    def __str__(self):
        return f"{self.approval_number} — {self.change_request.title}"

    @staticmethod
    def generate_approval_number(tenant):
        prefix = "CHA-"
        last = ChangeApproval.unscoped.filter(
            tenant=tenant, approval_number__startswith=prefix
        ).order_by('-approval_number').first()
        if last:
            last_num = int(last.approval_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 10. AuditEntry
# ──────────────────────────────────────────────
class AuditEntry(TenantAwareModel):
    """Complete transaction history / audit trail."""

    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Export'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]

    entry_number = models.CharField(max_length=20, db_index=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, db_index=True)
    record_id = models.PositiveIntegerField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ac_audit_entries',
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    changes_summary = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-timestamp']
        unique_together = ('tenant', 'entry_number')
        verbose_name_plural = 'Audit entries'
        indexes = [
            models.Index(fields=['model_name', 'record_id']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.entry_number} — {self.action} on {self.model_name}"

    @staticmethod
    def generate_entry_number(tenant):
        prefix = "AUD-"
        last = AuditEntry.unscoped.filter(
            tenant=tenant, entry_number__startswith=prefix
        ).order_by('-entry_number').first()
        if last:
            last_num = int(last.entry_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 11. ExceptionRule
# ──────────────────────────────────────────────
class ExceptionRule(TenantAwareModel):
    """Rules for anomaly detection and outlier analysis."""

    RULE_TYPE_CHOICES = [
        ('threshold', 'Threshold'),
        ('pattern', 'Pattern'),
        ('duplicate', 'Duplicate'),
        ('missing', 'Missing'),
        ('timing', 'Timing'),
    ]
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]

    rule_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES, default='threshold')
    target_model = models.CharField(max_length=100, blank=True)
    condition = models.JSONField(default=dict, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='warning')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['name']
        unique_together = ('tenant', 'rule_number')

    def __str__(self):
        return f"{self.rule_number} — {self.name}"

    @staticmethod
    def generate_rule_number(tenant):
        prefix = "EXR-"
        last = ExceptionRule.unscoped.filter(
            tenant=tenant, rule_number__startswith=prefix
        ).order_by('-rule_number').first()
        if last:
            last_num = int(last.rule_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 12. AuditException
# ──────────────────────────────────────────────
class AuditException(TenantAwareModel):
    """Detected anomalies and exceptions."""

    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]

    exception_number = models.CharField(max_length=20, db_index=True)
    rule = models.ForeignKey(ExceptionRule, on_delete=models.CASCADE, related_name='exceptions')
    detected_at = models.DateTimeField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='warning')
    description = models.TextField(blank=True)
    record_model = models.CharField(max_length=100, blank=True)
    record_id = models.PositiveIntegerField(null=True, blank=True)
    record_details = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ac_exceptions_assigned',
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ac_exceptions_resolved',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-detected_at']
        unique_together = ('tenant', 'exception_number')

    def __str__(self):
        return f"{self.exception_number} — {self.rule.name}"

    @staticmethod
    def generate_exception_number(tenant):
        prefix = "EXC-"
        last = AuditException.unscoped.filter(
            tenant=tenant, exception_number__startswith=prefix
        ).order_by('-exception_number').first()
        if last:
            last_num = int(last.exception_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 13. DocumentCategory
# ──────────────────────────────────────────────
class DocumentCategory(TenantAwareModel):
    """Categories for organizing audit documents."""

    category_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['name']
        unique_together = ('tenant', 'category_number')
        verbose_name_plural = 'Document categories'

    def __str__(self):
        return self.name

    @staticmethod
    def generate_category_number(tenant):
        prefix = "DCC-"
        last = DocumentCategory.unscoped.filter(
            tenant=tenant, category_number__startswith=prefix
        ).order_by('-category_number').first()
        if last:
            last_num = int(last.category_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"


# ──────────────────────────────────────────────
# 14. Document
# ──────────────────────────────────────────────
class Document(TenantAwareModel):
    """Supporting document attachment and retrieval."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]

    document_number = models.CharField(max_length=20, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        DocumentCategory, on_delete=models.PROTECT,
        related_name='documents',
    )
    file = models.FileField(upload_to='audit/documents/%Y/%m/')
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    file_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ac_documents_uploaded',
    )
    linked_model = models.CharField(max_length=100, blank=True)
    linked_record_id = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    version = models.IntegerField(default=1)
    tags = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'document_number')

    def __str__(self):
        return f"{self.document_number} — {self.title}"

    @staticmethod
    def generate_document_number(tenant):
        prefix = "DOC-"
        last = Document.unscoped.filter(
            tenant=tenant, document_number__startswith=prefix
        ).order_by('-document_number').first()
        if last:
            last_num = int(last.document_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        return f"{prefix}0001"
