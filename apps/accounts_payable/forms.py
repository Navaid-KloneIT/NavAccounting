from django import forms
from django.forms import inlineformset_factory

from apps.general_ledger.models import Account

from .models import (
    PaymentTerm, Vendor, VendorContact,
    Bill, BillLine, BillApproval, BillUpload,
    Payment, PaymentAllocation, PaymentBatch,
    ScheduledPayment, VendorMessage,
)


# =============================================================================
# Payment Term Forms
# =============================================================================

class PaymentTermForm(forms.ModelForm):
    class Meta:
        model = PaymentTerm
        exclude = ['tenant', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. Net 30'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. NET30'
            }),
            'due_days': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'discount_days': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =============================================================================
# Vendor Forms
# =============================================================================

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        exclude = ['tenant', 'created_at', 'updated_at', 'vendor_number']
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Legal company name'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Display name'
            }),
            'vendor_type': forms.Select(attrs={'class': 'form-select'}),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'EIN or SSN'
            }),
            'is_1099_eligible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'w9_on_file': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'w9_received_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'address_line_1': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Street address'
            }),
            'address_line_2': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Suite, unit, etc.'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'State'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'ZIP code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Country'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'email@example.com'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control', 'placeholder': 'https://'
            }),
            'default_payment_term': forms.Select(attrs={'class': 'form-select'}),
            'default_expense_account': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'preferred_payment_method': forms.Select(attrs={'class': 'form-select'}),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Bank name'
            }),
            'bank_account_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Account number'
            }),
            'bank_routing_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Routing number'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['default_payment_term'].queryset = PaymentTerm.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['default_expense_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )


class VendorContactForm(forms.ModelForm):
    class Meta:
        model = VendorContact
        fields = ['first_name', 'last_name', 'title', 'email', 'phone', 'is_primary']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Last name'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Job title'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Phone'
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


VendorContactFormSet = inlineformset_factory(
    Vendor, VendorContact,
    form=VendorContactForm,
    extra=2,
    can_delete=True,
)


# =============================================================================
# Bill Forms
# =============================================================================

class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = [
            'vendor', 'vendor_invoice_number', 'bill_date', 'due_date',
            'received_date', 'payment_term', 'currency', 'exchange_rate',
            'ap_account', 'fiscal_period', 'po_reference', 'receipt_reference',
            'description', 'notes',
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'vendor_invoice_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': "Vendor's invoice number"
            }),
            'bill_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'received_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'payment_term': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.00000001'
            }),
            'ap_account': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'po_reference': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'PO reference (optional)'
            }),
            'receipt_reference': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Receipt reference (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'placeholder': 'Bill description'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Internal notes'
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalPeriod
            self.fields['vendor'].queryset = Vendor.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['payment_term'].queryset = PaymentTerm.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['ap_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='LIABILITY'
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


class BillLineForm(forms.ModelForm):
    class Meta:
        model = BillLine
        fields = ['account', 'description', 'quantity', 'unit_price', 'amount', 'tax_amount']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Line description'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.0001', 'min': '0'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0', 'readonly': 'readonly'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )


BillLineFormSet = inlineformset_factory(
    Bill, BillLine,
    form=BillLineForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class BillApprovalActionForm(forms.Form):
    """Form for approval/rejection comments."""
    comments = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'Enter comments...'
        }),
        required=False,
    )


# =============================================================================
# Bill Capture Forms
# =============================================================================

class BillUploadForm(forms.Form):
    """File upload form for bill capture."""
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control', 'accept': '.pdf,.png,.jpg,.jpeg,.tiff'
        }),
        help_text='Upload PDF or image files (PDF, PNG, JPG, TIFF)'
    )


# =============================================================================
# Payment Forms
# =============================================================================

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'vendor', 'payment_date', 'amount', 'currency', 'exchange_rate',
            'payment_method', 'check_number', 'reference',
            'bank_account', 'ap_account', 'fiscal_period', 'memo',
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.00000001'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'check_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Check number (if applicable)'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'ACH/Wire reference'
            }),
            'bank_account': forms.Select(attrs={'class': 'form-select'}),
            'ap_account': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'memo': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Payment memo'
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalPeriod
            self.fields['vendor'].queryset = Vendor.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['bank_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='ASSET'
            )
            self.fields['ap_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='LIABILITY'
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


class PaymentAllocationForm(forms.ModelForm):
    class Meta:
        model = PaymentAllocation
        fields = ['bill', 'amount', 'discount_taken']
        widgets = {
            'bill': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'discount_taken': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
        }


PaymentAllocationFormSet = inlineformset_factory(
    Payment, PaymentAllocation,
    form=PaymentAllocationForm,
    extra=5,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class PaymentBatchForm(forms.ModelForm):
    class Meta:
        model = PaymentBatch
        fields = ['description', 'payment_date', 'payment_method', 'bank_account']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Batch description'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'bank_account': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['bank_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='ASSET'
            )


# =============================================================================
# Payment Scheduling Forms
# =============================================================================

class ScheduledPaymentForm(forms.ModelForm):
    class Meta:
        model = ScheduledPayment
        fields = ['bill', 'scheduled_date', 'amount', 'priority', 'notes']
        widgets = {
            'bill': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['bill'].queryset = Bill.unscoped.filter(
                tenant=tenant, status__in=['approved', 'partially_paid']
            )


# =============================================================================
# Aging Report Filter
# =============================================================================

class AgingReportFilterForm(forms.Form):
    """Filter form for aging reports."""
    as_of_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    vendor = forms.ModelChoiceField(
        required=False,
        queryset=Vendor.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['vendor'].queryset = Vendor.unscoped.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# Vendor Portal Forms
# =============================================================================

class PortalLoginForm(forms.Form):
    """Token-based login for vendor portal."""
    token = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your access token'
        }),
    )


class PortalMessageForm(forms.Form):
    """Message form for vendor portal."""
    subject = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Subject'
        }),
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 5, 'placeholder': 'Your message...'
        }),
    )
