"""Tests run against the compose PostgreSQL, in a dedicated database (<DATABASE_URL name>_test)
rebuilt from the migrations at each run. Each test runs in a transaction rolled back afterwards.
"""
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from config import settings
from db import get_session
from main import app

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def recreate_database(admin_url: str, name: str) -> None:
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))


@pytest.fixture(scope="session")
def alembic_cfg() -> Config:
    return Config(str(ALEMBIC_INI))


@pytest.fixture(scope="session")
def engine(alembic_cfg: Config) -> Iterator[Engine]:
    url = make_url(settings.database_url)
    test_url = url.set(database=f"{url.database}_test")
    # psycopg wants a plain libpq URL, without SQLAlchemy's "+psycopg" driver suffix
    recreate_database(url.set(drivername="postgresql").render_as_string(hide_password=False), test_url.database)
    test_engine = create_engine(test_url)
    with test_engine.begin() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "head")
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with engine.connect() as connection:
        transaction = connection.begin()
        # Route commits only release a savepoint: the outer transaction is rolled back below.
        with Session(bind=connection, join_transaction_mode="create_savepoint") as test_session:
            yield test_session
        transaction.rollback()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
