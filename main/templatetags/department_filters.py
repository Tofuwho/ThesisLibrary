from django import template
import re

register = template.Library()

@register.filter
def department_color(value):
    """
    Convert department name to a valid CSS class name.
    Takes first 4 characters, removes spaces and special characters.
    """
    if not value:
        return ''
    
    # Take first 4 characters
    short_name = value[:4]
    
    # Remove spaces and special characters, keep only alphanumeric
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', short_name)
    
    # Convert to lowercase
    return clean_name.lower()

@register.filter
def department_display(value):
    """
    Convert department name to display format.
    Takes first 4 characters and converts to uppercase.
    """
    if not value:
        return ''
    
    # Take first 4 characters and remove spaces
    short_name = value[:4].strip()
    
    # Convert to uppercase
    return short_name.upper()
