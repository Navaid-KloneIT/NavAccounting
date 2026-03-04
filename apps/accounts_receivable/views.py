import csv
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from .forms import (
    CustomerForm, CustomerContactFormSet,
    InvoiceForm, InvoiceLineFormSet, InvoiceApprovalActionForm,
    ReceiptForm, ReceiptAllocationFormSet,
    RecurringInvoiceTemplateForm, RecurringInvoiceTemplateLineFormSet,
    CreditMemoForm, CollectionActivityForm, WriteOffForm,
    ARAgingReportFilterForm,
)
from .models import (
    Customer, CustomerContact,
    Invoice, InvoiceLine, InvoiceApproval,
    Receipt, ReceiptAllocation,
    RecurringInvoiceTemplate, RecurringInvoiceTemplateLine,
    CreditMemo, CollectionActivity, WriteOff,
)
from .services import (
    create_receipt_journal_entry, create_void_receipt_journal_entry,
    create_credit_memo_journal_entry, create_write_off_journal_entry,
    calculate_ar_aging_buckets, auto_match_receipt,
    get_dunning_candidates, generate_recurring_invoices,
    check_credit_limits,
)


# =============================================================================
# 1. Customer Management
# =============================================================================

@login_required
def customer_list(request, tenant_slug):
    """List customers with search, type filter, status filter, and stat cards."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = Customer.objects.filter(tenant=tenant).select_related(
        'default_payment_term', 'default_revenue_account', 'currency'
    )

    # Stats (computed before filtering)
    total_count = qs.count()
    active_count = qs.filter(is_active=True).count()
    inactive_count = qs.filter(is_active=False).count()
    on_credit_hold_count = qs.filter(credit_hold=True).count()

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(customer_number__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(display_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Type filter
    type_filter = request.GET.get('type', '')
    if type_filter:
        qs = qs.filter(customer_type=type_filter)

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)
    elif status_filter == 'credit_hold':
        qs = qs.filter(credit_hold=True)

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_receivable/customers/customer_list.html', {
        'customers': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'on_credit_hold_count': on_credit_hold_count,
    })


@login_required
def customer_create(request, tenant_slug):
    """Create a new customer with contact formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = CustomerForm(request.POST, tenant=tenant)
        formset = CustomerContactFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            customer = form.save(commit=False)
            customer.tenant = tenant
            customer.customer_number = Customer.generate_customer_number(tenant)
            customer.save()

            formset.instance = customer
            formset.save()

            messages.success(request, f'Customer "{customer.display_name}" created.')
            return redirect('accounts_receivable:customer_detail',
                            tenant_slug=tenant_slug, pk=customer.pk)
    else:
        form = CustomerForm(tenant=tenant)
        formset = CustomerContactFormSet()

    return render(request, 'accounts_receivable/customers/customer_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Customer',
    })


@login_required
def customer_detail(request, tenant_slug, pk):
    """View customer profile with recent invoices, receipts, and collection activities."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    customer = get_object_or_404(
        Customer.unscoped.select_related(
            'default_payment_term', 'default_revenue_account', 'currency'
        ),
        pk=pk, tenant=tenant
    )
    contacts = customer.contacts.all()
    recent_invoices = Invoice.unscoped.filter(
        customer=customer, tenant=tenant
    ).order_by('-invoice_date')[:10]
    recent_receipts = Receipt.unscoped.filter(
        customer=customer, tenant=tenant
    ).order_by('-receipt_date')[:10]
    recent_collection_activities = CollectionActivity.unscoped.filter(
        customer=customer, tenant=tenant
    ).order_by('-created_at')[:10]

    return render(request, 'accounts_receivable/customers/customer_detail.html', {
        'customer': customer,
        'contacts': contacts,
        'recent_invoices': recent_invoices,
        'recent_receipts': recent_receipts,
        'recent_collection_activities': recent_collection_activities,
    })


@login_required
def customer_edit(request, tenant_slug, pk):
    """Edit an existing customer with contact formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    customer = get_object_or_404(Customer.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer, tenant=tenant)
        formset = CustomerContactFormSet(request.POST, instance=customer)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Customer "{customer.display_name}" updated.')
            return redirect('accounts_receivable:customer_detail',
                            tenant_slug=tenant_slug, pk=customer.pk)
    else:
        form = CustomerForm(instance=customer, tenant=tenant)
        formset = CustomerContactFormSet(instance=customer)

    return render(request, 'accounts_receivable/customers/customer_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit: {customer.display_name}',
        'customer': customer,
    })


@login_required
def customer_toggle_active(request, tenant_slug, pk):
    """Toggle customer active status. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    customer = get_object_or_404(Customer.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        customer.is_active = not customer.is_active
        customer.save()
        status_text = 'activated' if customer.is_active else 'deactivated'
        messages.success(request, f'Customer "{customer.display_name}" {status_text}.')

    return redirect('accounts_receivable:customer_detail',
                    tenant_slug=tenant_slug, pk=customer.pk)


@login_required
def customer_credit_hold(request, tenant_slug, pk):
    """Toggle customer credit hold status. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    customer = get_object_or_404(Customer.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        customer.credit_hold = not customer.credit_hold
        if not customer.credit_hold:
            customer.credit_hold_reason = ''
        else:
            customer.credit_hold_reason = request.POST.get('reason', 'Manual credit hold')
        customer.save()
        status_text = 'placed on credit hold' if customer.credit_hold else 'removed from credit hold'
        messages.success(request, f'Customer "{customer.display_name}" {status_text}.')

    return redirect('accounts_receivable:customer_detail',
                    tenant_slug=tenant_slug, pk=customer.pk)


# =============================================================================
# 2. Invoice Management
# =============================================================================

@login_required
def invoice_list(request, tenant_slug):
    """List invoices with stat cards, search, and filters."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = Invoice.objects.filter(tenant=tenant).select_related(
        'customer', 'payment_term', 'currency', 'fiscal_period', 'created_by'
    )

    # Stats (computed before filtering)
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    sent_count = qs.filter(status='sent').count()
    overdue_count = qs.filter(
        due_date__lt=timezone.now().date()
    ).exclude(status__in=['paid', 'void', 'written_off']).count()
    total_outstanding = qs.exclude(
        status__in=['draft', 'void', 'written_off']
    ).aggregate(
        outstanding=Sum(F('total_amount') - F('amount_paid'))
    )['outstanding'] or Decimal('0.00')

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(invoice_number__icontains=search_query) |
            Q(customer__display_name__icontains=search_query) |
            Q(po_number__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Customer filter
    customer_filter = request.GET.get('customer', '')
    if customer_filter:
        qs = qs.filter(customer_id=customer_filter)

    # Date range filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        qs = qs.filter(invoice_date__gte=date_from)
    if date_to:
        qs = qs.filter(invoice_date__lte=date_to)

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Customers for filter dropdown
    customers = Customer.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'accounts_receivable/invoices/invoice_list.html', {
        'invoices': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'sent_count': sent_count,
        'overdue_count': overdue_count,
        'total_outstanding': total_outstanding,
        'customers': customers,
    })


@login_required
def invoice_create(request, tenant_slug):
    """Create a new invoice with line formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, tenant=tenant)
        formset = InvoiceLineFormSet(
            request.POST, form_kwargs={'tenant': tenant}
        )
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.tenant = tenant
            invoice.invoice_number = Invoice.generate_invoice_number(tenant)
            invoice.created_by = request.user
            invoice.status = 'draft'
            invoice.save()

            formset.instance = invoice
            formset.save()

            invoice.update_totals()
            invoice.save()

            messages.success(request, f'Invoice "{invoice.invoice_number}" created.')
            return redirect('accounts_receivable:invoice_detail',
                            tenant_slug=tenant_slug, pk=invoice.pk)
    else:
        form = InvoiceForm(tenant=tenant)
        formset = InvoiceLineFormSet(form_kwargs={'tenant': tenant})

    return render(request, 'accounts_receivable/invoices/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Invoice',
    })


@login_required
def invoice_detail(request, tenant_slug, pk):
    """View invoice with lines, approval history, and receipt allocations."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    invoice = get_object_or_404(
        Invoice.unscoped.select_related(
            'customer', 'payment_term', 'currency', 'ar_account',
            'fiscal_period', 'created_by'
        ),
        pk=pk, tenant=tenant
    )
    lines = invoice.lines.select_related('account')
    approvals = invoice.approvals.select_related('approver').all()
    receipt_allocations = invoice.receipt_allocations.select_related(
        'receipt', 'receipt__customer'
    ).all()

    return render(request, 'accounts_receivable/invoices/invoice_detail.html', {
        'invoice': invoice,
        'lines': lines,
        'approvals': approvals,
        'receipt_allocations': receipt_allocations,
    })


@login_required
def invoice_edit(request, tenant_slug, pk):
    """Edit a draft invoice with line formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    invoice = get_object_or_404(Invoice.unscoped, pk=pk, tenant=tenant)

    if invoice.status != 'draft':
        messages.error(request, 'Only draft invoices can be edited.')
        return redirect('accounts_receivable:invoice_detail',
                        tenant_slug=tenant_slug, pk=pk)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice, tenant=tenant)
        formset = InvoiceLineFormSet(
            request.POST, instance=invoice, form_kwargs={'tenant': tenant}
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            invoice.update_totals()
            invoice.save()

            messages.success(request, f'Invoice "{invoice.invoice_number}" updated.')
            return redirect('accounts_receivable:invoice_detail',
                            tenant_slug=tenant_slug, pk=pk)
    else:
        form = InvoiceForm(instance=invoice, tenant=tenant)
        formset = InvoiceLineFormSet(
            instance=invoice, form_kwargs={'tenant': tenant}
        )

    return render(request, 'accounts_receivable/invoices/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit: {invoice.invoice_number}',
        'invoice': invoice,
    })


@login_required
def invoice_submit(request, tenant_slug, pk):
    """Submit an invoice for approval. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    invoice = get_object_or_404(Invoice.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if invoice.status != 'draft':
            messages.error(request, 'Only draft invoices can be submitted for approval.')
        else:
            invoice.status = 'submitted'
            invoice.save()

            InvoiceApproval.objects.create(
                tenant=tenant,
                invoice=invoice,
                approver=request.user,
                status='pending',
            )
            messages.success(
                request,
                f'Invoice "{invoice.invoice_number}" submitted for approval.'
            )

    return redirect('accounts_receivable:invoice_detail',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def invoice_approve(request, tenant_slug, pk):
    """Approve an invoice. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    invoice = get_object_or_404(Invoice.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = InvoiceApprovalActionForm(request.POST)
        if invoice.status != 'submitted':
            messages.error(request, 'Only submitted invoices can be approved.')
        elif form.is_valid():
            comments = form.cleaned_data.get('comments', '')

            # Update or create approval record
            approval = invoice.approvals.filter(status='pending').first()
            if approval:
                approval.status = 'approved'
                approval.comments = comments
                approval.approved_at = timezone.now()
                approval.approver = request.user
                approval.save()
            else:
                InvoiceApproval.objects.create(
                    tenant=tenant,
                    invoice=invoice,
                    approver=request.user,
                    status='approved',
                    comments=comments,
                    approved_at=timezone.now(),
                )

            invoice.status = 'approved'
            invoice.save()
            messages.success(request, f'Invoice "{invoice.invoice_number}" approved.')

    return redirect('accounts_receivable:invoice_approval_queue',
                    tenant_slug=tenant_slug)


@login_required
def invoice_reject(request, tenant_slug, pk):
    """Reject an invoice back to draft. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    invoice = get_object_or_404(Invoice.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = InvoiceApprovalActionForm(request.POST)
        if invoice.status != 'submitted':
            messages.error(request, 'Only submitted invoices can be rejected.')
        elif form.is_valid():
            comments = form.cleaned_data.get('comments', '')

            # Update or create approval record
            approval = invoice.approvals.filter(status='pending').first()
            if approval:
                approval.status = 'rejected'
                approval.comments = comments
                approval.approved_at = timezone.now()
                approval.approver = request.user
                approval.save()
            else:
                InvoiceApproval.objects.create(
                    tenant=tenant,
                    invoice=invoice,
                    approver=request.user,
                    status='rejected',
                    comments=comments,
                    approved_at=timezone.now(),
                )

            invoice.status = 'draft'
            invoice.save()
            messages.success(request, f'Invoice "{invoice.invoice_number}" rejected.')

    return redirect('accounts_receivable:invoice_approval_queue',
                    tenant_slug=tenant_slug)


@login_required
def invoice_send(request, tenant_slug, pk):
    """Send an approved invoice to the customer. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    invoice = get_object_or_404(Invoice.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if invoice.status != 'approved':
            messages.error(request, 'Only approved invoices can be sent.')
        else:
            invoice.status = 'sent'
            invoice.sent_date = timezone.now().date()
            invoice.save()
            messages.success(request, f'Invoice "{invoice.invoice_number}" marked as sent.')

    return redirect('accounts_receivable:invoice_detail',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def invoice_void(request, tenant_slug, pk):
    """Void an invoice. POST only. Cannot void paid or already voided invoices."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    invoice = get_object_or_404(Invoice.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if invoice.status in ('paid', 'void'):
            messages.error(request, 'Cannot void a paid or already voided invoice.')
        else:
            invoice.status = 'void'
            invoice.save()
            messages.success(request, f'Invoice "{invoice.invoice_number}" has been voided.')

    return redirect('accounts_receivable:invoice_detail',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def invoice_approval_queue(request, tenant_slug):
    """List invoices pending approval (submitted status)."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = Invoice.objects.filter(
        tenant=tenant, status='submitted'
    ).select_related('customer', 'currency', 'created_by')

    pending_count = qs.count()

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_receivable/invoices/invoice_approval_queue.html', {
        'invoices': page_obj,
        'page_obj': page_obj,
        'pending_count': pending_count,
    })


# =============================================================================
# 3. Recurring Invoicing
# =============================================================================

@login_required
def recurring_list(request, tenant_slug):
    """List recurring invoice templates with stats."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = RecurringInvoiceTemplate.objects.filter(tenant=tenant).select_related(
        'customer', 'payment_term', 'currency', 'created_by'
    )

    # Stats (computed before filtering)
    total_count = qs.count()
    active_count = qs.filter(status='active').count()
    paused_count = qs.filter(status='paused').count()
    completed_count = qs.filter(status='completed').count()

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_receivable/recurring/recurring_list.html', {
        'templates': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'paused_count': paused_count,
        'completed_count': completed_count,
    })


@login_required
def recurring_create(request, tenant_slug):
    """Create a new recurring invoice template with line formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = RecurringInvoiceTemplateForm(request.POST, tenant=tenant)
        formset = RecurringInvoiceTemplateLineFormSet(
            request.POST, form_kwargs={'tenant': tenant}
        )
        if form.is_valid() and formset.is_valid():
            template = form.save(commit=False)
            template.tenant = tenant
            template.template_number = RecurringInvoiceTemplate.generate_template_number(tenant)
            template.created_by = request.user
            template.status = 'active'
            template.save()

            formset.instance = template
            formset.save()

            # Calculate totals from lines
            agg = template.lines.aggregate(
                sub=Sum('amount'),
                tax=Sum('tax_amount'),
            )
            template.subtotal = agg['sub'] or Decimal('0.00')
            template.tax_amount = agg['tax'] or Decimal('0.00')
            template.total_amount = template.subtotal + template.tax_amount
            template.save()

            messages.success(request, f'Recurring template "{template.name}" created.')
            return redirect('accounts_receivable:recurring_detail',
                            tenant_slug=tenant_slug, pk=template.pk)
    else:
        form = RecurringInvoiceTemplateForm(tenant=tenant)
        formset = RecurringInvoiceTemplateLineFormSet(form_kwargs={'tenant': tenant})

    return render(request, 'accounts_receivable/recurring/recurring_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Recurring Invoice Template',
    })


@login_required
def recurring_detail(request, tenant_slug, pk):
    """View recurring template with generated invoice history."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    template = get_object_or_404(
        RecurringInvoiceTemplate.unscoped.select_related(
            'customer', 'payment_term', 'ar_account', 'currency', 'created_by'
        ),
        pk=pk, tenant=tenant
    )
    lines = template.lines.select_related('account')
    generated_invoices = Invoice.unscoped.filter(
        recurring_template=template, tenant=tenant
    ).order_by('-invoice_date')

    return render(request, 'accounts_receivable/recurring/recurring_detail.html', {
        'template': template,
        'lines': lines,
        'generated_invoices': generated_invoices,
    })


@login_required
def recurring_edit(request, tenant_slug, pk):
    """Edit a recurring invoice template with line formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    template = get_object_or_404(
        RecurringInvoiceTemplate.unscoped, pk=pk, tenant=tenant
    )

    if request.method == 'POST':
        form = RecurringInvoiceTemplateForm(
            request.POST, instance=template, tenant=tenant
        )
        formset = RecurringInvoiceTemplateLineFormSet(
            request.POST, instance=template, form_kwargs={'tenant': tenant}
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            # Recalculate totals from lines
            agg = template.lines.aggregate(
                sub=Sum('amount'),
                tax=Sum('tax_amount'),
            )
            template.subtotal = agg['sub'] or Decimal('0.00')
            template.tax_amount = agg['tax'] or Decimal('0.00')
            template.total_amount = template.subtotal + template.tax_amount
            template.save()

            messages.success(request, f'Recurring template "{template.name}" updated.')
            return redirect('accounts_receivable:recurring_detail',
                            tenant_slug=tenant_slug, pk=template.pk)
    else:
        form = RecurringInvoiceTemplateForm(instance=template, tenant=tenant)
        formset = RecurringInvoiceTemplateLineFormSet(
            instance=template, form_kwargs={'tenant': tenant}
        )

    return render(request, 'accounts_receivable/recurring/recurring_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit: {template.name}',
        'template': template,
    })


@login_required
def recurring_pause(request, tenant_slug, pk):
    """Toggle recurring template between active and paused. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    template = get_object_or_404(
        RecurringInvoiceTemplate.unscoped, pk=pk, tenant=tenant
    )

    if request.method == 'POST':
        if template.status == 'active':
            template.status = 'paused'
            template.save()
            messages.success(request, f'Recurring template "{template.name}" paused.')
        elif template.status == 'paused':
            template.status = 'active'
            template.save()
            messages.success(request, f'Recurring template "{template.name}" resumed.')
        else:
            messages.error(request, 'Only active or paused templates can be toggled.')

    return redirect('accounts_receivable:recurring_detail',
                    tenant_slug=tenant_slug, pk=template.pk)


@login_required
def recurring_cancel(request, tenant_slug, pk):
    """Cancel a recurring template. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    template = get_object_or_404(
        RecurringInvoiceTemplate.unscoped, pk=pk, tenant=tenant
    )

    if request.method == 'POST':
        if template.status in ('completed', 'cancelled'):
            messages.error(request, 'This template is already completed or cancelled.')
        else:
            template.status = 'cancelled'
            template.save()
            messages.success(request, f'Recurring template "{template.name}" cancelled.')

    return redirect('accounts_receivable:recurring_detail',
                    tenant_slug=tenant_slug, pk=template.pk)


@login_required
def recurring_generate(request, tenant_slug, pk):
    """Generate invoices from a specific recurring template. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    template = get_object_or_404(
        RecurringInvoiceTemplate.unscoped, pk=pk, tenant=tenant
    )

    if request.method == 'POST':
        if template.status != 'active':
            messages.error(request, 'Only active templates can generate invoices.')
        else:
            created = generate_recurring_invoices(tenant, timezone.now().date())
            # Filter to only invoices from this template
            template_invoices = [inv for inv in created if inv.recurring_template_id == template.pk]
            if template_invoices:
                messages.success(
                    request,
                    f'{len(template_invoices)} invoice(s) generated from "{template.name}".'
                )
            else:
                messages.info(
                    request,
                    f'No invoices due for generation from "{template.name}" at this time.'
                )

    return redirect('accounts_receivable:recurring_detail',
                    tenant_slug=tenant_slug, pk=template.pk)


# =============================================================================
# 4. Receipt (Payment Collection)
# =============================================================================

@login_required
def receipt_list(request, tenant_slug):
    """List receipts with stats and filters."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = Receipt.objects.filter(tenant=tenant).select_related(
        'customer', 'currency', 'bank_account', 'created_by'
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
            Q(receipt_number__icontains=search_query) |
            Q(customer__display_name__icontains=search_query) |
            Q(reference__icontains=search_query) |
            Q(check_number__icontains=search_query)
        )

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Customer filter
    customer_filter = request.GET.get('customer', '')
    if customer_filter:
        qs = qs.filter(customer_id=customer_filter)

    # Date range filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        qs = qs.filter(receipt_date__gte=date_from)
    if date_to:
        qs = qs.filter(receipt_date__lte=date_to)

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_receivable/receipts/receipt_list.html', {
        'receipts': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'completed_count': completed_count,
        'void_count': void_count,
        'total_amount': total_amount,
    })


@login_required
def receipt_create(request, tenant_slug):
    """Create a new receipt with allocation formset."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ReceiptForm(request.POST, tenant=tenant)
        formset = ReceiptAllocationFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            receipt = form.save(commit=False)
            receipt.tenant = tenant
            receipt.receipt_number = Receipt.generate_receipt_number(tenant)
            receipt.created_by = request.user
            receipt.status = 'draft'
            receipt.save()

            formset.instance = receipt
            formset.save()

            messages.success(
                request,
                f'Receipt "{receipt.receipt_number}" created.'
            )
            return redirect('accounts_receivable:receipt_detail',
                            tenant_slug=tenant_slug, pk=receipt.pk)
    else:
        form = ReceiptForm(tenant=tenant)
        formset = ReceiptAllocationFormSet()

    return render(request, 'accounts_receivable/receipts/receipt_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Receipt',
    })


@login_required
def receipt_detail(request, tenant_slug, pk):
    """View receipt with allocations and journal entry reference."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    receipt = get_object_or_404(
        Receipt.unscoped.select_related(
            'customer', 'currency', 'bank_account', 'ar_account',
            'journal_entry', 'fiscal_period', 'created_by', 'voided_by'
        ),
        pk=pk, tenant=tenant
    )
    allocations = receipt.allocations.select_related('invoice', 'invoice__customer')

    return render(request, 'accounts_receivable/receipts/receipt_detail.html', {
        'receipt': receipt,
        'allocations': allocations,
    })


@login_required
def receipt_complete(request, tenant_slug, pk):
    """Mark receipt as completed, create GL journal entry, update invoice balances. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    receipt = get_object_or_404(Receipt.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if receipt.status not in ('draft', 'pending'):
            messages.error(request, 'Only draft or pending receipts can be completed.')
        else:
            # Create GL journal entry
            je = create_receipt_journal_entry(receipt, tenant, request.user)
            receipt.journal_entry = je
            receipt.status = 'completed'
            receipt.save()

            # Update invoice amount_paid and status for each allocation
            for alloc in receipt.allocations.select_related('invoice'):
                invoice = alloc.invoice
                invoice.amount_paid += alloc.amount
                invoice.update_payment_status()
                invoice.save()

            messages.success(
                request,
                f'Receipt "{receipt.receipt_number}" completed.'
            )

    return redirect('accounts_receivable:receipt_detail',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def receipt_void(request, tenant_slug, pk):
    """Void a completed receipt, reverse invoice balances, create reversal JE. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    receipt = get_object_or_404(Receipt.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if receipt.status != 'completed':
            messages.error(request, 'Only completed receipts can be voided.')
        else:
            void_reason = request.POST.get('void_reason', '')

            # Create reversal JE
            create_void_receipt_journal_entry(receipt, tenant, request.user)

            # Reverse invoice amount_paid for each allocation
            for alloc in receipt.allocations.select_related('invoice'):
                invoice = alloc.invoice
                invoice.amount_paid -= alloc.amount
                if invoice.amount_paid < Decimal('0.00'):
                    invoice.amount_paid = Decimal('0.00')
                invoice.update_payment_status()
                # If invoice was fully paid and is now reversed, set back to sent
                if invoice.status == 'paid' and invoice.amount_paid < invoice.total_amount:
                    if invoice.amount_paid > Decimal('0.00'):
                        invoice.status = 'partially_paid'
                    else:
                        invoice.status = 'sent'
                invoice.save()

            receipt.status = 'void'
            receipt.voided_by = request.user
            receipt.voided_at = timezone.now()
            receipt.void_reason = void_reason
            receipt.save()

            messages.success(
                request,
                f'Receipt "{receipt.receipt_number}" voided.'
            )

    return redirect('accounts_receivable:receipt_detail',
                    tenant_slug=tenant_slug, pk=pk)


# =============================================================================
# 5. Credit Memos
# =============================================================================

@login_required
def credit_memo_list(request, tenant_slug):
    """List credit memos with stats."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = CreditMemo.objects.filter(tenant=tenant).select_related(
        'customer', 'invoice', 'created_by'
    )

    # Stats (computed before filtering)
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    approved_count = qs.filter(status='approved').count()
    applied_count = qs.filter(status='applied').count()
    total_amount = qs.exclude(
        status='void'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_receivable/credit_memos/credit_memo_list.html', {
        'credit_memos': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'approved_count': approved_count,
        'applied_count': applied_count,
        'total_amount': total_amount,
    })


@login_required
def credit_memo_create(request, tenant_slug):
    """Create a new credit memo."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = CreditMemoForm(request.POST, tenant=tenant)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.tenant = tenant
            memo.memo_number = CreditMemo.generate_memo_number(tenant)
            memo.created_by = request.user
            memo.status = 'draft'
            memo.save()

            messages.success(request, f'Credit memo "{memo.memo_number}" created.')
            return redirect('accounts_receivable:credit_memo_detail',
                            tenant_slug=tenant_slug, pk=memo.pk)
    else:
        form = CreditMemoForm(tenant=tenant)

    return render(request, 'accounts_receivable/credit_memos/credit_memo_form.html', {
        'form': form,
        'title': 'Create Credit Memo',
    })


@login_required
def credit_memo_detail(request, tenant_slug, pk):
    """View credit memo details."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    memo = get_object_or_404(
        CreditMemo.unscoped.select_related(
            'customer', 'invoice', 'ar_account', 'fiscal_period',
            'journal_entry', 'created_by'
        ),
        pk=pk, tenant=tenant
    )

    return render(request, 'accounts_receivable/credit_memos/credit_memo_detail.html', {
        'credit_memo': memo,
    })


@login_required
def credit_memo_approve(request, tenant_slug, pk):
    """Approve a credit memo and create GL journal entry. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    memo = get_object_or_404(CreditMemo.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if memo.status != 'draft':
            messages.error(request, 'Only draft credit memos can be approved.')
        else:
            je = create_credit_memo_journal_entry(memo, tenant, request.user)
            memo.journal_entry = je
            memo.status = 'approved'
            memo.save()

            # If linked to an invoice, reduce the invoice balance
            if memo.invoice:
                memo.invoice.amount_paid += memo.amount
                memo.invoice.update_payment_status()
                memo.invoice.save()

            messages.success(request, f'Credit memo "{memo.memo_number}" approved.')

    return redirect('accounts_receivable:credit_memo_detail',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def credit_memo_edit(request, tenant_slug, pk):
    """Edit a draft credit memo."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    memo = get_object_or_404(CreditMemo.unscoped, pk=pk, tenant=tenant)

    if memo.status != 'draft':
        messages.error(request, 'Only draft credit memos can be edited.')
        return redirect('accounts_receivable:credit_memo_detail',
                        tenant_slug=tenant_slug, pk=pk)

    if request.method == 'POST':
        form = CreditMemoForm(request.POST, instance=memo, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Credit memo "{memo.memo_number}" updated.')
            return redirect('accounts_receivable:credit_memo_detail',
                            tenant_slug=tenant_slug, pk=memo.pk)
    else:
        form = CreditMemoForm(instance=memo, tenant=tenant)

    return render(request, 'accounts_receivable/credit_memos/credit_memo_form.html', {
        'form': form,
        'title': f'Edit Credit Memo - {memo.memo_number}',
    })


@login_required
def credit_memo_void(request, tenant_slug, pk):
    """Void an approved credit memo. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    memo = get_object_or_404(CreditMemo.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if memo.status != 'approved':
            messages.error(request, 'Only approved credit memos can be voided.')
        else:
            memo.status = 'void'
            memo.save()
            messages.success(request, f'Credit memo "{memo.memo_number}" voided.')

    return redirect('accounts_receivable:credit_memo_detail',
                    tenant_slug=tenant_slug, pk=pk)


# =============================================================================
# 6. Cash Application
# =============================================================================

@login_required
def cash_application(request, tenant_slug):
    """Dashboard showing unallocated receipts for cash application."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    # Find completed receipts with unallocated amounts
    receipts = Receipt.objects.filter(
        tenant=tenant, status='completed'
    ).select_related('customer', 'currency')

    unallocated_receipts = []
    for receipt in receipts:
        allocated_total = receipt.allocations.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        unallocated = receipt.amount - allocated_total
        if unallocated > Decimal('0.00'):
            unallocated_receipts.append({
                'receipt': receipt,
                'allocated_total': allocated_total,
                'unallocated': unallocated,
            })

    return render(request, 'accounts_receivable/cash_application/cash_application.html', {
        'unallocated_receipts': unallocated_receipts,
    })


@login_required
def cash_application_auto_match(request, tenant_slug, pk):
    """Auto-match a receipt to open invoices using FIFO strategy. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    receipt = get_object_or_404(Receipt.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if receipt.status != 'completed':
            messages.error(request, 'Only completed receipts can be auto-matched.')
        else:
            allocations = auto_match_receipt(receipt, tenant)
            if allocations:
                messages.success(
                    request,
                    f'{len(allocations)} invoice(s) matched to receipt '
                    f'"{receipt.receipt_number}".'
                )
            else:
                messages.info(
                    request,
                    f'No open invoices found to match for receipt '
                    f'"{receipt.receipt_number}".'
                )

    return redirect('accounts_receivable:cash_application',
                    tenant_slug=tenant_slug)


# =============================================================================
# 7. Collections
# =============================================================================

@login_required
def collections_dashboard(request, tenant_slug):
    """Overview of overdue invoices grouped by aging bucket."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    today = timezone.now().date()

    # Get overdue invoices (past due_date, not paid/void/written_off)
    overdue_invoices = Invoice.objects.filter(
        tenant=tenant,
        due_date__lt=today,
    ).exclude(
        status__in=['paid', 'void', 'written_off', 'draft']
    ).select_related('customer')

    # Group into aging buckets
    buckets = {
        '1_30': [],
        '31_60': [],
        '61_90': [],
        '90_plus': [],
    }
    bucket_totals = {
        '1_30': Decimal('0.00'),
        '31_60': Decimal('0.00'),
        '61_90': Decimal('0.00'),
        '90_plus': Decimal('0.00'),
    }

    for invoice in overdue_invoices:
        days_overdue = (today - invoice.due_date).days
        balance = invoice.total_amount - invoice.amount_paid

        if days_overdue <= 30:
            buckets['1_30'].append(invoice)
            bucket_totals['1_30'] += balance
        elif days_overdue <= 60:
            buckets['31_60'].append(invoice)
            bucket_totals['31_60'] += balance
        elif days_overdue <= 90:
            buckets['61_90'].append(invoice)
            bucket_totals['61_90'] += balance
        else:
            buckets['90_plus'].append(invoice)
            bucket_totals['90_plus'] += balance

    total_overdue = sum(bucket_totals.values())

    return render(request, 'accounts_receivable/collections/collections_dashboard.html', {
        'buckets': buckets,
        'bucket_totals': bucket_totals,
        'total_overdue': total_overdue,
        'today': today,
    })


@login_required
def collection_customer_detail(request, tenant_slug, pk):
    """View a customer's collection history and overdue invoices."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    customer = get_object_or_404(Customer.unscoped, pk=pk, tenant=tenant)

    # Overdue invoices for this customer
    today = timezone.now().date()
    overdue_invoices = Invoice.unscoped.filter(
        tenant=tenant,
        customer=customer,
        due_date__lt=today,
    ).exclude(
        status__in=['paid', 'void', 'written_off', 'draft']
    ).order_by('due_date')

    # Collection activities
    activities = CollectionActivity.unscoped.filter(
        tenant=tenant, customer=customer
    ).order_by('-created_at')

    return render(request, 'accounts_receivable/collections/collection_customer_detail.html', {
        'customer': customer,
        'overdue_invoices': overdue_invoices,
        'activities': activities,
    })


@login_required
def collection_add_activity(request, tenant_slug, pk):
    """Add a collection activity for a customer."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    customer = get_object_or_404(Customer.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = CollectionActivityForm(
            request.POST, tenant=tenant, customer=customer
        )
        if form.is_valid():
            activity = form.save(commit=False)
            activity.tenant = tenant
            activity.customer = customer
            activity.created_by = request.user
            activity.save()

            messages.success(request, 'Collection activity recorded.')
            return redirect('accounts_receivable:collection_customer_detail',
                            tenant_slug=tenant_slug, pk=customer.pk)
    else:
        form = CollectionActivityForm(tenant=tenant, customer=customer)

    return render(request, 'accounts_receivable/collections/collection_activity_form.html', {
        'form': form,
        'customer': customer,
        'title': f'Add Collection Activity: {customer.display_name}',
    })


@login_required
def collection_activity_list(request, tenant_slug):
    """List all collection activities across customers."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = CollectionActivity.objects.filter(tenant=tenant).select_related(
        'customer', 'invoice', 'created_by'
    )

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts_receivable/collections/collection_activity_list.html', {
        'activities': page_obj,
        'page_obj': page_obj,
    })


# =============================================================================
# 8. Write-Offs
# =============================================================================

@login_required
def write_off_create(request, tenant_slug, pk):
    """Create a write-off for a specific invoice."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    invoice = get_object_or_404(Invoice.unscoped, pk=pk, tenant=tenant)

    if invoice.status in ('paid', 'void', 'written_off'):
        messages.error(request, 'Cannot write off a paid, voided, or already written-off invoice.')
        return redirect('accounts_receivable:invoice_detail',
                        tenant_slug=tenant_slug, pk=pk)

    if request.method == 'POST':
        form = WriteOffForm(request.POST, tenant=tenant)
        if form.is_valid():
            write_off = form.save(commit=False)
            write_off.tenant = tenant
            write_off.invoice = invoice
            write_off.created_by = request.user
            write_off.status = 'pending'
            write_off.save()

            messages.success(
                request,
                f'Write-off created for invoice "{invoice.invoice_number}". '
                f'Pending approval.'
            )
            return redirect('accounts_receivable:invoice_detail',
                            tenant_slug=tenant_slug, pk=pk)
    else:
        form = WriteOffForm(
            tenant=tenant,
            initial={'amount': invoice.balance_due}
        )

    return render(request, 'accounts_receivable/write_offs/write_off_form.html', {
        'form': form,
        'invoice': invoice,
        'title': f'Write Off: {invoice.invoice_number}',
    })


@login_required
def write_off_approve(request, tenant_slug, pk):
    """Approve a write-off and create GL journal entry. POST only."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    write_off = get_object_or_404(WriteOff.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if write_off.status != 'pending':
            messages.error(request, 'Only pending write-offs can be approved.')
        else:
            je = create_write_off_journal_entry(write_off, tenant, request.user)
            write_off.journal_entry = je
            write_off.status = 'approved'
            write_off.approved_by = request.user
            write_off.save()

            # Update invoice status
            invoice = write_off.invoice
            invoice.amount_paid += write_off.amount
            if invoice.amount_paid >= invoice.total_amount:
                invoice.status = 'written_off'
            else:
                invoice.update_payment_status()
            invoice.save()

            messages.success(
                request,
                f'Write-off approved for invoice "{invoice.invoice_number}".'
            )

    return redirect('accounts_receivable:invoice_detail',
                    tenant_slug=tenant_slug, pk=write_off.invoice.pk)


# =============================================================================
# 9. Aging Reports
# =============================================================================

@login_required
def ar_aging_summary(request, tenant_slug):
    """Calculate AR aging buckets grouped by customer."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    form = ARAgingReportFilterForm(request.GET or None, tenant=tenant)

    as_of_date = timezone.now().date()
    if form.is_valid():
        if form.cleaned_data.get('as_of_date'):
            as_of_date = form.cleaned_data['as_of_date']

    # Get open invoices (exclude draft, void, written_off, paid)
    invoices_qs = Invoice.objects.filter(tenant=tenant).exclude(
        status__in=['draft', 'void', 'written_off', 'paid']
    ).select_related('customer')

    # Filter by customer if specified
    customer_filter = None
    if form.is_valid() and form.cleaned_data.get('customer'):
        customer_filter = form.cleaned_data['customer']
        invoices_qs = invoices_qs.filter(customer=customer_filter)

    # Calculate aging buckets per customer
    customer_aging = {}
    for invoice in invoices_qs:
        customer_id = invoice.customer_id
        if customer_id not in customer_aging:
            customer_aging[customer_id] = {
                'customer': invoice.customer,
                'current': Decimal('0.00'),
                'days_1_30': Decimal('0.00'),
                'days_31_60': Decimal('0.00'),
                'days_61_90': Decimal('0.00'),
                'days_over_90': Decimal('0.00'),
                'total': Decimal('0.00'),
            }

        balance = invoice.total_amount - invoice.amount_paid
        days_outstanding = (as_of_date - invoice.due_date).days

        entry = customer_aging[customer_id]
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
    for entry in customer_aging.values():
        grand_totals['current'] += entry['current']
        grand_totals['days_1_30'] += entry['days_1_30']
        grand_totals['days_31_60'] += entry['days_31_60']
        grand_totals['days_61_90'] += entry['days_61_90']
        grand_totals['days_over_90'] += entry['days_over_90']
        grand_totals['total'] += entry['total']

    aging_data = sorted(customer_aging.values(), key=lambda x: x['customer'].display_name)

    return render(request, 'accounts_receivable/reports/ar_aging_summary.html', {
        'form': form,
        'aging_data': aging_data,
        'grand_totals': grand_totals,
        'as_of_date': as_of_date,
    })


@login_required
def ar_aging_detail(request, tenant_slug, customer_pk):
    """Show individual invoices for a customer with aging details."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    customer = get_object_or_404(Customer.unscoped, pk=customer_pk, tenant=tenant)

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

    invoices = Invoice.objects.filter(
        tenant=tenant, customer=customer
    ).exclude(
        status__in=['draft', 'void', 'written_off', 'paid']
    ).order_by('due_date')

    # Add aging info to each invoice
    invoice_aging = []
    total_balance = Decimal('0.00')
    for invoice in invoices:
        balance = invoice.total_amount - invoice.amount_paid
        days_outstanding = (as_of_date - invoice.due_date).days

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

        invoice_aging.append({
            'invoice': invoice,
            'balance': balance,
            'days_outstanding': days_outstanding,
            'aging_bucket': aging_bucket,
        })
        total_balance += balance

    return render(request, 'accounts_receivable/reports/ar_aging_detail.html', {
        'customer': customer,
        'invoice_aging': invoice_aging,
        'total_balance': total_balance,
        'as_of_date': as_of_date,
    })


@login_required
def ar_aging_export(request, tenant_slug):
    """Export AR aging report as CSV."""
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

    invoices = Invoice.objects.filter(tenant=tenant).exclude(
        status__in=['draft', 'void', 'written_off', 'paid']
    ).select_related('customer').order_by('customer__display_name', 'due_date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="ar_aging_{as_of_date}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        'Customer', 'Invoice Number', 'Invoice Date', 'Due Date',
        'Total Amount', 'Amount Paid', 'Balance',
        'Days Outstanding', 'Aging Bucket',
    ])

    for invoice in invoices:
        balance = invoice.total_amount - invoice.amount_paid
        days_outstanding = (as_of_date - invoice.due_date).days

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
            invoice.customer.display_name,
            invoice.invoice_number,
            invoice.invoice_date,
            invoice.due_date,
            invoice.total_amount,
            invoice.amount_paid,
            balance,
            days_outstanding,
            aging_bucket,
        ])

    return response
