from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import WorkersCompClassForm, WorkersCompAssignmentForm
from ..models import WorkersCompClass, WorkersCompAssignment


# -------------------------------------------------------------------------
# Workers Comp Classes
# -------------------------------------------------------------------------

@login_required
def comp_class_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = WorkersCompClass.objects.filter(tenant=tenant)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'payroll/workers_comp/workers_comp_list.html', {
        'classes': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def comp_class_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = WorkersCompClassForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Workers comp class "{obj.name}" created.')
            return redirect('payroll:comp_class_list', tenant_slug=tenant.slug)
    else:
        form = WorkersCompClassForm(tenant=tenant)

    return render(request, 'payroll/workers_comp/workers_comp_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def comp_class_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    comp_class = get_object_or_404(WorkersCompClass.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = WorkersCompClassForm(request.POST, instance=comp_class, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Workers comp class "{comp_class.name}" updated.')
            return redirect('payroll:comp_class_list', tenant_slug=tenant.slug)
    else:
        form = WorkersCompClassForm(instance=comp_class, tenant=tenant)

    return render(request, 'payroll/workers_comp/workers_comp_form.html', {
        'form': form, 'is_edit': True, 'comp_class': comp_class,
    })


@login_required
def comp_class_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    comp_class = get_object_or_404(WorkersCompClass.unscoped, pk=pk, tenant=tenant)
    assignments = comp_class.assignments.select_related('employee').all()

    return render(request, 'payroll/workers_comp/workers_comp_detail.html', {
        'comp_class': comp_class,
        'assignments': assignments,
    })


# -------------------------------------------------------------------------
# Workers Comp Assignments
# -------------------------------------------------------------------------

@login_required
def assignment_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = WorkersCompAssignmentForm(request.POST, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Workers comp assignment created.')
            return redirect('payroll:comp_class_list', tenant_slug=tenant.slug)
    else:
        form = WorkersCompAssignmentForm(tenant=tenant)

    return render(request, 'payroll/workers_comp/assignment_form.html', {
        'form': form,
    })


@login_required
def assignment_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    assignment = get_object_or_404(WorkersCompAssignment, pk=pk)

    if request.method == 'POST':
        form = WorkersCompAssignmentForm(request.POST, instance=assignment, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated.')
            return redirect('payroll:comp_class_detail', tenant_slug=tenant.slug,
                            pk=assignment.comp_class.pk)
    else:
        form = WorkersCompAssignmentForm(instance=assignment, tenant=tenant)

    return render(request, 'payroll/workers_comp/assignment_form.html', {
        'form': form, 'assignment': assignment,
    })
