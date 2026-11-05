"""Alembic environment: migrates the DATABASE_URL database, or the connection passed by the tests."""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection

import models
from db import engine

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name, disable_existing_loggers=False)


def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=models.Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    raise SystemExit("Offline mode (--sql) is not supported: run migrations against a database")

shared_connection = config.attributes.get("connection")
if shared_connection is None:
    with engine.connect() as connection:
        run_migrations(connection)
else:
    run_migrations(shared_connection)
