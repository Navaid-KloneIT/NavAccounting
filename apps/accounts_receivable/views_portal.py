"""Customer Portal views — token-based authentication, no Django user required."""
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from .forms import CustomerPortalLoginForm, CustomerPortalMessageForm
from .models import Customer, CustomerMessage, CustomerPortalToken, Invoice, Receipt


def _get_portal_context(request):
    """Get customer and tenant from session token. Returns (customer, tenant) or None."""
    token_str = request.session.get('customer_portal_token')
    if not token_str:
        return None, None

    try:
        portal_token = CustomerPortalToken.unscoped.select_related(
            'customer', 'tenant'
        ).get(token=token_str, is_active=True)
    except CustomerPortalToken.DoesNotExist:
        return None, None

    if portal_token.is_expired:
        return None, None

    # Update last accessed
    portal_token.last_accessed = timezone.now()
    portal_token.save(update_fields=['last_accessed'])

    return portal_token.customer, portal_token.tenant


def portal_login(request):
    """Token-based login for customer portal."""
    if request.method == 'POST':
        form = CustomerPortalLoginForm(request.POST)
        if form.is_valid():
            token_str = form.cleaned_data['token'].strip()
            try:
                portal_token = CustomerPortalToken.unscoped.get(
                    token=token_str, is_active=True
                )
                if not portal_token.is_expired:
                    request.session['customer_portal_token'] = token_str
                    portal_token.last_accessed = timezone.now()
                    portal_token.save(update_fields=['last_accessed'])
                    return redirect('customer_portal:portal_dashboard')
                else:
                    form.add_error('token', 'This access token has expired.')
            except CustomerPortalToken.DoesNotExist:
                form.add_error('token', 'Invalid access token.')
    else:
        form = CustomerPortalLoginForm()

    return render(request, 'accounts_receivable/portal/portal_login.html', {
        'form': form,
    })


def portal_dashboard(request):
    """Customer portal dashboard — shows outstanding invoices, recent receipts, messages."""
    customer, tenant = _get_portal_context(request)
    if not customer:
        return redirect('customer_portal:portal_login')

    set_current_tenant(tenant)

    outstanding_invoices = Invoice.unscoped.filter(
        tenant=tenant, customer=customer,
        status__in=['sent', 'approved', 'partially_paid']
    ).order_by('-invoice_date')[:10]

    total_outstanding = sum(inv.balance_due for inv in outstanding_invoices)

    recent_receipts = Receipt.unscoped.filter(
        tenant=tenant, customer=customer, status='completed'
    ).order_by('-receipt_date')[:10]

    unread_messages = CustomerMessage.unscoped.filter(
        tenant=tenant, customer=customer, is_from_customer=False, is_read=False
    ).count()

    return render(request, 'accounts_receivable/portal/portal_dashboard.html', {
        'customer': customer,
        'tenant': tenant,
        'outstanding_invoices': outstanding_invoices,
        'total_outstanding': total_outstanding,
        'outstanding_count': outstanding_invoices.count() if hasattr(outstanding_invoices, 'count') else len(outstanding_invoices),
        'recent_receipts': recent_receipts,
        'unread_messages': unread_messages,
    })


def portal_invoice_list(request):
    """List all invoices for this customer."""
    customer, tenant = _get_portal_context(request)
    if not customer:
        return redirect('customer_portal:portal_login')

    set_current_tenant(tenant)

    invoices = Invoice.unscoped.filter(
        tenant=tenant, customer=customer
    ).exclude(status='draft').order_by('-invoice_date')

    return render(request, 'accounts_receivable/portal/portal_invoice_list.html', {
        'customer': customer,
        'tenant': tenant,
        'invoices': invoices,
    })


def portal_invoice_detail(request, pk):
    """Customer views an invoice detail (read-only) with line items."""
    customer, tenant = _get_portal_context(request)
    if not customer:
        return redirect('customer_portal:portal_login')

    set_current_tenant(tenant)
    invoice = get_object_or_404(
        Invoice.unscoped, pk=pk, tenant=tenant, customer=customer
    )

    return render(request, 'accounts_receivable/portal/portal_invoice_detail.html', {
        'customer': customer,
        'tenant': tenant,
        'invoice': invoice,
        'lines': invoice.lines.all().select_related('account'),
    })


def portal_make_payment(request, pk):
    """Placeholder for online payment — shows payment options info."""
    customer, tenant = _get_portal_context(request)
    if not customer:
        return redirect('customer_portal:portal_login')

    set_current_tenant(tenant)
    invoice = get_object_or_404(
        Invoice.unscoped, pk=pk, tenant=tenant, customer=customer
    )

    return render(request, 'accounts_receivable/portal/portal_make_payment.html', {
        'customer': customer,
        'tenant': tenant,
        'invoice': invoice,
    })


def portal_messages(request):
    """Customer portal messaging."""
    customer, tenant = _get_portal_context(request)
    if not customer:
        return redirect('customer_portal:portal_login')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = CustomerPortalMessageForm(request.POST)
        if form.is_valid():
            CustomerMessage.unscoped.create(
                tenant=tenant,
                customer=customer,
                subject=form.cleaned_data['subject'],
                body=form.cleaned_data['body'],
                is_from_customer=True,
                sender_name=customer.display_name,
            )
            return redirect('customer_portal:portal_messages')
    else:
        form = CustomerPortalMessageForm()

    messages_list = CustomerMessage.unscoped.filter(
        tenant=tenant, customer=customer
    ).order_by('-created_at')

    # Mark incoming messages as read
    CustomerMessage.unscoped.filter(
        tenant=tenant, customer=customer, is_from_customer=False, is_read=False
    ).update(is_read=True)

    return render(request, 'accounts_receivable/portal/portal_messages.html', {
        'customer': customer,
        'tenant': tenant,
        'messages_list': messages_list,
        'form': form,
    })


def portal_message_detail(request, pk):
    """View a single message."""
    customer, tenant = _get_portal_context(request)
    if not customer:
        return redirect('customer_portal:portal_login')

    set_current_tenant(tenant)
    message = get_object_or_404(
        CustomerMessage.unscoped, pk=pk, tenant=tenant, customer=customer
    )

    if not message.is_from_customer and not message.is_read:
        message.is_read = True
        message.save(update_fields=['is_read'])

    return render(request, 'accounts_receivable/portal/portal_message_detail.html', {
        'customer': customer,
        'tenant': tenant,
        'message': message,
    })


def portal_logout(request):
    """Clear customer portal session."""
    request.session.pop('customer_portal_token', None)
    return redirect('customer_portal:portal_login')
