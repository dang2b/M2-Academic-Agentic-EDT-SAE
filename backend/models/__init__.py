"""SQLAlchemy models: the source of truth for the schema.

Importing this package registers every table on Base.metadata, which Alembic compares
against the database. A new model module must be imported here.
"""
from models import pedagogy, personal, rooms, sessions, users
from models.base import Base

__all__ = ["Base", "pedagogy", "personal", "rooms", "sessions", "users"]
