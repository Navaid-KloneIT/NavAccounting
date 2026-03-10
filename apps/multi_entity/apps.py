from django.apps import AppConfig


class MultiEntityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.multi_entity'
    verbose_name = 'Multi-Entity & Consolidation'
