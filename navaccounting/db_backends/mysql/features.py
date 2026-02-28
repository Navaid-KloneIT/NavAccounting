import operator
from functools import cached_property

from django.db.backends.mysql.features import DatabaseFeatures as MySQLDatabaseFeatures


class DatabaseFeatures(MySQLDatabaseFeatures):
    @cached_property
    def minimum_database_version(self):
        if self.connection.mysql_is_mariadb:
            return (10, 4)
        return super().minimum_database_version

    @cached_property
    def can_return_columns_from_insert(self):
        # MariaDB 10.5+ supports INSERT ... RETURNING, but 10.4 does not.
        if self.connection.mysql_is_mariadb:
            return self.connection.mysql_version >= (10, 5)
        return False

    can_return_rows_from_bulk_insert = property(
        operator.attrgetter("can_return_columns_from_insert")
    )
