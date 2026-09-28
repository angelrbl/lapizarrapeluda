from nicegui import app, ui

from models import Club

from services.club_service import update_club_name, delete_club, get_squad_length
from services.auth_service import authenticate_user


def handle_update_club_name(club_id: int, new_name: str, error_label: ui.label) -> None:
    if not new_name:
        error_label.text = "Por favor, introduce un nombre válido antes de guardar los cambios."
        error_label.classes(remove='hidden')
        return

    try:
        update_club_name(club_id=club_id, new_name=new_name)
        ui.notify("¡Nombre del club actualizado con éxito!", type="positive")
    except ValueError as e:
        match str(e):
            case "error_club_already_exists":
                error_text = "El nombre introducido ya está en uso, pruebe otro."
            case "error_club_no_longer_exists":
                error_text = "El club cuyo nombre se intenta actualizar ya no existe, pruebe de nuevo."
            case _:
                error_text = "No se ha podido actualizar el nombre. Inténtalo de nuevo."
                print(e)

        error_label.text = error_text
        error_label.classes(remove='hidden')

    return

def handle_delete_club(
    club_id: int,
    admin_name: str,
    admin_password: str,
    admin_password_repeat: str,
    error_label: ui.label
) -> None:
    if not (club_id and admin_name and admin_password and admin_password_repeat):
        error_label.text = "Por favor, rellena todos los campos antes de eliminar el club."
        error_label.classes(remove='hidden')
        return

    if admin_password != admin_password_repeat:
        error_label.text = "Las contraseñas dadas no coinciden."
        error_label.classes(remove='hidden')
        return

    try:
        admin = authenticate_user(club_id=club_id, name=admin_name, password=admin_password)
        if admin and admin.is_admin:
            if delete_club(club_id=club_id):
                ui.notify("¡Club eliminado con éxito!")
                app.storage.user.clear()
                ui.navigate.to('/create_club')
            else:
                ui.notify("No se pudo borrar el club, por favor, inténtelo de nuevo.")
    except ValueError as e:
        match str(e):
            case "error_user_does_not_exist":
                error_text = "El usuario no existe en este club, pruebe otro."
            case "error_account_not_activated":
                error_text = "Este usuario no está activo, por favor, actívelo primero mediante el enlace de activación."
            case "error_invalid_password":
                error_text = "La contraseña es incorrecta, pruebe otra."
            case 'error_club_does_not_exist':
                error_text = "El club que está intentando borrar no existe."
            case _:
                error_text = "No se ha podido borrar el club. Inténtalo de nuevo."
                print(e)

        error_label.text = error_text
        error_label.classes(remove='hidden')

    return

def club_tab_page(club: Club):
    with ui.row().classes('mt-3 w-full items-center justify-between gap-5'):
        with ui.card().classes('w-full p-4 bg-gray-50 border border-gray-200 rounded-xl shadow-none gap-2'):
            ui.label("Datos del club").classes('text-xl text-gray-900 font-bold')
            name = ui.input(
                label="Nombre del club",
                value=club.name,
                placeholder="Por ejemplo, 'Grandiosa y Peluda'").classes('w-full').props('standout="bg-primary text-white"')

            error_label = ui.label(text="").classes('text-md text-negative hidden')

            ui.button(
                text="Guardar cambios",
                on_click=lambda: handle_update_club_name(
                    club_id=club.id,
                    new_name=name.value,
                    error_label=error_label
                )
            ).classes('w-full pt-3 pb-3 rounded-md font-bold')
        
        with ui.card().classes('w-full p-4 bg-gray-50 border border-gray-200 rounded-xl shadow-none gap-2 items-center pt-5 pb-5'):
            with ui.column().classes('items-center gap-1 text-center justify-between'):
                ui.label(get_squad_length(club_id=club.id)).classes('text-4xl text-primary font-black')
                ui.label("Jugadores en plantilla").classes('text-lg font-bold text-gray-900')

        with ui.dropdown_button(text="Borrar club", icon="delete", split=False).classes('absolute left-1/2 -translate-x-1/2 mb-5 ' \
        'pt-3 pb-3 rounded-md font-bold fixed bottom-0'):
            with ui.column().classes("p-4 gap-1 w-full text-center mb-2"):
                ui.label("Admin info").classes('text-md text-slate-500')
                admin_name = ui.input(label="Usuario").classes('w-full').props('standout="bg-primary text-white"')
                admin_password = ui.input(label="Contraseña", password=True, password_toggle_button=True).classes('w-full').props('standout="bg-primary text-white"')
                admin_password_repeat = ui.input(label="Repetir contraseña", password=True, password_toggle_button=True).classes('w-full').props('standout="bg-primary text-white"')

                error_label = ui.label(text="").classes('text-md text-negative hidden')

                (
                    ui.button(
                        text="Borrar",
                        on_click=lambda: handle_delete_club(
                            club_id=club.id,
                            admin_name=admin_name.value,
                            admin_password=admin_password.value,
                            admin_password_repeat=admin_password_repeat.value,
                            error_label=error_label
                        )
                    )
                    .classes('w-full pt-3 pb-3 rounded-md font-bold')
                )