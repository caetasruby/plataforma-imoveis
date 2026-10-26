from django.apps import AppConfig


class AdministracaoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "administracao"
    verbose_name = "Administração"

    def ready(self):
        # Inscreve os observadores (receptores dos sinais) quando o Django arranca
        from . import sinais  # noqa: F401
