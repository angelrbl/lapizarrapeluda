from datetime import date, time, datetime, timedelta

from sqlalchemy import select

from core import get_session
from models import Event, EventStatus, EventType, Slot, User, Unavailability

from services.club_service import get_club_by_name

def generate_slots(
    date_from: date,
    date_to: date,
    weekdays: set[int],
    daily_start: time,
    daily_end: time,
    duration_minutes: int
) -> list[tuple[date, time, time]]:
    if date_from > date_to:
        raise ValueError("error_date_range_invalid")
    if daily_start >= daily_end:
        raise ValueError("error_daily_window_invalid")
    if duration_minutes <= 0:
        raise ValueError("error_duration_invalid")

    slots = []
    current_date = date_from
    step = timedelta(minutes=duration_minutes)

    while current_date <= date_to:
        if current_date.weekday() in weekdays:
            current_datetime = datetime.combine(current_date, daily_start)
            day_end = datetime.combine(current_date, daily_end)
            while current_datetime + step <= day_end:
                slot_end = current_datetime + step
                slots.append((current_datetime, current_datetime.time(), slot_end.time()))
                current_datetime = slot_end
        current_date += timedelta(days=1)

    return slots

def create_event(
    club_id: int,
    title: str,
    event_type: EventType,
    slots: list[tuple[date, time, time]],
    response_deadline: datetime | None = None,
    description: str | None = None,
    opponent_name: str | None = None,
    base_event_id: int | None = None,
) -> tuple[Event, int, int]:
    if not slots:
        raise ValueError("error_event_needs_at_least_one_slot")

    with get_session() as session:
        opponent_club = get_club_by_name(name=opponent_name) if opponent_name else None

        base_slot_map = {}
        unavs_by_base_slot = {}
        active_club_player_ids = set()

        # 1. Si hay evento base, validamos restricciones temporales y de club
        if base_event_id:
            base_event = session.get(Event, base_event_id)
            base_slots = session.scalars(select(Slot).where(Slot.event_id == base_event_id)).all()

            if not base_event or base_event.club_id != club_id:
                raise ValueError("error_base_event_not_found")
            
            if base_slots:
                min_new_date = min(s[0] for s in slots)
                max_base_date = max(bs.day for bs in base_slots)
                
                # El evento base debe ser estrictamente anterior al nuevo
                if max_base_date >= min_new_date:
                    raise ValueError("error_base_event_must_be_earlier")

                # Obtener jugadores activos del club para evitar fantasmas
                active_club_player_ids = {
                    u.id for u in session.scalars(
                        select(User).where(User.club_id == club_id, User.is_active == True)
                    ).all()
                }

                # Mapear slots del evento base por clave de equivalencia: (weekday, start_time, end_time)
                for bs in base_slots:
                    key = (bs.day.weekday(), bs.start_time, bs.end_time)
                    base_slot_map[key] = bs.id

                base_slot_ids = list(base_slot_map.values())
                if base_slot_ids:
                    base_unavailabilities = session.scalars(
                        select(Unavailability).where(Unavailability.slot_id.in_(base_slot_ids))
                    ).all()
                    for unav in base_unavailabilities:
                        if unav.user_id in active_club_player_ids:
                            unavs_by_base_slot.setdefault(unav.slot_id, []).append(unav.user_id)

        # 2. Crear el nuevo evento base
        event = Event(
            club_id=club_id,
            title=title,
            event_type=event_type,
            response_deadline=response_deadline,
            description=description,
            opponent_name=opponent_name,
            opponent=opponent_club,
            status="open"
        )

        session.add(event)
        session.flush()

        preloaded_unavs_count = 0
        preloaded_players_set = set()

        # 3. Crear franjas y cruzar indisponibilidades si procede
        for day, start, end in slots:
            new_slot = Slot(event_id=event.id, day=day, start_time=start, end_time=end)
            session.add(new_slot)
            session.flush()

            if base_event_id:
                key = (day.weekday(), start, end)
                matching_base_slot_id = base_slot_map.get(key)

                if matching_base_slot_id and matching_base_slot_id in unavs_by_base_slot:
                    for user_id in unavs_by_base_slot[matching_base_slot_id]:
                        session.add(Unavailability(user_id=user_id, slot_id=new_slot.id))
                        preloaded_unavs_count += 1
                        preloaded_players_set.add(user_id)

        session.commit()
        session.refresh(event)
        session.expunge(event)
        
        return event, preloaded_unavs_count, len(preloaded_players_set)
    
def delete_event(event_id: int) -> bool:
    with get_session() as session:
        event = session.get(Event, event_id)

        if not event:
            raise ValueError("error_event_does_not_exist")

        event.confirmed_slot_id = None
        session.flush()

        # 2. Procedemos con el borrado
        session.delete(event)
        session.commit()

        return True

def list_events_for_club(club_id: int) -> list[Event]:
    with get_session() as session:
        stmt = select(Event).where(Event.club_id == club_id).order_by(Event.id.desc())
        events = session.scalars(stmt).all()

        for e in events:
            session.expunge(e)
        return list(events)

def get_event_by_id(event_id: int) -> Event | None:
    with get_session() as session:
        event = session.get(Event, event_id)
        if event:
            session.expunge(event)
        return event

def get_event_slots(event_id: int) -> list[Slot]:
    with get_session() as session:
        stmt = select(Slot).where(Slot.event_id == event_id).order_by(Slot.day, Slot.start_time)
        slots = session.scalars(stmt).all()

        for s in slots:
            session.expunge(s)
        return list(slots)

def get_slot_by_id(slot_id: int) -> Slot | None:
    with get_session() as session:
        slot = session.get(Slot, slot_id)
        if slot:
            session.expunge(slot)
        return slot

def confirm_slot(event_id: int, slot_id: int) -> None:
    with get_session() as session:
        event = session.get(Event, event_id)
        if not event:
            raise ValueError("error_event_does_not_exist")

        slot = session.get(Slot, slot_id)
        if not slot or slot.event_id != event_id:
            raise ValueError("error_slot_does_not_belong_to_event")

        event.confirmed_slot_id = slot_id
        event.status = EventStatus.CONFIRMED
        session.commit()

