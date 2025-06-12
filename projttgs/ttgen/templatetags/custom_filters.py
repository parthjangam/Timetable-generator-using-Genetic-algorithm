from django import template
import re

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key."""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def split(value, delimiter=','):
    """Split a string into a list using a delimiter."""
    return value.split(delimiter)

@register.filter
def make_list(value):
    """Convert a string to a list of characters."""
    return list(value)

@register.filter
def range(total):
    """Create a range from 1 to total (inclusive)"""
    return range(1, total + 1)