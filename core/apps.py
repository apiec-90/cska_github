from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = 'Спортивная CRM'

    def ready(self):
        """Импортируем сигналы при запуске приложения"""
        import core.signals  # CLEANUP: import for side-effects; noqa: F401
