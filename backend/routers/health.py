from fastapi import APIRouter
from sqlalchemy import text

from db import SessionDep
from schemas.health import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(session: SessionDep) -> HealthOut:
    session.execute(text("SELECT 1"))  # fails with a 500 if the database is unreachable
    return HealthOut(status="ok")
