import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class CourseSession(Base):
    """A scheduled class (table `sessions`); named so it is not mistaken for a SQLAlchemy Session."""

    __tablename__ = "sessions"
    __table_args__ = (CheckConstraint("end_time > start_time", name="check"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    session_type_id: Mapped[int] = mapped_column(ForeignKey("session_types.id", ondelete="RESTRICT"))
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"))
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]
    status: Mapped[str] = mapped_column(String(20), server_default=text("'PLANNED'"))  # e.g. PLANNED, CANCELLED
    comment: Mapped[str | None] = mapped_column(Text)
    recurrence_group_id: Mapped[uuid.UUID | None]


class SessionTeacher(Base):
    __tablename__ = "session_teachers"

    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(server_default=text("false"))


class SessionGroup(Base):
    __tablename__ = "session_groups"

    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)


class UserUnavailability(Base):
    __tablename__ = "user_unavailabilities"
    __table_args__ = (CheckConstraint("end_time > start_time", name="check"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]
    reason: Mapped[str | None] = mapped_column(String(255))


class TeacherPreference(Base):
    __tablename__ = "teacher_preferences"
    __table_args__ = (CheckConstraint("day_of_week BETWEEN 1 AND 7", name="day_of_week_check"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    day_of_week: Mapped[int | None] = mapped_column(SmallInteger)  # 1 = Monday
    time_slot: Mapped[str | None] = mapped_column(String(20))  # e.g. MORNING, AFTERNOON
    priority: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    comment: Mapped[str | None] = mapped_column(Text)
