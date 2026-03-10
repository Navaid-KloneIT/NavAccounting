from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import (
    ItemCategoryForm, UnitOfMeasureForm, ItemForm, ItemFilterForm,
    WarehouseForm,
)
from ..models import ItemCategory, UnitOfMeasure, Item, Warehouse


# =============================================================================
# Item Categories
# =============================================================================

@login_required
def category_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ItemCategory.objects.filter(tenant=tenant)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))
    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/categories/category_list.html', {
        'categories': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def category_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ItemCategoryForm(request.POST, tenant=tenant)
        if form.is_valid():
            category = form.save(commit=False)
            category.tenant = tenant
            category.save()
            messages.success(request, f'Category "{category.name}" created.')
            return redirect('inventory:category_list', tenant_slug=tenant.slug)
    else:
        form = ItemCategoryForm(tenant=tenant)

    return render(request, 'inventory/categories/category_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def category_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    category = get_object_or_404(ItemCategory.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ItemCategoryForm(request.POST, instance=category, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated.')
            return redirect('inventory:category_list', tenant_slug=tenant.slug)
    else:
        form = ItemCategoryForm(instance=category, tenant=tenant)

    return render(request, 'inventory/categories/category_form.html', {
        'form': form, 'is_edit': True, 'category': category,
    })


# =============================================================================
# Units of Measure
# =============================================================================

@login_required
def uom_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = UnitOfMeasure.objects.filter(tenant=tenant)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))
    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/uom/uom_list.html', {
        'units': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def uom_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = UnitOfMeasureForm(request.POST)
        if form.is_valid():
            uom = form.save(commit=False)
            uom.tenant = tenant
            uom.save()
            messages.success(request, f'Unit of measure "{uom.name}" created.')
            return redirect('inventory:uom_list', tenant_slug=tenant.slug)
    else:
        form = UnitOfMeasureForm()

    return render(request, 'inventory/uom/uom_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def uom_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    uom = get_object_or_404(UnitOfMeasure.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = UnitOfMeasureForm(request.POST, instance=uom)
        if form.is_valid():
            form.save()
            messages.success(request, f'Unit of measure "{uom.name}" updated.')
            return redirect('inventory:uom_list', tenant_slug=tenant.slug)
    else:
        form = UnitOfMeasureForm(instance=uom)

    return render(request, 'inventory/uom/uom_form.html', {
        'form': form, 'is_edit': True, 'uom': uom,
    })


# =============================================================================
# Items
# =============================================================================

@login_required
def item_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = Item.objects.filter(tenant=tenant).select_related('category', 'base_uom')

    filter_form = ItemFilterForm(request.GET, tenant=tenant)
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(sku__icontains=search) | Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        category = filter_form.cleaned_data.get('category')
        if category:
            qs = qs.filter(category=category)
        item_type = filter_form.cleaned_data.get('item_type')
        if item_type:
            qs = qs.filter(item_type=item_type)
        status = filter_form.cleaned_data.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)

    total_count = qs.count()
    total_value = sum(i.inventory_value for i in qs.filter(item_type='inventory')[:100])

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = ItemCategory.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'inventory/items/item_list.html', {
        'items': page_obj,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'categories': categories,
        'total_count': total_count,
        'total_value': total_value,
    })


@login_required
def item_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ItemForm(request.POST, tenant=tenant)
        if form.is_valid():
            item = form.save(commit=False)
            item.tenant = tenant
            item.sku = Item.generate_sku(tenant)
            item.save()
            messages.success(request, f'Item "{item.name}" created with SKU {item.sku}.')
            return redirect('inventory:item_detail', tenant_slug=tenant.slug, pk=item.pk)
    else:
        form = ItemForm(tenant=tenant)

    return render(request, 'inventory/items/item_create.html', {
        'form': form,
    })


@login_required
def item_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    item = get_object_or_404(
        Item.unscoped.select_related('category', 'base_uom'),
        pk=pk, tenant=tenant
    )

    recent_transactions = item.transactions.order_by('-date', '-pk')[:10]
    cost_layers = item.cost_layers.filter(is_depleted=False).order_by('receipt_date')

    return render(request, 'inventory/items/item_detail.html', {
        'item': item,
        'recent_transactions': recent_transactions,
        'cost_layers': cost_layers,
    })


@login_required
def item_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    item = get_object_or_404(Item.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Item "{item.name}" updated.')
            return redirect('inventory:item_detail', tenant_slug=tenant.slug, pk=item.pk)
    else:
        form = ItemForm(instance=item, tenant=tenant)

    return render(request, 'inventory/items/item_edit.html', {
        'form': form, 'item': item,
    })


# =============================================================================
# Warehouses
# =============================================================================

@login_required
def warehouse_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = Warehouse.objects.filter(tenant=tenant)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))
    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/warehouses/warehouse_list.html', {
        'warehouses': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def warehouse_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            warehouse = form.save(commit=False)
            warehouse.tenant = tenant
            warehouse.save()
            messages.success(request, f'Warehouse "{warehouse.name}" created.')
            return redirect('inventory:warehouse_list', tenant_slug=tenant.slug)
    else:
        form = WarehouseForm()

    return render(request, 'inventory/warehouses/warehouse_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def warehouse_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    warehouse = get_object_or_404(Warehouse.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            messages.success(request, f'Warehouse "{warehouse.name}" updated.')
            return redirect('inventory:warehouse_list', tenant_slug=tenant.slug)
    else:
        form = WarehouseForm(instance=warehouse)

    return render(request, 'inventory/warehouses/warehouse_form.html', {
        'form': form, 'is_edit': True, 'warehouse': warehouse,
    })
