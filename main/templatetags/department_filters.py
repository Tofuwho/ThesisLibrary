from django import template
import re
import json

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
def dept_theme_code(value):
    """
    Map department names to specific theme color codes used in the UI.
    Returns: 'graduate', 'ce', 'cict', 'cas', 'cbm', 'ccj', 'chtm', 'cet', or 'coll'
    """
    if not value:
        return 'coll'
    
    dl = value.lower()
    if 'graduate' in dl:
        return 'graduate'
    elif 'education' in dl:
        return 'ce'
    elif any(word in dl for word in ['information', 'ict', 'computer']):
        return 'cict'
    elif any(word in dl for word in ['arts', 'sciences', 'science']):
        return 'cas'
    elif any(word in dl for word in ['business', 'management', 'account']):
        return 'cbm'
    elif any(word in dl for word in ['criminal', 'justice']):
        return 'ccj'
    elif any(word in dl for word in ['hospitality', 'tourism', 'hotel']):
        return 'chtm'
    elif any(word in dl for word in ['engineering', 'technology', 'industrial']):
        return 'cet'
    
    return 'coll'

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

@register.filter
def admin_changed_fields(change_message):
    """
    Extract a concise, human-readable list of changed field names from a
    Django admin LogEntry.change_message. When Django records a change, the
    message is typically a JSON array of objects like:
    [{"changed": {"fields": ["title", "status"]}}]

    This filter returns a string like: "Changed: title, status"
    If the message isn't JSON or has a different structure, the original
    message is returned.
    """
    if not change_message:
        return ''

    # If it doesn't look like JSON, return as-is
    if not isinstance(change_message, str) or not change_message.strip().startswith('['):
        return change_message

    try:
        data = json.loads(change_message)
    except Exception:
        return change_message

    # Find any "changed" entries and aggregate field names
    changed_fields = []
    try:
        for entry in data:
            if not isinstance(entry, dict):
                continue
            changed = entry.get('changed') or entry.get('fields_changed')
            if isinstance(changed, dict):
                fields = changed.get('fields')
                if isinstance(fields, list):
                    for field in fields:
                        if isinstance(field, str):
                            changed_fields.append(field)
    except Exception:
        return change_message

    if changed_fields:
        return 'Changed: ' + ', '.join(changed_fields)

    return change_message

@register.filter
def format_coauthors(value):
    """
    Render co-authors from various stored formats into a readable string.
    Supports:
    - list[str]
    - list[dict{first_name,last_name,student_id,email}]
    - JSON string of the above
    - plain string (returned as-is)
    """
    if not value:
        return ''

    data = value
    if isinstance(value, str):
        # Try JSON first; otherwise return as-is
        v = value.strip()
        if v.startswith('[') or v.startswith('{'):
            try:
                data = json.loads(value)
            except Exception:
                return value
        else:
            return value

    # Handle Django QuerySets or Managers
    from django.db.models.query import QuerySet
    from django.db.models.manager import Manager
    if isinstance(data, (QuerySet, Manager)):
        data = list(data)

    names = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                first = (item.get('first_name') or '').strip()
                last = (item.get('last_name') or '').strip()
                full = (first + ' ' + last).strip()
                if full:
                    names.append(full)
            elif hasattr(item, 'first_name') and hasattr(item, 'last_name'):
                # Handle model instances (CoAuthor objects)
                first = (getattr(item, 'first_name', '') or '').strip()
                last = (getattr(item, 'last_name', '') or '').strip()
                full = (first + ' ' + last).strip()
                if full:
                    names.append(full)
                elif hasattr(item, 'student_id') and item.student_id:
                    names.append(f"Student ID: {item.student_id}")
            elif isinstance(item, str) and item.strip():
                names.append(item.strip())
    return ', '.join(names)

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Helper tag to replace or add parameters to the current URL query string.
    Used for pagination to preserve existing filters.
    """
    query = context['request'].GET.copy()
    for kwarg, value in kwargs.items():
        query[kwarg] = value
    return query.urlencode()
