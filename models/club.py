from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from core import Base

if TYPE_CHECKING:
    from models.user import User
    from models.event import Event

class Club(Base):
    __tablename__ = "club"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    squad: Mapped[list["User"]] = relationship(back_populates="club", cascade="all, delete-orphan", order_by="User.number.asc().nullslast()")
    events: Mapped[list["Event"]] = relationship(back_populates="club", foreign_keys="[Event.club_id]", cascade="all, delete-orphan")