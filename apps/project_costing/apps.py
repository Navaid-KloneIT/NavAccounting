from django.apps import AppConfig


class ProjectCostingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.project_costing'
    verbose_name = 'Project/Job Costing'

    def ready(self):
        import apps.project_costing.signals  # noqa: F401
