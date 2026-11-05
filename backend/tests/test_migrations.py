from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Engine

from models import Base


def test_models_match_migrations(engine: Engine) -> None:
    # Fails when a model changed without its migration (or the reverse).
    with engine.connect() as connection:
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []


def test_every_migration_downgrades_and_upgrades_again(engine: Engine, alembic_cfg: Config) -> None:
    with engine.connect() as connection:
        transaction = connection.begin()
        alembic_cfg.attributes["connection"] = connection
        command.downgrade(alembic_cfg, "base")
        command.upgrade(alembic_cfg, "head")
        transaction.rollback()
