# shop/templatetags/custom_tags.py

from django import template

register = template.Library()

@register.filter
def to_range(start, end):
    """Return a range of integers from start up to and including end."""
    try:
        start, end = int(start), int(end)
        return range(start, end + 1)
    except ValueError:
        return []
