from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.users import Role, User, UserRole
from seed import create_demo_admin


def test_demo_admin_gets_a_bcrypt_hash_and_the_admin_role(session: Session) -> None:
    assert create_demo_admin(session, "demo@example.com", "s3cret-pass")

    user = session.scalars(select(User).where(User.email == "demo@example.com")).one()
    assert user.password_hash.startswith("$2")
    assert session.scalar(select(func.crypt("s3cret-pass", user.password_hash) == user.password_hash))
    role_codes = session.scalars(
        select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)
    ).all()
    assert role_codes == ["ADMIN"]


def test_demo_admin_is_created_only_once(session: Session) -> None:
    assert create_demo_admin(session, "demo@example.com", "s3cret-pass")
    assert not create_demo_admin(session, "demo@example.com", "another-pass")
