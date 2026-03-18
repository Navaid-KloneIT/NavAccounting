from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import WorkflowDefinitionForm, WorkflowStepForm
from ..models import WorkflowDefinition, WorkflowStep, WorkflowInstance, WorkflowStepLog


# ──────────────────────────────────────────────
# Workflow Definition Views
# ──────────────────────────────────────────────

@login_required
def workflow_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = WorkflowDefinition.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(workflow_number__icontains=search) | Q(name__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    trigger_filter = request.GET.get('trigger_event', '')
    if trigger_filter:
        qs = qs.filter(trigger_event=trigger_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = WorkflowDefinition.objects.filter(tenant=tenant)
    return render(request, 'system_admin/workflows/workflow_list.html', {
        'workflows': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'active_count': all_items.filter(status='active').count(),
        'draft_count': all_items.filter(status='draft').count(),
        'status_choices': WorkflowDefinition.STATUS_CHOICES,
        'trigger_choices': WorkflowDefinition.TRIGGER_CHOICES,
    })


@login_required
def workflow_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = WorkflowDefinitionForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.workflow_number = WorkflowDefinition.generate_workflow_number(tenant)
            obj.created_by = request.user
            obj.save()
            form.save_m2m()
            messages.success(request, f'Workflow "{obj.name}" created.')
            return redirect('system_admin:workflow_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = WorkflowDefinitionForm()

    return render(request, 'system_admin/workflows/workflow_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def workflow_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    workflow = get_object_or_404(WorkflowDefinition.unscoped, pk=pk, tenant=tenant)
    steps = workflow.steps.order_by('order')
    return render(request, 'system_admin/workflows/workflow_detail.html', {
        'workflow': workflow,
        'steps': steps,
    })


@login_required
def workflow_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    workflow = get_object_or_404(WorkflowDefinition.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = WorkflowDefinitionForm(request.POST, instance=workflow)
        if form.is_valid():
            form.save()
            messages.success(request, f'Workflow "{workflow.name}" updated.')
            return redirect('system_admin:workflow_detail', tenant_slug=tenant.slug, pk=workflow.pk)
    else:
        form = WorkflowDefinitionForm(instance=workflow)

    return render(request, 'system_admin/workflows/workflow_form.html', {
        'form': form, 'is_edit': True, 'workflow': workflow,
    })


# ──────────────────────────────────────────────
# Workflow Step Views
# ──────────────────────────────────────────────

@login_required
def workflow_step_create(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    workflow = get_object_or_404(WorkflowDefinition.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = WorkflowStepForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.step_number = WorkflowStep.generate_step_number(tenant)
            obj.workflow = workflow
            obj.save()
            form.save_m2m()
            messages.success(request, f'Step "{obj.name}" added to workflow.')
            return redirect('system_admin:workflow_detail', tenant_slug=tenant.slug, pk=workflow.pk)
    else:
        form = WorkflowStepForm()

    return render(request, 'system_admin/workflows/workflow_step_form.html', {
        'form': form, 'workflow': workflow, 'is_edit': False,
    })


@login_required
def workflow_step_edit(request, tenant_slug, pk, step_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    workflow = get_object_or_404(WorkflowDefinition.unscoped, pk=pk, tenant=tenant)
    step = get_object_or_404(WorkflowStep.unscoped, pk=step_pk, tenant=tenant, workflow=workflow)

    if request.method == 'POST':
        form = WorkflowStepForm(request.POST, instance=step)
        if form.is_valid():
            form.save()
            messages.success(request, f'Step "{step.name}" updated.')
            return redirect('system_admin:workflow_detail', tenant_slug=tenant.slug, pk=workflow.pk)
    else:
        form = WorkflowStepForm(instance=step)

    return render(request, 'system_admin/workflows/workflow_step_form.html', {
        'form': form, 'workflow': workflow, 'step': step, 'is_edit': True,
    })


@login_required
def workflow_step_delete(request, tenant_slug, pk, step_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    workflow = get_object_or_404(WorkflowDefinition.unscoped, pk=pk, tenant=tenant)
    step = get_object_or_404(WorkflowStep.unscoped, pk=step_pk, tenant=tenant, workflow=workflow)

    if request.method == 'POST':
        step.delete()
        messages.success(request, f'Step "{step.name}" deleted.')
    return redirect('system_admin:workflow_detail', tenant_slug=tenant.slug, pk=workflow.pk)


# ──────────────────────────────────────────────
# Workflow Instance Views
# ──────────────────────────────────────────────

@login_required
def workflow_instance_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = WorkflowInstance.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(instance_number__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = WorkflowInstance.objects.filter(tenant=tenant)
    return render(request, 'system_admin/workflows/workflow_instance_list.html', {
        'instances': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'in_progress_count': all_items.filter(status='in_progress').count(),
        'completed_count': all_items.filter(status='completed').count(),
        'status_choices': WorkflowInstance.STATUS_CHOICES,
    })


@login_required
def workflow_instance_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    instance = get_object_or_404(WorkflowInstance.unscoped, pk=pk, tenant=tenant)
    step_logs = instance.step_logs.all()
    return render(request, 'system_admin/workflows/workflow_instance_detail.html', {
        'instance': instance,
        'step_logs': step_logs,
    })
