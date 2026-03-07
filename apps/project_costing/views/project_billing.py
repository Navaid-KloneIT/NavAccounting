from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import ProjectMilestoneForm, ProjectInvoiceForm, ProjectInvoiceLineFormSet
from ..models import Project, ProjectMilestone, ProjectInvoice


# -------------------------------------------------------------------------
# Milestone CRUD
# -------------------------------------------------------------------------

@login_required
def milestone_list(request, tenant_slug, project_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    milestones = ProjectMilestone.unscoped.filter(project=project)
    totals = milestones.aggregate(total_amount=Sum('amount'))

    return render(request, 'project_costing/milestones/milestone_list.html', {
        'project': project,
        'milestones': milestones,
        'totals': totals,
    })


@login_required
def milestone_create(request, tenant_slug, project_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)

    if request.method == 'POST':
        form = ProjectMilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.tenant = tenant
            milestone.project = project
            milestone.save()
            messages.success(request, f'Milestone "{milestone.name}" created.')
            return redirect('project_costing:milestone_list', tenant_slug=tenant.slug, project_pk=project.pk)
    else:
        form = ProjectMilestoneForm()

    return render(request, 'project_costing/milestones/milestone_form.html', {
        'form': form, 'project': project, 'is_edit': False,
    })


@login_required
def milestone_edit(request, tenant_slug, project_pk, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    milestone = get_object_or_404(ProjectMilestone.unscoped, pk=pk, project=project)

    if request.method == 'POST':
        form = ProjectMilestoneForm(request.POST, instance=milestone)
        if form.is_valid():
            form.save()
            messages.success(request, f'Milestone "{milestone.name}" updated.')
            return redirect('project_costing:milestone_list', tenant_slug=tenant.slug, project_pk=project.pk)
    else:
        form = ProjectMilestoneForm(instance=milestone)

    return render(request, 'project_costing/milestones/milestone_form.html', {
        'form': form, 'project': project, 'is_edit': True, 'milestone': milestone,
    })


@login_required
def milestone_complete(request, tenant_slug, project_pk, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    milestone = get_object_or_404(ProjectMilestone.unscoped, pk=pk, project=project)

    if request.method == 'POST':
        milestone.status = 'completed'
        milestone.actual_date = timezone.now().date()
        milestone.completion_percentage = Decimal('100.00')
        milestone.save()
        messages.success(request, f'Milestone "{milestone.name}" marked as completed.')

    return redirect('project_costing:milestone_list', tenant_slug=tenant.slug, project_pk=project.pk)


# -------------------------------------------------------------------------
# Invoice CRUD
# -------------------------------------------------------------------------

@login_required
def invoice_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ProjectInvoice.objects.filter(tenant=tenant).select_related('project')

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(invoice_number__icontains=search) |
            Q(project__project_number__icontains=search) |
            Q(project__name__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    totals = qs.aggregate(
        total_subtotal=Sum('subtotal'),
        total_retention=Sum('retention_amount'),
        total_amount=Sum('total_amount'),
    )

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'project_costing/invoices/invoice_list.html', {
        'invoices': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'totals': totals,
    })


@login_required
def invoice_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ProjectInvoiceForm(request.POST, tenant=tenant)
        formset = ProjectInvoiceLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.tenant = tenant
            invoice.invoice_number = ProjectInvoice.generate_invoice_number(tenant)
            invoice.save()

            formset.instance = invoice
            lines = formset.save()

            # Calculate totals
            subtotal = sum(line.amount for line in invoice.lines.all())
            invoice.subtotal = subtotal
            retention_pct = invoice.project.retention_percentage or Decimal('0.00')
            invoice.retention_amount = subtotal * retention_pct / 100
            invoice.total_amount = subtotal - invoice.retention_amount + invoice.tax_amount
            invoice.save()

            messages.success(request, f'Invoice {invoice.invoice_number} created.')
            return redirect('project_costing:invoice_detail', tenant_slug=tenant.slug, pk=invoice.pk)
    else:
        form = ProjectInvoiceForm(tenant=tenant)
        formset = ProjectInvoiceLineFormSet()

    return render(request, 'project_costing/invoices/invoice_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def invoice_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    invoice = get_object_or_404(
        ProjectInvoice.unscoped.select_related('project', 'fiscal_period'),
        pk=pk, tenant=tenant
    )
    lines = invoice.lines.select_related('wbs_element').all()

    return render(request, 'project_costing/invoices/invoice_detail.html', {
        'invoice': invoice,
        'lines': lines,
    })


@login_required
def invoice_approve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    invoice = get_object_or_404(ProjectInvoice.unscoped, pk=pk, tenant=tenant)

    if invoice.status != 'draft':
        messages.warning(request, 'Only draft invoices can be approved.')
        return redirect('project_costing:invoice_detail', tenant_slug=tenant.slug, pk=invoice.pk)

    if request.method == 'POST':
        invoice.status = 'approved'
        invoice.save()
        messages.success(request, f'Invoice {invoice.invoice_number} approved.')

    return redirect('project_costing:invoice_detail', tenant_slug=tenant.slug, pk=invoice.pk)


@login_required
def invoice_void(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    invoice = get_object_or_404(ProjectInvoice.unscoped, pk=pk, tenant=tenant)

    if invoice.status == 'paid':
        messages.error(request, 'Cannot void a paid invoice.')
        return redirect('project_costing:invoice_detail', tenant_slug=tenant.slug, pk=invoice.pk)

    if request.method == 'POST':
        invoice.status = 'void'
        invoice.save()
        messages.success(request, f'Invoice {invoice.invoice_number} voided.')

    return redirect('project_costing:invoice_detail', tenant_slug=tenant.slug, pk=invoice.pk)
