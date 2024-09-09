from nicegui import ui

def error_message(msg: str):
    with ui.row(align_items='center').classes('p-2 bg-red-100'):
        ui.icon('error', color='red')
        ui.label(msg)
