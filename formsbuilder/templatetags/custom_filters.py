from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    """Get a value from a dictionary using a key, returning default if key doesn't exist."""
    return dictionary.get(key) if dictionary and key else None