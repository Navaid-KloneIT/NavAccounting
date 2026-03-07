from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import RevenueRecognitionForm
from ..models import Project, RevenueRecognition


@login_required
def rev_rec_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = RevenueRecognition.objects.filter(tenant=tenant).select_related(
        'project', 'fiscal_period'
    )

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(project__project_number__icontains=search) |
            Q(project__name__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    method_filter = request.GET.get('method', '')
    if method_filter:
        qs = qs.filter(method=method_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'project_costing/revenue_recognition/rev_rec_list.html', {
        'records': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def rev_rec_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = RevenueRecognitionForm(request.POST, tenant=tenant)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.tenant = tenant
            # Get prior recognized amount
            prior = RevenueRecognition.unscoped.filter(
                tenant=tenant, project=rec.project, status='posted'
            ).aggregate(total=Sum('recognized_this_period'))
            rec.total_recognized_prior = prior['total'] or Decimal('0.00')
            rec.contract_amount = rec.project.contract_amount
            rec.calculate()
            rec.save()
            messages.success(request, 'Revenue recognition entry created.')
            return redirect('project_costing:rev_rec_detail', tenant_slug=tenant.slug, pk=rec.pk)
    else:
        form = RevenueRecognitionForm(tenant=tenant)

    return render(request, 'project_costing/revenue_recognition/rev_rec_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def rev_rec_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rec = get_object_or_404(RevenueRecognition.unscoped.select_related(
        'project', 'fiscal_period', 'gl_journal_entry'
    ), pk=pk, tenant=tenant)

    return render(request, 'project_costing/revenue_recognition/rev_rec_detail.html', {
        'rec': rec,
    })


@login_required
def rev_rec_calculate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rec = get_object_or_404(RevenueRecognition.unscoped, pk=pk, tenant=tenant)

    if rec.status == 'posted':
        messages.error(request, 'Cannot recalculate a posted entry.')
        return redirect('project_costing:rev_rec_detail', tenant_slug=tenant.slug, pk=rec.pk)

    if request.method == 'POST':
        prior = RevenueRecognition.unscoped.filter(
            tenant=tenant, project=rec.project, status='posted'
        ).exclude(pk=rec.pk).aggregate(total=Sum('recognized_this_period'))
        rec.total_recognized_prior = prior['total'] or Decimal('0.00')
        rec.contract_amount = rec.project.contract_amount
        rec.calculate()
        rec.save()
        messages.success(request, 'Revenue recognition recalculated.')

    return redirect('project_costing:rev_rec_detail', tenant_slug=tenant.slug, pk=rec.pk)


@login_required
def rev_rec_post(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rec = get_object_or_404(RevenueRecognition.unscoped, pk=pk, tenant=tenant)

    if rec.status == 'posted':
        messages.warning(request, 'Already posted.')
        return redirect('project_costing:rev_rec_detail', tenant_slug=tenant.slug, pk=rec.pk)

    if request.method == 'POST':
        rec.status = 'posted'
        rec.save()
        messages.success(request, 'Revenue recognition posted.')

    return redirect('project_costing:rev_rec_detail', tenant_slug=tenant.slug, pk=rec.pk)
