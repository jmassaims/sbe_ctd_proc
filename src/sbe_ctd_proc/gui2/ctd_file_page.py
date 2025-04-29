import logging
import os
from typing import Optional

from nicegui import ui, html

from ..analysis import check_for_negatives
from .processing_state import PROC_STATE
from ..config import CONFIG
from ..ctd_file import CTDFile
from .components import PlotSection, build_negative_cols_view, build_scan_counts_view, \
    build_file_info_summary_view
from .widgets import error_message


@ui.page('/ctd_file/{base_file_name}')
def ctd_file_page(base_file_name: str):
    # file could be in any of the directories, so easiest to ask Manager for it.
    try:
        ctdfile = PROC_STATE.mgr.ctdfile[base_file_name]
    except KeyError:
        logging.warning(f'Manager is not tracking CTDFile "{base_file_name}", trying raw')

        hex_path = CONFIG.raw_dir / f'{base_file_name}.hex'
        if not hex_path.exists():
            error_message(f'HEX file does not exist: {hex_path}')
            return

        ctdfile = CTDFile(hex_path)

    ctdfile.parse_hex()
    ctdfile.refresh_dirs()
    file_status = ctdfile.status()

    prev_file, next_file = get_prev_next_files(base_file_name)

    is_approvable = file_status == 'processed'

    if file_status.startswith('proc'):
        working_dir = ctdfile.processing_dir
        cnv_files = ctdfile.processing_cnvs
    elif file_status == 'done':
        working_dir = ctdfile.approved_dir
        cnv_files = ctdfile.destination_cnvs
    else:
        working_dir = None
        cnv_files = None

    # change flex column to fill height of window
    ui.add_css('''
        .nicegui-content {
            height: 100vh;
        }
    ''')

    # Main toolbar row
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

        if working_dir:
            with ui.button(icon='folder_open',
                        on_click=lambda: os.startfile(working_dir)):
                ui.tooltip('Open directory')

        if ctdfile.serial_number:
            with ui.chip(ctdfile.serial_number, color='gray', text_color='white'):
                ui.tooltip('Serial Number')

        if ctdfile.cast_date:
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

                # go to next file in processing state.
                prev, next = get_prev_next_files(base_file_name)
                # prefer next, otherwise go back to previous
                next_processing = next or prev
                if next_processing:
                    ui.navigate.to(f'/ctd_file/{next_processing.base_file_name}')
                else:
                    # go back to overview page
                    ui.navigate.to('/')

                # Alternatively, could refresh page with:
                # ui.navigate.reload()

            approve_btn.on_click(approve)

        elif file_status == 'done':
            ui.chip('Done', color='green', text_color='white')

    if file_status == 'pending':
        ui.label('Not processed')
    elif file_status == 'unknown':
        error_message('Files in processing and done!')

    # Tabs: Chart, Scan Counts
    show_chart_tab = cnv_files is not None and len(cnv_files) > 0

    # find derive step cnv file
    # TODO move code to utility
    derive_file = None
    bin_file = None
    if cnv_files:
        matching = [f for f in cnv_files if f.name.endswith('D.cnv')]
        derive_file = matching[0] if matching else None

        matching = [f for f in cnv_files if f.name.endswith('B.cnv')]
        bin_file = matching[0] if matching else None

    def on_tab_change(name: str):
        # lazy-load and refresh the Info tab when it's selected.
        if name == 'Info':
            build_file_info_summary_view.refresh(ctdfile)

    with ui.tabs(on_change=lambda e: on_tab_change(e.value)) as tabs:
        if show_chart_tab:
            chart_tab = ui.tab('Chart')

        info_tab = ui.tab('Info')

        if derive_file:
            sc_tab = ui.tab('Scan Counts')

        if bin_file:
            negative_cols = check_for_negatives(bin_file)
            # UI: maybe "Data Checks" with multiple checkes in this tab.
            neg_tab = ui.tab('Data Checker')

            negative_col_count = len(negative_cols)
            if negative_col_count > 0:
                # show red badge with problem count.
                with neg_tab:
                    # override top so badge isn't on text
                    ui.badge(str(negative_col_count), color='red') \
                        .props('floating').style('top: 2px;')

        hex_tab = ui.tab('Hex File')


    # flex auto to fill vertical space
    selected_tab = chart_tab if show_chart_tab else info_tab
    with ui.tab_panels(tabs, value=selected_tab).classes('w-full').style('flex: auto'):
        if show_chart_tab and cnv_files:
            with ui.tab_panel(chart_tab):
                PlotSection(ctdfile, cnv_files)

        with ui.tab_panel(info_tab):
            # render now (pass ctdfile) if not showing chart tab
            build_file_info_summary_view(None if show_chart_tab else ctdfile)

        if derive_file:
            with ui.tab_panel(sc_tab):
                build_scan_counts_view(derive_file)

        if bin_file:
            with ui.tab_panel(neg_tab):
                build_negative_cols_view(bin_file, negative_cols)

        with ui.tab_panel(hex_tab):
            lines = ctdfile.info.get_header_lines()
            html.textarea(inner_html='\n'.join(lines)).classes('w-full h-full')


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
