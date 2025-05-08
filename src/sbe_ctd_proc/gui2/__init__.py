import watchfiles
import logging
from nicegui import ui, app
# load ui.page routes
from .ctd_file_page import ctd_file_page
from .overview_page import overview_page
from ..config import CONFIG

def start_gui():
    # reload=False avoids error "You must call ui.run() to start the server."
    # https://github.com/zauberzeug/nicegui/discussions/1048
    ui.run(reload=False)

async def watch_my_file():
    file = CONFIG.config_file
    logging.debug(f'watching {file}')
    async for change in watchfiles.awatch(file):
        logging.debug('config toml file changed, reloading config and page')
        # assumming Change.modified event
        try:
            CONFIG.reload()
            # reload page
            # may not be working, but not important, user can reload manually
            ui.navigate.reload()
        except Exception:
            logging.exception(f'Error reloading {file}')

def start_watching_config():
    ui.timer(0, watch_my_file, once=True)
