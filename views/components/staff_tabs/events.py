from datetime import date, timedelta

from nicegui import ui

from models import Club, EventStatus
from services.availability_service import unavailability_counts_by_slot
from services.event_service import (
    confirm_slot,
    delete_event,
    get_event_by_id,
    get_event_slots,
    list_events_for_club,
)
from services.token_service import get_event_token
from services.user_service import list_users_for_club
from views.layout import APP_BASE_URL
from views.theme import mix_color

DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

STATUS_BADGE = {
    EventStatus.OPEN: ("Abierto", "bg-amber-100 text-amber-700"),
    EventStatus.CONFIRMED: ("Confirmado", "bg-green-100 text-green-700"),
    EventStatus.PAST: ("Pasado", "bg-gray-200 text-gray-600"),
}

RANK_STYLE = {
    0: ("bg-amber-400", "text-white", "emoji_events"),
    1: ("bg-slate-300", "text-white", "military_tech"),
    2: ("bg-amber-700", "text-white", "military_tech"),
}


def handle_confirm_slot(event_id: int, slot_id: int, dialog) -> None:
    confirm_slot(event_id, slot_id)
    dialog.close()
    ui.notify("Horario confirmado", type="positive")
    ui.navigate.reload()


def handle_delete_event(event_id: int, on_change=None) -> None:
    delete_event(event_id)
    ui.notify("Evento eliminado", type="positive")
    if on_change:
        on_change()
    else:
        ui.navigate.reload()


def confirm_delete_event(event_id: int, parent_dialog=None) -> None:
    def do_delete() -> None:
        confirm_dialog.close()
        if parent_dialog:
            parent_dialog.close()
        handle_delete_event(event_id)

    with ui.dialog() as confirm_dialog, ui.card().classes('w-full max-w-sm p-5 gap-3 rounded-2xl'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('warning', color='negative').classes('text-2xl')
            ui.label('¿Eliminar este evento?').classes('text-base font-bold text-gray-900')
        ui.label(
            'Esta acción no se puede deshacer y se perderán las respuestas de disponibilidad asociadas.'
        ).classes('text-sm text-gray-500')
        with ui.row().classes('w-full justify-end gap-2 mt-2'):
            ui.button('Cancelar', on_click=confirm_dialog.close).props('flat no-caps').classes('text-gray-600')
            ui.button('Eliminar', on_click=do_delete).props('unelevated no-caps').classes(
                'bg-red-600 text-white rounded-lg'
            )
    confirm_dialog.open()


def open_best_slots_view(event, slots, baja_counts, total_users) -> None:
    if not slots:
        ui.notify('Este evento no tiene franjas candidatas.', type='warning')
        return

    ranked = sorted(slots, key=lambda s: (baja_counts.get(s.id, 0), s.day, s.start_time))[:5]

    with ui.dialog() as dialog, ui.card().tight().classes(
        'w-full max-w-sm rounded-[28px] overflow-hidden shadow-2xl'
    ):
        with ui.column().classes(
            'w-full items-center gap-1 px-6 pt-8 pb-7 bg-primary text-white'
        ):
            ui.image('static/badge.png').classes('size-20 text-amber-300 drop-shadow mb-1')
            ui.label(event.title).classes('text-xl font-black text-center leading-tight')
            if event.opponent_name:
                ui.label(f"vs. {event.opponent_name}").classes('text-sm text-white/80')
            ui.label('SOM-HI!').classes(
                'text-[11px] font-bold tracking-[0.25em] text-white/70 mt-3'
            )

        with ui.column().classes('w-full gap-2.5 px-5 py-5 bg-white'):
            for i, slot in enumerate(ranked):
                count = baja_counts.get(slot.id, 0)
                available = total_users - count if total_users else None
                ratio = (available / total_users) if total_users else None
                is_top = i == 0
                rank_bg, rank_text, rank_icon = RANK_STYLE.get(i, ("bg-gray-200", "text-gray-600", None))

                row_classes = (
                    'w-full items-center justify-between p-3.5 rounded-2xl border no-wrap gap-3 transition-all'
                )
                row_classes += (
                    ' bg-amber-50 border-amber-200 shadow-sm'
                    if is_top
                    else ' bg-gray-50 border-gray-100'
                )

                with ui.row().classes(row_classes):
                    with ui.row().classes('items-center gap-3 no-wrap'):
                        with ui.element('div').classes(
                            f'w-9 h-9 flex items-center justify-center rounded-full flex-shrink-0 {rank_bg} {rank_text}'
                        ):
                            if rank_icon:
                                ui.icon(rank_icon).classes('text-lg')
                            else:
                                ui.label(str(i + 1)).classes('text-sm font-black')

                        with ui.column().classes('gap-0'):
                            ui.label(
                                f"{DIAS_ES[slot.day.weekday()].capitalize()} {slot.day:%d/%m}"
                            ).classes('text-sm font-bold text-gray-900 leading-tight')
                            ui.label(f"{slot.start_time:%H:%M}").classes('text-xs text-gray-500')

                    with ui.column().classes('items-end gap-1 flex-shrink-0'):
                        if total_users:
                            ui.label(f"{available}/{total_users}").classes(
                                'text-xs font-bold text-green-700'
                            )
                            with ui.element('div').classes('w-16 h-1.5 rounded-full bg-gray-200 overflow-hidden'):
                                ui.element('div').classes('h-full rounded-full bg-green-500').style(
                                    f'width:{ratio * 100:.0f}%;'
                                )
                        else:
                            ui.label(f"{count} baja{'s' if count != 1 else ''}").classes(
                                'text-xs font-semibold text-gray-500'
                            )

            ui.button('Cerrar', on_click=dialog.close).props('flat no-caps').classes(
                'self-center text-gray-500 -mb-1'
            )
    dialog.open()


def open_event_detail(event_id: int) -> None:
    event = get_event_by_id(event_id)
    slots = get_event_slots(event_id)
    token = get_event_token(event_id)
    total_users = len(list_users_for_club(event.club_id))
    baja_counts = unavailability_counts_by_slot(event_id)
    link = f"{APP_BASE_URL}/e/{token.value}" if token else ""
    is_open = event.status == EventStatus.OPEN

    all_days = sorted({slot.day for slot in slots})
    all_times = sorted({slot.start_time for slot in slots})
    slot_lookup = {(slot.day, slot.start_time): slot for slot in slots}

    best_slot_id = min(baja_counts, key=baja_counts.get) if baja_counts else None
    confirmed_slot = next((s for s in slots if s.id == event.confirmed_slot_id), None)

    def week_start(d: date) -> date:
        return d - timedelta(days=d.weekday())

    days_by_week: dict[date, list[date]] = {}
    for day in all_days:
        days_by_week.setdefault(week_start(day), []).append(day)
    week_starts = sorted(days_by_week.keys())

    default_week_index = 0
    anchor_slot = confirmed_slot or next((s for s in slots if s.id == best_slot_id), None)
    if anchor_slot and week_start(anchor_slot.day) in days_by_week:
        default_week_index = week_starts.index(week_start(anchor_slot.day))

    state = {"week_index": default_week_index}

    def change_week(delta: int) -> None:
        new_index = state["week_index"] + delta
        if 0 <= new_index < len(week_starts):
            state["week_index"] = new_index
            render_grid.refresh()

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl p-5 gap-3 rounded-2xl'):
        with ui.row().classes('w-full justify-between items-start no-wrap'):
            with ui.column().classes('gap-0'):
                ui.label(event.title).classes('text-xl font-bold text-gray-900')
                if event.opponent_name:
                    ui.label(f"vs. {event.opponent_name}").classes('text-sm text-gray-500')
            label_text, badge_style = STATUS_BADGE[event.status]
            ui.label(label_text).classes(f'px-2.5 py-0.5 text-xs font-medium rounded-full {badge_style}')

        if confirmed_slot:
            with ui.row().classes('w-full items-center gap-2 p-3 bg-primary/10 rounded-lg'):
                ui.icon('event_available').classes('text-primary text-lg')
                ui.label(
                    f"Horario confirmado: {DIAS_ES[confirmed_slot.day.weekday()].capitalize()} "
                    f"{confirmed_slot.day:%d/%m} · {confirmed_slot.start_time:%H:%M}"
                ).classes('text-sm font-semibold text-primary')

        with ui.row().classes('w-full gap-2 items-center p-2 border border-gray-200 rounded-lg bg-gray-50'):
            ui.icon('link').classes('text-gray-400 text-base')
            ui.input(value=link).props('readonly borderless dense').classes('flex-grow text-sm')
            ui.button(
                icon='content_copy',
                on_click=lambda: (
                    ui.run_javascript(f'navigator.clipboard.writeText("{link}")'),
                    ui.notify('Enlace copiado', type='positive'),
                ),
            ).props('flat round dense').classes('text-gray-500')

        ui.button(
            'Ver mejores horarios',
            icon='leaderboard',
            on_click=lambda: open_best_slots_view(event, slots, baja_counts, total_users),
        ).props('outline no-caps').classes('w-full text-primary border-primary rounded-lg')

        if not slots:
            ui.label('Este evento todavía no tiene franjas candidatas.').classes('text-sm text-gray-500 py-2')
        else:
            @ui.refreshable
            def render_grid() -> None:
                current_week_start = week_starts[state["week_index"]]
                current_week_days = days_by_week[current_week_start]
                current_week_end = current_week_start + timedelta(days=6)
                is_first_week = state["week_index"] == 0
                is_last_week = state["week_index"] == len(week_starts) - 1

                with ui.row().classes('items-center justify-between w-full no-wrap'):
                    ui.button(icon='chevron_left', on_click=lambda: change_week(-1)).props(
                        'flat round dense' + (' disable' if is_first_week else '')
                    ).classes('text-primary')
                    ui.label(f"{current_week_start:%d/%m} – {current_week_end:%d/%m}").classes(
                        'text-base font-bold text-dark'
                    )
                    ui.button(icon='chevron_right', on_click=lambda: change_week(1)).props(
                        'flat round dense' + (' disable' if is_last_week else '')
                    ).classes('text-primary')

                grid_style = f"grid-template-columns: 56px repeat({len(current_week_days)}, minmax(64px, 1fr));"
                with ui.element('div').classes('w-full overflow-x-auto mt-2'):
                    with ui.element('div').classes('grid gap-2').style(grid_style):
                        ui.element('div')
                        for day in current_week_days:
                            with ui.column().classes('items-center gap-0'):
                                ui.label(DIAS_ES[day.weekday()][:3].capitalize()).classes(
                                    'text-sm font-semibold text-dark'
                                )
                                ui.label(f"{day:%d/%m}").classes('text-xs text-gray-500')

                        for t in all_times:
                            ui.label(f"{t:%H:%M}").classes('text-xs text-gray-500 flex items-center')
                            for day in current_week_days:
                                slot = slot_lookup.get((day, t))
                                if slot is None:
                                    ui.element('div')
                                    continue

                                count = baja_counts.get(slot.id, 0)
                                ratio = count / total_users if total_users else 0
                                bg = mix_color(ratio)
                                is_best = slot.id == best_slot_id and is_open
                                is_confirmed_slot = slot.id == event.confirmed_slot_id

                                cell_classes = (
                                    "h-16 w-full min-w-0 rounded-xl flex flex-col items-center justify-center "
                                    "text-white transition-transform relative shadow-sm"
                                )
                                if is_confirmed_slot:
                                    cell_classes += " ring-2 ring-offset-2 ring-primary"
                                if is_open:
                                    cell_classes += " cursor-pointer hover:scale-[1.04]"

                                cell = ui.element('div').classes(cell_classes).style(f'background:{bg} !important;')
                                if is_open:
                                    cell.on('click', lambda s=slot: handle_confirm_slot(event_id, s.id, dialog))
                                with cell:
                                    ui.label(str(count)).classes('text-lg font-bold leading-none')
                                    ui.label('baja' + ('s' if count != 1 else '')).classes(
                                        'text-[10px] leading-none opacity-90 mt-1'
                                    )
                                    if is_best:
                                        ui.icon('star').classes(
                                            'absolute top-1 right-1 text-white text-xs drop-shadow'
                                        )

                if is_open:
                    ui.label('Toca una franja para confirmarla como horario definitivo.').classes(
                        'text-xs text-gray-400 mt-1'
                    )

            render_grid()

        with ui.row().classes('w-full justify-between items-center mt-2'):
            ui.button('Eliminar evento', on_click=lambda: confirm_delete_event(event_id, dialog)).props(
                'flat no-caps'
            ).classes('text-red-600')
            ui.button('Cerrar', on_click=dialog.close).props('flat no-caps').classes('text-gray-600')

    dialog.open()


def events_tab_page(club: Club, on_change: callable, is_admin: bool = False):
    with ui.column().classes('w-full max-w-lg mx-auto min-h-screen p-4 gap-4'):

        events = list_events_for_club(club_id=club.id)

        with ui.row().classes('w-full justify-between items-center mb-2'):
            ui.label('Eventos').classes('text-2xl font-bold text-gray-900')
            ui.button(
                'Nuevo evento', icon='add', on_click=lambda: ui.navigate.to('/staff/events/new')
            ).props('unelevated no-caps').classes(
                'bg-primary text-white hover:bg-secondary text-sm font-medium rounded-lg px-3 py-1.5'
            )

        if not events:
            ui.label('Todavía no hay eventos. Crea el primero.').classes('text-sm text-gray-500')

        for event in events:
            label_text, badge_style = STATUS_BADGE[event.status]

            with ui.card().classes(
                'w-full p-4 bg-gray-50 border border-gray-200 rounded-xl shadow-none '
                'hover:shadow-md hover:border-gray-300 transition-all gap-2'
            ):
                with ui.row().classes('w-full items-start no-wrap gap-2'):
                    with ui.column().classes('flex-grow gap-0 cursor-pointer').on(
                        'click', lambda ev=event: open_event_detail(ev.id)
                    ):
                        title = (
                            event.title
                            if not event.opponent_name
                            else f"{event.title} · vs. {event.opponent_name}"
                        )
                        ui.label(title).classes('font-semibold text-gray-900 text-base leading-tight')
                        ui.label(event.event_type.value.replace("_", " ").title()).classes('text-sm text-gray-500')

                    with ui.column().classes('items-end gap-3 flex-shrink-0 justify-between'):
                        ui.label(label_text).classes(
                            f'px-2.5 py-0.5 text-xs font-medium rounded-full {badge_style}'
                        )
                        with ui.dropdown_button().props('flat round density=compact dropdown-icon="delete" no-icon-animation') \
                            .classes('text-gray-400 hover:text-primary hover:bg-accent'):
                            with ui.column().classes("p-4 gap-1 w-full text-center mb-2 items-center"):
                                ui.label("¿Estás seguro?").classes('font-bold text-md text-slate-600')
                                ui.label("No podrás recuperar los datos.").classes('text-sm mb-1 text-slate-500')
                                (
                                    ui.button(
                                        text="Borrar",
                                        on_click=lambda ev=event: handle_delete_event(ev.id, on_change=on_change),
                                    )
                                )
                                    