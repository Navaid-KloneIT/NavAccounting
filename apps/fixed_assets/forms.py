from django import forms
from django.forms import inlineformset_factory

from apps.general_ledger.models import Account

from .models import (
    AssetCategory, AssetLocation, Asset, AssetAcquisition,
    DepreciationProfile, DepreciationSchedule, DepreciationEntry,
    AssetTransfer, AssetDisposal, ImpairmentTest,
    PhysicalInventory, PhysicalInventoryItem,
    TaxDepreciationBook, TaxDepreciationEntry,
)


# =============================================================================
# 1. Asset Register Forms
# =============================================================================

class AssetCategoryForm(forms.ModelForm):
    class Meta:
        model = AssetCategory
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'depreciation_method': forms.Select(attrs={'class': 'form-select'}),
            'default_useful_life_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'default_salvage_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'asset_gl_account': forms.Select(attrs={'class': 'form-select'}),
            'depreciation_gl_account': forms.Select(attrs={'class': 'form-select'}),
            'accumulated_depreciation_gl_account': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            gl_qs = Account.unscoped.filter(tenant=tenant, is_active=True, is_header=False)
            self.fields['asset_gl_account'].queryset = gl_qs
            self.fields['depreciation_gl_account'].queryset = gl_qs
            self.fields['accumulated_depreciation_gl_account'].queryset = gl_qs


class AssetLocationForm(forms.ModelForm):
    class Meta:
        model = AssetLocation
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        exclude = ['tenant', 'created_at', 'updated_at', 'asset_number', 'accumulated_depreciation']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'custodian': forms.Select(attrs={'class': 'form-select'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'tag_number': forms.TextInput(attrs={'class': 'form-control'}),
            'acquisition_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'acquisition_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'salvage_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'useful_life_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'depreciation_method': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'warranty_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = AssetCategory.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['location'].queryset = AssetLocation.unscoped.filter(
                tenant=tenant, is_active=True
            )
            from apps.accounts.models import CustomUser
            from apps.tenants.models import TenantMembership
            member_ids = TenantMembership.objects.filter(
                tenant=tenant
            ).values_list('user_id', flat=True)
            self.fields['custodian'].queryset = CustomUser.objects.filter(id__in=member_ids)


class AssetFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Search assets...'
        })
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=AssetCategory.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Categories'
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Asset.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    location = forms.ModelChoiceField(
        required=False,
        queryset=AssetLocation.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Locations'
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = AssetCategory.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['location'].queryset = AssetLocation.unscoped.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# 2. Acquisition Forms
# =============================================================================

class AssetAcquisitionForm(forms.ModelForm):
    class Meta:
        model = AssetAcquisition
        exclude = ['tenant', 'created_at', 'updated_at', 'acquisition_number',
                    'is_capitalized', 'capitalization_date', 'journal_entry']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'acquisition_type': forms.Select(attrs={'class': 'form-select'}),
            'vendor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_order': forms.TextInput(attrs={'class': 'form-control'}),
            'acquisition_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['asset'].queryset = Asset.unscoped.filter(
                tenant=tenant, is_active=True
            )
            from apps.company.models import Currency
            self.fields['currency'].queryset = Currency.objects.all()


# =============================================================================
# 3. Depreciation Forms
# =============================================================================

class DepreciationProfileForm(forms.ModelForm):
    class Meta:
        model = DepreciationProfile
        exclude = ['tenant', 'created_at', 'updated_at', 'asset']
        widgets = {
            'method': forms.Select(attrs={'class': 'form-select'}),
            'useful_life_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salvage_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_units': forms.NumberInput(attrs={'class': 'form-control'}),
            'declining_balance_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class RunDepreciationForm(forms.Form):
    fiscal_period = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Select Fiscal Period'
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalPeriod
            self.fields['fiscal_period'].queryset = FiscalPeriod.objects.filter(
                fiscal_year__tenant=tenant, is_closed=False
            ).order_by('-period_number')


# =============================================================================
# 4. Transfer Forms
# =============================================================================

class AssetTransferForm(forms.ModelForm):
    class Meta:
        model = AssetTransfer
        exclude = ['tenant', 'created_at', 'updated_at', 'transfer_number',
                    'created_by', 'approved_by', 'status']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'from_location': forms.Select(attrs={'class': 'form-select'}),
            'to_location': forms.Select(attrs={'class': 'form-select'}),
            'from_department': forms.TextInput(attrs={'class': 'form-control'}),
            'to_department': forms.TextInput(attrs={'class': 'form-control'}),
            'from_custodian': forms.Select(attrs={'class': 'form-select'}),
            'to_custodian': forms.Select(attrs={'class': 'form-select'}),
            'transfer_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['asset'].queryset = Asset.unscoped.filter(
                tenant=tenant, is_active=True, status='in_service'
            )
            loc_qs = AssetLocation.unscoped.filter(tenant=tenant, is_active=True)
            self.fields['from_location'].queryset = loc_qs
            self.fields['to_location'].queryset = loc_qs
            from apps.accounts.models import CustomUser
            from apps.tenants.models import TenantMembership
            member_ids = TenantMembership.objects.filter(
                tenant=tenant
            ).values_list('user_id', flat=True)
            user_qs = CustomUser.objects.filter(id__in=member_ids)
            self.fields['from_custodian'].queryset = user_qs
            self.fields['to_custodian'].queryset = user_qs


# =============================================================================
# 5. Disposal Forms
# =============================================================================

class AssetDisposalForm(forms.ModelForm):
    class Meta:
        model = AssetDisposal
        exclude = ['tenant', 'created_at', 'updated_at', 'disposal_number',
                    'net_book_value_at_disposal', 'gain_loss', 'created_by',
                    'approved_by', 'journal_entry', 'status']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'disposal_type': forms.Select(attrs={'class': 'form-select'}),
            'disposal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'proceeds': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'buyer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['asset'].queryset = Asset.unscoped.filter(
                tenant=tenant, is_active=True
            ).exclude(status__in=['disposed', 'written_off'])


# =============================================================================
# 6. Impairment Forms
# =============================================================================

class ImpairmentTestForm(forms.ModelForm):
    class Meta:
        model = ImpairmentTest
        exclude = ['tenant', 'created_at', 'updated_at', 'recoverable_amount',
                    'impairment_loss', 'is_impaired', 'journal_entry', 'created_by']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'test_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'carrying_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'value_in_use': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fair_value_less_costs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['asset'].queryset = Asset.unscoped.filter(
                tenant=tenant, is_active=True, status='in_service'
            )


# =============================================================================
# 7. Physical Inventory Forms
# =============================================================================

class PhysicalInventoryForm(forms.ModelForm):
    class Meta:
        model = PhysicalInventory
        exclude = ['tenant', 'created_at', 'updated_at', 'inventory_number',
                    'conducted_by', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'count_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['location'].queryset = AssetLocation.unscoped.filter(
                tenant=tenant, is_active=True
            )


class PhysicalInventoryItemForm(forms.ModelForm):
    class Meta:
        model = PhysicalInventoryItem
        exclude = ['inventory']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'expected_location': forms.Select(attrs={'class': 'form-select'}),
            'found_location': forms.Select(attrs={'class': 'form-select'}),
            'is_found': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'scanned_barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


PhysicalInventoryItemFormSet = inlineformset_factory(
    PhysicalInventory, PhysicalInventoryItem,
    form=PhysicalInventoryItemForm,
    extra=5,
    can_delete=True,
)


# =============================================================================
# 8. Tax Depreciation Forms
# =============================================================================

class TaxDepreciationBookForm(forms.ModelForm):
    class Meta:
        model = TaxDepreciationBook
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_method': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TaxDepreciationEntryForm(forms.ModelForm):
    class Meta:
        model = TaxDepreciationEntry
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'tax_book': forms.Select(attrs={'class': 'form-select'}),
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'depreciation_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'accumulated_depreciation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'recovery_period_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'convention': forms.Select(attrs={'class': 'form-select'}),
            'property_class': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['tax_book'].queryset = TaxDepreciationBook.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['asset'].queryset = Asset.unscoped.filter(
                tenant=tenant, is_active=True
            )
