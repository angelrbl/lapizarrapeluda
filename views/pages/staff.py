from nicegui import ui, app

from views.layout import frame
from views.components.staff_tabs import club_tab_page, squad_tab_page, events_tab_page

from services.club_service import get_club_by_id


@ui.page('/staff')
def admin_page() -> None:
    if not app.storage.user.get('user_id', None) or not app.storage.user.get('club_id', None):
        ui.navigate.to('/login')
        return

    club_id = app.storage.user.get('club_id')
    is_admin = app.storage.user.get('is_admin', None)
    is_active = app.storage.user.get('is_active', None)
    club = get_club_by_id(club_id=club_id)

    with frame(navigation_title=(club.name if len(club.name) < 10 else "Staff")):
        if not is_active:
            ui.label("¡Prohíbido el paso!").classes("text-3xl font-black text-negative")
            ui.label("Solo el staff de tu club puede estar aquí.").classes('text-xl font-bold text-slate-700')
            return

        with ui.tabs().classes('w-full text-primary') as tabs:
            club_tab = ui.tab('Club', icon='sports_soccer')
            squad_tab = ui.tab('Plantilla', icon='groups')
            events_tab = ui.tab('Eventos', icon='event')

        @ui.refreshable
        def render_admin_tabs(value: ui.tab = events_tab):
            with ui.tab_panels(tabs, value=value).classes('w-full'):
                with ui.tab_panel(club_tab):
                    club_tab_page(club=club, is_admin=is_admin)

                with ui.tab_panel(squad_tab):
                    squad_tab_page(club=club, is_admin=is_admin, on_change=lambda: render_admin_tabs.refresh(value=squad_tab))

                with ui.tab_panel(events_tab):
                    events_tab_page(club=club, is_admin=is_admin, on_change=lambda: render_admin_tabs.refresh(value=events_tab))

        render_admin_tabs()