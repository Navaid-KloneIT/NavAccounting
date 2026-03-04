from django import forms
from django.forms import inlineformset_factory

from apps.general_ledger.models import Account

from .models import (
    Customer, CustomerContact,
    Invoice, InvoiceLine, InvoiceApproval,
    Receipt, ReceiptAllocation,
    RecurringInvoiceTemplate, RecurringInvoiceTemplateLine,
    CreditMemo, CollectionActivity, WriteOff,
    CustomerMessage,
)


# =============================================================================
# Customer Forms
# =============================================================================

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        exclude = ['tenant', 'created_at', 'updated_at', 'customer_number',
                    'credit_hold', 'credit_hold_reason']
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Legal company name'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Display name'
            }),
            'customer_type': forms.Select(attrs={'class': 'form-select'}),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Tax ID / EIN'
            }),
            'tax_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tax_exemption_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Exemption certificate number'
            }),
            # Billing address
            'billing_address_line_1': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Street address'
            }),
            'billing_address_line_2': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Suite, unit, etc.'
            }),
            'billing_city': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'City'
            }),
            'billing_state': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'State'
            }),
            'billing_postal_code': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'ZIP code'
            }),
            'billing_country': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Country'
            }),
            # Shipping address
            'shipping_address_line_1': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Street address'
            }),
            'shipping_address_line_2': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Suite, unit, etc.'
            }),
            'shipping_city': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'City'
            }),
            'shipping_state': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'State'
            }),
            'shipping_postal_code': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'ZIP code'
            }),
            'shipping_country': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Country'
            }),
            # Contact
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'email@example.com'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control', 'placeholder': 'https://'
            }),
            # Financial
            'default_payment_term': forms.Select(attrs={'class': 'form-select'}),
            'default_revenue_account': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'credit_rating': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. A, B, C'
            }),
            'preferred_payment_method': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.accounts_payable.models import PaymentTerm
            self.fields['default_payment_term'].queryset = PaymentTerm.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['default_revenue_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )


class CustomerContactForm(forms.ModelForm):
    class Meta:
        model = CustomerContact
        fields = ['first_name', 'last_name', 'title', 'email', 'phone',
                  'is_primary', 'is_billing_contact']
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
            'is_billing_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


CustomerContactFormSet = inlineformset_factory(
    Customer, CustomerContact,
    form=CustomerContactForm,
    extra=2,
    can_delete=True,
)


# =============================================================================
# Invoice Forms
# =============================================================================

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'customer', 'invoice_date', 'due_date', 'payment_term',
            'currency', 'exchange_rate', 'ar_account', 'fiscal_period',
            'po_number', 'so_reference', 'description', 'notes', 'internal_notes',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'invoice_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'payment_term': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.00000001'
            }),
            'ar_account': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'po_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Customer PO number (optional)'
            }),
            'so_reference': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Sales order reference (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'placeholder': 'Invoice description'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Notes for customer'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Internal notes'
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.accounts_payable.models import PaymentTerm
            from apps.company.models import FiscalPeriod
            self.fields['customer'].queryset = Customer.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['payment_term'].queryset = PaymentTerm.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['ar_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='ASSET'
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


class InvoiceLineForm(forms.ModelForm):
    class Meta:
        model = InvoiceLine
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


InvoiceLineFormSet = inlineformset_factory(
    Invoice, InvoiceLine,
    form=InvoiceLineForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class InvoiceApprovalActionForm(forms.Form):
    """Form for approval/rejection comments."""
    comments = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'Enter comments...'
        }),
        required=False,
    )


# =============================================================================
# Receipt Forms
# =============================================================================

class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = [
            'customer', 'receipt_date', 'amount', 'discount_given',
            'currency', 'exchange_rate', 'payment_method', 'check_number',
            'reference', 'bank_account', 'ar_account', 'fiscal_period', 'memo',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'receipt_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'discount_given': forms.NumberInput(attrs={
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
                'class': 'form-control', 'placeholder': 'Transaction reference'
            }),
            'bank_account': forms.Select(attrs={'class': 'form-select'}),
            'ar_account': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
            'memo': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Receipt memo'
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalPeriod
            self.fields['customer'].queryset = Customer.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['bank_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='ASSET'
            )
            self.fields['ar_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='ASSET'
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


class ReceiptAllocationForm(forms.ModelForm):
    class Meta:
        model = ReceiptAllocation
        fields = ['invoice', 'amount', 'discount_given']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'discount_given': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
        }


ReceiptAllocationFormSet = inlineformset_factory(
    Receipt, ReceiptAllocation,
    form=ReceiptAllocationForm,
    extra=5,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


# =============================================================================
# Recurring Invoice Forms
# =============================================================================

class RecurringInvoiceTemplateForm(forms.ModelForm):
    class Meta:
        model = RecurringInvoiceTemplate
        fields = [
            'name', 'customer', 'frequency', 'start_date', 'end_date',
            'next_invoice_date', 'occurrences_limit', 'payment_term',
            'ar_account', 'currency', 'description', 'auto_send',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Template name'
            }),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'next_invoice_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'occurrences_limit': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0',
                'placeholder': '0 = unlimited'
            }),
            'payment_term': forms.Select(attrs={'class': 'form-select'}),
            'ar_account': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
            'auto_send': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.accounts_payable.models import PaymentTerm
            self.fields['customer'].queryset = Customer.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['payment_term'].queryset = PaymentTerm.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['ar_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='ASSET'
            )


class RecurringInvoiceTemplateLineForm(forms.ModelForm):
    class Meta:
        model = RecurringInvoiceTemplateLine
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


RecurringInvoiceTemplateLineFormSet = inlineformset_factory(
    RecurringInvoiceTemplate, RecurringInvoiceTemplateLine,
    form=RecurringInvoiceTemplateLineForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


# =============================================================================
# Credit Memo Forms
# =============================================================================

class CreditMemoForm(forms.ModelForm):
    class Meta:
        model = CreditMemo
        fields = [
            'customer', 'invoice', 'memo_date', 'amount', 'reason',
            'ar_account', 'fiscal_period',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'memo_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for credit memo'
            }),
            'ar_account': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalPeriod
            self.fields['customer'].queryset = Customer.unscoped.filter(
                tenant=tenant, is_active=True
            )
            self.fields['invoice'].queryset = Invoice.unscoped.filter(
                tenant=tenant
            ).exclude(status__in=['draft', 'void', 'written_off'])
            self.fields['ar_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='ASSET'
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


# =============================================================================
# Collection Forms
# =============================================================================

class CollectionActivityForm(forms.ModelForm):
    class Meta:
        model = CollectionActivity
        fields = [
            'invoice', 'activity_type', 'dunning_level', 'subject',
            'description', 'contact_person', 'follow_up_date',
            'promise_date', 'promise_amount', 'is_resolved',
        ]
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'dunning_level': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Activity subject'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Contact person'
            }),
            'follow_up_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'promise_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'promise_amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, tenant=None, customer=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant and customer:
            self.fields['invoice'].queryset = Invoice.unscoped.filter(
                tenant=tenant, customer=customer
            ).exclude(status__in=['draft', 'paid', 'void', 'written_off'])


# =============================================================================
# Write-Off Forms
# =============================================================================

class WriteOffForm(forms.ModelForm):
    class Meta:
        model = WriteOff
        fields = ['write_off_date', 'amount', 'reason', 'bad_debt_account',
                  'ar_account', 'fiscal_period']
        widgets = {
            'write_off_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for write-off'
            }),
            'bad_debt_account': forms.Select(attrs={'class': 'form-select'}),
            'ar_account': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_period': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from apps.company.models import FiscalPeriod
            self.fields['bad_debt_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='EXPENSE'
            )
            self.fields['ar_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='ASSET'
            )
            self.fields['fiscal_period'].queryset = FiscalPeriod.unscoped.filter(
                tenant=tenant, is_closed=False
            )


# =============================================================================
# Aging Report Filter
# =============================================================================

class ARAgingReportFilterForm(forms.Form):
    """Filter form for AR aging reports."""
    as_of_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    customer = forms.ModelChoiceField(
        required=False,
        queryset=Customer.unscoped.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['customer'].queryset = Customer.unscoped.filter(
                tenant=tenant, is_active=True
            )


# =============================================================================
# Customer Portal Forms
# =============================================================================

class CustomerPortalLoginForm(forms.Form):
    """Token-based login for customer portal."""
    token = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your access token'
        }),
    )


class CustomerPortalMessageForm(forms.Form):
    """Message form for customer portal."""
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
