from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import CurrencyTranslationRuleForm, TranslationRunForm
from ..models import CurrencyTranslationRule, Entity, TranslationAdjustment


@login_required
def translation_rule_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = CurrencyTranslationRule.objects.filter(tenant=tenant).select_related(
        'account_type', 'specific_account'
    )

    total_count = qs.count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search))

    # Rate type filter
    rate_type = request.GET.get('rate_type', '')
    if rate_type:
        qs = qs.filter(rate_type=rate_type)

    # Status filter
    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'multi_entity/translation/translation_rule_list.html', {
        'rules': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'rate_type_choices': CurrencyTranslationRule.RATE_TYPE_CHOICES,
    })


@login_required
def translation_rule_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = CurrencyTranslationRuleForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Translation rule "{obj.name}" created.')
            return redirect('multi_entity:translation_rule_list', tenant_slug=tenant.slug)
    else:
        form = CurrencyTranslationRuleForm(tenant=tenant)

    return render(request, 'multi_entity/translation/translation_rule_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def translation_rule_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rule = get_object_or_404(CurrencyTranslationRule.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = CurrencyTranslationRuleForm(request.POST, instance=rule, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Translation rule "{rule.name}" updated.')
            return redirect('multi_entity:translation_rule_list', tenant_slug=tenant.slug)
    else:
        form = CurrencyTranslationRuleForm(instance=rule, tenant=tenant)

    return render(request, 'multi_entity/translation/translation_rule_form.html', {
        'form': form,
        'rule': rule,
        'is_edit': True,
    })


@login_required
def translation_run(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    result = None

    if request.method == 'POST':
        form = TranslationRunForm(request.POST, tenant=tenant)
        if form.is_valid():
            entity = form.cleaned_data['entity']
            fiscal_period = form.cleaned_data['fiscal_period']
            from ..services import run_currency_translation
            try:
                result = run_currency_translation(entity, fiscal_period, tenant, request.user)
                messages.success(request, f'Currency translation completed for {entity.code}.')
            except Exception as e:
                messages.error(request, f'Translation error: {e}')
    else:
        form = TranslationRunForm(tenant=tenant)

    return render(request, 'multi_entity/translation/translation_run.html', {
        'form': form,
        'result': result,
    })


@login_required
def translation_adjustment_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TranslationAdjustment.objects.filter(tenant=tenant).select_related(
        'entity', 'fiscal_period', 'from_currency', 'to_currency'
    )

    # Entity filter
    entity_id = request.GET.get('entity', '')
    if entity_id:
        qs = qs.filter(entity_id=entity_id)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    entities = Entity.unscoped.filter(tenant=tenant, status='active')

    return render(request, 'multi_entity/translation/translation_adjustment_list.html', {
        'adjustments': page_obj,
        'page_obj': page_obj,
        'entities': entities,
    })


@login_required
def translation_adjustment_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    adj = get_object_or_404(
        TranslationAdjustment.unscoped.select_related(
            'entity', 'fiscal_period', 'from_currency', 'to_currency', 'journal_entry'
        ),
        pk=pk, tenant=tenant
    )

    return render(request, 'multi_entity/translation/translation_adjustment_detail.html', {
        'adj': adj,
    })
