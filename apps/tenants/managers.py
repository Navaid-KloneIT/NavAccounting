from threading import local

from django.db import models

_thread_locals = local()


def get_current_tenant():
    """Get the current tenant from thread-local storage."""
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant):
    """Set the current tenant in thread-local storage."""
    _thread_locals.tenant = tenant


class TenantAwareQuerySet(models.QuerySet):
    def filter_by_tenant(self):
        tenant = get_current_tenant()
        if tenant is not None:
            return self.filter(tenant=tenant)
        return self


class TenantAwareManager(models.Manager):
    def get_queryset(self):
        qs = TenantAwareQuerySet(self.model, using=self._db)
        return qs.filter_by_tenant()
