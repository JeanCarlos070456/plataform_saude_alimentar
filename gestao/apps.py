from django.apps import AppConfig


class GestaoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gestao"
    verbose_name = "Gestão do site"

    def ready(self):
        from . import signals  # noqa: F401
