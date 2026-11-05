"""Application settings, read once from the environment (set in docker-compose.yml)."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: tuple[str, ...]


def load_settings() -> Settings:
    # No default URL: credentials never live in the code.
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set, e.g. postgresql+psycopg://user:password@host:5432/db")
    origins = os.environ.get("CORS_ORIGINS", "")
    return Settings(
        database_url=database_url,
        cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
    )


settings = load_settings()
