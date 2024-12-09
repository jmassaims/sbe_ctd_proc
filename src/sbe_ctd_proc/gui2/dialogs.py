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
        ui.label('Error processing file').classes('text-lg')
        ui.label().classes('font-bold').bind_text_from(proc, 'file_error_base_name')
        ui.label().bind_text_from(proc, 'file_error_message')
        with ui.row():
            ui.button('Stop', color='red', on_click=lambda: submit('abort'))
            ui.button('Skip', on_click=lambda: submit('ignore'))
            ui.button('Retry', on_click=lambda: submit('retry'))

def setup_processing_error_dialog():
    proc = PROC_STATE

    dialog = ui.dialog().props('persistent') \
        .bind_value_from(proc, 'is_processing_error')

    with dialog, ui.card():
        ui.label('Processing Error').classes('text-lg')
        ui.label('Processing stopped with error:')
        ui.label().bind_text_from(proc, 'processing_error')

        ui.button('Ok', on_click=proc.clear_processing_error)

def setup_latitude_dialog():
    proc = PROC_STATE

    dialog = ui.dialog().props('persistent') \
        .bind_value_from(proc, 'is_requesting_latitude')

    with dialog, ui.card():
        ui.label('Latitude Needed').classes('text-lg')
        ui.label().bind_text_from(proc, 'current_basename')

        # TODO enter submit
        lat_input = ui.input(label='Latitude')

        def submit(command: str):
            dialog.close()
            if command == 'submit':
                lat = lat_input.value
                proc.respond_latitude(lat)
            elif command == 'stop':
                proc.stop_processing()
            elif command == 'skip':
                proc.skip_file()
            else:
                raise Exception(f'Unknown command "{command}"')


        with ui.row():
            ui.button('Stop', color='red', on_click=lambda: submit('stop'))
            ui.button('Skip', on_click=lambda: submit('skip'))
            ui.button('Submit', on_click=lambda: submit('submit'))
