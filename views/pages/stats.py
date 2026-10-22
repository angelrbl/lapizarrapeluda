from nicegui import ui, app

from models import RoleType
from views.layout import frame

from services.club_service import get_club_by_name, get_only_club
from services.stats_service import get_club_stats_ranking

@ui.page('/stats')
@ui.page('/{club_name}/stats')
def stats_page(club_name: str | None = None) -> None:
    club = get_club_by_name(name=club_name) if club_name else get_only_club()

    with frame(navigation_title="Estadísticas"):
        if not club:
            with ui.column().classes('w-full items-center justify-center min-h-[60vh] p-6 text-center gap-2'):
                ui.label("¡Qué lástima!").classes("text-3xl font-black text-negative")
                ui.label("No se ha encontrado ningún club con ese nombre.").classes('text-xl font-bold text-slate-700')
            return

        ui.label("Todavía no hay nada.").classes("text-3xl font-black text-negative")