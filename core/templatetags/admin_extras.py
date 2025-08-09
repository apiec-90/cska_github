from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получить элемент из словаря по ключу"""
    if isinstance(key, str) and ',' in key:
        # Разбираем ключ как "session_id,athlete_id"
        try:
            session_id, athlete_id = map(int, key.split(','))
            return dictionary.get((session_id, athlete_id), False)
        except (ValueError, TypeError):
            return False
    return dictionary.get(key, False)

@register.simple_tag
def attendance_status(attendance_map, session_id, athlete_id):
    """Получить статус посещаемости для конкретной сессии и спортсмена"""
    return attendance_map.get((session_id, athlete_id), None)


