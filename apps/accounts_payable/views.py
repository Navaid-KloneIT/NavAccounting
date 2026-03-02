import csv
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.company.models import FiscalPeriod
from apps.tenants.managers import set_current_tenant

from .forms import (
    PaymentTermForm, VendorForm, VendorContactFormSet,
    BillForm, BillLineFormSet, BillApprovalActionForm,
    BillUploadForm,
    PaymentForm, PaymentAllocationFormSet, PaymentBatchForm,
    ScheduledPaymentForm, AgingReportFilterForm,
)
from .models import (
    PaymentTerm, Vendor, VendorContact,
    Bill, BillLine, BillApproval, BillUpload,
    Payment, PaymentAllocation, PaymentBatch,
    ScheduledPayment,
)


# =============================================================================
# 1. Vendor Management
# =============================================================================

@login_required
def vendor_list(request, tenant_slug):
    """List vendors with search, type filter, status filter, and stat cards."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = Vendor.objects.filter(tenant=tenant).select_related(
        'default_payment_term', 'default_expense_account', 'currency'
    )

    # Stats (computed before filtering)
    total_count = qs.count()
    active_count = qs.filter(is_active=True).count()
    inactive_count = qs.filter(is_active=False).count()
    eligible_1099_count = qs.filter(is_1099_eligible=True).count()

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(vendor_number__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(display_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Type filter
    type_filter = request.GET.get('type', '')
    if type_filter:
        qs = qs.filter(vendor_type=type_filter)

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_payable/vendors/vendor_list.html', {
        'vendors': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'eligible_1099_count': eligible_1099_count,
    })


@login_required
def vendor_create(request, tenant_slug):
    """Create a new vendor with contact formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = VendorForm(request.POST, tenant=tenant)
        formset = VendorContactFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            vendor = form.save(commit=False)
            vendor.tenant = tenant
            vendor.vendor_number = Vendor.generate_vendor_number(tenant)
            vendor.save()

            formset.instance = vendor
            formset.save()

            messages.success(request, f'Vendor "{vendor.display_name}" created.')
            return redirect('accounts_payable:vendor_detail',
                            tenant_slug=tenant_slug, pk=vendor.pk)
    else:
        form = VendorForm(tenant=tenant)
        formset = VendorContactFormSet()

    return render(request, 'accounts_payable/vendors/vendor_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Vendor',
    })


@login_required
def vendor_detail(request, tenant_slug, pk):
    """View vendor profile with recent bills and payments."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    vendor = get_object_or_404(
        Vendor.unscoped.select_related(
            'default_payment_term', 'default_expense_account', 'currency'
        ),
        pk=pk, tenant=tenant
    )
    contacts = vendor.contacts.all()
    recent_bills = Bill.unscoped.filter(
        vendor=vendor, tenant=tenant
    ).order_by('-bill_date')[:10]
    recent_payments = Payment.unscoped.filter(
        vendor=vendor, tenant=tenant
    ).order_by('-payment_date')[:10]

    return render(request, 'accounts_payable/vendors/vendor_detail.html', {
        'vendor': vendor,
        'contacts': contacts,
        'recent_bills': recent_bills,
        'recent_payments': recent_payments,
    })


@login_required
def vendor_edit(request, tenant_slug, pk):
    """Edit an existing vendor with contact formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    vendor = get_object_or_404(Vendor.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor, tenant=tenant)
        formset = VendorContactFormSet(request.POST, instance=vendor)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Vendor "{vendor.display_name}" updated.')
            return redirect('accounts_payable:vendor_detail',
                            tenant_slug=tenant_slug, pk=vendor.pk)
    else:
        form = VendorForm(instance=vendor, tenant=tenant)
        formset = VendorContactFormSet(instance=vendor)

    return render(request, 'accounts_payable/vendors/vendor_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit: {vendor.display_name}',
        'vendor': vendor,
    })


@login_required
def vendor_toggle_active(request, tenant_slug, pk):
    """Toggle vendor active status. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    vendor = get_object_or_404(Vendor.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        vendor.is_active = not vendor.is_active
        vendor.save()
        status_text = 'activated' if vendor.is_active else 'deactivated'
        messages.success(request, f'Vendor "{vendor.display_name}" {status_text}.')

    return redirect('accounts_payable:vendor_detail',
                    tenant_slug=tenant_slug, pk=vendor.pk)


# =============================================================================
# Payment Terms
# =============================================================================

@login_required
def payment_term_list(request, tenant_slug):
    """List payment terms with stats."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = PaymentTerm.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    active_count = qs.filter(is_active=True).count()

    return render(request, 'accounts_payable/vendors/payment_term_list.html', {
        'payment_terms': qs,
        'total_count': total_count,
        'active_count': active_count,
    })


@login_required
def payment_term_create(request, tenant_slug):
    """Create a new payment term."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = PaymentTermForm(request.POST)
        if form.is_valid():
            term = form.save(commit=False)
            term.tenant = tenant
            term.save()
            messages.success(request, f'Payment term "{term.name}" created.')
            return redirect('accounts_payable:payment_term_list',
                            tenant_slug=tenant_slug)
    else:
        form = PaymentTermForm()

    return render(request, 'accounts_payable/vendors/payment_term_form.html', {
        'form': form,
        'title': 'Create Payment Term',
    })


@login_required
def payment_term_edit(request, tenant_slug, pk):
    """Edit an existing payment term."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    term = get_object_or_404(PaymentTerm.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = PaymentTermForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            messages.success(request, f'Payment term "{term.name}" updated.')
            return redirect('accounts_payable:payment_term_list',
                            tenant_slug=tenant_slug)
    else:
        form = PaymentTermForm(instance=term)

    return render(request, 'accounts_payable/vendors/payment_term_form.html', {
        'form': form,
        'title': f'Edit: {term.name}',
    })


# =============================================================================
# 2. Bill Processing
# =============================================================================

@login_required
def bill_list(request, tenant_slug):
    """List bills with stat cards, search, and filters."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = Bill.objects.filter(tenant=tenant).select_related(
        'vendor', 'payment_term', 'currency', 'fiscal_period', 'created_by'
    )

    # Stats (computed before filtering)
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    pending_count = qs.filter(status='pending_approval').count()
    approved_count = qs.filter(status='approved').count()
    overdue_count = qs.filter(
        due_date__lt=timezone.now().date()
    ).exclude(status__in=['paid', 'void']).count()
    total_outstanding = qs.exclude(
        status__in=['draft', 'void']
    ).aggregate(
        outstanding=Sum(F('total_amount') - F('amount_paid'))
    )['outstanding'] or Decimal('0.00')

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(bill_number__icontains=search_query) |
            Q(vendor__display_name__icontains=search_query) |
            Q(vendor_invoice_number__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Vendor filter
    vendor_filter = request.GET.get('vendor', '')
    if vendor_filter:
        qs = qs.filter(vendor_id=vendor_filter)

    # Date range filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        qs = qs.filter(bill_date__gte=date_from)
    if date_to:
        qs = qs.filter(bill_date__lte=date_to)

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Vendors for filter dropdown
    vendors = Vendor.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'accounts_payable/bills/bill_list.html', {
        'bills': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'overdue_count': overdue_count,
        'total_outstanding': total_outstanding,
        'vendors': vendors,
    })


@login_required
def bill_create(request, tenant_slug):
    """Create a new bill with line formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = BillForm(request.POST, tenant=tenant)
        formset = BillLineFormSet(
            request.POST, form_kwargs={'tenant': tenant}
        )
        if form.is_valid() and formset.is_valid():
            bill = form.save(commit=False)
            bill.tenant = tenant
            bill.bill_number = Bill.generate_bill_number(tenant)
            bill.created_by = request.user
            bill.status = 'draft'
            bill.save()

            formset.instance = bill
            formset.save()

            bill.update_totals()
            bill.save()

            messages.success(request, f'Bill "{bill.bill_number}" created.')
            return redirect('accounts_payable:bill_detail',
                            tenant_slug=tenant_slug, pk=bill.pk)
    else:
        form = BillForm(tenant=tenant)
        formset = BillLineFormSet(form_kwargs={'tenant': tenant})

    return render(request, 'accounts_payable/bills/bill_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Bill',
    })


@login_required
def bill_detail(request, tenant_slug, pk):
    """View bill with lines, approval history, and payment history."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    bill = get_object_or_404(
        Bill.unscoped.select_related(
            'vendor', 'payment_term', 'currency', 'ap_account',
            'fiscal_period', 'created_by'
        ),
        pk=pk, tenant=tenant
    )
    lines = bill.lines.select_related('account')
    approvals = bill.approvals.select_related('approver').all()
    payment_allocations = bill.payment_allocations.select_related(
        'payment', 'payment__vendor'
    ).all()

    return render(request, 'accounts_payable/bills/bill_detail.html', {
        'bill': bill,
        'lines': lines,
        'approvals': approvals,
        'payment_allocations': payment_allocations,
    })


@login_required
def bill_edit(request, tenant_slug, pk):
    """Edit a draft bill with line formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    bill = get_object_or_404(Bill.unscoped, pk=pk, tenant=tenant)

    if bill.status != 'draft':
        messages.error(request, 'Only draft bills can be edited.')
        return redirect('accounts_payable:bill_detail',
                        tenant_slug=tenant_slug, pk=pk)

    if request.method == 'POST':
        form = BillForm(request.POST, instance=bill, tenant=tenant)
        formset = BillLineFormSet(
            request.POST, instance=bill, form_kwargs={'tenant': tenant}
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            bill.update_totals()
            bill.save()

            messages.success(request, f'Bill "{bill.bill_number}" updated.')
            return redirect('accounts_payable:bill_detail',
                            tenant_slug=tenant_slug, pk=pk)
    else:
        form = BillForm(instance=bill, tenant=tenant)
        formset = BillLineFormSet(
            instance=bill, form_kwargs={'tenant': tenant}
        )

    return render(request, 'accounts_payable/bills/bill_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit: {bill.bill_number}',
        'bill': bill,
    })


@login_required
def bill_submit(request, tenant_slug, pk):
    """Submit a bill for approval. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    bill = get_object_or_404(Bill.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if bill.status != 'draft':
            messages.error(request, 'Only draft bills can be submitted for approval.')
        else:
            bill.status = 'pending_approval'
            bill.save()

            BillApproval.objects.create(
                tenant=tenant,
                bill=bill,
                approver=request.user,
                status='pending',
            )
            messages.success(
                request,
                f'Bill "{bill.bill_number}" submitted for approval.'
            )

    return redirect('accounts_payable:bill_detail',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def bill_void(request, tenant_slug, pk):
    """Void a bill. POST only. Cannot void paid or already voided bills."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    bill = get_object_or_404(Bill.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if bill.status in ('paid', 'void'):
            messages.error(request, 'Cannot void a paid or already voided bill.')
        else:
            bill.status = 'void'
            bill.save()
            messages.success(request, f'Bill "{bill.bill_number}" has been voided.')

    return redirect('accounts_payable:bill_detail',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def bill_approval_queue(request, tenant_slug):
    """List bills pending approval."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = Bill.objects.filter(
        tenant=tenant, status='pending_approval'
    ).select_related('vendor', 'currency', 'created_by')

    pending_count = qs.count()

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_payable/bills/approval_queue.html', {
        'bills': page_obj,
        'page_obj': page_obj,
        'pending_count': pending_count,
    })


@login_required
def bill_approve(request, tenant_slug, pk):
    """Approve a bill. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    bill = get_object_or_404(Bill.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = BillApprovalActionForm(request.POST)
        if bill.status != 'pending_approval':
            messages.error(request, 'Only pending bills can be approved.')
        elif form.is_valid():
            comments = form.cleaned_data.get('comments', '')

            # Update or create approval record
            approval = bill.approvals.filter(status='pending').first()
            if approval:
                approval.status = 'approved'
                approval.comments = comments
                approval.approved_at = timezone.now()
                approval.approver = request.user
                approval.save()
            else:
                BillApproval.objects.create(
                    tenant=tenant,
                    bill=bill,
                    approver=request.user,
                    status='approved',
                    comments=comments,
                    approved_at=timezone.now(),
                )

            bill.status = 'approved'
            bill.save()
            messages.success(request, f'Bill "{bill.bill_number}" approved.')

    return redirect('accounts_payable:bill_approval_queue',
                    tenant_slug=tenant_slug)


@login_required
def bill_reject(request, tenant_slug, pk):
    """Reject a bill. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    bill = get_object_or_404(Bill.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = BillApprovalActionForm(request.POST)
        if bill.status != 'pending_approval':
            messages.error(request, 'Only pending bills can be rejected.')
        elif form.is_valid():
            comments = form.cleaned_data.get('comments', '')

            # Update or create approval record
            approval = bill.approvals.filter(status='pending').first()
            if approval:
                approval.status = 'rejected'
                approval.comments = comments
                approval.approved_at = timezone.now()
                approval.approver = request.user
                approval.save()
            else:
                BillApproval.objects.create(
                    tenant=tenant,
                    bill=bill,
                    approver=request.user,
                    status='rejected',
                    comments=comments,
                    approved_at=timezone.now(),
                )

            bill.status = 'draft'
            bill.save()
            messages.success(request, f'Bill "{bill.bill_number}" rejected.')

    return redirect('accounts_payable:bill_approval_queue',
                    tenant_slug=tenant_slug)


# =============================================================================
# 3. Payment Processing
# =============================================================================

@login_required
def payment_list(request, tenant_slug):
    """List payments with stats and filters."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = Payment.objects.filter(tenant=tenant).select_related(
        'vendor', 'currency', 'bank_account', 'created_by'
    )

    # Stats (computed before filtering)
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    completed_count = qs.filter(status='completed').count()
    void_count = qs.filter(status='void').count()
    total_amount = qs.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(payment_number__icontains=search_query) |
            Q(vendor__display_name__icontains=search_query) |
            Q(reference__icontains=search_query) |
            Q(check_number__icontains=search_query)
        )

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Vendor filter
    vendor_filter = request.GET.get('vendor', '')
    if vendor_filter:
        qs = qs.filter(vendor_id=vendor_filter)

    # Date range filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        qs = qs.filter(payment_date__gte=date_from)
    if date_to:
        qs = qs.filter(payment_date__lte=date_to)

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_payable/payments/payment_list.html', {
        'payments': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'completed_count': completed_count,
        'void_count': void_count,
        'total_amount': total_amount,
    })


@login_required
def payment_create(request, tenant_slug):
    """Create a new payment with allocation formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = PaymentForm(request.POST, tenant=tenant)
        formset = PaymentAllocationFormSet(
            request.POST, form_kwargs={'tenant': tenant}
        )
        if form.is_valid() and formset.is_valid():
            payment = form.save(commit=False)
            payment.tenant = tenant
            payment.payment_number = Payment.generate_payment_number(tenant)
            payment.created_by = request.user
            payment.status = 'draft'
            payment.save()

            formset.instance = payment
            formset.save()

            messages.success(
                request,
                f'Payment "{payment.payment_number}" created.'
            )
            return redirect('accounts_payable:payment_detail',
                            tenant_slug=tenant_slug, pk=payment.pk)
    else:
        form = PaymentForm(tenant=tenant)
        formset = PaymentAllocationFormSet(form_kwargs={'tenant': tenant})

    return render(request, 'accounts_payable/payments/payment_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Payment',
    })


@login_required
def payment_detail(request, tenant_slug, pk):
    """View payment with allocated bills and journal entry link."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    payment = get_object_or_404(
        Payment.unscoped.select_related(
            'vendor', 'currency', 'bank_account', 'ap_account',
            'journal_entry', 'fiscal_period', 'created_by', 'voided_by'
        ),
        pk=pk, tenant=tenant
    )
    allocations = payment.allocations.select_related('bill', 'bill__vendor')

    return render(request, 'accounts_payable/payments/payment_detail.html', {
        'payment': payment,
        'allocations': allocations,
    })


@login_required
def payment_complete(request, tenant_slug, pk):
    """Mark payment as completed, create GL journal entry, update bill balances. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    payment = get_object_or_404(Payment.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if payment.status not in ('draft', 'pending'):
            messages.error(request, 'Only draft or pending payments can be completed.')
        else:
            from .services import create_payment_journal_entry

            # Create GL journal entry
            je = create_payment_journal_entry(payment, request.user)
            payment.journal_entry = je
            payment.status = 'completed'
            payment.save()

            # Update bill amount_paid and status for each allocation
            for alloc in payment.allocations.select_related('bill'):
                bill = alloc.bill
                bill.amount_paid += alloc.amount
                bill.update_payment_status()
                bill.save()

            messages.success(
                request,
                f'Payment "{payment.payment_number}" completed.'
            )

    return redirect('accounts_payable:payment_detail',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def payment_void(request, tenant_slug, pk):
    """Void a completed payment, reverse bill balances, create reversal JE. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    payment = get_object_or_404(Payment.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if payment.status != 'completed':
            messages.error(request, 'Only completed payments can be voided.')
        else:
            from .services import create_void_journal_entry

            void_reason = request.POST.get('void_reason', '')

            # Create reversal JE
            create_void_journal_entry(payment, request.user)

            # Reverse bill amount_paid for each allocation
            for alloc in payment.allocations.select_related('bill'):
                bill = alloc.bill
                bill.amount_paid -= alloc.amount
                if bill.amount_paid < Decimal('0.00'):
                    bill.amount_paid = Decimal('0.00')
                bill.update_payment_status()
                # If bill was fully paid and is now reversed, set back to approved
                if bill.status == 'paid' and bill.amount_paid < bill.total_amount:
                    if bill.amount_paid > Decimal('0.00'):
                        bill.status = 'partially_paid'
                    else:
                        bill.status = 'approved'
                bill.save()

            payment.status = 'void'
            payment.voided_by = request.user
            payment.voided_at = timezone.now()
            payment.void_reason = void_reason
            payment.save()

            messages.success(
                request,
                f'Payment "{payment.payment_number}" voided.'
            )

    return redirect('accounts_payable:payment_detail',
                    tenant_slug=tenant_slug, pk=pk)


# =============================================================================
# Payment Batches
# =============================================================================

@login_required
def batch_list(request, tenant_slug):
    """List payment batches."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = PaymentBatch.objects.filter(tenant=tenant).select_related(
        'bank_account', 'created_by'
    )

    # Stats
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    completed_count = qs.filter(status='completed').count()

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_payable/payments/batch_list.html', {
        'batches': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'completed_count': completed_count,
    })


@login_required
def batch_create(request, tenant_slug):
    """Create a payment batch and select bills to include."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    # Get approved bills that can be paid
    approved_bills = Bill.objects.filter(
        tenant=tenant, status__in=['approved', 'partially_paid']
    ).select_related('vendor')

    if request.method == 'POST':
        form = PaymentBatchForm(request.POST, tenant=tenant)
        selected_bill_ids = request.POST.getlist('bills')

        if form.is_valid():
            batch = form.save(commit=False)
            batch.tenant = tenant
            batch.batch_number = PaymentBatch.generate_batch_number(tenant)
            batch.created_by = request.user
            batch.status = 'draft'
            batch.save()

            # Calculate totals from selected bills
            selected_bills = Bill.unscoped.filter(
                pk__in=selected_bill_ids, tenant=tenant
            )
            total = selected_bills.aggregate(
                total=Sum(F('total_amount') - F('amount_paid'))
            )['total'] or Decimal('0.00')
            batch.total_amount = total
            batch.payment_count = selected_bills.count()
            batch.save()

            # Store selected bill IDs in session for batch processing
            request.session[f'batch_{batch.pk}_bills'] = selected_bill_ids

            messages.success(
                request,
                f'Payment batch "{batch.batch_number}" created with '
                f'{batch.payment_count} bills.'
            )
            return redirect('accounts_payable:batch_detail',
                            tenant_slug=tenant_slug, pk=batch.pk)
    else:
        form = PaymentBatchForm(tenant=tenant)

    return render(request, 'accounts_payable/payments/batch_form.html', {
        'form': form,
        'approved_bills': approved_bills,
        'title': 'Create Payment Batch',
    })


@login_required
def batch_detail(request, tenant_slug, pk):
    """View batch with associated payments."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    batch = get_object_or_404(
        PaymentBatch.unscoped.select_related('bank_account', 'created_by'),
        pk=pk, tenant=tenant
    )

    # Get payments created by this batch (linked via memo or reference)
    payments = Payment.unscoped.filter(
        tenant=tenant, reference__startswith=f'BATCH-{batch.batch_number}'
    ).select_related('vendor')

    # Get selected bill IDs from session if batch is still draft
    selected_bill_ids = request.session.get(f'batch_{batch.pk}_bills', [])
    selected_bills = Bill.unscoped.filter(
        pk__in=selected_bill_ids, tenant=tenant
    ).select_related('vendor') if selected_bill_ids else Bill.unscoped.none()

    return render(request, 'accounts_payable/payments/batch_detail.html', {
        'batch': batch,
        'payments': payments,
        'selected_bills': selected_bills,
    })


@login_required
def batch_process(request, tenant_slug, pk):
    """Process a batch: create payments for selected bills. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    batch = get_object_or_404(PaymentBatch.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if batch.status not in ('draft', 'ready'):
            messages.error(request, 'Only draft or ready batches can be processed.')
        else:
            selected_bill_ids = request.session.get(f'batch_{batch.pk}_bills', [])
            selected_bills = Bill.unscoped.filter(
                pk__in=selected_bill_ids, tenant=tenant,
                status__in=['approved', 'partially_paid']
            ).select_related('vendor')

            if not selected_bills.exists():
                messages.error(request, 'No eligible bills found for this batch.')
            else:
                # Get current fiscal period
                current_period = FiscalPeriod.objects.filter(
                    tenant=tenant, is_closed=False
                ).order_by('period_number').first()

                if not current_period:
                    messages.error(request, 'No open fiscal period available.')
                    return redirect('accounts_payable:batch_detail',
                                    tenant_slug=tenant_slug, pk=pk)

                created_count = 0
                for bill in selected_bills:
                    balance = bill.total_amount - bill.amount_paid
                    if balance <= Decimal('0.00'):
                        continue

                    payment = Payment.objects.create(
                        tenant=tenant,
                        payment_number=Payment.generate_payment_number(tenant),
                        vendor=bill.vendor,
                        payment_date=batch.payment_date,
                        amount=balance,
                        currency=bill.currency,
                        exchange_rate=bill.exchange_rate,
                        payment_method=batch.payment_method,
                        bank_account=batch.bank_account,
                        ap_account=bill.ap_account,
                        fiscal_period=current_period,
                        status='draft',
                        memo=f'Batch payment: {batch.batch_number}',
                        reference=f'BATCH-{batch.batch_number}',
                        created_by=request.user,
                    )

                    PaymentAllocation.objects.create(
                        payment=payment,
                        bill=bill,
                        amount=balance,
                    )
                    created_count += 1

                batch.status = 'completed'
                batch.payment_count = created_count
                batch.save()

                # Clean up session
                session_key = f'batch_{batch.pk}_bills'
                if session_key in request.session:
                    del request.session[session_key]

                messages.success(
                    request,
                    f'Batch "{batch.batch_number}" processed. '
                    f'{created_count} payments created.'
                )

    return redirect('accounts_payable:batch_detail',
                    tenant_slug=tenant_slug, pk=pk)


# =============================================================================
# 4. Bill Capture
# =============================================================================

@login_required
def bill_upload_list(request, tenant_slug):
    """List bill uploads with OCR status stats."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = BillUpload.objects.filter(tenant=tenant).select_related(
        'bill', 'uploaded_by'
    )

    # Stats
    total_count = qs.count()
    pending_count = qs.filter(ocr_status='pending').count()
    processing_count = qs.filter(ocr_status='processing').count()
    completed_count = qs.filter(ocr_status='completed').count()
    failed_count = qs.filter(ocr_status='failed').count()

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_payable/capture/upload_list.html', {
        'uploads': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'pending_count': pending_count,
        'processing_count': processing_count,
        'completed_count': completed_count,
        'failed_count': failed_count,
    })


@login_required
def bill_upload_create(request, tenant_slug):
    """Upload a bill document for OCR processing."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = BillUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            upload = BillUpload(
                tenant=tenant,
                upload_number=BillUpload.generate_upload_number(tenant),
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                mime_type=uploaded_file.content_type or '',
                uploaded_by=request.user,
                ocr_status='pending',
            )
            upload.save()

            messages.success(
                request,
                f'File "{uploaded_file.name}" uploaded. '
                f'OCR processing will begin shortly.'
            )
            return redirect('accounts_payable:bill_upload_detail',
                            tenant_slug=tenant_slug, pk=upload.pk)
    else:
        form = BillUploadForm()

    return render(request, 'accounts_payable/capture/upload_form.html', {
        'form': form,
        'title': 'Upload Bill Document',
    })


@login_required
def bill_upload_detail(request, tenant_slug, pk):
    """View uploaded document and extracted data."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    upload = get_object_or_404(
        BillUpload.unscoped.select_related('bill', 'uploaded_by'),
        pk=pk, tenant=tenant
    )

    return render(request, 'accounts_payable/capture/upload_detail.html', {
        'upload': upload,
    })


@login_required
def bill_upload_create_bill(request, tenant_slug, pk):
    """Create a bill from extracted OCR data. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    upload = get_object_or_404(BillUpload.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if upload.bill:
            messages.error(request, 'A bill has already been created from this upload.')
        elif not upload.extracted_data:
            messages.error(request, 'No extracted data available to create a bill.')
        else:
            data = upload.extracted_data

            # Get current fiscal period
            current_period = FiscalPeriod.objects.filter(
                tenant=tenant, is_closed=False
            ).order_by('period_number').first()

            if not current_period:
                messages.error(request, 'No open fiscal period available.')
                return redirect('accounts_payable:bill_upload_detail',
                                tenant_slug=tenant_slug, pk=pk)

            # Attempt to find vendor by name or number from extracted data
            vendor = None
            vendor_name = data.get('vendor_name', '')
            if vendor_name:
                vendor = Vendor.unscoped.filter(
                    tenant=tenant,
                    display_name__icontains=vendor_name
                ).first()

            if not vendor:
                messages.error(
                    request,
                    'Could not match a vendor from the extracted data. '
                    'Please create the bill manually.'
                )
                return redirect('accounts_payable:bill_upload_detail',
                                tenant_slug=tenant_slug, pk=pk)

            # Find default AP account
            from apps.general_ledger.models import Account
            ap_account = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='LIABILITY'
            ).first()

            if not ap_account:
                messages.error(request, 'No AP liability account found.')
                return redirect('accounts_payable:bill_upload_detail',
                                tenant_slug=tenant_slug, pk=pk)

            # Get currency from vendor or default
            from apps.company.models import CompanySettings
            company_settings = CompanySettings.unscoped.filter(tenant=tenant).first()
            currency = vendor.currency
            if not currency and company_settings:
                currency = company_settings.base_currency

            bill_date = data.get('bill_date', timezone.now().date())
            due_date = data.get('due_date')
            if not due_date:
                if vendor.default_payment_term:
                    due_date = bill_date + timedelta(
                        days=vendor.default_payment_term.due_days
                    )
                else:
                    due_date = bill_date + timedelta(days=30)

            total = Decimal(str(data.get('total_amount', '0.00')))

            bill = Bill.objects.create(
                tenant=tenant,
                bill_number=Bill.generate_bill_number(tenant),
                vendor=vendor,
                vendor_invoice_number=data.get('invoice_number', ''),
                bill_date=bill_date,
                due_date=due_date,
                payment_term=vendor.default_payment_term,
                currency=currency,
                ap_account=ap_account,
                fiscal_period=current_period,
                subtotal=total,
                total_amount=total,
                status='draft',
                description=data.get('description', 'Created from uploaded document'),
                created_by=request.user,
            )

            # Link upload to bill
            upload.bill = bill
            upload.save()

            messages.success(
                request,
                f'Bill "{bill.bill_number}" created from uploaded document.'
            )
            return redirect('accounts_payable:bill_detail',
                            tenant_slug=tenant_slug, pk=bill.pk)

    return redirect('accounts_payable:bill_upload_detail',
                    tenant_slug=tenant_slug, pk=pk)


# =============================================================================
# 5. Payment Scheduling
# =============================================================================

@login_required
def schedule_list(request, tenant_slug):
    """List scheduled payments grouped by date, with stats."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = ScheduledPayment.objects.filter(tenant=tenant).select_related(
        'bill', 'bill__vendor', 'payment', 'created_by'
    )

    # Stats
    total_count = qs.count()
    scheduled_count = qs.filter(status='scheduled').count()
    executed_count = qs.filter(status='executed').count()
    cancelled_count = qs.filter(status='cancelled').count()
    total_scheduled_amount = qs.filter(
        status='scheduled'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_payable/scheduling/schedule_list.html', {
        'schedules': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'scheduled_count': scheduled_count,
        'executed_count': executed_count,
        'cancelled_count': cancelled_count,
        'total_scheduled_amount': total_scheduled_amount,
    })


@login_required
def schedule_create(request, tenant_slug):
    """Create a new scheduled payment."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ScheduledPaymentForm(request.POST, tenant=tenant)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.tenant = tenant
            schedule.created_by = request.user
            schedule.status = 'scheduled'
            schedule.save()
            messages.success(request, 'Scheduled payment created.')
            return redirect('accounts_payable:schedule_list',
                            tenant_slug=tenant_slug)
    else:
        form = ScheduledPaymentForm(tenant=tenant)

    return render(request, 'accounts_payable/scheduling/schedule_form.html', {
        'form': form,
        'title': 'Schedule Payment',
    })


@login_required
def schedule_execute(request, tenant_slug, pk):
    """Execute a scheduled payment: create a Payment and mark as executed. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    schedule = get_object_or_404(ScheduledPayment.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if schedule.status != 'scheduled':
            messages.error(request, 'Only scheduled payments can be executed.')
        else:
            bill = schedule.bill

            # Get current fiscal period
            current_period = FiscalPeriod.objects.filter(
                tenant=tenant, is_closed=False
            ).order_by('period_number').first()

            if not current_period:
                messages.error(request, 'No open fiscal period available.')
                return redirect('accounts_payable:schedule_list',
                                tenant_slug=tenant_slug)

            # Find bank and AP accounts from the bill
            from apps.general_ledger.models import Account
            bank_account = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code='ASSET'
            ).first()

            if not bank_account:
                messages.error(request, 'No bank account found.')
                return redirect('accounts_payable:schedule_list',
                                tenant_slug=tenant_slug)

            payment = Payment.objects.create(
                tenant=tenant,
                payment_number=Payment.generate_payment_number(tenant),
                vendor=bill.vendor,
                payment_date=schedule.scheduled_date,
                amount=schedule.amount,
                currency=bill.currency,
                exchange_rate=bill.exchange_rate,
                payment_method=bill.vendor.preferred_payment_method,
                bank_account=bank_account,
                ap_account=bill.ap_account,
                fiscal_period=current_period,
                status='draft',
                memo=f'From scheduled payment for {bill.bill_number}',
                created_by=request.user,
            )

            PaymentAllocation.objects.create(
                payment=payment,
                bill=bill,
                amount=schedule.amount,
            )

            schedule.payment = payment
            schedule.status = 'executed'
            schedule.save()

            messages.success(
                request,
                f'Scheduled payment executed. Payment '
                f'"{payment.payment_number}" created.'
            )

    return redirect('accounts_payable:schedule_list',
                    tenant_slug=tenant_slug)


@login_required
def schedule_cancel(request, tenant_slug, pk):
    """Cancel a scheduled payment. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    schedule = get_object_or_404(ScheduledPayment.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if schedule.status != 'scheduled':
            messages.error(request, 'Only scheduled payments can be cancelled.')
        else:
            schedule.status = 'cancelled'
            schedule.save()
            messages.success(request, 'Scheduled payment cancelled.')

    return redirect('accounts_payable:schedule_list',
                    tenant_slug=tenant_slug)


# =============================================================================
# 6. Aging Reports
# =============================================================================

@login_required
def aging_summary(request, tenant_slug):
    """Calculate aging buckets grouped by vendor."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    form = AgingReportFilterForm(request.GET or None, tenant=tenant)

    as_of_date = timezone.now().date()
    if form.is_valid():
        if form.cleaned_data.get('as_of_date'):
            as_of_date = form.cleaned_data['as_of_date']

    # Get open bills (exclude draft and void)
    bills_qs = Bill.objects.filter(tenant=tenant).exclude(
        status__in=['draft', 'void', 'paid']
    ).select_related('vendor')

    # Filter by vendor if specified
    vendor_filter = None
    if form.is_valid() and form.cleaned_data.get('vendor'):
        vendor_filter = form.cleaned_data['vendor']
        bills_qs = bills_qs.filter(vendor=vendor_filter)

    # Calculate aging buckets per vendor
    vendor_aging = {}
    for bill in bills_qs:
        vendor_id = bill.vendor_id
        if vendor_id not in vendor_aging:
            vendor_aging[vendor_id] = {
                'vendor': bill.vendor,
                'current': Decimal('0.00'),
                'days_1_30': Decimal('0.00'),
                'days_31_60': Decimal('0.00'),
                'days_61_90': Decimal('0.00'),
                'days_over_90': Decimal('0.00'),
                'total': Decimal('0.00'),
            }

        balance = bill.total_amount - bill.amount_paid
        days_outstanding = (as_of_date - bill.due_date).days

        entry = vendor_aging[vendor_id]
        if days_outstanding <= 0:
            entry['current'] += balance
        elif days_outstanding <= 30:
            entry['days_1_30'] += balance
        elif days_outstanding <= 60:
            entry['days_31_60'] += balance
        elif days_outstanding <= 90:
            entry['days_61_90'] += balance
        else:
            entry['days_over_90'] += balance
        entry['total'] += balance

    # Calculate grand totals
    grand_totals = {
        'current': Decimal('0.00'),
        'days_1_30': Decimal('0.00'),
        'days_31_60': Decimal('0.00'),
        'days_61_90': Decimal('0.00'),
        'days_over_90': Decimal('0.00'),
        'total': Decimal('0.00'),
    }
    for entry in vendor_aging.values():
        grand_totals['current'] += entry['current']
        grand_totals['days_1_30'] += entry['days_1_30']
        grand_totals['days_31_60'] += entry['days_31_60']
        grand_totals['days_61_90'] += entry['days_61_90']
        grand_totals['days_over_90'] += entry['days_over_90']
        grand_totals['total'] += entry['total']

    aging_data = sorted(vendor_aging.values(), key=lambda x: x['vendor'].display_name)

    return render(request, 'accounts_payable/aging/aging_summary.html', {
        'form': form,
        'aging_data': aging_data,
        'grand_totals': grand_totals,
        'as_of_date': as_of_date,
    })


@login_required
def aging_detail(request, tenant_slug, vendor_pk):
    """Show individual bills for a vendor with aging details."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    vendor = get_object_or_404(Vendor.unscoped, pk=vendor_pk, tenant=tenant)

    as_of_date_str = request.GET.get('as_of_date', '')
    if as_of_date_str:
        try:
            from datetime import date
            parts = as_of_date_str.split('-')
            as_of_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            as_of_date = timezone.now().date()
    else:
        as_of_date = timezone.now().date()

    bills = Bill.objects.filter(
        tenant=tenant, vendor=vendor
    ).exclude(
        status__in=['draft', 'void', 'paid']
    ).order_by('due_date')

    # Add aging info to each bill
    bill_aging = []
    total_balance = Decimal('0.00')
    for bill in bills:
        balance = bill.total_amount - bill.amount_paid
        days_outstanding = (as_of_date - bill.due_date).days

        if days_outstanding <= 0:
            aging_bucket = 'Current'
        elif days_outstanding <= 30:
            aging_bucket = '1-30 days'
        elif days_outstanding <= 60:
            aging_bucket = '31-60 days'
        elif days_outstanding <= 90:
            aging_bucket = '61-90 days'
        else:
            aging_bucket = '90+ days'

        bill_aging.append({
            'bill': bill,
            'balance': balance,
            'days_outstanding': days_outstanding,
            'aging_bucket': aging_bucket,
        })
        total_balance += balance

    return render(request, 'accounts_payable/aging/aging_detail.html', {
        'vendor': vendor,
        'bill_aging': bill_aging,
        'total_balance': total_balance,
        'as_of_date': as_of_date,
    })


@login_required
def aging_export(request, tenant_slug):
    """Export aging report as CSV."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    as_of_date_str = request.GET.get('as_of_date', '')
    if as_of_date_str:
        try:
            from datetime import date
            parts = as_of_date_str.split('-')
            as_of_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            as_of_date = timezone.now().date()
    else:
        as_of_date = timezone.now().date()

    bills = Bill.objects.filter(tenant=tenant).exclude(
        status__in=['draft', 'void', 'paid']
    ).select_related('vendor').order_by('vendor__display_name', 'due_date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="ap_aging_{as_of_date}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        'Vendor', 'Bill Number', 'Bill Date', 'Due Date',
        'Total Amount', 'Amount Paid', 'Balance',
        'Days Outstanding', 'Aging Bucket',
    ])

    for bill in bills:
        balance = bill.total_amount - bill.amount_paid
        days_outstanding = (as_of_date - bill.due_date).days

        if days_outstanding <= 0:
            aging_bucket = 'Current'
        elif days_outstanding <= 30:
            aging_bucket = '1-30'
        elif days_outstanding <= 60:
            aging_bucket = '31-60'
        elif days_outstanding <= 90:
            aging_bucket = '61-90'
        else:
            aging_bucket = '90+'

        writer.writerow([
            bill.vendor.display_name,
            bill.bill_number,
            bill.bill_date,
            bill.due_date,
            bill.total_amount,
            bill.amount_paid,
            balance,
            days_outstanding,
            aging_bucket,
        ])

    return response


# =============================================================================
# 7. Early Payment Discounts
# =============================================================================

@login_required
def discount_opportunities(request, tenant_slug):
    """List bills with available early payment discounts and potential savings."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    today = timezone.now().date()

    # Get approved/partially paid bills that have discount terms
    bills = Bill.objects.filter(
        tenant=tenant,
        status__in=['approved', 'partially_paid'],
        payment_term__discount_percentage__gt=0,
        payment_term__discount_days__gt=0,
    ).select_related('vendor', 'payment_term')

    opportunities = []
    total_potential_savings = Decimal('0.00')

    for bill in bills:
        discount_date = bill.discount_date
        if discount_date and today <= discount_date:
            balance = bill.total_amount - bill.amount_paid
            discount = (
                balance * bill.payment_term.discount_percentage / Decimal('100')
            ).quantize(Decimal('0.01'))
            days_remaining = (discount_date - today).days

            opportunities.append({
                'bill': bill,
                'discount_date': discount_date,
                'discount_percentage': bill.payment_term.discount_percentage,
                'discount_amount': discount,
                'balance': balance,
                'days_remaining': days_remaining,
            })
            total_potential_savings += discount

    # Sort by days remaining (most urgent first)
    opportunities.sort(key=lambda x: x['days_remaining'])

    return render(request, 'accounts_payable/discounts/discount_opportunities.html', {
        'opportunities': opportunities,
        'total_potential_savings': total_potential_savings,
        'today': today,
    })
