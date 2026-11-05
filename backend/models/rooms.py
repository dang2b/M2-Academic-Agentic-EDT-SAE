from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (CheckConstraint("capacity >= 0", name="capacity_check"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    capacity: Mapped[int]
    room_type: Mapped[str | None] = mapped_column(String(50))
    building: Mapped[str | None] = mapped_column(String(100))
    floor: Mapped[str | None] = mapped_column(String(20))


class Equipment(Base):
    __tablename__ = "equipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(100), unique=True)


class RoomEquipment(Base):
    __tablename__ = "room_equipments"
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_check"),)

    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipments.id", ondelete="CASCADE"), primary_key=True)
    quantity: Mapped[int] = mapped_column(server_default=text("1"))


class RoomUnavailability(Base):
    __tablename__ = "room_unavailabilities"
    __table_args__ = (CheckConstraint("end_time > start_time", name="check"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]
    reason: Mapped[str | None] = mapped_column(String(255))
