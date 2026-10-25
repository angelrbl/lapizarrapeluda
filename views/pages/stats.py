from nicegui import ui, app

from models import RoleType
from views.layout import frame

from services.role_service import get_user_roles
from services.club_service import get_club_by_name, get_only_club
from services.stats_service import get_club_stats_ranking

from views.components.stats_dialog import open_player_stats_dialog

def open_ranking_dialog(title: str, players, metric_getter, icon: str, color_class: str):
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-sm p-6 rounded-2xl shadow-xl bg-white gap-4'):
        with ui.row().classes('w-full items-center justify-between no-wrap'):
            with ui.row().classes('items-center gap-2'):
                ui.icon(icon, size='sm').classes(color_class)
                ui.label(title).classes('text-lg font-bold text-gray-900')
            ui.button(icon='close', on_click=dialog.close).props('flat round dense').classes('text-gray-400')
        
        ui.separator().classes('bg-gray-100 my-1')

        with ui.column().classes('w-full gap-2 max-h-[350px] overflow-y-auto'):
            if not players:
                ui.label('No hay datos registrados.').classes('text-sm text-gray-400 italic')
            else:
                for i, p in enumerate(players):
                    val = metric_getter(p)
                    with ui.row().classes('w-full items-center justify-between p-3 rounded-xl bg-gray-50 border border-gray-100'):
                        with ui.row().classes('items-center gap-2.5'):
                            ui.label(f"#{i+1}").classes('text-xs font-black text-gray-400 w-5 text-center')
                            if p.number:
                                ui.label(f"{p.number}").classes('font-black text-xs text-gray-800 px-1.5 py-0.5 rounded')
                            ui.label(p.name).classes('font-semibold text-sm text-gray-900 truncate max-w-[160px]')
                        ui.label(str(val)).classes('font-black text-sm text-gray-900')

        with ui.row().classes('w-full justify-end mt-2'):
            ui.button('Cerrar', on_click=dialog.close).props('flat no-caps').classes('text-gray-600')
    dialog.open()

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

        with ui.column().classes('w-full max-w-lg mx-auto min-h-screen p-4 gap-4 bg-white'):
            
            with ui.row().classes('w-full justify-between items-end mb-1'):
                ui.label('Estadísticas').classes('text-2xl font-bold text-gray-900')
                ui.image('static/badge.png').classes('size-10')

            if not players:
                ui.label('No hay jugadores registrados en este club.').classes('text-sm text-gray-500 italic')
                return

            valid_players = [p for p in players if p.stats]

            scorers = sorted(valid_players, key=lambda p: p.stats.goals, reverse=True)
            assistants = sorted(valid_players, key=lambda p: p.stats.assists, reverse=True)
            gplusa = sorted(valid_players, key=lambda p: (p.stats.assists + p.stats.goals), reverse=True)
            mvps = sorted(valid_players, key=lambda p: getattr(p.stats, 'mvp_count', 0), reverse=True)
            yellows_list = sorted(valid_players, key=lambda p: p.stats.yellow_cards, reverse=True)
            reds_list = sorted(valid_players, key=lambda p: p.stats.red_cards, reverse=True)

            def render_top_section(title, full_list, metric_getter, icon, color_class="text-primary"):
                top_3 = full_list[:3]
                with ui.column().classes('w-full gap-2 mb-1'):
                    with ui.row().classes('w-full justify-between items-center'):
                        with ui.row().classes('items-center gap-1.5'):
                            ui.icon(icon, size='xs').classes(color_class)
                            ui.label(title).classes('text-xs font-bold text-gray-400 uppercase tracking-wider')
                        
                        if len(full_list) > 0:
                            ui.button('Ver más', on_click=lambda t=title, l=full_list, mg=metric_getter, ic=icon, cc=color_class: open_ranking_dialog(t, l, mg, ic, cc)).props('flat dense no-caps').classes('text-xs text-primary font-semibold')

                    with ui.card().classes('w-full p-3 bg-gray-50 border border-gray-200 rounded-xl shadow-none gap-2'):
                        if not top_3 or all(metric_getter(p) == 0 for p in top_3):
                            ui.label('Sin registros todavía.').classes('text-xs text-gray-400 italic py-1')
                        else:
                            for idx, p in enumerate(top_3):
                                val = metric_getter(p)
                                with ui.row().classes('w-full justify-between items-center py-0.5'):
                                    with ui.row().classes('items-center gap-2 no-wrap'):
                                        ui.label(f"#{idx+1}").classes('text-xs font-bold text-gray-400 w-4')
                                        if p.number:
                                            ui.label(f"{p.number}").classes('font-bold text-xs text-gray-700')
                                        ui.label(p.name).classes('text-sm font-semibold text-gray-900 truncate max-w-[200px]')
                                    ui.label(str(val)).classes('text-sm font-black text-gray-900')

            render_top_section('Top 3 Goleadores', scorers, lambda p: p.stats.goals, 'sports_soccer')
            render_top_section('Top 3 Asistentes', assistants, lambda p: p.stats.assists, 'handshake')
            render_top_section('Top 3 G + A', gplusa, lambda p: (p.stats.assists + p.stats.goals), 'whatshot')
            render_top_section('Top 3 Estrellas Damm', mvps, lambda p: getattr(p.stats, 'mvp_count', 0), 'star', 'text-amber-500')
            render_top_section('Top 3 Más Amarillas', yellows_list, lambda p: p.stats.yellow_cards, 'style', 'text-amber-300')
            render_top_section('Top 3 Más Rojas', reds_list, lambda p: p.stats.red_cards, 'style')

            ui.label('Plantilla').classes('text-xs font-bold text-gray-400 uppercase tracking-wider mt-3 mb-1')

            for player in players:
                stats = player.stats
                goals = stats.goals if stats else 0
                assists = stats.assists if stats else 0
                starters = stats.starter_amount if stats else 0
                matches_played = getattr(stats, 'matches_played', starters) if stats else 0
                yellows = stats.yellow_cards if stats else 0
                reds = stats.red_cards if stats else 0

                user_roles = get_user_roles(user_id=player.id)

                with ui.card().classes(
                    'w-full p-4 bg-gray-50 border border-gray-200 rounded-xl shadow-none gap-2 '
                    'cursor-pointer hover:bg-gray-100 transition-colors'
                ).on('click', lambda usr=player, is_c=(RoleType.CAPTAIN in user_roles): open_player_stats_dialog(
                    user=usr, 
                    is_admin=False,
                    is_captain=is_c,
                    on_change=lambda: ui.navigate.to(f'/{club.name}/stats' if club_name else '/stats')
                )):
                    
                    with ui.row().classes('w-full justify-between items-center no-wrap'):
                        with ui.row().classes('w-full justify-between items-start no-wrap'):
                            with ui.row().classes('gap-1'):
                                if RoleType.CAPTAIN in user_roles:
                                    ui.label("C").classes('font-bold text-md text-primary')
                                    ui.label("|").classes('font-black text-sm text-gray-900')
        
                                if player.number:
                                    ui.label(f"{player.number}").classes('font-black text-sm text-gray-900')
                                    ui.label("|").classes('font-black text-sm text-gray-900')
                            
                                ui.label(player.name).classes('font-semibold text-gray-900 text-base leading-tight truncate')

                        with ui.row().classes('items-center gap-2 text-xs font-semibold text-gray-600 flex-shrink-0'):
                            
                            with ui.row().classes('items-center gap-0.5'):
                                ui.label('PJ:').classes('text-[10px] text-gray-400')
                                ui.label(str(matches_played)).classes('font-bold text-primary')

                            with ui.row().classes('items-center gap-0.5'):
                                ui.label('PT:').classes('text-[10px] text-gray-400')
                                ui.label(str(starters)).classes('font-bold text-primary')

                            with ui.row().classes('items-center gap-0.5'):
                                ui.icon('sports_soccer', size='xs')
                                ui.label(str(goals)).classes('font-bold text-primary')
                            
                            with ui.row().classes('items-center gap-0.5'):
                                ui.icon('handshake', size='xs')
                                ui.label(str(assists)).classes('text-primary')

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