from django.apps import AppConfig


class ReportingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reporting'
    verbose_name = 'Reporting & Compliance'

    def ready(self):
        import apps.reporting.signals  # noqa: F401
