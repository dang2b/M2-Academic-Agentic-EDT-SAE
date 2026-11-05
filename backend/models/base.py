from datetime import datetime

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase

# PostgreSQL's own default names: the schema stays identical to the former db/init.sql,
# and every constraint has a stable name that a migration can drop or alter.
NAMING_CONVENTION = {
    "pk": "%(table_name)s_pkey",
    "uq": "%(table_name)s_%(column_0_N_name)s_key",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "ck": "%(table_name)s_%(constraint_name)s",
    "ix": "%(table_name)s_%(column_0_N_name)s_idx",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Every datetime column is TIMESTAMPTZ: no naive datetime can be stored.
    type_annotation_map = {datetime: DateTime(timezone=True)}
