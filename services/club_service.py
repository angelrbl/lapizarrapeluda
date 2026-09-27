import re
from sqlalchemy import select, func

from core import get_session
from models import Club, User, UserRole, RoleType

def _normalize_for_matching(name: str) -> str:
    return re.sub(r"[\s\-_]+", "", name.strip().lower())

def _normalized_name_column():
    expr = func.lower(Club.name)
    expr = func.replace(expr, " ", "")
    expr = func.replace(expr, "-", "")
    expr = func.replace(expr, "_", "")
    return expr

def create_club(name: str) -> Club:
    with get_session() as session:
        normalized_name = name.strip()
        target = _normalize_for_matching(name=name)
        stmt = select(Club).where(_normalized_name_column() == target)
        club = session.scalars(stmt).first()

        if club:
            raise ValueError("error_club_already_exists")

        club = Club(name=normalized_name)

        session.add(club)
        session.commit()

        session.refresh(club)
        session.expunge(club)

        return club

def delete_club(club_id: int) -> bool:
    with get_session() as session:
        club = session.get(Club, club_id)

        if not club:
            raise ValueError("error_club_does_not_exist")

        session.delete(club)
        session.commit()

        return True

def update_club_name(club_id: int, new_name: str) -> None:
    with get_session() as session:
        normalized_name = new_name.strip()
        target = _normalize_for_matching(normalized_name)
        stmt = select(Club).where(_normalized_name_column() == target)
        existing_club = session.scalars(stmt).first()

        if existing_club and existing_club.id != club_id:
            raise ValueError("error_club_already_exists")

        club = session.get(Club, club_id)
        if not club:
            raise ValueError("error_club_no_longer_exists")
        
        club.name = normalized_name
        session.commit()

def get_club_by_id(club_id: int) -> Club | None:
    if not club_id:
        return None

    with get_session() as session:
        club = session.get(Club, club_id)
        if club:
            session.expunge(club)
        return club

def get_club_by_name(name: str) -> Club | None:
    with get_session() as session:
        target = _normalize_for_matching(name)
        stmt = (
            select(Club)
            .where(_normalized_name_column() == target)
        )
        club = session.scalars(stmt).first()
        if club:
            session.expunge(club)
        return club

def get_only_club() -> Club | None:
    with get_session() as session:
        stmt = select(Club)
        club = session.scalars(stmt).first()
        if club:
            session.expunge(club)
        return club

def any_club_exists() -> bool:
    with get_session() as session:
        return session.scalars(select(Club)).first() is not None

def get_squad_length(club_id: int) -> int | None:
    if not club_id:
        return None

    with get_session() as session:
        stmt = (
            select(func.count(User.id))
            .join(UserRole, User.id == UserRole.user_id)
            .where(
                User.club_id == club_id,
                UserRole.role == RoleType.PLAYER
            )
        )
        
        return session.scalar(stmt) or 0