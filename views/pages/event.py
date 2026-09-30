from datetime import date, datetime, timedelta
from urllib.parse import urlencode, quote
from datetime import datetime

from nicegui import ui

from models import EventStatus, TokenType, Slot, Event
from services.availability_service import get_user_unavailable_slot_ids, set_unavailability
from services.event_service import get_event_by_id, get_event_slots, get_slot_by_id
from services.token_service import get_valid_token
from services.user_service import list_users_for_club

from views.layout import frame

DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


@ui.page("/e/{token_value}")
def event_page(token_value: str):
    with frame(navigation_title="SOM-HI"):
        token = get_valid_token(token_value, TokenType.EVENT)
        if not token:
            ui.label("¡Qué lastima!").classes("text-3xl font-black text-negative")
            ui.label("Este enlace no es válido o ha caducado.").classes('text-xl font-bold text-slate-700')
            return

        event = get_event_by_id(token.event_id)

        with ui.column().classes('w-full bg-white relative z-10 pb-8'):
            if event.status == EventStatus.OPEN:
                render_open_event(event)
            else:
                render_confirmed_event(event)

        with ui.row().classes('fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-3xl items-center justify-between px-6 -z-10'):
            ui.image('/static/tag-heuer.png').classes('ml-3 w-16 sm:w-20 h-12 sm:h-16').props('fit="contain"')
            ui.image('/static/estrella-damm.png').classes('w-16 sm:w-20 h-12 sm:h-16').props('fit="contain"')
            ui.image('/static/suave.png').classes('w-16 sm:w-20 h-12 sm:h-16').props('fit="contain"')

def render_confirmed_event(event) -> None:
    slot = get_slot_by_id(event.confirmed_slot_id) if event.confirmed_slot_id else None
    is_past = event.status == EventStatus.PAST

    with ui.column().classes("w-full max-w-lg mx-auto gap-1"):
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            ui.label(event.title).classes("text-lg font-bold text-dark")
            badge_text = "Pasado" if is_past else "Confirmado"
            badge_style = "bg-gray-200 text-gray-600" if is_past else "bg-primary/10 text-primary"
            ui.label(badge_text).classes(f"px-2.5 py-0.5 text-xs font-medium rounded-full {badge_style}")

        if event.opponent_name:
            ui.label(f"vs. {event.opponent_name}").classes("text-dark text-sm")

        if slot:
            with ui.column().classes("gap-1 mt-4 p-4 w-full bg-gray-50 border border-gray-200 rounded-xl shadow-none gap-2"):
                ui.label("Horario confirmado").classes("text-primary text-xs font-semibold")
                ui.label(
                    f"{DAYS[slot.day.weekday()].capitalize()} {slot.day:%d/%m} · {slot.start_time:%H:%M}"
                ).classes("text-dark text-base font-bold")

            if not is_past:
                ui.button(
                    "Añadir a mi calendario",
                    icon="event",
                    on_click=lambda: ui.navigate.to(generate_gcal_link(event, slot)),
                ).props("unelevated").classes("mt-4 w-full bg-primary text-white rounded-lg")
        else:
            ui.label("Este evento está confirmado, pero falta el horario.").classes("mt-4 text-sm text-gray-500")

def generate_gcal_link(event: "Event", slot: "Slot") -> str:
    title = event.title or "Partido"
    if event.opponent_name:
        title = f"{title} vs {event.opponent_name}"

    start_dt = datetime.combine(slot.day, slot.start_time)
    end_dt = datetime.combine(slot.day, slot.end_time)
    
    dates_str = f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"

    opponent = event.opponent_name or "rival"
    html_details = f'<p>Partido contra "{opponent}". A por todas, ¡SOM-HI GRANDIOSA!</p>'
    
    location = "Universidad Jaume I"

    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": dates_str,
        "details": html_details,
        "location": location,
        "ctz": "Europe/Madrid"
    }
    
    base_url = "https://calendar.google.com/calendar/render"
    query_string = urlencode(params, quote_via=quote)
    
    return f"{base_url}?{query_string}"

def render_open_event(event) -> None:
    slots = get_event_slots(event.id)
    members = list_users_for_club(event.club_id)

    all_days = sorted({slot.day for slot in slots})
    all_times = sorted({slot.start_time for slot in slots})
    slot_lookup = {(slot.day, slot.start_time): slot for slot in slots}

    def week_start(d: date) -> date:
        return d - timedelta(days=d.weekday())

    days_by_week: dict[date, list[date]] = {}
    for day in all_days:
        days_by_week.setdefault(week_start(day), []).append(day)
    week_starts = sorted(days_by_week.keys())

    today_week = week_start(date.today())
    default_week_index = week_starts.index(today_week) if today_week in week_starts else 0

    state = {"user_id": None, "week_index": default_week_index}
    slot_buttons: dict[int, ui.button] = {}
    selected_slots: dict[int, bool] = {}
    count_label_ref: dict[str, ui.label] = {}

    BASE_CLASSES = "h-10 w-full min-w-0 rounded-lg border text-sm font-semibold transition-colors"
    UNSELECTED = "bg-white text-dark border-gray-300"
    SELECTED = "bg-primary text-white border-primary"

    def style_slot_button(slot_id: int) -> None:
        btn = slot_buttons[slot_id]
        if selected_slots[slot_id]:
            btn.classes(remove=UNSELECTED, add=SELECTED)
        else:
            btn.classes(remove=SELECTED, add=UNSELECTED)

    def toggle_slot(slot_id: int) -> None:
        selected_slots[slot_id] = not selected_slots[slot_id]
        style_slot_button(slot_id)
        update_count()

    def update_count() -> None:
        if "label" not in count_label_ref:
            return
        n = sum(1 for v in selected_slots.values() if v)
        if n:
            count_label_ref["label"].text = f"{n} franja{'s' if n != 1 else ''} marcada{'s' if n != 1 else ''}"
        else:
            count_label_ref["label"].text = "Ninguna franja marcada"

    def save() -> None:
        if not state["user_id"]:
            ui.notify("Elige tu nombre primero.", type="negative")
            return
        chosen = [sid for sid, is_selected in selected_slots.items() if is_selected]
        set_unavailability(user_id=state["user_id"], event_id=event.id, slot_ids=chosen)
        ui.notify("¡Guardado!", type="positive")

    def change_week(delta: int) -> None:
        new_index = state["week_index"] + delta
        if 0 <= new_index < len(week_starts):
            state["week_index"] = new_index
            render_grid()

    def render_grid() -> None:
        grid_container.clear()
        slot_buttons.clear()

        with grid_container:
            if not state["user_id"]:
                ui.label("Elige tu nombre arriba para ver y marcar las franjas.").classes("text-sm text-gray-500 mt-4")
                return

            if not slots:
                ui.label("Este evento no tiene franjas candidatas todavía.").classes("mt-4 text-sm text-gray-500")
                return

            with ui.row().classes("items-start gap-2 mt-3 p-3 pl-0 bg-primary/10 rounded-lg no-wrap"):
                ui.icon("warning").classes("text-primary text-base flex-shrink-0 font-black")
                ui.label("Marca solo las franjas en las que NO puedes asistir.").classes(
                    "text-primary text-xs leading-relaxed font-bold"
                )

            current_week_start = week_starts[state["week_index"]]
            current_week_days = days_by_week[current_week_start]
            current_week_end = current_week_start + timedelta(days=6)
            is_first_week = state["week_index"] == 0
            is_last_week = state["week_index"] == len(week_starts) - 1

            with ui.row().classes("items-center justify-between w-full no-wrap mt-4"):
                ui.button(icon="chevron_left", on_click=lambda: change_week(-1)).props(
                    "flat round dense" + (" disable" if is_first_week else "")
                ).classes("text-primary")
                ui.label(f"{current_week_start:%d/%m} - {current_week_end:%d/%m}").classes(
                    "text-base font-bold text-dark"
                )
                ui.button(icon="chevron_right", on_click=lambda: change_week(1)).props(
                    "flat round dense" + (" disable" if is_last_week else "")
                ).classes("text-primary")

            grid_style = f"grid-template-columns: 56px repeat({len(current_week_days)}, minmax(64px, 1fr));"
            with ui.element("div").classes("w-full overflow-x-auto mt-3"):
                with ui.element("div").classes("grid gap-1 sm:gap-2").style(grid_style):
                    ui.element("div")
                    for day in current_week_days:
                        with ui.column().classes("items-center gap-0"):
                            ui.label(DAYS[day.weekday()][:3].capitalize()).classes("text-sm font-semibold text-dark")
                            ui.label(f"{day:%d/%m}").classes("text-xs text-gray-500")

                    for t in all_times:
                        ui.label(f"{t:%H:%M}").classes("text-xs text-gray-500 flex items-center")
                        for day in current_week_days:
                            slot = slot_lookup.get((day, t))
                            if slot is None:
                                ui.element("div")
                                continue
                            btn = (
                                ui.button(on_click=lambda sid=slot.id: toggle_slot(sid))
                                .props(f'unelevated dense aria-label="{DAYS[day.weekday()]} {day:%d/%m} {t:%H:%M}"')
                                .classes(f"{BASE_CLASSES} {UNSELECTED}")
                            )
                            slot_buttons[slot.id] = btn
                            style_slot_button(slot.id)

            with ui.column().classes("items-center justify-between w-full no-wrap gap-2"):
                count_label_ref["label"] = ui.label("").classes("text-gray-800 font-semibold text-xs mt-4")
                ui.button("Guardar", on_click=save).props("unelevated").classes(
                    "bg-primary text-white rounded-lg w-full"
                )
            update_count()

    def on_pick(e) -> None:
        state["user_id"] = e.value
        my_unavailable = get_user_unavailable_slot_ids(state["user_id"], event.id)
        selected_slots.clear()
        for slot in slots:
            selected_slots[slot.id] = slot.id in my_unavailable
        state["week_index"] = default_week_index
        render_grid()

    with ui.column().classes("w-full max-w-2xl mx-auto gap-1"):
        ui.label(event.title).classes("text-xl font-black text-dark")
        if event.opponent_name:
            ui.label(f"vs. {event.opponent_name}").classes("text-dark text-sm")

        if not members:
            ui.label("Todavía no hay jugadores dados de alta en el club.").classes("mt-4 text-sm text-gray-500")
            return

        ui.select(
            {m.id: m.name for m in members},
            label="¿Quién eres?",
            on_change=on_pick,
        ).classes("w-full mt-3").props('standout="bg-primary text-white"')

        grid_container = ui.column().classes("w-full")
        render_grid()