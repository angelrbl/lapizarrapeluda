from nicegui import ui, app

from views.layout import frame

from services.auth_service import authenticate_user
from services.club_service import get_club_by_name, get_only_club

def handle_login(
    club_id: int,
    name: str,
    password: str,
    error_label: ui.label 
) -> None:
    if not (club_id and name and password):
        error_label.text = "Por favor, rellena todos los campos antes de iniciar sesión."
        error_label.classes(remove='hidden')
        return

    try:
        user = authenticate_user(name=name, club_id=club_id, password=password)
        app.storage.user['user_id'] = user.id
        app.storage.user['is_admin'] = user.is_admin
        app.storage.user['is_active'] = user.is_active
        app.storage.user['club_id'] = club_id

        ui.notify("¡Sesión iniciada con éxito! Redirigiéndole a staff...", type="positive")
        ui.navigate.to('/staff')
    except ValueError as e:
        match str(e):
            case "error_user_does_not_exist":
                error_text = "El usuario no existe en este club, pruebe otro o pídale al administrador que lo cree."
            case "error_account_not_activated":
                error_text = "Este usuario no está activo, por favor, actívelo primero mediante el enlace de activación."
            case "error_invalid_password":
                error_text = "La contraseña es incorrecta, pruebe otra."
            case _:
                error_text = "No se ha podido iniciar sesión. Inténtalo de nuevo."
                print(e)

        error_label.text = error_text
        error_label.classes(remove='hidden')

    return

@ui.page('/login')
@ui.page('/{club_name}/login')
def login_page(club_name: str | None = None) -> None:
    if app.storage.user.get("user_id", None):
        ui.navigate.to('/staff')
        return

    club = get_club_by_name(name=club_name) if club_name else get_only_club()

    with frame(navigation_title="Iniciar Sesión"):
        if not club:
            ui.label("Club no encontrado.").classes("text-3xl font-black text-negative")
            ui.label("No se ha encontrado ningún club con ese nombre.").classes('text-xl font-bold text-slate-700')

        with ui.column().classes("items-center gap-5 sm:gap-10 w-full text-center sm:mt-10"):
            ui.image('static/badge.png').classes('size-25')

            with ui.column().classes("items-center gap-3 w-full text-center"):
                ui.label("¡Bienvenido!").classes("text-3xl font-black text-primary")
                ui.label("Inicia sesión y comienza a gestionar tu club!").classes('text-xl font-bold text-slate-700')

            with ui.card().classes('w-full bg-primary/40 p-7 rounded-xl'):

                with ui.column().classes("gap-1 w-full text-center mb-2 mt-2"):
                    ui.label("Iniciar sesión").classes('text-md text-slate-500')
                    name = ui.input(label="Usuario").classes('w-full').props('standout="bg-primary text-white"')
                    password = ui.input(label="Contraseña", password=True, password_toggle_button=True).classes('w-full').props('standout="bg-primary text-white"')

                error_label = ui.label(text="").classes('text-md text-negative hidden')

                (
                    ui.button(
                        text="Iniciar sesión",
                        on_click=lambda: handle_login(
                            club_id=club.id,
                            name=name.value,
                            password=password.value,
                            error_label=error_label
                        )
                    )
                    .classes('w-full pt-3 pb-3 rounded-md font-bold')
                )