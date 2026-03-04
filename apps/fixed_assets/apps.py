from django.apps import AppConfig


class FixedAssetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fixed_assets'
    verbose_name = 'Fixed Assets'

    def ready(self):
        import apps.fixed_assets.signals  # noqa: F401
