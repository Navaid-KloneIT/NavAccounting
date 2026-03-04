from django.contrib import admin

from .models import (
    Customer, CustomerContact,
    Invoice, InvoiceLine, InvoiceApproval,
    Receipt, ReceiptAllocation,
    RecurringInvoiceTemplate, RecurringInvoiceTemplateLine,
    CreditMemo, CollectionActivity, WriteOff,
    CustomerPortalToken, CustomerMessage,
)


class CustomerContactInline(admin.TabularInline):
    model = CustomerContact
    extra = 1


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 2


class ReceiptAllocationInline(admin.TabularInline):
    model = ReceiptAllocation
    extra = 1


class RecurringInvoiceTemplateLineInline(admin.TabularInline):
    model = RecurringInvoiceTemplateLine
    extra = 2


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_number', 'company_name', 'display_name', 'customer_type',
                    'is_active', 'credit_hold', 'tenant')
    list_filter = ('customer_type', 'is_active', 'credit_hold', 'tenant')
    search_fields = ('customer_number', 'company_name', 'display_name', 'tax_id')
    inlines = [CustomerContactInline]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'invoice_date', 'due_date',
                    'total_amount', 'amount_paid', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('invoice_number', 'description', 'po_number')
    inlines = [InvoiceLineInline]


@admin.register(InvoiceApproval)
class InvoiceApprovalAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'approver', 'status', 'approved_at', 'tenant')
    list_filter = ('status', 'tenant')


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'customer', 'receipt_date', 'amount',
                    'payment_method', 'status', 'tenant')
    list_filter = ('status', 'payment_method', 'tenant')
    search_fields = ('receipt_number', 'reference', 'check_number')
    inlines = [ReceiptAllocationInline]


@admin.register(RecurringInvoiceTemplate)
class RecurringInvoiceTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_number', 'name', 'customer', 'frequency', 'status',
                    'next_invoice_date', 'occurrences_created', 'tenant')
    list_filter = ('status', 'frequency', 'tenant')
    search_fields = ('template_number', 'name')
    inlines = [RecurringInvoiceTemplateLineInline]


@admin.register(CreditMemo)
class CreditMemoAdmin(admin.ModelAdmin):
    list_display = ('memo_number', 'customer', 'memo_date', 'amount', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('memo_number',)


@admin.register(CollectionActivity)
class CollectionActivityAdmin(admin.ModelAdmin):
    list_display = ('customer', 'activity_type', 'dunning_level', 'subject',
                    'is_resolved', 'created_at', 'tenant')
    list_filter = ('activity_type', 'dunning_level', 'is_resolved', 'tenant')
    search_fields = ('subject', 'description')


@admin.register(WriteOff)
class WriteOffAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'write_off_date', 'amount', 'status', 'tenant')
    list_filter = ('status', 'tenant')


@admin.register(CustomerPortalToken)
class CustomerPortalTokenAdmin(admin.ModelAdmin):
    list_display = ('customer', 'is_active', 'last_accessed', 'expires_at', 'tenant')
    list_filter = ('is_active', 'tenant')


@admin.register(CustomerMessage)
class CustomerMessageAdmin(admin.ModelAdmin):
    list_display = ('customer', 'subject', 'is_from_customer', 'is_read',
                    'created_at', 'tenant')
    list_filter = ('is_from_customer', 'is_read', 'tenant')
    search_fields = ('subject', 'body')
