from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.users import Role
from pagination import Page


def list_roles(session: Session, page: Page) -> Sequence[Role]:
    return session.scalars(select(Role).order_by(Role.id).limit(page.limit).offset(page.offset)).all()
