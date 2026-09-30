from nicegui import ui, app

from views.layout import frame

from models import TokenType
from services.token_service import get_valid_token, activate_account
from services.user_service import get_user_by_id


def handle_activate(
    token_value: str,
    password: str,
    password_repeat: str,
    error_label: ui.label,
) -> None:
    if not (password and password_repeat):
        error_label.text = "Por favor, rellena los dos campos."
        error_label.classes(remove='hidden')
        return

    if password != password_repeat:
        error_label.text = "Las contraseñas no coinciden."
        error_label.classes(remove='hidden')
        return

    try:
        activate_account(token_value, password)
        ui.notify("¡Cuenta activada! Ya puedes iniciar sesión.", type="positive")
        ui.navigate.to('/login')
    except ValueError as e:
        match str(e):
            case "error_token_not_found":
                error_text = "Este enlace no es válido."
            case "error_token_expired":
                error_text = "Este enlace ha caducado. Pide uno nuevo al admin de tu club."
            case "error_user_does_not_exist":
                error_text = "Este usuario ya no existe."
            case _:
                error_text = "No se ha podido activar la cuenta. Inténtalo de nuevo."
                print(e)

        error_label.text = error_text
        error_label.classes(remove='hidden')


@ui.page('/activate/{token_value}')
def activate_page(token_value: str) -> None:
    if app.storage.user.get("user_id", None):
        ui.navigate.to('/staff')
        return

    token = get_valid_token(token_value, TokenType.ACTIVATION)

    with frame(navigation_title="Activar cuenta"):
        if not token:
            ui.label("¡Qué lástima!").classes("text-3xl font-black text-negative")
            ui.label(
                "Este enlace no es válido o ha caducado. Pide uno nuevo al admin de tu club."
            ).classes('text-xl font-bold text-slate-700')
            return

        user = get_user_by_id(token.user_id)
        if not user:
            ui.label("¡Qué lástima!").classes("text-3xl font-black text-negative")
            ui.label("Este usuario ya no existe.").classes('text-xl font-bold text-slate-700')
            return

        with ui.column().classes("items-center gap-5 sm:gap-10 w-full text-center sm:mt-10"):
            ui.image('static/badge.png').classes('size-25')

            with ui.column().classes("items-center gap-3 w-full text-center"):
                ui.label("¡Ya casi estás!").classes("text-3xl font-black text-primary")
                # El nombre es fijo, lo puso el admin al crear la cuenta —
                # aquí no se elige ni se edita, solo se confirma la contraseña.
                ui.label(f"Activa la cuenta de {user.name}").classes('text-xl font-bold text-slate-700')

            with ui.card().classes('w-full bg-primary/40 p-7 rounded-xl'):
                with ui.column().classes("gap-1 w-full text-center mb-2 mt-2"):
                    ui.label("Crea tu contraseña").classes('text-md text-slate-500')
                    password = (
                        ui.input(label="Contraseña", password=True, password_toggle_button=True)
                        .classes('w-full')
                        .props('standout="bg-primary text-white"')
                    )
                    password_repeat = (
                        ui.input(label="Repetir contraseña", password=True, password_toggle_button=True)
                        .classes('w-full')
                        .props('standout="bg-primary text-white"')
                    )

                error_label = ui.label(text="").classes('text-md text-negative hidden')

                (
                    ui.button(
                        text="Activar cuenta",
                        on_click=lambda: handle_activate(
                            token_value=token_value,
                            password=password.value,
                            password_repeat=password_repeat.value,
                            error_label=error_label,
                        )
                    )
                    .classes('w-full pt-3 pb-3 rounded-md font-bold')
                )
