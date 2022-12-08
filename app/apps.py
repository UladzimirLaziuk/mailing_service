from django.apps import AppConfig
from django.dispatch import receiver


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    def ready(self):
        from app.signals import new_signal
