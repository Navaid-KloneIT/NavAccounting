from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from .forms import CompanySetupForm, FiscalYearForm
from .models import (
    ChartOfAccountsTemplate,
    CompanySettings,
    Currency,
    FiscalYear,
)


@login_required
def company_setup(request, tenant_slug):
    """Company settings setup page."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    settings_obj, created = CompanySettings.unscoped.get_or_create(
        tenant=tenant,
        defaults={
            'company_name': tenant.name,
            'base_currency': Currency.objects.filter(code='USD').first() or Currency.objects.first(),
        }
    )
    currencies = Currency.objects.filter(is_active=True)

    if request.method == 'POST':
        form = CompanySetupForm(request.POST, instance=settings_obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, 'Company settings updated successfully.')
            return redirect('company:setup', tenant_slug=tenant_slug)
    else:
        form = CompanySetupForm(instance=settings_obj)

    return render(request, 'company/setup.html', {
        'form': form,
        'currencies': currencies,
    })


@login_required
def fiscal_year_list(request, tenant_slug):
    """List all fiscal years."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = FiscalYear.objects.filter(tenant=tenant).prefetch_related('periods')

    # Stats (before filtering)
    total_count = qs.count()
    open_count = qs.filter(is_closed=False).count()
    closed_count = qs.filter(is_closed=True).count()

    # Search filter
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(name__icontains=search_query)

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'open':
        qs = qs.filter(is_closed=False)
    elif status_filter == 'closed':
        qs = qs.filter(is_closed=True)

    # Pagination
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'company/fiscal_year_list.html', {
        'fiscal_years': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'open_count': open_count,
        'closed_count': closed_count,
    })


@login_required
def fiscal_year_create(request, tenant_slug):
    """Create a new fiscal year."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = FiscalYearForm(request.POST)
        if form.is_valid():
            fy = form.save(commit=False)
            fy.tenant = tenant
            fy.save()
            messages.success(request, f'Fiscal year "{fy.name}" created.')
            return redirect('company:fiscal_year_list', tenant_slug=tenant_slug)
    else:
        form = FiscalYearForm()

    return render(request, 'company/fiscal_year_form.html', {
        'form': form,
        'title': 'Create Fiscal Year',
    })


@login_required
def fiscal_year_edit(request, tenant_slug, pk):
    """Edit a fiscal year."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    fy = get_object_or_404(FiscalYear, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = FiscalYearForm(request.POST, instance=fy)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fiscal year "{fy.name}" updated.')
            return redirect('company:fiscal_year_list', tenant_slug=tenant_slug)
    else:
        form = FiscalYearForm(instance=fy)

    return render(request, 'company/fiscal_year_form.html', {
        'form': form,
        'title': f'Edit: {fy.name}',
    })


@login_required
def currency_settings(request, tenant_slug):
    """View currency settings."""
    qs = Currency.objects.all()

    # Stats (before filtering)
    total_count = qs.count()
    active_count = qs.filter(is_active=True).count()
    inactive_count = qs.filter(is_active=False).count()

    # Search filter
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(Q(code__icontains=search_query) | Q(name__icontains=search_query))

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    # Pagination
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'company/currency_settings.html', {
        'currencies': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
    })


@login_required
def coa_template_list(request, tenant_slug):
    """List chart of accounts templates."""
    qs = ChartOfAccountsTemplate.objects.all().prefetch_related('items')

    # Stats (before filtering)
    total_count = qs.count()

    # Search filter
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(name__icontains=search_query) |
            Q(country__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Country filter
    country_filter = request.GET.get('country', '')
    if country_filter:
        qs = qs.filter(country=country_filter)

    # Get unique countries for dropdown
    all_countries = (
        ChartOfAccountsTemplate.objects
        .exclude(country='')
        .values_list('country', flat=True)
        .distinct()
        .order_by('country')
    )

    # Pagination
    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'company/coa_template_list.html', {
        'templates': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'all_countries': all_countries,
    })


@login_required
def coa_template_detail(request, tenant_slug, pk):
    """View a specific COA template and its accounts."""
    template = get_object_or_404(ChartOfAccountsTemplate, pk=pk)
    items = template.items.select_related('account_type', 'parent').all()
    return render(request, 'company/coa_template_form.html', {
        'template': template,
        'items': items,
    })
