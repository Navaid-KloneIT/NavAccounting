from django.apps import AppConfig


class AccountsPayableConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts_payable'
    verbose_name = 'Accounts Payable'

    def ready(self):
        import apps.accounts_payable.signals  # noqa: F401
