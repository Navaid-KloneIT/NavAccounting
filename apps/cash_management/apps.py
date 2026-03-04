from django.apps import AppConfig


class CashManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cash_management'
    verbose_name = 'Cash Management'

    def ready(self):
        import apps.cash_management.signals  # noqa: F401
