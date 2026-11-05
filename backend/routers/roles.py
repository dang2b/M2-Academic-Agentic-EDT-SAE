from collections.abc import Sequence

from fastapi import APIRouter

from db import SessionDep
from models.users import Role
from pagination import PageDep
from repositories.roles import list_roles
from schemas.roles import RoleOut

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleOut])
def get_roles(session: SessionDep, page: PageDep) -> Sequence[Role]:
    return list_roles(session, page)
