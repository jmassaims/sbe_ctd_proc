from src.sbe_ctd_proc.gui2 import build_ui
from nicegui import ui

if __name__ in {"__main__", "__mp_main__"}:
    build_ui()
    ui.run()
