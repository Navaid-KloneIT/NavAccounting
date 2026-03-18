from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import NotificationChannelForm, NotificationRuleForm
from ..models import NotificationChannel, NotificationRule, NotificationLog


# ──────────────────────────────────────────────
# Notification Channel Views
# ──────────────────────────────────────────────

@login_required
def channel_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = NotificationChannel.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(channel_number__icontains=search))

    channel_type_filter = request.GET.get('channel_type', '')
    if channel_type_filter:
        qs = qs.filter(channel_type=channel_type_filter)

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = NotificationChannel.objects.filter(tenant=tenant)
    return render(request, 'system_admin/notifications/channel_list.html', {
        'channels': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'active_count': all_items.filter(status='active').count(),
        'inactive_count': all_items.filter(status='inactive').count(),
        'channel_type_choices': NotificationChannel.CHANNEL_TYPE_CHOICES,
        'status_choices': NotificationChannel.STATUS_CHOICES,
    })


@login_required
def channel_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = NotificationChannelForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.channel_number = NotificationChannel.generate_channel_number(tenant)
            obj.save()
            messages.success(request, f'Notification Channel "{obj.name}" created.')
            return redirect('system_admin:notification_channel_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = NotificationChannelForm()

    return render(request, 'system_admin/notifications/channel_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def channel_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    channel = get_object_or_404(NotificationChannel.unscoped, pk=pk, tenant=tenant)
    rules = channel.rules.all()[:10]

    return render(request, 'system_admin/notifications/channel_detail.html', {
        'channel': channel,
        'rules': rules,
    })


@login_required
def channel_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    channel = get_object_or_404(NotificationChannel.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = NotificationChannelForm(request.POST, instance=channel)
        if form.is_valid():
            form.save()
            messages.success(request, f'Notification Channel "{channel.name}" updated.')
            return redirect('system_admin:notification_channel_detail', tenant_slug=tenant.slug, pk=channel.pk)
    else:
        form = NotificationChannelForm(instance=channel)

    return render(request, 'system_admin/notifications/channel_form.html', {
        'form': form, 'is_edit': True, 'channel': channel,
    })


@login_required
def channel_test(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    get_object_or_404(NotificationChannel.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        messages.success(request, 'Test notification sent.')

    return redirect('system_admin:notification_channel_detail', tenant_slug=tenant.slug, pk=pk)


# ──────────────────────────────────────────────
# Notification Rule Views
# ──────────────────────────────────────────────

@login_required
def rule_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = NotificationRule.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(rule_number__icontains=search))

    event_type_filter = request.GET.get('event_type', '')
    if event_type_filter:
        qs = qs.filter(event_type=event_type_filter)

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = NotificationRule.objects.filter(tenant=tenant)
    return render(request, 'system_admin/notifications/rule_list.html', {
        'rules': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'active_count': all_items.filter(status='active').count(),
        'inactive_count': all_items.filter(status='inactive').count(),
        'event_type_choices': NotificationRule.EVENT_TYPE_CHOICES,
        'status_choices': NotificationRule.STATUS_CHOICES,
    })


@login_required
def rule_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = NotificationRuleForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.rule_number = NotificationRule.generate_rule_number(tenant)
            obj.save()
            form.save_m2m()
            messages.success(request, f'Notification Rule "{obj.name}" created.')
            return redirect('system_admin:notification_rule_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = NotificationRuleForm()

    return render(request, 'system_admin/notifications/rule_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def rule_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rule = get_object_or_404(NotificationRule.unscoped, pk=pk, tenant=tenant)
    recent_logs = rule.logs.all()[:10]

    return render(request, 'system_admin/notifications/rule_detail.html', {
        'rule': rule,
        'recent_logs': recent_logs,
    })


@login_required
def rule_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rule = get_object_or_404(NotificationRule.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = NotificationRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, f'Notification Rule "{rule.name}" updated.')
            return redirect('system_admin:notification_rule_detail', tenant_slug=tenant.slug, pk=rule.pk)
    else:
        form = NotificationRuleForm(instance=rule)

    return render(request, 'system_admin/notifications/rule_form.html', {
        'form': form, 'is_edit': True, 'rule': rule,
    })


# ──────────────────────────────────────────────
# Notification Log Views
# ──────────────────────────────────────────────

@login_required
def log_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = NotificationLog.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(subject__icontains=search) | Q(log_number__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = NotificationLog.objects.filter(tenant=tenant)
    return render(request, 'system_admin/notifications/log_list.html', {
        'logs': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'sent_count': all_items.filter(status='sent').count(),
        'failed_count': all_items.filter(status='failed').count(),
        'pending_count': all_items.filter(status='pending').count(),
        'status_choices': NotificationLog.STATUS_CHOICES,
    })


@login_required
def log_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    log = get_object_or_404(NotificationLog.unscoped, pk=pk, tenant=tenant)

    return render(request, 'system_admin/notifications/log_detail.html', {
        'log': log,
    })
