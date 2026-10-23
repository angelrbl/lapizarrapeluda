from typing import Optional, TYPE_CHECKING
from enum import Enum
from werkzeug.security import check_password_hash, generate_password_hash

from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship

from core import Base

if TYPE_CHECKING:
    from models.club import Club
    from models.availability import Unavailability

class RoleType(str, Enum):
    PLAYER = "jugador"
    STAFF = "staff"
    CAPTAIN = "capitán"

class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    role: Mapped["RoleType"] = mapped_column()

    user: Mapped["User"] = relationship("User", back_populates="roles")

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column()

    number: Mapped[Optional[int]] = mapped_column()
    stats: Mapped["PlayerStats"] = relationship(
        back_populates="player",
        uselist=False,
        cascade="all, delete-orphan",
    )

    club_id: Mapped[int] = mapped_column(ForeignKey("club.id"))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    club: Mapped["Club"] = relationship(back_populates="squad")
    roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    unavailabilities: Mapped[list["Unavailability"]] = relationship("Unavailability", back_populates="user", cascade="all, delete-orphan")

    @property
    def password(self):
        raise AttributeError("Password is not an accessible property.")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password=password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User(id={self.id}, name={self.name})"

class PlayerStats(Base):
    __tablename__ = "player_stats"

    id: Mapped[int] = mapped_column(primary_key=True)

    player_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    matches_played: Mapped[int] = mapped_column(default=0)
    starter_amount: Mapped[int] = mapped_column(default=0)
    goals: Mapped[int] = mapped_column(default=0)
    assists: Mapped[int] = mapped_column(default=0)
    yellow_cards: Mapped[int] = mapped_column(default=0)
    red_cards: Mapped[int] = mapped_column(default=0)
    mvp_count: Mapped[int] = mapped_column(default=0)

    player: Mapped["User"] = relationship(back_populates="stats")