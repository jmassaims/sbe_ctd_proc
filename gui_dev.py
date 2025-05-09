from nicegui import ui
# load the NiceGUI module
import sbe_ctd_proc.gui2
from sbe_ctd_proc.gui2 import start_watching_config

if __name__ in {"__main__", "__mp_main__"}:
    start_watching_config()
    ui.run(show=False)
