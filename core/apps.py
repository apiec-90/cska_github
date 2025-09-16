from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = 'Спортивная CRM'

    def ready(self):
        """Импортируем сигналы при запуске приложения"""
        # CLEANUP: import signals module for side effects without linter warning
        from importlib import import_module
        import_module('core.signals')
