from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.tenants.managers import get_current_tenant

from .models import (
    AuditTrail, JournalEntry, JournalApproval, Account, PeriodCloseChecklist
)

AUDITED_MODELS = [JournalEntry, JournalApproval, Account, PeriodCloseChecklist]


@receiver(pre_save)
def capture_old_values(sender, instance, **kwargs):
    """Capture old field values before save for audit comparison."""
    if sender not in AUDITED_MODELS:
        return
    if instance.pk:
        try:
            manager = sender.unscoped if hasattr(sender, 'unscoped') else sender.objects
            old_instance = manager.get(pk=instance.pk)
            instance._old_values = {
                f.name: str(getattr(old_instance, f.name))
                for f in sender._meta.fields
            }
        except sender.DoesNotExist:
            instance._old_values = {}
    else:
        instance._old_values = {}


@receiver(post_save)
def log_audit_trail(sender, instance, created, **kwargs):
    """Create audit trail entries after save."""
    if sender not in AUDITED_MODELS:
        return
    tenant = get_current_tenant()
    if not tenant:
        return

    table_name = sender._meta.db_table

    if created:
        AuditTrail.unscoped.create(
            tenant=tenant,
            table_name=table_name,
            record_id=instance.pk,
            action='create',
            field_name='',
            old_value='',
            new_value=str(instance),
            user=getattr(instance, '_current_user', None),
        )
    else:
        old_values = getattr(instance, '_old_values', {})
        for field in sender._meta.fields:
            old_val = old_values.get(field.name, '')
            new_val = str(getattr(instance, field.name))
            if old_val != new_val:
                AuditTrail.unscoped.create(
                    tenant=tenant,
                    table_name=table_name,
                    record_id=instance.pk,
                    action='update',
                    field_name=field.name,
                    old_value=old_val,
                    new_value=new_val,
                    user=getattr(instance, '_current_user', None),
                )
