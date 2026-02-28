from django import template

register = template.Library()


@register.inclusion_tag('dashboard/widgets/_kpi_card.html')
def kpi_card(title, value, icon, color, change=None, change_color='success', change_direction='up'):
    """Render a KPI card widget."""
    return {
        'title': title,
        'value': value,
        'icon': icon,
        'color': color,
        'change': change,
        'change_color': change_color,
        'change_direction': change_direction,
    }


@register.filter
def currency(value):
    """Format a number as currency."""
    try:
        return f"${value:,.2f}"
    except (ValueError, TypeError):
        return value


@register.filter
def percentage(value):
    """Format a number as percentage."""
    try:
        return f"{value:.1f}%"
    except (ValueError, TypeError):
        return value
