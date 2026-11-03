from nicegui import app, ui

from services.stats_service import get_player_stats, update_player_stats
from services.stats_service import increment_stat
from services.user_service import list_users_for_club

def open_player_stats_dialog(user: User, is_admin: bool, is_captain: bool, on_change: callable) -> None:
    stats = get_player_stats(user.id)

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6 rounded-[28px] shadow-2xl bg-white gap-4'):
        
        with ui.row().classes('w-full items-center justify-between no-wrap'):
            with ui.row().classes('items-center gap-3'):
                with ui.element('div').classes('w-12 h-12 flex items-center justify-center rounded-2xl bg-primary/10 text-primary font-black text-lg'):
                    ui.label(("C | " if is_captain else "") + (f"{user.number}" if user.number else "-"))
                with ui.column().classes('gap-0'):
                    ui.label(user.name).classes('text-lg font-bold text-gray-900 leading-tight')
            
            ui.button(icon='close', on_click=dialog.close).props('flat round dense').classes('text-gray-400 hover:text-gray-700')

        ui.separator().classes('bg-gray-100 my-1')

        if is_admin:
            with ui.column().classes('w-full gap-3 py-2'):
                with ui.row().classes('w-full gap-3'):
                    in_pj = ui.number(label="Partidos Jugados", value=stats.matches_played, min=0).classes('flex-1').props('standout="bg-primary text-white"')
                    in_starter = ui.number(label="Titularidades", value=stats.starter_amount, min=0).classes('flex-1').props('standout="bg-primary text-white"')
                
                with ui.row().classes('w-full gap-3'):
                    in_goals = ui.number(label="Goles", value=stats.goals, min=0).classes('flex-1').props('standout="bg-primary text-white"')
                    in_assists = ui.number(label="Asistencias", value=stats.assists, min=0).classes('flex-1').props('standout="bg-primary text-white"')
                
                with ui.row().classes('w-full gap-3'):
                    in_yellow = ui.number(label="Tarjetas Amarillas", value=stats.yellow_cards, min=0).classes('flex-1').props('standout="bg-primary text-white"')
                    in_red = ui.number(label="Tarjetas Rojas", value=stats.red_cards, min=0).classes('flex-1').props('standout="bg-primary text-white"')
                
                with ui.row().classes('w-full gap-3'):
                    in_mvp = ui.number(label="Jugador Estrella Damm", value=stats.mvp_count, min=0).classes('flex-1').props('standout="bg-primary text-white"')

                error_label = ui.label("").classes('text-xs text-negative hidden')

            with ui.row().classes('w-full justify-end gap-2 mt-2'):
                ui.button('Cancelar', on_click=dialog.close).props('flat no-caps').classes('text-gray-500')
                
                def handle_save():
                    try:
                        update_player_stats(
                            player_id=user.id,
                            matches_played=int(in_pj.value or 0),
                            goals=int(in_goals.value or 0),
                            assists=int(in_assists.value or 0),
                            starter_amount=int(in_starter.value or 0),
                            yellow_cards=int(in_yellow.value or 0),
                            red_cards=int(in_red.value or 0),
                            mvp_count=int(in_mvp.value or 0)
                        )
                        ui.notify('¡Estadísticas actualizadas con éxito!', type='positive')
                        dialog.close()
                        on_change()
                    except Exception as e:
                        error_label.text = "Error al guardar los datos."
                        error_label.classes(remove='hidden')

                ui.button('Guardar cambios', on_click=handle_save).props('unelevated no-caps').classes('bg-primary text-white font-bold rounded-xl px-4')
        else:
            with ui.column().classes('w-full gap-3 py-3'):
                def stat_row(icon, label, value, color="text-primary", is_image=False):
                    with ui.row().classes('w-full items-center justify-between p-3 rounded-xl bg-gray-50 border border-gray-100'):
                        with ui.row().classes('items-center gap-2'):
                            if is_image:
                                ui.image(icon).classes('size-5')
                            else:
                                ui.icon(icon).classes('text-primary text-base')
                            ui.label(label).classes('text-sm font-medium text-gray-600')
                        ui.label(str(value)).classes(f'text-base font-black {color}')

                stat_row('sports', 'Partidos Jugados', stats.matches_played)
                stat_row('person', 'Titularidades', stats.starter_amount)
                stat_row('sports_soccer', 'Goles', stats.goals)
                stat_row('static/cleat.svg', 'Asistencias', stats.assists, is_image=True)
                stat_row('style', 'Tarjetas Amarillas', stats.yellow_cards)
                stat_row('style', 'Tarjetas Rojas', stats.red_cards)
                stat_row('static/estrella-damm.png', 'Jugador Estrella Damm', stats.mvp_count, 'text-amber-600', True)

            with ui.row().classes('w-full justify-end mt-2'):
                ui.button('Cerrar', on_click=dialog.close).props('unelevated no-caps').classes('bg-gray-100 text-gray-700 font-bold px-5 py-2 rounded-xl')

    dialog.open()

STAT_LABELS = {
    'matches_played': 'Partidos jugados (+1 PJ)',
    'starter_amount': 'Titularidades (+1 PT)',
    'goals': 'Goles (+1 Gol)',
    'assists': 'Asistencias (+1 Asist.)',
    'yellow_cards': 'Tarjetas amarillas (+1 Amarilla)',
    'red_cards': 'Tarjetas rojas (+1 Roja)',
    'mvp_count': 'Jugador Estrella Damm (+1 MVP)'
}

def open_fast_registration_dialog(club_id: int, on_success: callable):
    players = list_users_for_club(club_id)

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6 rounded-2xl shadow-xl bg-white gap-4'):
        
        with ui.row().classes('w-full items-center justify-between no-wrap'):
            ui.label("Registro Rápido").classes('text-xl font-bold text-gray-900')
            ui.button(icon='close', on_click=dialog.close).props('flat round dense').classes('text-gray-400')

        ui.separator().classes('bg-gray-100 my-1')

        stat_select = ui.select(
            options=STAT_LABELS, 
            label="Métrica a actualizar",
            value='matches_played'
        ).classes('w-full').props('outlined dense')

        with ui.row().classes('w-full justify-between items-center mt-2'):
            ui.label("Jugadores participantes").classes('text-xs font-bold text-gray-400 uppercase tracking-wider')
            
            all_selected = False
            checkboxes = {}

            def toggle_all():
                nonlocal all_selected
                all_selected = not all_selected
                for cb in checkboxes.values():
                    cb.value = all_selected

            ui.button('Seleccionar todos', on_click=toggle_all).props('flat dense no-caps').classes('text-xs text-primary font-semibold')

        with ui.column().classes('w-full gap-2 max-h-[320px] overflow-y-auto border border-gray-100 rounded-xl p-2 bg-gray-50'):
            if not players:
                ui.label('No hay jugadores en el club.').classes('text-sm text-gray-400 italic p-2')
            else:
                for p in players:
                    with ui.row().classes('w-full items-center justify-between p-2.5 bg-white rounded-lg border border-gray-100'):
                        with ui.row().classes('items-center gap-2.5'):
                            if p.number:
                                ui.label(f"#{p.number}").classes('font-black text-xs text-gray-800 w-6')
                            else:
                                ui.label('-').classes('font-bold text-xs text-gray-400 w-6 text-center')
                            ui.label(p.name).classes('font-semibold text-sm text-gray-900 truncate max-w-[200px]')
                        
                        cb = ui.checkbox().props('dense')
                        checkboxes[p.id] = cb

        error_label = ui.label("").classes('text-xs text-negative hidden')

        with ui.row().classes('w-full justify-end items-center mt-2 gap-2 pt-2 border-t border-gray-100'):
            ui.button('Cancelar', on_click=dialog.close).props('flat no-caps').classes('text-gray-500')
            
            def handle_confirm():
                selected_ids = [pid for pid, cb in checkboxes.items() if cb.value]
                selected_stat = stat_select.value

                if not selected_ids:
                    error_label.text = "Selecciona al menos un jugador."
                    error_label.classes(remove='hidden')
                    return

                try:
                    count = increment_stat(club_id=club_id, player_ids=selected_ids, stat=selected_stat)
                    stat_title = STAT_LABELS.get(selected_stat, selected_stat).split('(')[0].strip()
                    ui.notify(f'¡{stat_title} +1 aplicado a {count} jugadores!', type='positive')
                    dialog.close()
                    on_success()
                except ValueError as e:
                    error_label.text = f"Error: {str(e)}"
                    error_label.classes(remove='hidden')
                except Exception:
                    error_label.text = "Error al procesar el registro."
                    error_label.classes(remove='hidden')

            ui.button('Aplicar cambios', on_click=handle_confirm).props('unelevated no-caps').classes('bg-primary text-white font-bold px-4 rounded-lg')

    dialog.open()