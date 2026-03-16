from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import BudgetVersionForm
from ..models import Budget, BudgetVersion
from ..services import create_budget_version_snapshot


@login_required
def version_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = BudgetVersion.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(version_number__icontains=search) |
            Q(name__icontains=search) |
            Q(budget__name__icontains=search)
        )

    version_type_filter = request.GET.get('version_type', '')
    if version_type_filter:
        qs = qs.filter(version_type=version_type_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'budgeting/versions/version_list.html', {
        'versions': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'version_type_choices': BudgetVersion.VERSION_TYPE_CHOICES,
    })


@login_required
def version_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = BudgetVersionForm(request.POST, tenant=tenant)
        if form.is_valid():
            version = form.save(commit=False)
            version.tenant = tenant
            version.version_number = BudgetVersion.generate_version_number(tenant)
            version.created_by = request.user
            version.save()
            create_budget_version_snapshot(version.budget, version)
            messages.success(request, f'Version "{version.name}" created.')
            return redirect('budgeting:version_detail', tenant_slug=tenant.slug, pk=version.pk)
    else:
        form = BudgetVersionForm(tenant=tenant)

    return render(request, 'budgeting/versions/version_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def version_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    version = get_object_or_404(BudgetVersion.unscoped, pk=pk, tenant=tenant)

    return render(request, 'budgeting/versions/version_detail.html', {
        'version': version,
    })


@login_required
def version_set_current(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    version = get_object_or_404(BudgetVersion.unscoped, pk=pk, tenant=tenant)
    BudgetVersion.unscoped.filter(
        tenant=tenant, budget=version.budget
    ).update(is_current=False)
    version.is_current = True
    version.save(update_fields=['is_current', 'updated_at'])
    messages.success(request, f'Version "{version.name}" set as current.')
    return redirect('budgeting:version_detail', tenant_slug=tenant.slug, pk=version.pk)
