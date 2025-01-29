import os
from pathlib import Path
from typing import Optional

from nicegui import ui

from seabirdscientific.instrument_data import cnv_to_instrument_data, InstrumentData

from .processing_state import PROC_STATE
from ..config import CONFIG
from ..ctd_file import CTDFile
from ..viz_cnv import plot_for_cnv_file
from .widgets import error_message

class PlotSection:
    """CNV file selection and Measurement selection with chart"""

    selected_cnv: str

    def __init__(self, ctdfile: CTDFile, cnv_paths: list[Path]) -> None:
        cnv_names = [x.name for x in cnv_paths]
        selected_cnv = cnv_names[-1]
        self.cnv_dir = cnv_paths[0].parent
        steps_done, total_steps = ctdfile.get_step_count()

        with ui.row(align_items='center'):
            ui.select(cnv_names, value=selected_cnv,
                          on_change=lambda e: self.show_cnv(e.value)
                          ).bind_value(self, 'selected_cnv')

            if steps_done == total_steps:
                ui.chip(f'{steps_done} steps', color='gray', text_color='white')
            else:
                ui.chip(f'{steps_done}/{total_steps} steps', color='orange', text_color='white')

            with ui.button(icon='folder_open', color='white',
                           on_click=lambda: os.startfile(self.cnv_dir)):
                ui.tooltip('Open destination directory')

            ui.button("Select Measurements",
                      on_click=lambda: self.open_measurements_dialog())

        self.plot_container = ui.column().classes('w-full').style('flex: auto')

        self.measurements_dialog = MeasurementsDialog()

        self.show_cnv(selected_cnv)

    def show_cnv(self, filename: str, include: set[str] | None = None):
        """Re-create the plot for the given cnv file.
         @param filename: CNV filename in the cnv_dir
         @param include: measurements to display
        """

        # completely recreate the plot, could consider plotly update in future.
        self.plot_container.clear()

        cnv_path = self.cnv_dir / filename
        instrument_data = cnv_to_instrument_data(cnv_path)

        self.measurements_dialog.update(instrument_data)

        if include is None:
            selected = self.measurements_dialog.get_selected()
            if len(selected) == 0:
                include = {'tv290C'}

        fig = plot_for_cnv_file(instr_data=instrument_data, include=include)

        with self.plot_container:
            ui.plotly(fig).classes('w-full h-full')

    async def open_measurements_dialog(self):
        result = await self.measurements_dialog.dialog

        # always update for now. could add dialog buttons
        selected = self.measurements_dialog.get_selected()
        self.show_cnv(self.selected_cnv, set(selected))


class MeasurementsDialog:
    """Dialog for multi-selecting measurements"""

    # measurement labels to omit
    ignored = {'depSM', 'prdM'}

    def __init__(self) -> None:
        columns = [
            {'name': 'id', 'label': 'Label', 'field': 'id'},
            {'name': 'desc', 'label': 'Description', 'field': 'desc'},
            {'name': 'units', 'label': 'Units', 'field': 'units'}
        ]

        with ui.dialog() as dialog, ui.card() as card:
            # remove default max-width
            card.style('max-width: unset')
            self.dialog = dialog
            self.table = ui.table(columns=columns, rows=[], row_key='id', selection='multiple')

    def update(self, instrument_data: InstrumentData):
        rows = self.build_rows(instrument_data)
        self.table.update_rows(rows, clear_selection=False)

        if not self.table.selected:
            # default selection using description
            default_select = {'Temperature', 'Conductivity'}
            selected = [r for r in self.table.rows if r['desc'] in default_select]
            self.table.selected = selected

    def open(self):
        self.dialog.open()

    def build_rows(self, instrument_data: InstrumentData):
        def measurement_to_row(m):
            return {
                'id': m.label,
                'desc': m.description,
                'units': m.units
            }

        return [measurement_to_row(m)
                for m in instrument_data.measurements.values()
                if m.label not in self.ignored]

    def get_selected(self) -> list[str]:
        return [row['id'] for row in self.table.selected]


@ui.page('/ctd_file/{base_file_name}')
def sbe_plot(base_file_name: str):
    hex_path = CONFIG.raw_path / f'{base_file_name}.hex'
    if not hex_path.exists():
        error_message(f'HEX file does not exist: {hex_path}')
        return

    ctdfile = CTDFile(hex_path)
    ctdfile.parse_hex()
    ctdfile.refresh_dirs()
    file_status = ctdfile.status()

    prev_file, next_file = get_prev_next_files(base_file_name)

    is_approvable = file_status == 'processed'

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
            prev_btn = ui.button(icon='navigate_before')
            if prev_file is None:
                prev_btn.disable()
            else:
                prev_btn.tooltip(prev_file.base_file_name)
                prev_btn.on_click(lambda: ui.navigate.to(f'./{prev_file.base_file_name}'))

            next_btn = ui.button(icon='navigate_next')
            if next_file is None:
                next_btn.disable()
            else:
                next_btn.tooltip(next_file.base_file_name)
                next_btn.on_click(lambda: ui.navigate.to(f'./{next_file.base_file_name}'))

        ui.label(base_file_name).classes('text-h5')

        with ui.chip(ctdfile.serial_number, color='gray', text_color='white'):
            ui.tooltip('Serial Number')

        with ui.chip(ctdfile.cast_date.strftime('%Y %b %d'), color='gray', text_color='white'):
            ui.tooltip('Cast Date')

        if CONFIG.lookup_latitude:
            try:
                lat = CONFIG.lookup_latitude(ctdfile.base_file_name)
                if lat:
                    with ui.chip(str(lat), color='gray', text_color='white'):
                        ui.tooltip('Latitude')
            except LookupError:
                pass

        ui.label().style('flex: auto;')

        if is_approvable:
            approve_btn = ui.button('Approve', icon='thumb_up', color='green')
            async def approve():
                approve_btn.disable()
                await PROC_STATE.approve(ctdfile)
                ui.navigate.reload()

            approve_btn.on_click(approve)

        elif file_status == 'done':
            ui.chip('Done', color='green', text_color='white')

    if file_status == 'pending':
        ui.label('Not processed')
    elif file_status == 'unknown':
        error_message('Files in processing and done!')

    if file_status.startswith('proc'):
        PlotSection(ctdfile, ctdfile.processing_cnvs)
    elif file_status == 'done':
        PlotSection(ctdfile, ctdfile.destination_cnvs)

def get_prev_next_files(current_name: str) -> tuple[Optional[CTDFile], Optional[CTDFile]]:
    """Returns the previous and next base file names that are processing/processed.
    Values are None if no previous/next.
    """
    ctdfiles = [f for f in PROC_STATE.mgr.ctdfiles if f.status().startswith('proc')]

    if not ctdfiles:
        return None, None

    index = None
    for i, ctdfile in enumerate(ctdfiles):
        if ctdfile.base_file_name == current_name:
            index = i
            break

    if index is None:
        # current file not in ctdfiles. this may happen when selected done file.
        # -1 so next_file will be the first processing ctdfile in the list
        index = -1

    prev_file = ctdfiles[index - 1] if index > 0 else None
    next_file = ctdfiles[index + 1] if index < len(ctdfiles) - 1 else None
    return prev_file, next_file
