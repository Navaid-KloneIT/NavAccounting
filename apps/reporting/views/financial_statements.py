from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import FinancialStatementForm, FinancialStatementLineFormSet
from ..models import FinancialStatement


@login_required
def statement_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = FinancialStatement.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    published_count = qs.filter(status='published').count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(statement_number__icontains=search) | Q(name__icontains=search)
        )

    # Type filter
    stmt_type = request.GET.get('type', '')
    if stmt_type:
        qs = qs.filter(statement_type=stmt_type)

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reporting/financial_statements/statement_list.html', {
        'statements': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'published_count': published_count,
        'type_choices': FinancialStatement.STATEMENT_TYPE_CHOICES,
        'status_choices': FinancialStatement.STATUS_CHOICES,
    })


@login_required
def statement_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = FinancialStatementForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Financial statement "{obj.statement_number}" created.')
            return redirect('reporting:statement_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = FinancialStatementForm(tenant=tenant)

    return render(request, 'reporting/financial_statements/statement_form.html', {
        'form': form,
        'is_create': True,
    })


@login_required
def statement_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    statement = get_object_or_404(FinancialStatement, pk=pk, tenant=tenant)
    lines = statement.lines.all()

    return render(request, 'reporting/financial_statements/statement_detail.html', {
        'statement': statement,
        'lines': lines,
    })


@login_required
def statement_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    statement = get_object_or_404(FinancialStatement, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = FinancialStatementForm(request.POST, instance=statement, tenant=tenant)
        line_formset = FinancialStatementLineFormSet(request.POST, instance=statement)
        if form.is_valid() and line_formset.is_valid():
            form.save()
            lines = line_formset.save(commit=False)
            for line in lines:
                line.tenant = tenant
                line.save()
            for line in line_formset.deleted_objects:
                line.delete()
            messages.success(request, f'Statement "{statement.statement_number}" updated.')
            return redirect('reporting:statement_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = FinancialStatementForm(instance=statement, tenant=tenant)
        line_formset = FinancialStatementLineFormSet(instance=statement)

    return render(request, 'reporting/financial_statements/statement_form.html', {
        'form': form,
        'line_formset': line_formset,
        'statement': statement,
        'is_create': False,
    })


@login_required
def statement_generate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    statement = get_object_or_404(FinancialStatement, pk=pk, tenant=tenant)
    if statement.status == 'draft':
        statement.status = 'generated'
        statement.generated_at = timezone.now()
        statement.generated_by = request.user
        statement.save()
        messages.success(request, f'Statement "{statement.statement_number}" generated.')
    else:
        messages.warning(request, 'Statement can only be generated from draft status.')

    return redirect('reporting:statement_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def statement_approve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    statement = get_object_or_404(FinancialStatement, pk=pk, tenant=tenant)
    if statement.status == 'reviewed':
        statement.status = 'approved'
        statement.approved_by = request.user
        statement.approved_at = timezone.now()
        statement.save()
        messages.success(request, f'Statement "{statement.statement_number}" approved.')
    else:
        messages.warning(request, 'Statement must be reviewed before approval.')

    return redirect('reporting:statement_detail', tenant_slug=tenant.slug, pk=pk)
