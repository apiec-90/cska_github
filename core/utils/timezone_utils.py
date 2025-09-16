from typing import Set
from django.utils import timezone


ALLOWED_TZ: Set[str] = {
    'UTC', 'Europe/Moscow', 'Asia/Almaty', 'Europe/Kyiv', 'Europe/Berlin',
    'Europe/Samara', 'Asia/Yekaterinburg', 'Asia/Novosibirsk', 'Europe/Minsk',
}


def set_request_timezone(request, tz_name: str) -> bool:
    """CLEANUP: Безопасно сохраняет выбранный пользователем часовой пояс в сессии.

    Возвращает True, если tz_name допустим и сохранён; иначе False.
    """
    if tz_name in ALLOWED_TZ:
        request.session['tz'] = tz_name
        return True
    return False


def activate_request_timezone(request) -> None:
    """Активирует часовой пояс из сессии для текущего запроса (если доступен)."""
    tz_name = request.session.get('tz')
    if not tz_name or tz_name not in ALLOWED_TZ:
        return
    try:
        from zoneinfo import ZoneInfo
        timezone.activate(ZoneInfo(tz_name))
    except Exception:
        # Не критично: просто работаем с настройкой TIME_ZONE
        pass


