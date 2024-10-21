import os
from nicegui import ui

from sbs.process.instrument_data import cnv_to_instrument_data, InstrumentData

from ..config import CONFIG
from ..ctd_file import CTDFile
from ..viz_cnv import plot_for_cnv_file
from .widgets import error_message

class PlotSection:
    """CNV file selection and Measurement selection with chart"""

    selected_cnv: str

    def __init__(self, ctdfile: CTDFile) -> None:
        cnv_names = [x.name for x in ctdfile.destination_cnvs]
        selected_cnv = cnv_names[-1]
        self.cnv_dir = ctdfile.destination_cnvs[0].parent

        with ui.row(align_items='center'):
            ui.select(cnv_names, value=selected_cnv,
                          on_change=lambda e: self.show_cnv(e.value)
                          ).bind_value(self, 'selected_cnv')

            ui.badge(f'{len(ctdfile.destination_cnvs)} steps')
            with ui.button(icon='folder_open', color='white',
                           on_click=lambda: os.startfile(ctdfile.destination_dir)):
                ui.tooltip('Open destination directory')

            ui.button("Select Measurements",
                      on_click=lambda: self.open_measurements_dialog())

        self.plot_container = ui.column().classes('w-full').style('flex: auto')

        self.measurements_dialog = MeasurementsDialog()

        self.show_cnv(selected_cnv)

    def show_cnv(self, filename: str, include=None):
        """Re-create the plot for the given cnv file.
         @param filename: CNV filename in the cnv_dir
         @param include: measurements to display
        """

        # completly recreate the plot, could consider plotly update in future.
        self.plot_container.clear()

        cnv_path = self.cnv_dir / filename
        instrument_data = cnv_to_instrument_data(cnv_path)

        self.measurements_dialog.update(instrument_data)

        if include is None:
            include = self.measurements_dialog.get_selected()
            if len(include) == 0:
                include = {'tv290C'}

        fig = plot_for_cnv_file(instr_data=instrument_data, include=include)

        with self.plot_container:
            ui.plotly(fig).classes('w-full h-full')

    async def open_measurements_dialog(self):
        result = await self.measurements_dialog.dialog

        # always update for now. could add dialog buttons
        selected = self.measurements_dialog.get_selected()
        self.show_cnv(self.selected_cnv, selected)


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

    def get_selected(self):
        return [row['id'] for row in self.table.selected]


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
        PlotSection(ctdfile)
