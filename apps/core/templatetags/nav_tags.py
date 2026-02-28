from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def is_active(context, url_name, *args):
    """Check if the current URL matches the given URL name."""
    request = context.get('request')
    if not request:
        return ''

    from django.urls import resolve, reverse

    try:
        current_url = resolve(request.path_info).url_name
        if current_url == url_name:
            return 'active'
    except Exception:
        pass

    return ''


@register.simple_tag(takes_context=True)
def is_menu_open(context, *url_names):
    """Check if any of the given URL names match (for submenu expansion)."""
    request = context.get('request')
    if not request:
        return ''

    from django.urls import resolve

    try:
        current_url = resolve(request.path_info).url_name
        if current_url in url_names:
            return 'show'
    except Exception:
        pass

    return ''


@register.filter
def has_permission(user, permission_codename):
    """Check if a user has a specific permission in the current tenant."""
    if user.is_superuser:
        return True

    from apps.roles.models import TenantUserRole
    return TenantUserRole.unscoped.filter(
        user=user,
        role__permissions__codename=permission_codename
    ).exists()
