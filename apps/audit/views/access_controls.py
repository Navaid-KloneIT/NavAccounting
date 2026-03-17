from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import AccessPolicyForm, AccessReviewForm, AccessReviewItemFormSet
from ..models import AccessPolicy, AccessReview, AccessReviewItem
from ..services import calculate_access_review_findings


# =============================================================================
# Access Policies
# =============================================================================

@login_required
def access_policy_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = AccessPolicy.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(policy_number__icontains=search) |
            Q(name__icontains=search)
        )

    policy_type_filter = request.GET.get('policy_type', '')
    if policy_type_filter:
        qs = qs.filter(policy_type=policy_type_filter)

    access_level_filter = request.GET.get('access_level', '')
    if access_level_filter:
        qs = qs.filter(access_level=access_level_filter)

    status_filter = request.GET.get('status', '')
    if status_filter:
        if status_filter == 'active':
            qs = qs.filter(is_active=True)
        elif status_filter == 'inactive':
            qs = qs.filter(is_active=False)
        else:
            qs = qs.filter(status=status_filter)

    stats = {
        'total_count': qs.count(),
        'active_count': qs.filter(is_active=True).count(),
        'inactive_count': qs.filter(is_active=False).count(),
    }

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'audit/access_controls/access_policy_list.html', {
        'policies': page_obj,
        'page_obj': page_obj,
        'total_count': stats['total_count'],
        'active_count': stats['active_count'],
        'inactive_count': stats['inactive_count'],
        'policy_type_choices': AccessPolicy.POLICY_TYPE_CHOICES,
        'access_level_choices': AccessPolicy.ACCESS_LEVEL_CHOICES,
        'status_choices': AccessPolicy.STATUS_CHOICES,
    })


@login_required
def access_policy_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = AccessPolicyForm(request.POST, tenant=tenant)
        if form.is_valid():
            policy = form.save(commit=False)
            policy.tenant = tenant
            policy.policy_number = AccessPolicy.generate_policy_number(tenant)
            policy.save()
            messages.success(request, f'Access Policy "{policy.name}" created.')
            return redirect('audit:access_policy_detail', tenant_slug=tenant.slug, pk=policy.pk)
    else:
        form = AccessPolicyForm(tenant=tenant)

    return render(request, 'audit/access_controls/access_policy_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def access_policy_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    policy = get_object_or_404(AccessPolicy.unscoped, pk=pk, tenant=tenant)

    return render(request, 'audit/access_controls/access_policy_detail.html', {
        'policy': policy,
    })


@login_required
def access_policy_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    policy = get_object_or_404(AccessPolicy.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = AccessPolicyForm(request.POST, instance=policy, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Access Policy "{policy.name}" updated.')
            return redirect('audit:access_policy_detail', tenant_slug=tenant.slug, pk=policy.pk)
    else:
        form = AccessPolicyForm(instance=policy, tenant=tenant)

    return render(request, 'audit/access_controls/access_policy_form.html', {
        'form': form, 'is_edit': True, 'policy': policy,
    })


# =============================================================================
# Access Reviews
# =============================================================================

@login_required
def access_review_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = AccessReview.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(review_number__icontains=search) |
            Q(name__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    scope_filter = request.GET.get('scope', '')
    if scope_filter:
        qs = qs.filter(scope=scope_filter)

    stats = {
        'total_count': qs.count(),
        'planned_count': qs.filter(status='planned').count(),
        'completed_count': qs.filter(status='completed').count(),
    }

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'audit/access_controls/access_review_list.html', {
        'reviews': page_obj,
        'page_obj': page_obj,
        'total_count': stats['total_count'],
        'planned_count': stats['planned_count'],
        'completed_count': stats['completed_count'],
        'status_choices': AccessReview.STATUS_CHOICES,
        'scope_choices': AccessReview.SCOPE_CHOICES,
    })


@login_required
def access_review_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = AccessReviewForm(request.POST)
        formset = AccessReviewItemFormSet(request.POST, prefix='items')
        if form.is_valid() and formset.is_valid():
            review = form.save(commit=False)
            review.tenant = tenant
            review.review_number = AccessReview.generate_review_number(tenant)
            if not review.reviewer_id:
                review.reviewer = request.user
            review.save()
            formset.instance = review
            items = formset.save(commit=False)
            for item in items:
                item.tenant = tenant
                item.item_number = AccessReviewItem.generate_item_number(tenant)
                item.save()
            for obj in formset.deleted_objects:
                obj.delete()
            calculate_access_review_findings(review)
            messages.success(request, f'Access Review "{review.name}" created.')
            return redirect('audit:access_review_detail', tenant_slug=tenant.slug, pk=review.pk)
    else:
        form = AccessReviewForm()
        formset = AccessReviewItemFormSet(prefix='items')

    return render(request, 'audit/access_controls/access_review_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def access_review_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    review = get_object_or_404(AccessReview.unscoped, pk=pk, tenant=tenant)
    items = review.items.select_related('policy', 'user').all()

    return render(request, 'audit/access_controls/access_review_detail.html', {
        'review': review,
        'items': items,
    })


@login_required
def access_review_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    review = get_object_or_404(AccessReview.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = AccessReviewForm(request.POST, instance=review)
        formset = AccessReviewItemFormSet(
            request.POST, instance=review, prefix='items',
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            items = formset.save(commit=False)
            for item in items:
                item.tenant = tenant
                if not item.item_number:
                    item.item_number = AccessReviewItem.generate_item_number(tenant)
                item.save()
            for obj in formset.deleted_objects:
                obj.delete()
            calculate_access_review_findings(review)
            messages.success(request, f'Access Review "{review.name}" updated.')
            return redirect('audit:access_review_detail', tenant_slug=tenant.slug, pk=review.pk)
    else:
        form = AccessReviewForm(instance=review)
        formset = AccessReviewItemFormSet(instance=review, prefix='items')

    return render(request, 'audit/access_controls/access_review_form.html', {
        'form': form, 'formset': formset, 'is_edit': True, 'review': review,
    })
