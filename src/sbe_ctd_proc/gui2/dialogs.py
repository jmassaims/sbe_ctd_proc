from nicegui import ui

from .processing_state import PROC_STATE

def setup_file_error_dialog():
    proc = PROC_STATE
    # show when there is a file error
    dialog = ui.dialog().props('persistent') \
        .bind_value_from(proc, 'is_file_error')

    def submit(command: str):
        dialog.close()
        proc.respond_file_error(command)

    with dialog, ui.card():
        ui.label('Error processing file')
        ui.label().classes('font-bold').bind_text_from(proc, 'file_error_base_name')
        ui.label().bind_text_from(proc, 'file_error_message')
        with ui.row():
            # proc.respond_file_error() pydoc, close
            ui.button('Abort', color='red', on_click=lambda: submit('abort'))
            ui.button('Retry', on_click=lambda: submit('retry'))
            ui.button('Skip', on_click=lambda: submit('ignore'))