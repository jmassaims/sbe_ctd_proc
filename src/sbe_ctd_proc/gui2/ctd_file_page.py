import os
from nicegui import ui

from ..config import CONFIG
from ..ctd_file import CTDFile
from ..viz_cnv import plot_for_cnv_file
from .widgets import error_message

@ui.page('/ctd_file/{base_file_name}')
def sbe_plot(base_file_name: str):
    # change flex column to fill height of window
    ui.add_css('''
        .nicegui-content {
            height: 100vh;
        }
    ''')

    with ui.row().classes('w-full'):
        with ui.button(icon='list', on_click=lambda: ui.navigate.to('/')):
            ui.tooltip('List of files')

        with ui.button_group().props('rounded'):
            # TODO tooltip with file name
            # TODO implement. are we in processing or processed mode?
            ui.button(icon='navigate_before')
            ui.button(icon='navigate_next')

        ui.label(base_file_name).classes('text-h5').style('flex: auto;')

        ui.button('Approve', icon='thumb_up', color='green')

    hex_path = CONFIG.raw_path / f'{base_file_name}.hex'
    if not hex_path.exists():
        error_message(f'HEX file does not exist: {hex_path}')
        return

    ctdfile = CTDFile(hex_path)
    ctdfile.refresh_dirs()

    # TODO better abstraction over processing/dest mode.
    if ctdfile.processing_cnvs:
        ui.badge(f'{len(ctdfile.processing_cnvs)} processing')

    if ctdfile.destination_cnvs:
        cnv_names = [x.name for x in ctdfile.destination_cnvs]
        selected_cnv = cnv_names[-1]
        cnv_dir = ctdfile.destination_cnvs[0].parent

        with ui.row(align_items='center'):
            ui.select(cnv_names, value=selected_cnv,
                          on_change=lambda e: show_cnv(e.value))

            ui.badge(f'{len(ctdfile.destination_cnvs)} steps')
            with ui.button(icon='folder_open', color='white',
                           on_click=lambda: os.startfile(ctdfile.destination_dir)):
                ui.tooltip('Open destination directory')

        plot_container = ui.column().classes('w-full').style('flex: auto')

        def show_cnv(filename: str):
            plot_container.clear()

            cnv_path = cnv_dir / filename
            fig = plot_for_cnv_file(cnv_path)

            with plot_container:
                ui.plotly(fig).classes('w-full h-full')

        show_cnv(selected_cnv)
