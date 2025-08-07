from django.utils.deprecation import MiddlewareMixin
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


