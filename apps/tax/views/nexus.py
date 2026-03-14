from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import NexusJurisdictionForm, NexusActivityForm
from ..models import NexusJurisdiction


@login_required
def nexus_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = NexusJurisdiction.objects.filter(tenant=tenant).select_related('jurisdiction')

    total_count = qs.count()
    has_nexus_count = qs.filter(has_nexus=True).count()
    registered_count = qs.filter(registration_status='registered').count()

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(jurisdiction__code__icontains=search) |
            Q(jurisdiction__name__icontains=search)
        )

    nexus_type = request.GET.get('nexus_type', '')
    if nexus_type:
        qs = qs.filter(nexus_type=nexus_type)

    status = request.GET.get('status', '')
    if status == 'has_nexus':
        qs = qs.filter(has_nexus=True)
    elif status == 'no_nexus':
        qs = qs.filter(has_nexus=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tax/nexus/nexus_list.html', {
        'nexus_records': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'has_nexus_count': has_nexus_count,
        'registered_count': registered_count,
        'nexus_type_choices': NexusJurisdiction.NEXUS_TYPE_CHOICES,
    })


@login_required
def nexus_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = NexusJurisdictionForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, 'Nexus jurisdiction created.')
            return redirect('tax:nexus_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = NexusJurisdictionForm(tenant=tenant)

    return render(request, 'tax/nexus/nexus_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def nexus_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    nexus = get_object_or_404(NexusJurisdiction.unscoped, pk=pk, tenant=tenant)
    activities = nexus.activities.all()

    return render(request, 'tax/nexus/nexus_detail.html', {
        'nexus': nexus,
        'activities': activities,
    })


@login_required
def nexus_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    nexus = get_object_or_404(NexusJurisdiction.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = NexusJurisdictionForm(request.POST, instance=nexus, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nexus jurisdiction updated.')
            return redirect('tax:nexus_detail', tenant_slug=tenant.slug, pk=nexus.pk)
    else:
        form = NexusJurisdictionForm(instance=nexus, tenant=tenant)

    return render(request, 'tax/nexus/nexus_form.html', {
        'form': form, 'is_edit': True, 'nexus': nexus,
    })


@login_required
def nexus_activity_create(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    nexus = get_object_or_404(NexusJurisdiction.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = NexusActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.tenant = tenant
            activity.nexus_jurisdiction = nexus
            activity.save()

            # Update nexus thresholds
            from ..services import update_nexus_thresholds
            update_nexus_thresholds(tenant)

            messages.success(request, 'Activity period recorded.')
            return redirect('tax:nexus_detail', tenant_slug=tenant.slug, pk=nexus.pk)
    else:
        form = NexusActivityForm()

    return render(request, 'tax/nexus/activity_form.html', {
        'form': form, 'nexus': nexus,
    })


@login_required
def nexus_dashboard(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    # Update thresholds
    from ..services import update_nexus_thresholds, get_nexus_alerts
    update_nexus_thresholds(tenant)

    alerts = get_nexus_alerts(tenant)
    all_records = NexusJurisdiction.objects.filter(
        tenant=tenant, is_active=True
    ).select_related('jurisdiction')

    return render(request, 'tax/nexus/nexus_dashboard.html', {
        'alerts': alerts,
        'all_records': all_records,
    })
