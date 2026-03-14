from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import UseTaxAssessmentForm, UseTaxAccrualForm
from ..models import UseTaxAssessment, UseTaxAccrual


@login_required
def assessment_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = UseTaxAssessment.objects.filter(tenant=tenant).select_related(
        'vendor', 'jurisdiction'
    )

    total_count = qs.count()
    pending_count = qs.filter(status='pending').count()
    accrued_count = qs.filter(status='accrued').count()

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(assessment_number__icontains=search) |
            Q(vendor__company_name__icontains=search)
        )

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tax/use_tax/assessment_list.html', {
        'assessments': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'pending_count': pending_count,
        'accrued_count': accrued_count,
        'status_choices': UseTaxAssessment.STATUS_CHOICES,
    })


@login_required
def assessment_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = UseTaxAssessmentForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.assessment_number = UseTaxAssessment.generate_assessment_number(tenant)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Assessment "{obj.assessment_number}" created.')
            return redirect('tax:assessment_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = UseTaxAssessmentForm(tenant=tenant)

    return render(request, 'tax/use_tax/assessment_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def assessment_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    assessment = get_object_or_404(UseTaxAssessment.unscoped, pk=pk, tenant=tenant)

    return render(request, 'tax/use_tax/assessment_detail.html', {
        'assessment': assessment,
    })


@login_required
def assessment_accrue(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    assessment = get_object_or_404(UseTaxAssessment.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if assessment.status == 'pending':
            from ..services import accrue_use_tax
            accrue_use_tax(assessment, tenant, request.user)
            messages.success(request, f'Use tax accrued for "{assessment.assessment_number}".')
        else:
            messages.error(request, 'Only pending assessments can be accrued.')

    return redirect('tax:assessment_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def accrual_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = UseTaxAccrual.objects.filter(tenant=tenant)

    total_count = qs.count()

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tax/use_tax/accrual_list.html', {
        'accruals': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'status_choices': UseTaxAccrual.STATUS_CHOICES,
    })


@login_required
def accrual_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = UseTaxAccrualForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.accrual_number = UseTaxAccrual.generate_accrual_number(tenant)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Accrual "{obj.accrual_number}" created.')
            return redirect('tax:accrual_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = UseTaxAccrualForm()

    return render(request, 'tax/use_tax/accrual_form.html', {
        'form': form,
    })


@login_required
def accrual_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    accrual = get_object_or_404(UseTaxAccrual.unscoped, pk=pk, tenant=tenant)

    return render(request, 'tax/use_tax/accrual_detail.html', {
        'accrual': accrual,
    })


@login_required
def accrual_post(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    accrual = get_object_or_404(UseTaxAccrual.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if accrual.status == 'draft':
            from ..services import post_use_tax_accrual
            post_use_tax_accrual(accrual, tenant, request.user)
            messages.success(request, f'Accrual "{accrual.accrual_number}" posted to GL.')
        else:
            messages.error(request, 'Only draft accruals can be posted.')

    return redirect('tax:accrual_detail', tenant_slug=tenant.slug, pk=pk)
