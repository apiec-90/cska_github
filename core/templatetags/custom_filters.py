from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Фильтр для доступа к значению словаря по ключу"""
    if isinstance(key, str) and ',' in key:
        # Если ключ содержит запятую, разбиваем его на части
        keys = key.split(',')
        if len(keys) == 2:
            try:
                key1, key2 = int(keys[0]), int(keys[1])
                return dictionary.get((key1, key2), False)
            except (ValueError, TypeError):
                pass
    return dictionary.get(key, False)

@register.filter
def lookup2(dictionary, session_id, athlete_id):
    """Фильтр для доступа к значению словаря по двум ключам"""
    try:
        return dictionary.get((int(session_id), int(athlete_id)), False)
    except (ValueError, TypeError):
        return False

