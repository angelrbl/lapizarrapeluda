from nicegui import ui, app

from views.layout import frame

from models import RoleType

from services.club_service import create_club
from services.user_service import create_user
from services.role_service import set_user_roles

def handle_create_club(
    club_name: str,
    admin_name: str,
    admin_password: str,
    admin_password_repeat: str,
    error_label: ui.label
) -> None:
    if not (club_name and admin_name and admin_password and admin_password_repeat):
        error_label.text = "Por favor, rellena todos los campos antes de crear el club."
        error_label.classes(remove='hidden')
        return

    if admin_password != admin_password_repeat:
        error_label.text = "Las contraseñas dadas no coinciden."
        error_label.classes(remove='hidden')
        return

    try:
        club = create_club(name=club_name)
        app.storage.user['club_id'] = club.id

        user = create_user(name=admin_name, club_id=club.id, password=admin_password, is_admin=True)
        set_user_roles(user_id=user.id, roles=[RoleType.STAFF])
        app.storage.user['user_id'] = user.id
        app.storage.user['is_admin'] = True
        app.storage.user['is_active'] = True

        ui.notify("¡El club se creó con éxito! Iniciando sesión en el dashboard de administrador.", type="positive")
        ui.navigate.to('/login')
    except ValueError as e:
        match str(e):
            case 'error_club_already_exists':
                error_text = "Este club ya existe, por favor, pruebe otro nombre."
            case _:
                error_text = "No se ha podido iniciar sesión. Inténtalo de nuevo."
                print(e)

        error_label.text = error_text
        error_label.classes(remove='hidden')

    return
    

@ui.page('/create_club')
def create_club_page() -> None:
    app.storage.user.clear()

    with frame(navigation_title="Crear club"):
        with ui.column().classes("items-center gap-10 sm:gap-15 w-full text-center sm:mt-10"):
            with ui.column().classes("items-center gap-3 w-full text-center"):
                ui.label("¡Bienvenido!").classes("text-3xl font-black text-primary")
                ui.label("Crea un club y comienza a gestionarlo como es debido.").classes('text-xl font-bold text-slate-700')

            with ui.card().classes('w-full bg-primary/40 p-7 rounded-xl'):
                with ui.column().classes("gap-1 w-full text-center"):
                    ui.label("Nombre del club").classes('text-md text-slate-500')
                    club_name = ui.input(placeholder="Por ejemplo, 'Grandiosa y Peluda'").classes('w-full').props('standout="bg-primary text-white"')

                ui.separator()

                with ui.column().classes("gap-1 w-full text-center mb-2"):
                    ui.label("Admin").classes('text-md text-slate-500')
                    admin_name = ui.input(label="Usuario").classes('w-full').props('standout="bg-primary text-white"')
                    admin_password = ui.input(label="Contraseña", password=True, password_toggle_button=True).classes('w-full').props('standout="bg-primary text-white"')
                    admin_password_repeat = ui.input(label="Repetir contraseña", password=True, password_toggle_button=True).classes('w-full').props('standout="bg-primary text-white"')

                error_label = ui.label(text="").classes('text-md text-negative hidden')

                (
                    ui.button(
                        text="Crear club",
                        on_click=lambda: handle_create_club(
                            club_name=club_name.value,
                            admin_name=admin_name.value,
                            admin_password=admin_password.value,
                            admin_password_repeat=admin_password_repeat.value,
                            error_label=error_label
                        )
                    )
                    .classes('w-full pt-3 pb-3 rounded-md font-bold')
                )