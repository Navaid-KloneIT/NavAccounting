from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import TaxAuditForm, AuditFindingForm, AuditDocumentForm
from ..models import TaxAudit, AuditFinding


@login_required
def audit_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TaxAudit.objects.filter(tenant=tenant).select_related('jurisdiction')

    total_count = qs.count()
    in_progress_count = qs.filter(status='in_progress').count()
    closed_count = qs.filter(status__startswith='closed').count()

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(audit_number__icontains=search) | Q(name__icontains=search) |
            Q(auditing_authority__icontains=search)
        )

    tax_type = request.GET.get('tax_type', '')
    if tax_type:
        qs = qs.filter(tax_type=tax_type)

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tax/audit/audit_list.html', {
        'audits': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'in_progress_count': in_progress_count,
        'closed_count': closed_count,
        'tax_type_choices': TaxAudit.TAX_TYPE_CHOICES,
        'status_choices': TaxAudit.STATUS_CHOICES,
    })


@login_required
def audit_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TaxAuditForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.audit_number = TaxAudit.generate_audit_number(tenant)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Audit "{obj.audit_number}" created.')
            return redirect('tax:audit_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = TaxAuditForm(tenant=tenant)

    return render(request, 'tax/audit/audit_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def audit_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    audit = get_object_or_404(TaxAudit.unscoped, pk=pk, tenant=tenant)
    findings = audit.findings.all()
    documents = audit.documents.all()

    return render(request, 'tax/audit/audit_detail.html', {
        'audit': audit,
        'findings': findings,
        'documents': documents,
    })


@login_required
def audit_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    audit = get_object_or_404(TaxAudit.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = TaxAuditForm(request.POST, instance=audit, tenant=tenant)
        if form.is_valid():
            form.save()

            # Recalculate totals from findings
            findings = audit.findings.all()
            audit.total_proposed_adjustment = sum(f.proposed_amount for f in findings)
            audit.total_agreed_adjustment = sum(f.agreed_amount for f in findings)
            audit.save()

            messages.success(request, f'Audit "{audit.audit_number}" updated.')
            return redirect('tax:audit_detail', tenant_slug=tenant.slug, pk=audit.pk)
    else:
        form = TaxAuditForm(instance=audit, tenant=tenant)

    return render(request, 'tax/audit/audit_form.html', {
        'form': form, 'is_edit': True, 'audit': audit,
    })


@login_required
def finding_create(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    audit = get_object_or_404(TaxAudit.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = AuditFindingForm(request.POST)
        if form.is_valid():
            finding = form.save(commit=False)
            finding.tenant = tenant
            finding.audit = audit
            finding.save()

            # Update audit totals
            findings = audit.findings.all()
            audit.total_proposed_adjustment = sum(f.proposed_amount for f in findings)
            audit.total_agreed_adjustment = sum(f.agreed_amount for f in findings)
            audit.save()

            messages.success(request, f'Finding #{finding.finding_number} added.')
            return redirect('tax:audit_detail', tenant_slug=tenant.slug, pk=audit.pk)
    else:
        next_num = (audit.findings.count() or 0) + 1
        form = AuditFindingForm(initial={'finding_number': next_num})

    return render(request, 'tax/audit/finding_form.html', {
        'form': form, 'audit': audit, 'is_edit': False,
    })


@login_required
def finding_edit(request, tenant_slug, pk, finding_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    audit = get_object_or_404(TaxAudit.unscoped, pk=pk, tenant=tenant)
    finding = get_object_or_404(AuditFinding.unscoped, pk=finding_pk, audit=audit, tenant=tenant)

    if request.method == 'POST':
        form = AuditFindingForm(request.POST, instance=finding)
        if form.is_valid():
            form.save()

            # Update audit totals
            findings = audit.findings.all()
            audit.total_proposed_adjustment = sum(f.proposed_amount for f in findings)
            audit.total_agreed_adjustment = sum(f.agreed_amount for f in findings)
            audit.save()

            messages.success(request, f'Finding #{finding.finding_number} updated.')
            return redirect('tax:audit_detail', tenant_slug=tenant.slug, pk=audit.pk)
    else:
        form = AuditFindingForm(instance=finding)

    return render(request, 'tax/audit/finding_form.html', {
        'form': form, 'audit': audit, 'finding': finding, 'is_edit': True,
    })


@login_required
def document_upload(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    audit = get_object_or_404(TaxAudit.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = AuditDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.tenant = tenant
            doc.audit = audit
            doc.uploaded_by = request.user
            doc.save()
            messages.success(request, f'Document "{doc.name}" uploaded.')
            return redirect('tax:audit_detail', tenant_slug=tenant.slug, pk=audit.pk)
    else:
        form = AuditDocumentForm()

    return render(request, 'tax/audit/document_upload.html', {
        'form': form, 'audit': audit,
    })
