from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
<<<<<<< HEAD
    verbose_name = 'Спортивная CRM'

    def ready(self):
        """Импортируем сигналы при запуске приложения"""
        import core.signals
=======
    verbose_name = 'Основная структура'  # Отображение в админке 
>>>>>>> bedbb2b1a87a3bede18d794b18be9309c5599d3e
