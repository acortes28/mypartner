from django import template

register = template.Library()


@register.filter
def clp(value):
    """Formats a number as Chilean Peso: $1.234.567"""
    try:
        return "${:,.0f}".format(int(value)).replace(",", ".")
    except (ValueError, TypeError):
        return "$0"


@register.filter
def clp_abs(value):
    try:
        return "${:,.0f}".format(abs(int(value))).replace(",", ".")
    except (ValueError, TypeError):
        return "$0"


@register.filter
def abs_val(value):
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return 0


@register.filter
def is_negative(value):
    try:
        return int(value) < 0
    except (ValueError, TypeError):
        return False
