import json
from datetime import timedelta

from allauth.account.views import (
    ConfirmEmailView,
    LoginView,
    PasswordResetFromKeyView,
    PasswordResetView,
    SignupView,
)
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.roles.models import Role
from apps.tenants.managers import set_current_tenant
from apps.tenants.models import TenantMembership

from .forms import ProfileForm, UserInviteForm
from .models import CustomUser, UserInvitation, UserProfile


def root_redirect(request):
    """Redirect root URL to login or dashboard."""
    if request.user.is_authenticated:
        return redirect('tenants:select')
    return redirect('account_login')


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'


class CustomSignupView(SignupView):
    template_name = 'accounts/register.html'


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/forgot_password.html'


class CustomPasswordResetFromKeyView(PasswordResetFromKeyView):
    template_name = 'accounts/reset_password.html'


class CustomConfirmEmailView(ConfirmEmailView):
    template_name = 'accounts/email_confirm.html'


def email_verification_sent(request):
    return render(request, 'accounts/email_verification_sent.html')


def custom_logout(request):
    logout(request)
    return redirect('account_login')


@login_required
def user_profile(request, tenant_slug):
    """User profile edit page."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    profile, _ = UserProfile.unscoped.get_or_create(
        user=request.user,
        tenant=tenant,
        defaults={'job_title': '', 'department': ''}
    )

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            # Update user fields
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.phone = form.cleaned_data['phone']
            if form.cleaned_data.get('avatar'):
                request.user.avatar = form.cleaned_data['avatar']
            request.user.save()

            # Update profile fields
            profile.job_title = form.cleaned_data['job_title']
            profile.department = form.cleaned_data['department']
            profile.bio = form.cleaned_data['bio']
            profile.timezone = form.cleaned_data.get('timezone', 'UTC')
            profile.date_format = form.cleaned_data.get('date_format', 'YYYY-MM-DD')
            profile.save()

            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile', tenant_slug=tenant_slug)
    else:
        form = ProfileForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'phone': request.user.phone,
            'job_title': profile.job_title,
            'department': profile.department,
            'bio': profile.bio,
            'timezone': profile.timezone,
            'date_format': profile.date_format,
        })

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def user_list(request, tenant_slug):
    """List all users in the current tenant."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    memberships = TenantMembership.objects.filter(
        tenant=tenant
    ).select_related('user')

    # Compute stats before filtering
    total_members = memberships.count()
    active_members = memberships.filter(user__is_active=True).count()
    inactive_members = total_members - active_members

    # Server-side filters
    search_query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if search_query:
        memberships = memberships.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    if status_filter == 'active':
        memberships = memberships.filter(user__is_active=True)
    elif status_filter == 'inactive':
        memberships = memberships.filter(user__is_active=False)

    if role_filter:
        from apps.roles.models import TenantUserRole
        user_ids_with_role = TenantUserRole.unscoped.filter(
            role_id=role_filter, tenant=tenant
        ).values_list('user_id', flat=True)
        memberships = memberships.filter(user_id__in=user_ids_with_role)

    # Attach profile to each membership
    members = []
    for membership in memberships:
        profile = UserProfile.unscoped.filter(
            user=membership.user, tenant=tenant
        ).first()
        membership.profile = profile
        members.append(membership)

    # Pagination
    paginator = Paginator(members, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    invitations = UserInvitation.unscoped.filter(
        tenant=tenant, is_accepted=False
    )
    pending_invitations = invitations.count()

    # All roles for filter dropdown
    all_roles = Role.objects.filter(tenant=tenant)

    return render(request, 'accounts/user_list.html', {
        'members': page_obj,
        'page_obj': page_obj,
        'invitations': invitations,
        'total_members': total_members,
        'active_members': active_members,
        'inactive_members': inactive_members,
        'pending_invitations': pending_invitations,
        'all_roles': all_roles,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    })


@login_required
def user_invite(request, tenant_slug):
    """Invite a new user to the tenant."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    roles = Role.objects.filter(tenant=tenant)

    if request.method == 'POST':
        form = UserInviteForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            role_id = form.cleaned_data.get('role')

            # Check if already a member
            existing_user = CustomUser.objects.filter(email=email).first()
            if existing_user:
                if TenantMembership.objects.filter(user=existing_user, tenant=tenant).exists():
                    messages.warning(request, f'{email} is already a member of this organization.')
                    return redirect('accounts:user_list', tenant_slug=tenant_slug)

            # Check for existing invitation
            if UserInvitation.unscoped.filter(email=email, tenant=tenant, is_accepted=False).exists():
                messages.warning(request, f'An invitation has already been sent to {email}.')
                return redirect('accounts:user_list', tenant_slug=tenant_slug)

            role = None
            if role_id:
                role = Role.objects.filter(id=role_id, tenant=tenant).first()

            invitation = UserInvitation(
                email=email,
                invited_by=request.user,
                role=role,
                tenant=tenant,
                expires_at=timezone.now() + timedelta(days=7),
            )
            invitation.save()

            messages.success(request, f'Invitation sent to {email}.')
            return redirect('accounts:user_list', tenant_slug=tenant_slug)
    else:
        form = UserInviteForm()

    return render(request, 'accounts/user_invite.html', {
        'form': form,
        'roles': roles,
    })


def accept_invitation(request, token):
    """Accept an invitation to join a tenant."""
    invitation = get_object_or_404(
        UserInvitation.unscoped,
        token=token,
        is_accepted=False
    )

    if invitation.expires_at < timezone.now():
        messages.error(request, 'This invitation has expired.')
        return redirect('account_login')

    # If user exists, add them to the tenant
    existing_user = CustomUser.objects.filter(email=invitation.email).first()
    if existing_user:
        TenantMembership.objects.get_or_create(
            user=existing_user, tenant=invitation.tenant
        )
        invitation.is_accepted = True
        invitation.accepted_at = timezone.now()
        invitation.save()

        if invitation.role:
            from apps.roles.models import TenantUserRole
            TenantUserRole.unscoped.get_or_create(
                user=existing_user,
                role=invitation.role,
                tenant=invitation.tenant,
                defaults={'assigned_by': invitation.invited_by}
            )

        messages.success(request, f'You have joined {invitation.tenant.name}.')
        if request.user.is_authenticated:
            return redirect('dashboard:index', tenant_slug=invitation.tenant.slug)
        return redirect('account_login')

    # If user doesn't exist, redirect to registration
    messages.info(request, 'Please create an account to accept the invitation.')
    return redirect('account_signup')


@login_required
def user_profile_view(request, tenant_slug, user_id):
    """View another user's profile."""
    tenant = request.tenant
    user = get_object_or_404(CustomUser, id=user_id)
    profile = UserProfile.unscoped.filter(user=user, tenant=tenant).first()

    return render(request, 'accounts/profile.html', {
        'profile_user': user,
        'profile': profile,
    })
