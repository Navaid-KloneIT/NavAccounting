from django.apps import AppConfig


class TaxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tax'
    verbose_name = 'Tax Management'

    def ready(self):
        import apps.tax.signals  # noqa: F401
