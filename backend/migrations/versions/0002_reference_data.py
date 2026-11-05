"""reference data: roles and session types, needed in every environment

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-05
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0002'
down_revision: str | None = '0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen copies of the tables: a migration must not import the models, which keep changing.
roles = sa.table("roles", sa.column("code", sa.String), sa.column("label", sa.String))
session_types = sa.table(
    "session_types",
    sa.column("code", sa.String),
    sa.column("label", sa.String),
    sa.column("bg_color", sa.String),
    sa.column("text_color", sa.String),
)

ROLES = [
    {"code": "ADMIN", "label": "Administrateur"},
    {"code": "MANAGER", "label": "Gestionnaire de scolarité"},
    {"code": "TEACHER", "label": "Enseignant"},
    {"code": "STUDENT", "label": "Étudiant"},
]
SESSION_TYPES = [
    {"code": "CM", "label": "Cours magistral", "bg_color": "#1E3A8A", "text_color": "#FFFFFF"},
    {"code": "TD", "label": "Travaux dirigés", "bg_color": "#047857", "text_color": "#FFFFFF"},
    {"code": "TP", "label": "Travaux pratiques", "bg_color": "#B45309", "text_color": "#FFFFFF"},
    {"code": "EXAM", "label": "Examen", "bg_color": "#B91C1C", "text_color": "#FFFFFF"},
]


def upgrade() -> None:
    op.bulk_insert(roles, ROLES)
    op.bulk_insert(session_types, SESSION_TYPES)


def downgrade() -> None:
    op.execute(session_types.delete().where(session_types.c.code.in_([t["code"] for t in SESSION_TYPES])))
    op.execute(roles.delete().where(roles.c.code.in_([r["code"] for r in ROLES])))
