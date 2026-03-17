from django.utils import timezone


def create_audit_entry(tenant, action, model_name, record_id=None,
                       user=None, ip_address=None, old_values=None,
                       new_values=None, session_id='', notes=''):
    """Create an AuditEntry with auto-generated entry_number."""
    from .models import AuditEntry

    old_values = old_values or {}
    new_values = new_values or {}

    # Compute changes summary
    changes = []
    all_keys = set(list(old_values.keys()) + list(new_values.keys()))
    for key in sorted(all_keys):
        old_val = old_values.get(key)
        new_val = new_values.get(key)
        if old_val != new_val:
            changes.append(f"{key}: {old_val!r} -> {new_val!r}")
    changes_summary = '; '.join(changes) if changes else ''

    entry = AuditEntry.unscoped.create(
        tenant=tenant,
        entry_number=AuditEntry.generate_entry_number(tenant),
        action=action,
        model_name=model_name,
        record_id=record_id,
        user=user,
        ip_address=ip_address,
        old_values=old_values,
        new_values=new_values,
        changes_summary=changes_summary,
        session_id=session_id,
        notes=notes,
    )
    return entry


def scan_sod_conflicts(tenant):
    """Scan all users for segregation of duties violations."""
    from django.contrib.auth import get_user_model
    from .models import SoDRule, SoDViolation

    User = get_user_model()
    rules = SoDRule.unscoped.filter(tenant=tenant, status='active')
    users = User.objects.filter(tenant_memberships__tenant=tenant).distinct()
    created = 0

    for rule in rules:
        for user in users:
            user_roles = set(
                user.role_assignments.filter(
                    tenant=tenant
                ).values_list('role__name', flat=True)
            )
            if rule.conflicting_role_1 in user_roles and rule.conflicting_role_2 in user_roles:
                exists = SoDViolation.unscoped.filter(
                    tenant=tenant, rule=rule, user=user,
                    status__in=['open', 'acknowledged'],
                ).exists()
                if not exists:
                    SoDViolation.unscoped.create(
                        tenant=tenant,
                        violation_number=SoDViolation.generate_violation_number(tenant),
                        rule=rule,
                        user=user,
                        role_1_name=rule.conflicting_role_1,
                        role_2_name=rule.conflicting_role_2,
                        detected_at=timezone.now(),
                        status='open',
                    )
                    created += 1
    return created


def run_exception_scan(tenant, user=None):
    """Run all active exception rules and create findings."""
    from .models import ExceptionRule, AuditException

    rules = ExceptionRule.unscoped.filter(tenant=tenant, is_active=True)
    created = 0

    for rule in rules:
        # Placeholder: real implementation would evaluate rule.condition
        # against actual data based on rule.rule_type and rule.target_model
        pass

    return created


def process_change_approval(change_request):
    """Check if all approvals are in and update change request status."""
    approvals = change_request.approvals.all()
    if not approvals.exists():
        return change_request

    pending = approvals.filter(decision='pending')
    if pending.exists():
        return change_request

    rejected = approvals.filter(decision='rejected')
    if rejected.exists():
        change_request.status = 'rejected'
    else:
        change_request.status = 'approved'
    change_request.save(update_fields=['status', 'updated_at'])
    return change_request


def calculate_access_review_findings(review):
    """Count review items with revoked or modified decisions."""
    count = review.items.filter(
        reviewer_decision__in=['revoked', 'modified']
    ).count()
    review.findings_count = count
    review.save(update_fields=['findings_count', 'updated_at'])
    return review


def auto_populate_document_metadata(document):
    """Extract file metadata from the uploaded file."""
    if document.file:
        document.file_name = document.file.name.split('/')[-1]
        document.file_size = document.file.size
        # Guess content type from extension
        import mimetypes
        content_type, _ = mimetypes.guess_type(document.file.name)
        document.file_type = content_type or 'application/octet-stream'
        document.save(update_fields=['file_name', 'file_size', 'file_type', 'updated_at'])
    return document
