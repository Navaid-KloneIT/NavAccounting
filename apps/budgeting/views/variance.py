from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import VarianceAnalysisForm
from ..models import VarianceAnalysis
from ..services import generate_variance_analysis


@login_required
def variance_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = VarianceAnalysis.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(analysis_number__icontains=search) |
            Q(name__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'budgeting/variance/variance_list.html', {
        'analyses': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'status_choices': VarianceAnalysis.STATUS_CHOICES,
    })


@login_required
def variance_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = VarianceAnalysisForm(request.POST, tenant=tenant)
        if form.is_valid():
            analysis = form.save(commit=False)
            analysis.tenant = tenant
            analysis.analysis_number = VarianceAnalysis.generate_analysis_number(tenant)
            analysis.save()
            messages.success(request, f'Variance analysis "{analysis.name}" created.')
            return redirect('budgeting:variance_detail', tenant_slug=tenant.slug, pk=analysis.pk)
    else:
        form = VarianceAnalysisForm(tenant=tenant)

    return render(request, 'budgeting/variance/variance_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def variance_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    analysis = get_object_or_404(VarianceAnalysis.unscoped, pk=pk, tenant=tenant)
    line_items = analysis.line_items.select_related('gl_account').all()

    return render(request, 'budgeting/variance/variance_detail.html', {
        'analysis': analysis,
        'line_items': line_items,
    })


@login_required
def variance_generate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    analysis = get_object_or_404(VarianceAnalysis.unscoped, pk=pk, tenant=tenant)
    analysis.generated_by = request.user
    generate_variance_analysis(analysis, tenant)
    messages.success(request, f'Variance analysis "{analysis.name}" generated.')
    return redirect('budgeting:variance_detail', tenant_slug=tenant.slug, pk=analysis.pk)
