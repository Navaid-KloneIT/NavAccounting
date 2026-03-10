from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import EntityForm
from ..models import Entity


@login_required
def entity_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = Entity.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    active_count = qs.filter(status='active').count()
    inactive_count = qs.filter(status='inactive').count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(code__icontains=search) | Q(name__icontains=search) | Q(legal_name__icontains=search))

    # Entity type filter
    entity_type = request.GET.get('entity_type', '')
    if entity_type:
        qs = qs.filter(entity_type=entity_type)

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'multi_entity/entities/entity_list.html', {
        'entities': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'entity_type_choices': Entity.ENTITY_TYPE_CHOICES,
        'status_choices': Entity.STATUS_CHOICES,
    })


@login_required
def entity_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = EntityForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Entity "{obj.code}" created successfully.')
            return redirect('multi_entity:entity_list', tenant_slug=tenant.slug)
    else:
        form = EntityForm(tenant=tenant)

    return render(request, 'multi_entity/entities/entity_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def entity_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    entity = get_object_or_404(Entity.unscoped, pk=pk, tenant=tenant)
    children = Entity.unscoped.filter(tenant=tenant, parent=entity)
    ic_transactions = entity.ic_transactions_from.all()[:10]
    ic_balances = entity.ic_balances_from.all()[:10]

    return render(request, 'multi_entity/entities/entity_detail.html', {
        'entity': entity,
        'children': children,
        'ic_transactions': ic_transactions,
        'ic_balances': ic_balances,
    })


@login_required
def entity_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    entity = get_object_or_404(Entity.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = EntityForm(request.POST, instance=entity, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Entity "{entity.code}" updated successfully.')
            return redirect('multi_entity:entity_detail', tenant_slug=tenant.slug, pk=entity.pk)
    else:
        form = EntityForm(instance=entity, tenant=tenant)

    return render(request, 'multi_entity/entities/entity_form.html', {
        'form': form,
        'entity': entity,
        'is_edit': True,
    })


@login_required
def entity_hierarchy(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    # Get root entities (no parent)
    roots = Entity.objects.filter(tenant=tenant, parent__isnull=True).prefetch_related('children')

    return render(request, 'multi_entity/entities/entity_hierarchy.html', {
        'roots': roots,
    })
