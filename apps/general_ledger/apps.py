from django.apps import AppConfig


class GeneralLedgerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.general_ledger'
    verbose_name = 'General Ledger'

    def ready(self):
        import apps.general_ledger.signals  # noqa: F401
