from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from .forms import (
    AssetCategoryForm, AssetLocationForm, AssetForm, AssetFilterForm,
    AssetAcquisitionForm, DepreciationProfileForm, RunDepreciationForm,
    AssetTransferForm, AssetDisposalForm, ImpairmentTestForm,
    PhysicalInventoryForm, PhysicalInventoryItemFormSet,
    TaxDepreciationBookForm, TaxDepreciationEntryForm,
)
from .models import (
    AssetCategory, AssetLocation, Asset, AssetAcquisition,
    DepreciationProfile, DepreciationSchedule, DepreciationEntry,
    AssetTransfer, AssetDisposal, ImpairmentTest,
    PhysicalInventory, PhysicalInventoryItem,
    TaxDepreciationBook, TaxDepreciationEntry,
)
from .services import (
    create_acquisition_journal_entry, create_disposal_journal_entry,
    create_impairment_journal_entry, run_depreciation,
    generate_depreciation_schedule, calculate_disposal_gain_loss,
)


# =============================================================================
# 1. Asset Categories
# =============================================================================

@login_required
def category_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = AssetCategory.objects.filter(tenant=tenant)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'fixed_assets/categories/category_list.html', {
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
        form = AssetCategoryForm(request.POST, tenant=tenant)
        if form.is_valid():
            category = form.save(commit=False)
            category.tenant = tenant
            category.save()
            messages.success(request, f'Category "{category.name}" created.')
            return redirect('fixed_assets:category_list', tenant_slug=tenant.slug)
    else:
        form = AssetCategoryForm(tenant=tenant)

    return render(request, 'fixed_assets/categories/category_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def category_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    category = get_object_or_404(AssetCategory.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = AssetCategoryForm(request.POST, instance=category, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated.')
            return redirect('fixed_assets:category_list', tenant_slug=tenant.slug)
    else:
        form = AssetCategoryForm(instance=category, tenant=tenant)

    return render(request, 'fixed_assets/categories/category_form.html', {
        'form': form, 'is_edit': True, 'category': category,
    })


# =============================================================================
# 2. Asset Locations
# =============================================================================

@login_required
def location_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = AssetLocation.objects.filter(tenant=tenant)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'fixed_assets/locations/location_list.html', {
        'locations': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def location_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = AssetLocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.tenant = tenant
            location.save()
            messages.success(request, f'Location "{location.name}" created.')
            return redirect('fixed_assets:location_list', tenant_slug=tenant.slug)
    else:
        form = AssetLocationForm()

    return render(request, 'fixed_assets/locations/location_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def location_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    location = get_object_or_404(AssetLocation.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = AssetLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f'Location "{location.name}" updated.')
            return redirect('fixed_assets:location_list', tenant_slug=tenant.slug)
    else:
        form = AssetLocationForm(instance=location)

    return render(request, 'fixed_assets/locations/location_form.html', {
        'form': form, 'is_edit': True, 'location': location,
    })


# =============================================================================
# 3. Assets
# =============================================================================

@login_required
def asset_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = Asset.objects.filter(tenant=tenant).select_related('category', 'location', 'custodian')

    # Stats
    total_count = qs.count()
    in_service_count = qs.filter(status='in_service').count()
    total_cost = qs.filter(is_active=True).aggregate(
        total=Sum('acquisition_cost')
    )['total'] or Decimal('0.00')
    total_nbv = total_cost - (qs.filter(is_active=True).aggregate(
        total=Sum('accumulated_depreciation')
    )['total'] or Decimal('0.00'))

    # Filters
    filter_form = AssetFilterForm(request.GET, tenant=tenant)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(asset_number__icontains=search) |
            Q(name__icontains=search) |
            Q(serial_number__icontains=search) |
            Q(barcode__icontains=search)
        )
    category_id = request.GET.get('category')
    if category_id:
        qs = qs.filter(category_id=category_id)
    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)
    location_id = request.GET.get('location')
    if location_id:
        qs = qs.filter(location_id=location_id)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'fixed_assets/assets/asset_list.html', {
        'assets': page_obj,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_count': total_count,
        'in_service_count': in_service_count,
        'total_cost': total_cost,
        'total_nbv': total_nbv,
    })


@login_required
def asset_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = AssetForm(request.POST, tenant=tenant)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.tenant = tenant
            asset.asset_number = Asset.generate_asset_number(tenant)
            asset.save()

            # Auto-create depreciation profile
            DepreciationProfile.unscoped.create(
                tenant=tenant,
                asset=asset,
                method=asset.depreciation_method,
                useful_life_months=asset.useful_life_months,
                start_date=asset.acquisition_date,
                end_date=_add_months(asset.acquisition_date, asset.useful_life_months),
                salvage_value=asset.salvage_value,
            )

            # Generate depreciation schedule
            generate_depreciation_schedule(asset)

            messages.success(request, f'Asset "{asset.asset_number}" created.')
            return redirect('fixed_assets:asset_detail', tenant_slug=tenant.slug, pk=asset.pk)
    else:
        form = AssetForm(tenant=tenant)

    return render(request, 'fixed_assets/assets/asset_create.html', {
        'form': form,
    })


@login_required
def asset_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    asset = get_object_or_404(
        Asset.unscoped.select_related('category', 'location', 'custodian'),
        pk=pk, tenant=tenant
    )

    schedules = DepreciationSchedule.unscoped.filter(
        asset=asset
    ).order_by('period_number')[:24]

    acquisitions = AssetAcquisition.unscoped.filter(asset=asset).order_by('-acquisition_date')
    transfers = AssetTransfer.unscoped.filter(asset=asset).order_by('-transfer_date')
    disposals = AssetDisposal.unscoped.filter(asset=asset).order_by('-disposal_date')
    impairments = ImpairmentTest.unscoped.filter(asset=asset).order_by('-test_date')

    try:
        dep_profile = asset.depreciation_profile
    except DepreciationProfile.DoesNotExist:
        dep_profile = None

    return render(request, 'fixed_assets/assets/asset_detail.html', {
        'asset': asset,
        'dep_profile': dep_profile,
        'schedules': schedules,
        'acquisitions': acquisitions,
        'transfers': transfers,
        'disposals': disposals,
        'impairments': impairments,
    })


@login_required
def asset_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    asset = get_object_or_404(Asset.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Asset "{asset.asset_number}" updated.')
            return redirect('fixed_assets:asset_detail', tenant_slug=tenant.slug, pk=asset.pk)
    else:
        form = AssetForm(instance=asset, tenant=tenant)

    return render(request, 'fixed_assets/assets/asset_edit.html', {
        'form': form, 'asset': asset,
    })


# =============================================================================
# 4. Acquisitions
# =============================================================================

@login_required
def acquisition_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = AssetAcquisition.objects.filter(tenant=tenant).select_related('asset', 'currency')

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(acquisition_number__icontains=search) |
            Q(asset__asset_number__icontains=search) |
            Q(vendor_name__icontains=search)
        )

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    total_amount = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    capitalized_count = qs.filter(is_capitalized=True).count()

    return render(request, 'fixed_assets/acquisitions/acquisition_list.html', {
        'acquisitions': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'total_amount': total_amount,
        'capitalized_count': capitalized_count,
    })


@login_required
def acquisition_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = AssetAcquisitionForm(request.POST, tenant=tenant)
        if form.is_valid():
            acq = form.save(commit=False)
            acq.tenant = tenant
            acq.acquisition_number = AssetAcquisition.generate_acquisition_number(tenant)
            acq.save()
            messages.success(request, f'Acquisition "{acq.acquisition_number}" created.')
            return redirect('fixed_assets:acquisition_list', tenant_slug=tenant.slug)
    else:
        form = AssetAcquisitionForm(tenant=tenant)

    return render(request, 'fixed_assets/acquisitions/acquisition_form.html', {
        'form': form,
    })


@login_required
def acquisition_capitalize(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    acq = get_object_or_404(AssetAcquisition.unscoped, pk=pk, tenant=tenant)
    if acq.is_capitalized:
        messages.warning(request, 'This acquisition is already capitalized.')
        return redirect('fixed_assets:acquisition_list', tenant_slug=tenant.slug)

    if request.method == 'POST':
        je = create_acquisition_journal_entry(acq, tenant, request.user)
        acq.is_capitalized = True
        acq.capitalization_date = timezone.now().date()
        acq.journal_entry = je
        acq.save(update_fields=['is_capitalized', 'capitalization_date', 'journal_entry', 'updated_at'])

        messages.success(request, f'Acquisition "{acq.acquisition_number}" capitalized. Journal entry {je.entry_number} created.')
        return redirect('fixed_assets:acquisition_list', tenant_slug=tenant.slug)

    return render(request, 'fixed_assets/acquisitions/acquisition_form.html', {
        'acq': acq, 'capitalize': True,
    })


# =============================================================================
# 5. Depreciation
# =============================================================================

@login_required
def depreciation_dashboard(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    entries = DepreciationEntry.objects.filter(tenant=tenant).order_by('-run_date')[:10]

    # Stats
    total_assets = Asset.objects.filter(tenant=tenant, status='in_service').count()
    total_accumulated = Asset.objects.filter(tenant=tenant, is_active=True).aggregate(
        total=Sum('accumulated_depreciation')
    )['total'] or Decimal('0.00')
    total_nbv = (Asset.objects.filter(tenant=tenant, is_active=True).aggregate(
        total=Sum('acquisition_cost')
    )['total'] or Decimal('0.00')) - total_accumulated

    unposted_count = DepreciationSchedule.objects.filter(
        tenant=tenant, is_posted=False
    ).count()

    return render(request, 'fixed_assets/depreciation/depreciation_dashboard.html', {
        'entries': entries,
        'total_assets': total_assets,
        'total_accumulated': total_accumulated,
        'total_nbv': total_nbv,
        'unposted_count': unposted_count,
    })


@login_required
def run_depreciation_view(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = RunDepreciationForm(request.POST, tenant=tenant)
        if form.is_valid():
            fiscal_period = form.cleaned_data['fiscal_period']
            entry = run_depreciation(tenant, fiscal_period, request.user)
            if entry:
                messages.success(
                    request,
                    f'Depreciation run {entry.entry_number} completed. '
                    f'{entry.asset_count} assets, total ${entry.total_amount:,.2f}'
                )
            else:
                messages.info(request, 'No unposted depreciation schedules found for this period.')
            return redirect('fixed_assets:depreciation_dashboard', tenant_slug=tenant.slug)
    else:
        form = RunDepreciationForm(tenant=tenant)

    return render(request, 'fixed_assets/depreciation/run_depreciation.html', {
        'form': form,
    })


# Alias for URL mapping
run_depreciation = run_depreciation_view


@login_required
def schedule_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    asset = get_object_or_404(Asset.unscoped, pk=pk, tenant=tenant)
    schedules = DepreciationSchedule.unscoped.filter(
        asset=asset
    ).order_by('period_number')

    return render(request, 'fixed_assets/depreciation/schedule_detail.html', {
        'asset': asset,
        'schedules': schedules,
    })


# =============================================================================
# 6. Asset Transfers
# =============================================================================

@login_required
def transfer_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = AssetTransfer.objects.filter(tenant=tenant).select_related(
        'asset', 'from_location', 'to_location'
    )

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(transfer_number__icontains=search) |
            Q(asset__asset_number__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'fixed_assets/transfers/transfer_list.html', {
        'transfers': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def transfer_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = AssetTransferForm(request.POST, tenant=tenant)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.tenant = tenant
            transfer.transfer_number = AssetTransfer.generate_transfer_number(tenant)
            transfer.created_by = request.user
            transfer.status = 'draft'
            transfer.save()
            messages.success(request, f'Transfer "{transfer.transfer_number}" created.')
            return redirect('fixed_assets:transfer_list', tenant_slug=tenant.slug)
    else:
        form = AssetTransferForm(tenant=tenant)

    return render(request, 'fixed_assets/transfers/transfer_form.html', {
        'form': form,
    })


@login_required
def transfer_approve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    transfer = get_object_or_404(AssetTransfer.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        transfer.status = 'pending'
        transfer.approved_by = request.user
        transfer.save(update_fields=['status', 'approved_by', 'updated_at'])
        messages.success(request, f'Transfer "{transfer.transfer_number}" approved.')

    return redirect('fixed_assets:transfer_list', tenant_slug=tenant.slug)


@login_required
def transfer_complete(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    transfer = get_object_or_404(AssetTransfer.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        # Update asset location and custodian
        asset = transfer.asset
        if transfer.to_location:
            asset.location = transfer.to_location
        if transfer.to_custodian:
            asset.custodian = transfer.to_custodian
        asset.save(update_fields=['location', 'custodian', 'updated_at'])

        transfer.status = 'completed'
        transfer.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Transfer "{transfer.transfer_number}" completed.')

    return redirect('fixed_assets:transfer_list', tenant_slug=tenant.slug)


# =============================================================================
# 7. Disposals
# =============================================================================

@login_required
def disposal_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = AssetDisposal.objects.filter(tenant=tenant).select_related('asset')

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(disposal_number__icontains=search) |
            Q(asset__asset_number__icontains=search)
        )

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    total_proceeds = qs.filter(status='completed').aggregate(
        total=Sum('proceeds')
    )['total'] or Decimal('0.00')
    total_gain_loss = qs.filter(status='completed').aggregate(
        total=Sum('gain_loss')
    )['total'] or Decimal('0.00')

    return render(request, 'fixed_assets/disposals/disposal_list.html', {
        'disposals': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'total_proceeds': total_proceeds,
        'total_gain_loss': total_gain_loss,
    })


@login_required
def disposal_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = AssetDisposalForm(request.POST, tenant=tenant)
        if form.is_valid():
            disposal = form.save(commit=False)
            disposal.tenant = tenant
            disposal.disposal_number = AssetDisposal.generate_disposal_number(tenant)
            disposal.created_by = request.user
            disposal.status = 'draft'
            disposal.net_book_value_at_disposal = disposal.asset.net_book_value
            disposal.save()
            messages.success(request, f'Disposal "{disposal.disposal_number}" created.')
            return redirect('fixed_assets:disposal_list', tenant_slug=tenant.slug)
    else:
        form = AssetDisposalForm(tenant=tenant)

    return render(request, 'fixed_assets/disposals/disposal_form.html', {
        'form': form,
    })


@login_required
def disposal_process(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    disposal = get_object_or_404(AssetDisposal.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST' and disposal.status == 'draft':
        # Create GL journal entry
        je = create_disposal_journal_entry(disposal, tenant, request.user)
        disposal.status = 'completed'
        disposal.approved_by = request.user
        disposal.journal_entry = je
        disposal.save(update_fields=['status', 'approved_by', 'journal_entry', 'updated_at'])

        # Update asset status
        asset = disposal.asset
        if disposal.disposal_type == 'write_off':
            asset.status = 'written_off'
        else:
            asset.status = 'disposed'
        asset.is_active = False
        asset.save(update_fields=['status', 'is_active', 'updated_at'])

        messages.success(
            request,
            f'Disposal "{disposal.disposal_number}" processed. '
            f'Gain/Loss: ${disposal.gain_loss:,.2f}. Journal entry {je.entry_number} created.'
        )

    return redirect('fixed_assets:disposal_list', tenant_slug=tenant.slug)


# =============================================================================
# 8. Impairment Testing
# =============================================================================

@login_required
def impairment_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ImpairmentTest.objects.filter(tenant=tenant).select_related('asset')

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    impaired_count = qs.filter(is_impaired=True).count()
    total_loss = qs.filter(is_impaired=True).aggregate(
        total=Sum('impairment_loss')
    )['total'] or Decimal('0.00')

    return render(request, 'fixed_assets/impairment/impairment_list.html', {
        'tests': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'impaired_count': impaired_count,
        'total_loss': total_loss,
    })


@login_required
def impairment_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ImpairmentTestForm(request.POST, tenant=tenant)
        if form.is_valid():
            test = form.save(commit=False)
            test.tenant = tenant
            test.created_by = request.user
            test.save()  # save triggers impairment calculation

            if test.is_impaired:
                je = create_impairment_journal_entry(test, tenant, request.user)
                test.journal_entry = je
                test.save(update_fields=['journal_entry'])

                # Update asset accumulated depreciation
                asset = test.asset
                asset.accumulated_depreciation += test.impairment_loss
                asset.save(update_fields=['accumulated_depreciation', 'updated_at'])

                messages.success(
                    request,
                    f'Impairment loss of ${test.impairment_loss:,.2f} recorded for {asset.asset_number}.'
                )
            else:
                messages.info(request, 'No impairment detected. Asset is not impaired.')

            return redirect('fixed_assets:impairment_list', tenant_slug=tenant.slug)
    else:
        form = ImpairmentTestForm(tenant=tenant)

    return render(request, 'fixed_assets/impairment/impairment_form.html', {
        'form': form,
    })


# =============================================================================
# 9. Physical Inventory
# =============================================================================

@login_required
def inventory_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = PhysicalInventory.objects.filter(tenant=tenant).select_related('location', 'conducted_by')

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'fixed_assets/inventory/inventory_list.html', {
        'inventories': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def inventory_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = PhysicalInventoryForm(request.POST, tenant=tenant)
        if form.is_valid():
            inv = form.save(commit=False)
            inv.tenant = tenant
            inv.inventory_number = PhysicalInventory.generate_inventory_number(tenant)
            inv.conducted_by = request.user
            inv.save()

            # Auto-populate items from assets at that location
            if inv.location:
                assets = Asset.unscoped.filter(
                    tenant=tenant, location=inv.location, is_active=True
                )
            else:
                assets = Asset.unscoped.filter(tenant=tenant, is_active=True)

            items = []
            for asset in assets:
                items.append(PhysicalInventoryItem(
                    inventory=inv,
                    asset=asset,
                    expected_location=asset.location,
                ))
            PhysicalInventoryItem.objects.bulk_create(items)

            inv.status = 'in_progress'
            inv.save(update_fields=['status'])

            messages.success(
                request,
                f'Inventory "{inv.inventory_number}" created with {len(items)} items.'
            )
            return redirect('fixed_assets:inventory_count', tenant_slug=tenant.slug, pk=inv.pk)
    else:
        form = PhysicalInventoryForm(tenant=tenant)

    return render(request, 'fixed_assets/inventory/inventory_form.html', {
        'form': form,
    })


@login_required
def inventory_count(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    inv = get_object_or_404(PhysicalInventory.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        formset = PhysicalInventoryItemFormSet(request.POST, instance=inv)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Inventory count updated.')
            return redirect('fixed_assets:inventory_count', tenant_slug=tenant.slug, pk=inv.pk)
    else:
        formset = PhysicalInventoryItemFormSet(instance=inv)

    items = inv.items.select_related('asset', 'expected_location', 'found_location').all()

    return render(request, 'fixed_assets/inventory/inventory_count.html', {
        'inventory': inv,
        'formset': formset,
        'items': items,
    })


@login_required
def inventory_reconcile(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    inv = get_object_or_404(PhysicalInventory.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        inv.status = 'reconciled'
        inv.save(update_fields=['status', 'updated_at'])

        # Update asset locations based on found_location
        for item in inv.items.filter(is_found=True, found_location__isnull=False):
            if item.found_location != item.expected_location:
                item.asset.location = item.found_location
                item.asset.save(update_fields=['location', 'updated_at'])

        messages.success(request, f'Inventory "{inv.inventory_number}" reconciled.')

    return redirect('fixed_assets:inventory_list', tenant_slug=tenant.slug)


# =============================================================================
# 10. Tax Depreciation
# =============================================================================

@login_required
def tax_book_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TaxDepreciationBook.objects.filter(tenant=tenant)

    return render(request, 'fixed_assets/tax_depreciation/tax_book_list.html', {
        'books': qs,
        'total_count': qs.count(),
    })


@login_required
def tax_book_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TaxDepreciationBookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            book.tenant = tenant
            book.save()
            messages.success(request, f'Tax book "{book.name}" created.')
            return redirect('fixed_assets:tax_book_list', tenant_slug=tenant.slug)
    else:
        form = TaxDepreciationBookForm()

    return render(request, 'fixed_assets/tax_depreciation/tax_book_list.html', {
        'form': form, 'show_form': True,
        'books': TaxDepreciationBook.objects.filter(tenant=tenant),
        'total_count': TaxDepreciationBook.objects.filter(tenant=tenant).count(),
    })


@login_required
def tax_book_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    book = get_object_or_404(TaxDepreciationBook.unscoped, pk=pk, tenant=tenant)
    entries = TaxDepreciationEntry.unscoped.filter(
        tax_book=book
    ).select_related('asset').order_by('asset__asset_number', 'fiscal_year')

    return render(request, 'fixed_assets/tax_depreciation/tax_book_detail.html', {
        'book': book,
        'entries': entries,
    })


@login_required
def tax_entry_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TaxDepreciationEntryForm(request.POST, tenant=tenant)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.tenant = tenant
            entry.save()
            messages.success(request, 'Tax depreciation entry created.')
            return redirect('fixed_assets:tax_book_detail', tenant_slug=tenant.slug, pk=entry.tax_book.pk)
    else:
        form = TaxDepreciationEntryForm(tenant=tenant)

    return render(request, 'fixed_assets/tax_depreciation/tax_book_detail.html', {
        'form': form, 'show_form': True,
        'book': None,
        'entries': [],
    })


# =============================================================================
# Helpers
# =============================================================================

def _add_months(d, months):
    """Add months to a date."""
    import datetime
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                       31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return datetime.date(year, month, day)
