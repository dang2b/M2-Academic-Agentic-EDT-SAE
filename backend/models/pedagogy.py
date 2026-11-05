from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class AcademicYear(Base):
    __tablename__ = "academic_years"
    __table_args__ = (CheckConstraint("end_date > start_date", name="check"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(50), unique=True)
    start_date: Mapped[date]
    end_date: Mapped[date]


class Semester(Base):
    __tablename__ = "semesters"
    __table_args__ = (CheckConstraint("end_date > start_date", name="check"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(50))
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id", ondelete="CASCADE"))
    start_date: Mapped[date]
    end_date: Mapped[date]


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    level: Mapped[str | None] = mapped_column(String(50))


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("program_id", "code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(200))
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id", ondelete="RESTRICT"))


class SessionType(Base):
    __tablename__ = "session_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    label: Mapped[str] = mapped_column(String(100))
    bg_color: Mapped[str] = mapped_column(String(7))
    text_color: Mapped[str] = mapped_column(String(7))


class SubjectVolume(Base):
    __tablename__ = "subject_volumes"
    __table_args__ = (
        CheckConstraint("planned_hours >= 0", name="planned_hours_check"),
        UniqueConstraint("subject_id", "session_type_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    session_type_id: Mapped[int] = mapped_column(ForeignKey("session_types.id", ondelete="RESTRICT"))
    planned_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2))


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    group_type: Mapped[str] = mapped_column(String(20))  # e.g. PROMO, TD, TP
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id", ondelete="CASCADE"))
    parent_group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id", ondelete="SET NULL"))


class StudentGroup(Base):
    __tablename__ = "student_groups"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
