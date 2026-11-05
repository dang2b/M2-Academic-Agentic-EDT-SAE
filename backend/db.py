"""Database engine and the per-request session injected into routes."""
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    # Routers commit once, after every repository call; whatever is left uncommitted
    # (an exception midway) is rolled back when the session closes.
    with SessionLocal() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
