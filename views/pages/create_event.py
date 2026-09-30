from datetime import date, datetime, time

from nicegui import app, ui

from models import EventType

from services.event_service import create_event, generate_slots
from services.token_service import create_event_token
from services.user_service import get_user_by_id

from views.layout import frame

WEEKDAY_LABELS = ["L", "M", "X", "J", "V", "S", "D"]
DURATION_OPTIONS = {30: "30 min", 60: "1 h", 90: "1 h 30 min", 120: "2 h"}


@ui.page("/staff/events/new")
def new_event_page():
    if not app.storage.user.get('user_id', None) or not app.storage.user.get('club_id', None):
        ui.navigate.to('/login')
        return

    admin = get_user_by_id(app.storage.user["user_id"])
    if not admin or not admin.is_admin:
        ui.navigate.to("/staff")
        return

    club_id = app.storage.user.get('club_id', None)
    selected_weekdays: set[int] = {0, 1, 2, 3, 4}
    weekday_buttons: dict[int, ui.button] = {}

    with frame(navigation_title="Crear evento"):
        with ui.column().classes("w-full p-4 gap-2"):
            ui.label("← Volver a staff").classes('text-primary text-md hover:text-primary/90 cursor-pointer').on('click', lambda: ui.navigate.to('/staff'))
            ui.label("Nuevo evento").classes("text-3xl text-primary font-bold mt-3")

            title_input = ui.input("Título").classes("w-full text-gray-900").props('standout="bg-primary text-white"')
            type_input = ui.select(
                {t.value: t.value.replace('_', " ").title() for t in EventType}, value=EventType.GAME.value, label="Tipo"
            ).classes("w-full").props('standout="bg-primary text-white"')
            opponent_input = ui.input("Rival (opcional)").classes("w-full").props('standout="bg-primary text-white"')

            ui.label("Franjas candidatas").classes("font-bold text-lg mt-6 text-gray-900")

            with ui.input("Fechas (desde → hasta)").props("readonly").classes("w-full") as dates_input:
                with dates_input.add_slot("append"):
                    ui.icon("event").classes("cursor-pointer").on("click", lambda: date_menu.open())
                with ui.menu() as date_menu:
                    date_picker = ui.date().props('standout="bg-primary text-white" range')

            ui.label("Días de la semana").classes("text-gray-900 text-lg mt-4 font-bold")
            with ui.row().classes("gap-1"):
                for i, label in enumerate(WEEKDAY_LABELS):
                    btn = ui.button(label, on_click=lambda i=i: toggle_weekday(i)).props("dense").style(
                        "min-width:36px; padding:6px 0;"
                    )
                    weekday_buttons[i] = btn

            with ui.row().classes("gap-2 w-full"):
                with ui.input("Desde las", value="09:00").props('standout="bg-primary text-white" readonly').classes("col") as start_input:
                    with start_input.add_slot("append"):
                        ui.icon("access_time").classes("cursor-pointer").on("click", lambda: start_menu.open())
                    with ui.menu() as start_menu:
                        ui.time(value="09:00").bind_value(start_input)
                with ui.input("Hasta las", value="21:00").props('standout="bg-primary text-white" readonly').classes("col") as end_input:
                    with end_input.add_slot("append"):
                        ui.icon("access_time").classes("cursor-pointer").on("click", lambda: end_menu.open())
                    with ui.menu() as end_menu:
                        ui.time(value="21:00").bind_value(end_input)

            duration_input = ui.select(DURATION_OPTIONS, value=60, label="Duración de cada franja").classes("w-full").props('standout="bg-primary text-white"')

            preview_label = ui.label("Completa la horquilla de fechas para ver una previsualización.").classes("text-md mt-4 text-slate-500 font-semibold")
            error_label = ui.label("").classes("text-negative")

        def style_weekday_buttons() -> None:
            for i, btn in weekday_buttons.items():
                if i in selected_weekdays:
                    btn.props(add="color=primary", remove="color=dark")
                else:
                    btn.props(remove="color=primary", add="color=dark")

        def toggle_weekday(i: int) -> None:
            if i in selected_weekdays:
                selected_weekdays.discard(i)
            else:
                selected_weekdays.add(i)
            style_weekday_buttons()
            update_preview()

        style_weekday_buttons()

        def compute_slots() -> list[tuple[date, time, time]] | None:
            date_range = date_picker.value
            if not date_range or not date_range.get("from") or not date_range.get("to"):
                return None
            if not selected_weekdays:
                return None
            try:
                date_from = datetime.strptime(date_range["from"], "%Y-%m-%d").date()
                date_to = datetime.strptime(date_range["to"], "%Y-%m-%d").date()
                daily_start = datetime.strptime(start_input.value, "%H:%M").time()
                daily_end = datetime.strptime(end_input.value, "%H:%M").time()
            except (ValueError, TypeError):
                return None
            try:
                return generate_slots(
                    date_from=date_from,
                    date_to=date_to,
                    weekdays=selected_weekdays,
                    daily_start=daily_start,
                    daily_end=daily_end,
                    duration_minutes=int(duration_input.value),
                )
            except ValueError:
                return None

        def update_preview() -> None:
            date_range = date_picker.value
            if date_range and date_range.get("from") and date_range.get("to"):
                dates_input.value = f"{date_range['from']} → {date_range['to']}"
            slots = compute_slots()
            if slots is None:
                preview_label.text = "Completa la horquilla de fechas para ver una previsualización."
            elif not slots:
                preview_label.text = "Con estos parámetros no se generaría ninguna franja."
            else:
                preview_label.text = f"Se generarán {len(slots)} franjas."

        date_picker.on_value_change(lambda e: update_preview())
        start_input.on_value_change(lambda e: update_preview())
        end_input.on_value_change(lambda e: update_preview())
        duration_input.on_value_change(lambda e: update_preview())

        def save() -> None:
            if not title_input.value:
                error_label.text = "Ponle un título al evento."
                return

            slots = compute_slots()
            if not slots:
                error_label.text = "Revisa la horquilla de fechas, los días y la ventana horaria: no se generaría ninguna franja."
                return

            event = create_event(
                club_id=club_id,
                title=title_input.value,
                event_type=EventType(type_input.value),
                slots=slots,
                opponent_name=opponent_input.value or None,
            )
            create_event_token(event.id)
            ui.notify(f"Evento creado con {len(slots)} franjas", color="positive")
            ui.navigate.to("/staff")

        with ui.row().classes("justify-end w-full mt.4 gap-2"):
            ui.button("Cancelar", on_click=lambda: ui.navigate.to("/staff")).props("flat")
            ui.button("Crear evento", on_click=save).props("color=primary")
