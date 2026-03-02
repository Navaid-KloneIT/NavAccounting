from django.contrib import admin

from .models import (
    PaymentTerm, Vendor, VendorContact,
    Bill, BillLine, BillApproval, BillUpload,
    Payment, PaymentAllocation, PaymentBatch,
    ScheduledPayment, VendorPortalToken, VendorMessage,
)


class VendorContactInline(admin.TabularInline):
    model = VendorContact
    extra = 1


class BillLineInline(admin.TabularInline):
    model = BillLine
    extra = 2


class PaymentAllocationInline(admin.TabularInline):
    model = PaymentAllocation
    extra = 1


@admin.register(PaymentTerm)
class PaymentTermAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'due_days', 'discount_percentage', 'discount_days', 'is_active', 'tenant')
    list_filter = ('is_active', 'tenant')
    search_fields = ('name', 'code')


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('vendor_number', 'company_name', 'display_name', 'vendor_type', 'is_active', 'is_1099_eligible', 'tenant')
    list_filter = ('vendor_type', 'is_active', 'is_1099_eligible', 'tenant')
    search_fields = ('vendor_number', 'company_name', 'display_name', 'tax_id')
    inlines = [VendorContactInline]


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'vendor', 'bill_date', 'due_date', 'total_amount', 'amount_paid', 'status', 'tenant')
    list_filter = ('status', 'tenant')
    search_fields = ('bill_number', 'vendor_invoice_number', 'description')
    inlines = [BillLineInline]


@admin.register(BillApproval)
class BillApprovalAdmin(admin.ModelAdmin):
    list_display = ('bill', 'approver', 'status', 'approved_at', 'tenant')
    list_filter = ('status', 'tenant')


@admin.register(BillUpload)
class BillUploadAdmin(admin.ModelAdmin):
    list_display = ('upload_number', 'original_filename', 'ocr_status', 'bill', 'uploaded_by', 'tenant')
    list_filter = ('ocr_status', 'tenant')
    search_fields = ('upload_number', 'original_filename')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'vendor', 'payment_date', 'amount', 'payment_method', 'status', 'tenant')
    list_filter = ('status', 'payment_method', 'tenant')
    search_fields = ('payment_number', 'reference', 'check_number')
    inlines = [PaymentAllocationInline]


@admin.register(PaymentBatch)
class PaymentBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'description', 'payment_date', 'payment_method', 'status', 'total_amount', 'payment_count', 'tenant')
    list_filter = ('status', 'payment_method', 'tenant')
    search_fields = ('batch_number', 'description')


@admin.register(ScheduledPayment)
class ScheduledPaymentAdmin(admin.ModelAdmin):
    list_display = ('bill', 'scheduled_date', 'amount', 'priority', 'status', 'tenant')
    list_filter = ('status', 'priority', 'tenant')


@admin.register(VendorPortalToken)
class VendorPortalTokenAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'is_active', 'last_accessed', 'expires_at', 'tenant')
    list_filter = ('is_active', 'tenant')


@admin.register(VendorMessage)
class VendorMessageAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'subject', 'is_from_vendor', 'is_read', 'created_at', 'tenant')
    list_filter = ('is_from_vendor', 'is_read', 'tenant')
    search_fields = ('subject', 'body')
