from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from core import get_session
from models import User, UserRole, RoleType

def create_user(
    name: str,
    club_id: int,
    number: int | None = None,
    password: str | None = None,
    email:str | None = None,
    is_admin: bool = False
) -> User | None:
    with get_session() as session:
        stmt = select(User).where(User.name == name, User.club_id == club_id)
        user = session.scalars(stmt).first()

        if user:
            raise ValueError("error_user_already_exists")

        user = User(name=name, email=email, club_id=club_id, is_admin=is_admin, number=number)

        if password:
            user.password = password
            user.is_active = True

        session.add(user)
        session.commit()

        session.refresh(user)
        session.expunge(user)

        return user

def delete_user(user_id: int) -> bool:
    with get_session() as session:
        user = session.get(User, user_id)

        if not user:
            raise ValueError("error_user_does_not_exist")

        session.delete(user)
        session.commit()

        return True

def update_user(user_id: int, new_name: str, new_number: int | None = None) -> User | None:
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("error_user_no_longer_exists")
        
        stmt = select(User).where(or_(User.name == new_name, User.number == new_number), User.club_id == user.club_id)
        existing_user = session.scalar(stmt)

        if existing_user and existing_user.id != user_id:
            raise ValueError("error_name_or_number_already_exists")

        user.name = new_name
        user.number = new_number
        session.commit()

        session.refresh(user)
        session.expunge(user)

        return user

def get_user_by_id(user_id: int) -> User | None:
    if not user_id:
        return None

    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            session.expunge(user)
        return user

def get_user_by_club_name(name: str, club_id: int) -> User | None:
    with get_session() as session:
        stmt = select(User).where(User.name == name, User.club_id == club_id)
        user = session.scalars(stmt).first()
        if user:
            session.expunge(user)
        return user

def list_users_for_club(club_id: int) -> list[User]:
    with get_session() as session:
        stmt = (
            select(User)
            .where(User.club_id == club_id)
            .order_by(User.number.asc().nullslast())
        )
        
        users = session.scalars(stmt).all()
        for u in users:
            session.expunge(u)
            
        return list(users)