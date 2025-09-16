from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
import logging

from .models import RegistrationDraft

logger = logging.getLogger(__name__)


class RegistrationDraftCleanupMiddleware(MiddlewareMixin):
    """Автоочистка незавершенного черновика при переходах по сайту.

    Если в сессии есть draft_id и он еще не завершен, а запрос идет НЕ на
    страницы регистрации, то удаляем черновик и временного пользователя.
    """

    REGISTRATION_PATH_PREFIXES = [
        "/admin/auth/user/register/",
        "/register/",
    ]
    
    # Пути, которые не должны вызывать удаление черновика
    IGNORE_PATH_PREFIXES = [
        "/admin/jsi18n/",
        "/static/",
        "/media/",
        "/favicon.ico",
    ]

    def process_request(self, request):
        path: str = request.path
        
        # Игнорируем статические ресурсы и JS файлы
        if any(path.startswith(prefix) for prefix in self.IGNORE_PATH_PREFIXES):
            return None
        
        # Проверяем, является ли текущий путь частью процесса регистрации
        is_registration_path = any(path.startswith(prefix) for prefix in self.REGISTRATION_PATH_PREFIXES)
        
        if is_registration_path:
            logger.debug(f"Registration path detected: {path}, skipping cleanup")
            return None  # Не удаляем черновик на страницах регистрации

        draft_id = request.session.get("draft_id")
        if not draft_id:
            return None

        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
            logger.warning(f"Cleaning up draft #{draft_id} for path: {path}")
        except RegistrationDraft.DoesNotExist:
            logger.debug(f"Draft #{draft_id} not found, cleaning session")
            request.session.pop("draft_id", None)
            return None

        # Удаляем незавершенный черновик и временного пользователя
        draft.safe_dispose()
        request.session.pop("draft_id", None)
        logger.info(f"Draft #{draft_id} disposed due to navigation to: {path}")

        return None



class SessionTimeZoneMiddleware(MiddlewareMixin):
    """Активирует часовой пояс из сессии пользователя.

    Ищет ключ 'tz' в session и, если он валиден, активирует его для текущего запроса.
    Это дополняет стандартный Django TimeZoneMiddleware и не меняет внешнее поведение.
    """

    # Поддерживаемый whitelist для безопасности (может быть расширен через .env/настройки при необходимости)
    ALLOWED_TZ = {
        'UTC', 'Europe/Moscow', 'Asia/Almaty', 'Europe/Kyiv', 'Europe/Berlin',
        'Europe/Samara', 'Asia/Yekaterinburg', 'Asia/Novosibirsk', 'Europe/Minsk',
    }

    def process_request(self, request):
        tz_name = request.session.get('tz')
        if not tz_name:
            return None

        if tz_name in self.ALLOWED_TZ:
            try:
                from zoneinfo import ZoneInfo
                # CLEANUP: activate session-provided timezone per request
                timezone.activate(ZoneInfo(tz_name))
            except Exception as exc:
                logger.debug(f"Invalid timezone in session: {tz_name}: {exc}")
        else:
            logger.debug(f"Timezone not in whitelist: {tz_name}")
        return None

