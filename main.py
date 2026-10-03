from nicegui import ui, app
import os

from core import STORAGE_SECRET, init_db
import views
from views.theme import apply_theme

init_db()
apply_theme()

@ui.page('/')
def index() -> None:
    if not app.storage.user.get('user_id', None):
        ui.navigate.to('/login')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
            storage_secret=STORAGE_SECRET,
            title="La Pizarra Peluda",
            favicon='static/favicon.svg',
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 8080))
    )
