"""
Кастомные фильтры для Django шаблонов
"""
from django import template

register = template.Library()


@register.filter
def length_is(value, arg):
    """
    Возвращает True, если длина значения равна аргументу
    """
    try:
        return len(value) == int(arg)
    except (Exception,):
        return False


@register.filter(name="lookup")
def lookup(mapping, key):
    """
    Безопасный доступ к словарю по ключу из шаблона.
    Пример: {{ mydict|lookup:some_id }}
    - Пытается ключ как есть, как str и как int
    - Возвращает None, если ключа нет или объект не словарь
    """
    try:
        if mapping is None:
            return None
        # dict-like интерфейс
        if hasattr(mapping, "get"):
            if key in mapping:
                return mapping[key]
            # пробуем альтернативные представления ключа
            for alt in (str(key), int(key) if str(key).isdigit() else key):
                val = mapping.get(alt)
                if val is not None:
                    return val
            return mapping.get(key)
        # Списки/кортежи: пытаемся индекс
        if isinstance(mapping, (list, tuple)):
            try:
                idx = int(key)
                return mapping[idx]
            except Exception:
                return None
    except Exception:
        return None
    return None