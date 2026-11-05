"""Creates the demo admin account, for local development only: python -m seed

Reads DEMO_ADMIN_EMAIL and DEMO_ADMIN_PASSWORD; does nothing if they are unset, which is
the case in production. Running it again changes nothing.
"""
import os

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db import SessionLocal
from models.users import Role, User, UserRole


def create_demo_admin(session: Session, email: str, password: str) -> bool:
    """Returns False if the account already exists."""
    user_id = session.scalar(
        insert(User)
        .values(
            last_name="Admin",
            first_name="Super",
            email=email,
            password_hash=func.crypt(password, func.gen_salt("bf")),  # bcrypt, via pgcrypto
        )
        .on_conflict_do_nothing(index_elements=[User.email])
        .returning(User.id)
    )
    if user_id is None:
        return False
    admin_role_id = session.scalar(select(Role.id).where(Role.code == "ADMIN"))
    session.add(UserRole(user_id=user_id, role_id=admin_role_id))
    session.flush()
    return True


def main() -> None:
    email = os.environ.get("DEMO_ADMIN_EMAIL")
    password = os.environ.get("DEMO_ADMIN_PASSWORD")
    if not email or not password:
        print("seed: DEMO_ADMIN_EMAIL or DEMO_ADMIN_PASSWORD unset, no demo admin created")
        return
    with SessionLocal() as session:
        created = create_demo_admin(session, email, password)
        session.commit()
    print(f"seed: demo admin {email} {'created' if created else 'already exists'}")


if __name__ == "__main__":
    main()
