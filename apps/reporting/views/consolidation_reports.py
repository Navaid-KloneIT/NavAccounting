from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import ConsolidationPackageForm, ConsolidationPackageEntityFormSet
from ..models import ConsolidationPackage


@login_required
def package_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ConsolidationPackage.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    published_count = qs.filter(status='published').count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(package_number__icontains=search) | Q(name__icontains=search)
        )

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reporting/consolidation_reports/package_list.html', {
        'packages': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'published_count': published_count,
        'status_choices': ConsolidationPackage.STATUS_CHOICES,
    })


@login_required
def package_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ConsolidationPackageForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Package "{obj.package_number}" created.')
            return redirect('reporting:package_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = ConsolidationPackageForm(tenant=tenant)

    return render(request, 'reporting/consolidation_reports/package_form.html', {
        'form': form,
        'is_create': True,
    })


@login_required
def package_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    package = get_object_or_404(ConsolidationPackage, pk=pk, tenant=tenant)
    entities = package.entities.select_related('entity').all()
    lines = package.lines.all()

    return render(request, 'reporting/consolidation_reports/package_detail.html', {
        'package': package,
        'entities': entities,
        'lines': lines,
    })


@login_required
def package_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    package = get_object_or_404(ConsolidationPackage, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ConsolidationPackageForm(request.POST, instance=package, tenant=tenant)
        entity_formset = ConsolidationPackageEntityFormSet(request.POST, instance=package)
        if form.is_valid() and entity_formset.is_valid():
            form.save()
            entities = entity_formset.save(commit=False)
            for e in entities:
                e.tenant = tenant
                e.save()
            for e in entity_formset.deleted_objects:
                e.delete()
            messages.success(request, f'Package "{package.package_number}" updated.')
            return redirect('reporting:package_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = ConsolidationPackageForm(instance=package, tenant=tenant)
        entity_formset = ConsolidationPackageEntityFormSet(instance=package)

    return render(request, 'reporting/consolidation_reports/package_form.html', {
        'form': form,
        'entity_formset': entity_formset,
        'package': package,
        'is_create': False,
    })


@login_required
def package_consolidate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    package = get_object_or_404(ConsolidationPackage, pk=pk, tenant=tenant)
    if package.status in ('draft', 'collecting'):
        package.status = 'consolidated'
        package.generated_at = timezone.now()
        package.generated_by = request.user
        package.save()
        messages.success(request, f'Package "{package.package_number}" consolidated.')
    else:
        messages.warning(request, 'Package can only be consolidated from draft or collecting status.')

    return redirect('reporting:package_detail', tenant_slug=tenant.slug, pk=pk)
