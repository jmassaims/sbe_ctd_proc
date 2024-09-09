from .app import build_ui
from nicegui import ui
# load route: /ctd_file
from .ctd_file_page import sbe_plot

def start_gui():
    build_ui()

    # reload=False avoids error "You must call ui.run() to start the server."
    # https://github.com/zauberzeug/nicegui/discussions/1048
    ui.run(reload=False)
