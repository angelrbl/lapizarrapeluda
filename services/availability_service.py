from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from core import get_session
from models import Slot, Unavailability, User

def set_unavailability(user_id: int, event_id: int, slot_ids: list[int]) -> None:
    with get_session() as session:
        stmt = (select(Unavailability)
                .join(Slot)
                .where(
                    Unavailability.user_id == user_id,
                    Slot.event_id == event_id))
        existing = session.scalars(stmt).all()

        for slot in existing:
            session.delete(slot)

        session.flush()

        for slot_id in slot_ids:
            session.add(Unavailability(user_id=user_id, slot_id=slot_id))

        try:
            session.commit()
        except IntegrityError:
            session.rollback()

def get_user_unavailable_slot_ids(user_id: int, event_id: int) -> set[int]:
    with get_session() as session:
        stmt = (select(Unavailability)
                .join(Slot)
                .where(
                    Unavailability.user_id == user_id,
                    Slot.event_id == event_id
                ))
        unavailabilities = session.scalars(stmt).all()

        return {unavailability.slot_id for unavailability in unavailabilities}

def unavailability_counts_by_slot(event_id: int) -> dict[int, int]:
    with get_session() as session:
        stmt = select(Slot).where(Slot.event_id == event_id)
        slots = session.scalars(stmt).all()

        counts = {}
        for slot in slots:
            count = len(
                session.scalars(select(Unavailability).where(Unavailability.slot_id == slot.id)).all()
            )
            counts[slot.id] = count

        return counts

def get_slot_unavailable_users(slot_id: int) -> list[User]:
    if not slot_id:
        return []
    
    with get_session() as session:
        stmt = (
            select(User)
            .join(Unavailability, User.id == Unavailability.user_id)
            .where(Unavailability.slot_id == slot_id)
            .order_by(User.number.asc().nullslast())
        )
        users = session.scalars(stmt).all()
        
        for u in users:
            session.expunge(u)
            
        return list(users)