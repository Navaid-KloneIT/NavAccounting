from django.contrib import admin

from .models import (
    AssetCategory, AssetLocation, Asset, AssetAcquisition,
    DepreciationProfile, DepreciationSchedule, DepreciationEntry,
    AssetTransfer, AssetDisposal, ImpairmentTest,
    PhysicalInventory, PhysicalInventoryItem,
    TaxDepreciationBook, TaxDepreciationEntry,
)


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'depreciation_method', 'default_useful_life_months', 'is_active', 'tenant')
    list_filter = ('depreciation_method', 'is_active', 'tenant')
    search_fields = ('code', 'name')


@admin.register(AssetLocation)
class AssetLocationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('code', 'name')


class DepreciationProfileInline(admin.StackedInline):
    model = DepreciationProfile
    extra = 0


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('asset_number', 'name', 'category', 'status', 'acquisition_cost', 'net_book_value', 'tenant')
    list_filter = ('status', 'category', 'depreciation_method', 'is_active', 'tenant')
    search_fields = ('asset_number', 'name', 'serial_number', 'barcode')
    inlines = [DepreciationProfileInline]


@admin.register(AssetAcquisition)
class AssetAcquisitionAdmin(admin.ModelAdmin):
    list_display = ('acquisition_number', 'asset', 'acquisition_type', 'amount', 'is_capitalized', 'tenant')
    list_filter = ('acquisition_type', 'is_capitalized', 'tenant')
    search_fields = ('acquisition_number', 'vendor_name', 'invoice_reference')


@admin.register(DepreciationSchedule)
class DepreciationScheduleAdmin(admin.ModelAdmin):
    list_display = ('asset', 'period_number', 'period_start', 'period_end', 'depreciation_amount', 'is_posted', 'tenant')
    list_filter = ('is_posted', 'tenant')
    search_fields = ('asset__asset_number',)


@admin.register(DepreciationEntry)
class DepreciationEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_number', 'run_date', 'total_amount', 'asset_count', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('entry_number',)


@admin.register(AssetTransfer)
class AssetTransferAdmin(admin.ModelAdmin):
    list_display = ('transfer_number', 'asset', 'from_location', 'to_location', 'transfer_date', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('transfer_number', 'asset__asset_number')


@admin.register(AssetDisposal)
class AssetDisposalAdmin(admin.ModelAdmin):
    list_display = ('disposal_number', 'asset', 'disposal_type', 'proceeds', 'gain_loss', 'status', 'tenant')
    list_filter = ('disposal_type', 'status', 'tenant')
    search_fields = ('disposal_number', 'asset__asset_number')


@admin.register(ImpairmentTest)
class ImpairmentTestAdmin(admin.ModelAdmin):
    list_display = ('asset', 'test_date', 'carrying_amount', 'recoverable_amount', 'impairment_loss', 'is_impaired', 'tenant')
    list_filter = ('is_impaired', 'tenant')
    search_fields = ('asset__asset_number',)


class PhysicalInventoryItemInline(admin.TabularInline):
    model = PhysicalInventoryItem
    extra = 1


@admin.register(PhysicalInventory)
class PhysicalInventoryAdmin(admin.ModelAdmin):
    list_display = ('inventory_number', 'name', 'location', 'count_date', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('inventory_number', 'name')
    inlines = [PhysicalInventoryItemInline]


@admin.register(TaxDepreciationBook)
class TaxDepreciationBookAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'tax_method', 'is_active', 'tenant')
    list_filter = ('tax_method', 'is_active', 'tenant')
    search_fields = ('code', 'name')


@admin.register(TaxDepreciationEntry)
class TaxDepreciationEntryAdmin(admin.ModelAdmin):
    list_display = ('asset', 'tax_book', 'fiscal_year', 'depreciation_amount', 'accumulated_depreciation', 'tenant')
    list_filter = ('tax_book', 'fiscal_year', 'tenant')
    search_fields = ('asset__asset_number',)
