from nicegui import ui
from pathlib import Path
from seabirdscientific.instrument_data import cnv_to_instrument_data, InstrumentData

from sbe_ctd_proc.ctd_file import CTDFile
from sbe_ctd_proc.viz_cnv import plot_for_cnv_file
from sbe_ctd_proc.config import CONFIG

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
            else:
                include = set(selected)

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
            # determine default selection using config
            selected = []
            for id in CONFIG.chart_default_sensors:
                try:
                    alias = CONFIG.sensor_map[id]
                except KeyError:
                    alias = []

                for row in self.table.rows:
                    if row['id'] == id or row['id'] in alias:
                        selected.append(row)
                        # don't break, could be multiple sensors of same type

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
