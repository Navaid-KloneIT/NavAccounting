from django.conf import settings
from django.db import models

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


class DashboardWidgetConfig(TenantAwareModel):
    """Per-user, per-tenant widget configuration on the dashboard."""
    WIDGET_CHOICES = [
        ('kpi_cards', 'KPI Cards'),
        ('cash_flow', 'Cash Flow Chart'),
        ('alert_center', 'Alert Center'),
        ('quick_actions', 'Quick Actions'),
        ('executive_summary', 'Executive Summary'),
        ('revenue_chart', 'Revenue Chart'),
        ('expense_chart', 'Expense Chart'),
        ('receivables_aging', 'Receivables Aging'),
        ('payables_aging', 'Payables Aging'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='widget_configs'
    )
    widget_type = models.CharField(max_length=50, choices=WIDGET_CHOICES)
    position = models.PositiveSmallIntegerField(default=0)
    column_span = models.PositiveSmallIntegerField(default=6)
    is_visible = models.BooleanField(default=True)
    config_json = models.JSONField(default=dict, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['position']
        unique_together = ('user', 'tenant', 'widget_type')

    def __str__(self):
        return f"{self.user} - {self.get_widget_type_display()}"


class Alert(TenantAwareModel):
    """System-generated alerts for the alert center."""
    SEVERITY_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('danger', 'Critical'),
        ('success', 'Success'),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='info')
    alert_type = models.CharField(max_length=50)
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    link = models.CharField(max_length=500, blank=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
