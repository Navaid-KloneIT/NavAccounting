"""Vendor Portal views — token-based authentication, no Django user required."""
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from .forms import PortalLoginForm, PortalMessageForm
from .models import Bill, Payment, VendorMessage, VendorPortalToken


def _get_portal_context(request):
    """Get vendor and tenant from session token. Returns (vendor, tenant) or None."""
    token_str = request.session.get('vendor_portal_token')
    if not token_str:
        return None, None

    try:
        portal_token = VendorPortalToken.unscoped.select_related(
            'vendor', 'tenant'
        ).get(token=token_str, is_active=True)
    except VendorPortalToken.DoesNotExist:
        return None, None

    if portal_token.is_expired:
        return None, None

    # Update last accessed
    portal_token.last_accessed = timezone.now()
    portal_token.save(update_fields=['last_accessed'])

    return portal_token.vendor, portal_token.tenant


def portal_login(request):
    """Token-based login for vendor portal."""
    if request.method == 'POST':
        form = PortalLoginForm(request.POST)
        if form.is_valid():
            token_str = form.cleaned_data['token'].strip()
            try:
                portal_token = VendorPortalToken.unscoped.get(
                    token=token_str, is_active=True
                )
                if not portal_token.is_expired:
                    request.session['vendor_portal_token'] = token_str
                    portal_token.last_accessed = timezone.now()
                    portal_token.save(update_fields=['last_accessed'])
                    return redirect('vendor_portal:portal_dashboard')
                else:
                    form.add_error('token', 'This access token has expired.')
            except VendorPortalToken.DoesNotExist:
                form.add_error('token', 'Invalid access token.')
    else:
        form = PortalLoginForm()

    return render(request, 'accounts_payable/portal/portal_login.html', {
        'form': form,
    })


def portal_dashboard(request):
    """Vendor portal dashboard — shows bills and payments overview."""
    vendor, tenant = _get_portal_context(request)
    if not vendor:
        return redirect('vendor_portal:portal_login')

    set_current_tenant(tenant)

    recent_bills = Bill.unscoped.filter(
        tenant=tenant, vendor=vendor
    ).exclude(status='draft').order_by('-bill_date')[:10]

    recent_payments = Payment.unscoped.filter(
        tenant=tenant, vendor=vendor, status='completed'
    ).order_by('-payment_date')[:10]

    outstanding_bills = Bill.unscoped.filter(
        tenant=tenant, vendor=vendor,
        status__in=['approved', 'partially_paid']
    )
    total_outstanding = sum(b.balance_due for b in outstanding_bills)

    unread_messages = VendorMessage.unscoped.filter(
        tenant=tenant, vendor=vendor, is_from_vendor=False, is_read=False
    ).count()

    return render(request, 'accounts_payable/portal/portal_dashboard.html', {
        'vendor': vendor,
        'tenant': tenant,
        'recent_bills': recent_bills,
        'recent_payments': recent_payments,
        'total_outstanding': total_outstanding,
        'outstanding_count': outstanding_bills.count(),
        'unread_messages': unread_messages,
    })


def portal_bill_detail(request, pk):
    """Vendor views a bill detail (read-only)."""
    vendor, tenant = _get_portal_context(request)
    if not vendor:
        return redirect('vendor_portal:portal_login')

    set_current_tenant(tenant)
    bill = get_object_or_404(
        Bill.unscoped, pk=pk, tenant=tenant, vendor=vendor
    )

    return render(request, 'accounts_payable/portal/portal_bill_detail.html', {
        'vendor': vendor,
        'tenant': tenant,
        'bill': bill,
        'lines': bill.lines.all().select_related('account'),
    })


def portal_messages(request):
    """Vendor portal messaging."""
    vendor, tenant = _get_portal_context(request)
    if not vendor:
        return redirect('vendor_portal:portal_login')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = PortalMessageForm(request.POST)
        if form.is_valid():
            VendorMessage.unscoped.create(
                tenant=tenant,
                vendor=vendor,
                subject=form.cleaned_data['subject'],
                body=form.cleaned_data['body'],
                is_from_vendor=True,
                sender_name=vendor.display_name,
            )
            return redirect('vendor_portal:portal_messages')
    else:
        form = PortalMessageForm()

    messages_list = VendorMessage.unscoped.filter(
        tenant=tenant, vendor=vendor
    ).order_by('-created_at')

    # Mark incoming messages as read
    VendorMessage.unscoped.filter(
        tenant=tenant, vendor=vendor, is_from_vendor=False, is_read=False
    ).update(is_read=True)

    return render(request, 'accounts_payable/portal/portal_messages.html', {
        'vendor': vendor,
        'tenant': tenant,
        'messages_list': messages_list,
        'form': form,
    })


def portal_message_detail(request, pk):
    """View a single message."""
    vendor, tenant = _get_portal_context(request)
    if not vendor:
        return redirect('vendor_portal:portal_login')

    set_current_tenant(tenant)
    message = get_object_or_404(
        VendorMessage.unscoped, pk=pk, tenant=tenant, vendor=vendor
    )

    if not message.is_from_vendor and not message.is_read:
        message.is_read = True
        message.save(update_fields=['is_read'])

    return render(request, 'accounts_payable/portal/portal_message_detail.html', {
        'vendor': vendor,
        'tenant': tenant,
        'message': message,
    })


def portal_logout(request):
    """Clear vendor portal session."""
    request.session.pop('vendor_portal_token', None)
    return redirect('vendor_portal:portal_login')
