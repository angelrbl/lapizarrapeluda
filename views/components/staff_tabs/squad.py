from nicegui import app, ui

from models import User, Club, RoleType

from services.user_service import list_users_for_club, create_user, update_user, delete_user
from services.role_service import get_user_roles, set_user_roles
from services.token_service import create_activation_token
from services.stats_service import get_player_stats, update_player_stats

from views.layout import APP_BASE_URL

def handle_create_activation_link(user: User) -> None:
    if user.is_active:
        ui.notify('¡Este usuario ya está activo!', type="positive")
        return
 
    try:
        token = create_activation_token(user_id=user.id)
        link = f"{APP_BASE_URL}/activate/{token.value}"
    except ValueError as e:
        ui.notify(f"El usuario no existe, pruebe de nuevo.", type="negative")
        return
 
    with ui.dialog() as dialog:
        with ui.card().classes('w-full p-6 pl-8 pr-8 bg-gray-50 border border-gray-200 rounded-xl shadow-none gap-2'):
            ui.label("Link de activación").classes
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
    dialog.open()

def handle_user(
    club_id: int,
    name: str,
    error_label: ui.label,
    action: str,
    on_change: callable,
    user_id: int | None = None,
    number: int | None = None,
    roles: list[RoleType] | None = None
) -> None:
    if not (club_id and name):
        error_label.text = "Por favor, rellena todos los campos antes confirmar."
        error_label.classes(remove='hidden')
        return

    try:
        match action:
            case 'create':
                user = create_user(club_id=club_id, name=name, number=number)
            case 'edit':
                user = update_user(user_id=user_id, new_name=name, new_number=number)
            case _:
                error_label.text = "Acción desconocida."
                error_label.classes(remove='hidden')
                return
        set_user_roles(user_id=user.id, roles=roles)
        ui.notify(
            "Jugador creado correctamente" if action == "create" else "Jugador editado correctamente",
            type="positive",
        )   
        on_change()
    except ValueError as e:
        match str(e):
            case "error_user_already_exists":
                error_text = "El usuario ya existe en este club, pruebe otro."
            case "error_user_no_longer_exists":
                error_text = "Este usuario ya no existe, pruebe otra vez."
            case "error_name_or_number_already_exists":
                error_text = "O el nombre o el dorsal ya están en uso, pruebe otros."
            case _:
                error_text = "No se ha podido guardar el jugador. Inténtalo de nuevo."
                print(e)

        error_label.text = error_text
        error_label.classes(remove='hidden')

    return

def handle_delete_user(user_id: int, on_change: callable) -> None:
    try:
        delete_user(user_id=user_id)
        ui.notify("¡Usuario borrado con éxito!", type="positive")
        on_change()
    except ValueError as e:
        ui.notify("El usuario que intentas borrar no existe, prueba de nuevo.", type="negative")

def open_player_stats_dialog(user: User, is_admin: bool, is_captain: bool, on_change: callable) -> None:
    stats = get_player_stats(user.id)
    if is_captain:
        print(user.name)

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
                    in_goals = ui.number(label="Goles", value=stats.goals, min=0).classes('flex-1').props('outlined dense')
                    in_assists = ui.number(label="Asistencias", value=stats.assists, min=0).classes('flex-1').props('outlined dense')
                
                with ui.row().classes('w-full gap-3'):
                    in_starter = ui.number(label="Titularidades", value=stats.starter_amount, min=0).classes('flex-1').props('outlined dense')
                
                with ui.row().classes('w-full gap-3'):
                    in_yellow = ui.number(label="Tarjetas Amarillas", value=stats.yellow_cards, min=0).classes('flex-1').props('outlined dense')
                    in_red = ui.number(label="Tarjetas Rojas", value=stats.red_cards, min=0).classes('flex-1').props('outlined dense')
                
                with ui.row().classes('w-full gap-3'):
                    in_mvp = ui.number(label="Jugador Estrella Damm", value=stats.mvp_count, min=0).classes('flex-1').props('outlined dense')

                error_label = ui.label("").classes('text-xs text-negative hidden')

            with ui.row().classes('w-full justify-end gap-2 mt-2'):
                ui.button('Cancelar', on_click=dialog.close).props('flat no-caps').classes('text-gray-500')
                
                def handle_save():
                    try:
                        update_player_stats(
                            player_id=user.id,
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

                stat_row('sports_soccer', 'Goles', stats.goals)
                stat_row('handshake', 'Asistencias', stats.assists)
                stat_row('person', 'Titularidades', stats.starter_amount)
                stat_row('style', 'Tarjetas Amarillas', stats.yellow_cards)
                stat_row('style', 'Tarjetas Rojas', stats.red_cards)
                stat_row('static/estrella-damm.png', 'Jugador Estrella Damm', stats.mvp_count, 'text-amber-600', True)

            with ui.row().classes('w-full justify-end mt-2'):
                ui.button('Cerrar', on_click=dialog.close).props('unelevated no-caps').classes('bg-gray-100 text-gray-700 font-bold px-5 py-2 rounded-xl')

    dialog.open()

def squad_tab_page(club: Club, on_change: callable, is_admin: bool = False) -> None:
    with ui.column().classes('w-full max-w-lg mx-auto min-h-screen p-4 gap-4'):

        squad = list_users_for_club(club_id=club.id)

        if is_admin:
            with ui.row().classes('w-full justify-between items-center mb-2'):
                ui.label('Jugadores').classes('text-2xl font-bold text-gray-900')
                
                with ui.dropdown_button('Nuevo jugador', icon='add') \
                    .props('unelevated no-caps') \
                    .classes('bg-primary text-white hover:bg-secondary text-sm font-medium rounded-lg px-3 py-1.5'):
                    with ui.column().classes("p-4 gap-1 w-full text-center mb-2"):
                        ui.label("User info").classes('text-md text-slate-500').classes('text-md text-gray-900')
                        with ui.row().classes('w-full gap-1'):
                            create_name = ui.input(label="Nombre").props('standout="bg-primary text-white"')
                            create_number = ui.number(label="Dorsal", min=1, max=99, step=1).props('standout="bg-primary text-white"')

                        create_roles = ui.select({rt: rt.value.title() for rt in RoleType}, clearable=True, multiple=True, label="Roles").classes('w-full mb-2').props('use-chips')
        
                        create_error_label = ui.label(text="").classes('text-md text-negative hidden')
        
                        (
                            ui.button(
                                text="Crear",
                                on_click=lambda: handle_user(
                                    club_id=club.id,
                                    name=create_name.value,
                                    number=create_number.value,
                                    action="create",
                                    on_change=on_change,
                                    roles=create_roles.value or [],
                                    error_label=create_error_label
                                )
                            )
                            .classes('w-full pt-3 pb-3 rounded-md font-bold')
                        )

        for user in squad:
            user_roles = get_user_roles(user_id=user.id)

            with ui.card().classes('w-full p-4 bg-gray-50 border border-gray-200 rounded-xl shadow-none gap-2 ' + ("cursor-pointer" if RoleType.PLAYER in user_roles else "")) as card:
                if RoleType.PLAYER in user_roles:
                    is_captain = True if RoleType.CAPTAIN in user_roles else False
                    card.on('click', lambda usr=user, is_c=is_captain: open_player_stats_dialog(user=usr, is_admin=is_admin, is_captain=is_c, on_change=on_change))
                
                with ui.row().classes('w-full justify-between items-start no-wrap'):
                    with ui.row().classes('gap-1'):
                        if RoleType.CAPTAIN in user_roles:
                            ui.label("C").classes('font-bold text-md text-primary')
                            ui.label("|").classes('font-black text-sm text-gray-900')

                        if user.number:
                            ui.label(f"{user.number}").classes('font-black text-sm text-gray-900')
                            ui.label("|").classes('font-black text-sm text-gray-900')

                        with ui.column().classes('gap-0'):
                            ui.label(user.name).classes('font-semibold text-gray-900 text-base leading-tight')
                            ui.label(user.email or '').classes('text-sm text-gray-500')

                    if RoleType.STAFF in user_roles:
                        badge_style = 'bg-green-100 text-green-700' if user.is_active else 'bg-amber-100 text-amber-700'
                        (
                            ui.label("Activo" if user.is_active else "Pendiente")
                            .classes(f'px-2.5 py-0.5 text-xs font-medium rounded-full {badge_style}')
                        )

                ui.separator().classes('my-1 bg-gray-200')

                with ui.row().classes('w-full justify-between items-center'):
                    roles_text = ", ".join(role.value.title() for role in user_roles)
                    ui.label(roles_text).classes('text-sm font-medium text-gray-600')

                    if is_admin:
                        with ui.row().classes('gap-1 items-center'):
                            ui.button(icon='link', on_click=lambda usr=user: handle_create_activation_link(user=usr)) \
                                .props('flat round density=compact') \
                                .classes('text-gray-400 hover:text-gray-700 hover:bg-gray-200')

                            
                            with ui.dropdown_button(icon='edit').props('flat round density=compact') \
                                .classes('text-gray-400 hover:text-gray-700 hover:bg-gray-200'):
                                with ui.column().classes("p-4 gap-1 w-full text-center mb-2"):
                                    ui.label("User info").classes('text-md text-slate-500')
                                    with ui.row().classes('w-full gap-1'):
                                        edit_name = ui.input(label="Nombre", value=user.name).props('standout="bg-primary text-white"')
                                        edit_number = ui.number(label="Dorsal", min=1, max=99, step=1, value=user.number).props('standout="bg-primary text-white"')
                
                                    edit_roles = ui.select(
                                        {rt: rt.value.title() for rt in RoleType},
                                        value=user_roles,
                                        clearable=True, multiple=True, label="Roles").classes('w-full mb-2').props('use-chips')
                    
                                    edit_error_label = ui.label(text="").classes('text-md text-negative hidden')
                    
                                    (
                                        ui.button(
                                            text="Editar",
                                            on_click=lambda usr_id=user.id, n=edit_name, num=edit_number, r=edit_roles, err=edit_error_label: handle_user(
                                                club_id=club.id,
                                                name=n.value,
                                                number=num.value,
                                                action="edit",
                                                on_change=on_change,
                                                user_id=usr_id,
                                                roles=r.value or [],
                                                error_label=err,
                                            )
                                        )
                                        .classes('w-full pt-3 pb-3 rounded-md font-bold')
                                    )
                            
                            with ui.dropdown_button().props('flat round density=compact dropdown-icon="delete" no-icon-animation') \
                                .classes('text-gray-400 hover:text-primary hover:bg-accent'):
                                with ui.column().classes("p-4 gap-1 w-full text-center mb-2 items-center"):
                                    ui.label("¿Estás seguro?").classes('font-bold text-md text-slate-600')
                                    ui.label("No podrás recuperar los datos.").classes('text-sm mb-1 text-slate-500')
                                    (
                                        ui.button(
                                            text="Borrar",
                                            on_click=lambda usr_id=user.id: handle_delete_user(
                                                user_id=usr_id,
                                                on_change=on_change
                                            )
                                        )
                                    )