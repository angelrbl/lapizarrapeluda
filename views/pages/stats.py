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

        players = get_club_stats_ranking(club.id)

        with ui.column().classes('w-full max-w-lg mx-auto min-h-screen p-4 gap-4'):
            
            # Cabecera
            with ui.row().classes('w-full justify-between items-center mb-1'):
                ui.label('Estadísticas').classes('text-2xl font-bold text-gray-900')
                ui.label('Temporada').classes('text-xs font-semibold text-gray-500 uppercase tracking-wider')

            if not players:
                ui.label('No hay jugadores registrados en este club.').classes('text-sm text-gray-500 italic')
                return

            # --- SECCIÓN 1: DESTACADOS ---
            valid_players = [p for p in players if p.stats]
            top_scorer = max(valid_players, key=lambda p: p.stats.goals, default=None) if valid_players else None
            top_assistant = max(valid_players, key=lambda p: p.stats.assists, default=None) if valid_players else None

            if (top_scorer and top_scorer.stats.goals > 0) or (top_assistant and top_assistant.stats.assists > 0):
                with ui.column().classes('w-full gap-2 mb-1'):
                    ui.label('Destacados').classes('text-xs font-bold text-gray-400 uppercase tracking-wider')
                    
                    with ui.row().classes('w-full gap-3 no-wrap'):
                        if top_scorer and top_scorer.stats.goals > 0:
                            with ui.card().classes('flex-1 p-3.5 bg-gray-50 border border-gray-200 rounded-xl shadow-none gap-1'):
                                with ui.row().classes('items-center gap-1.5 text-amber-600 font-bold text-xs'):
                                    ui.icon('sports_soccer', size='xs')
                                    ui.label('Pichichi')
                                ui.label(top_scorer.name).classes('font-semibold text-gray-900 text-sm truncate')
                                ui.label(f"{top_scorer.stats.goals} Goles").classes('text-lg font-black text-gray-900')

                        if top_assistant and top_assistant.stats.assists > 0:
                            with ui.card().classes('flex-1 p-3.5 bg-gray-50 border border-gray-200 rounded-xl shadow-none gap-1'):
                                with ui.row().classes('items-center gap-1.5 text-blue-600 font-bold text-xs'):
                                    ui.icon('handshake', size='xs')
                                    ui.label('Asistente')
                                ui.label(top_assistant.name).classes('font-semibold text-gray-900 text-sm truncate')
                                ui.label(f"{top_assistant.stats.assists} Asist.").classes('text-lg font-black text-gray-900')

            # --- SECCIÓN 2: LISTA DE PLANTILLA ---
            ui.label('Plantilla').classes('text-xs font-bold text-gray-400 uppercase tracking-wider mt-2')

            for player in players:
                stats = player.stats
                goals = stats.goals if stats else 0
                assists = stats.assists if stats else 0
                
                # Si en PlayerStats tienes starter_amount, podemos tomarlo como Titularidades
                # y si le añadiste matches_played / total_matches, mostrar PJ.
                starters = stats.starter_amount if stats else 0
                # Si no tienes campo matches_played directo, de momento mostramos starters
                matches_played = getattr(stats, 'matches_played', starters) if stats else 0
                
                yellows = stats.yellow_cards if stats else 0
                reds = stats.red_cards if stats else 0

                with ui.card().classes(
                    'w-full p-4 bg-gray-50 border border-gray-200 rounded-xl shadow-none gap-2 '
                    'cursor-pointer hover:bg-gray-100 transition-colors'
                ).on('click', lambda usr=player: open_player_stats_dialog(
                    user=usr, 
                    is_admin=app.storage.user.get('is_admin', False), 
                    on_change=lambda: ui.navigate.to(f'/{club.name}/stats' if club_name else '/stats')
                )):
                    
                    with ui.row().classes('w-full justify-between items-center no-wrap'):
                        # Dorsal y Nombre
                        with ui.row().classes('items-center gap-1 no-wrap'):
                            if player.number:
                                ui.label(f"{player.number}").classes('font-black text-sm text-gray-900')
                                ui.label("|").classes('font-black text-sm text-gray-300 mx-0.5')
                            
                            ui.label(player.name).classes('font-semibold text-gray-900 text-base leading-tight truncate')

                        # Bloque de métricas a la derecha
                        with ui.row().classes('items-center gap-2.5 text-xs font-semibold text-gray-600 flex-shrink-0'):
                            
                            # Partidos Jugados (PJ) / Titulares (T)
                            with ui.row().classes('items-center gap-1'):
                                ui.icon('sports', size='xs').classes('text-gray-400')
                                ui.label(f"{matches_played} PJ").classes('font-bold text-gray-700')

                            # Goles
                            with ui.row().classes('items-center gap-0.5'):
                                ui.icon('sports_soccer', size='xs').classes('text-amber-600')
                                ui.label(str(goals)).classes('font-bold text-gray-900')
                            
                            # Asistencias
                            with ui.row().classes('items-center gap-0.5'):
                                ui.icon('handshake', size='xs').classes('text-blue-600')
                                ui.label(str(assists)).classes('font-bold text-gray-900')

                            # Tarjetas (con badges discretos de estilo rectangular)
                            if yellows > 0 or reds > 0:
                                with ui.row().classes('items-center gap-1 ml-0.5'):
                                    if yellows > 0:
                                        with ui.element('div').classes('w-3.5 h-4 bg-amber-400 rounded-[2px] flex items-center justify-center shadow-xs'):
                                            ui.label(str(yellows)).classes('text-[9px] font-black text-black leading-none')
                                    if reds > 0:
                                        with ui.element('div').classes('w-3.5 h-4 bg-red-600 rounded-[2px] flex items-center justify-center shadow-xs'):
                                            ui.label(str(reds)).classes('text-[9px] font-black text-white leading-none')

        with ui.row().classes('fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-3xl items-center justify-between px-6 -z-10'):
            ui.image('/static/tag-heuer.png').classes('ml-3 w-16 sm:w-20 h-12 sm:h-16').props('fit="contain"')
            ui.image('/static/estrella-damm.png').classes('w-16 sm:w-20 h-12 sm:h-16').props('fit="contain"')
            ui.image('/static/suave.png').classes('w-16 sm:w-20 h-12 sm:h-16').props('fit="contain"')