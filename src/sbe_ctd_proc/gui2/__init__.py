from nicegui import ui
# load ui.page routes
from .ctd_file_page import sbe_plot
from .overview_page import overview_page

def start_gui():
    # reload=False avoids error "You must call ui.run() to start the server."
    # https://github.com/zauberzeug/nicegui/discussions/1048
    ui.run(reload=False)
