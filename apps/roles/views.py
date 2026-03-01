from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from apps.tenants.models import TenantMembership

from .forms import RoleAssignForm, RoleForm
from .models import Permission, Role, TenantUserRole


@login_required
def role_list(request, tenant_slug):
    """List all roles for the current tenant."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    roles_qs = Role.objects.filter(tenant=tenant).prefetch_related('permissions', 'user_assignments')

    # Compute stats before filtering
    total_roles = roles_qs.count()
    system_roles = roles_qs.filter(is_system_role=True).count()
    custom_roles = total_roles - system_roles

    # Server-side filters
    search_query = request.GET.get('q', '').strip()
    role_type = request.GET.get('type', '').strip()

    if search_query:
        roles_qs = roles_qs.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    if role_type == 'system':
        roles_qs = roles_qs.filter(is_system_role=True)
    elif role_type == 'custom':
        roles_qs = roles_qs.filter(is_system_role=False)

    # Pagination
    paginator = Paginator(roles_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'roles/role_list.html', {
        'roles': page_obj,
        'page_obj': page_obj,
        'total_roles': total_roles,
        'system_roles': system_roles,
        'custom_roles': custom_roles,
        'search_query': search_query,
        'role_type': role_type,
    })


@login_required
def role_create(request, tenant_slug):
    """Create a new role."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    permissions = Permission.objects.all()

    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.tenant = tenant
            role.save()
            form.save_m2m()
            messages.success(request, f'Role "{role.name}" created successfully.')
            return redirect('roles:list', tenant_slug=tenant_slug)
    else:
        form = RoleForm()

    return render(request, 'roles/role_form.html', {
        'form': form,
        'permissions': permissions,
        'selected_permissions': [],
        'title': 'Create Role',
    })


@login_required
def role_edit(request, tenant_slug, pk):
    """Edit an existing role."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    role = get_object_or_404(Role, pk=pk, tenant=tenant)
    permissions = Permission.objects.all()

    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, f'Role "{role.name}" updated successfully.')
            return redirect('roles:list', tenant_slug=tenant_slug)
    else:
        form = RoleForm(instance=role)

    return render(request, 'roles/role_form.html', {
        'form': form,
        'permissions': permissions,
        'selected_permissions': list(role.permissions.values_list('id', flat=True)),
        'title': f'Edit Role: {role.name}',
    })


@login_required
def role_assign(request, tenant_slug):
    """Assign a role to a user."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    members = TenantMembership.objects.filter(tenant=tenant).select_related('user')
    roles = Role.objects.filter(tenant=tenant)
    selected_user = request.GET.get('user', '')

    if request.method == 'POST':
        user_id = request.POST.get('user')
        role_id = request.POST.get('role')

        from apps.accounts.models import CustomUser
        user = get_object_or_404(CustomUser, id=user_id)
        role = get_object_or_404(Role, id=role_id, tenant=tenant)

        TenantUserRole.unscoped.get_or_create(
            user=user,
            role=role,
            tenant=tenant,
            defaults={'assigned_by': request.user}
        )
        messages.success(request, f'Role "{role.name}" assigned to {user.get_full_name()}.')
        return redirect('accounts:user_list', tenant_slug=tenant_slug)

    return render(request, 'roles/assign_role.html', {
        'members': members,
        'roles': roles,
        'selected_user': selected_user,
    })
