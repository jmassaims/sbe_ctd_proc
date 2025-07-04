import logging
import asyncio
import inspect
from multiprocessing import Queue, JoinableQueue
from datetime import datetime
from typing import Optional

from nicegui import app, run, ui

from ..ctd_file import CTDFile
from ..manager import Manager, start_manager
from ..process import move_to_approved_dir


class ProcessingState:
    """
    Manages file processing initiated by the app and provides information
    related to processing status.

    This state shared across the app independent of user session (page/tab).
    App code may bind this class' attributes.
    Uses NiceGUI run and timer to interact with the Manager in a subprocess.
    """

    is_processing: bool = False
    # current progress
    progress: float = 0.0
    file_progress_init: float = 0.0

    # total processing file count this run.
    total_processing: int = 0
    # count of currently pending files
    num_pending: int = 0

    current_basename: str | None = None
    current_step: str | None = None
    current_serial_number: str | None = None
    current_cast_date: datetime | None = None

    # file error during processing, waiting for response
    # shows file error dialog
    is_file_error: bool = False
    file_error_base_name: str | None = None
    file_error_message: str | None = None

    # shows Latitude request dialog, waiting for response
    is_requesting_latitude: bool = False

    # error that stopped processing
    # shows processing error dialog
    is_processing_error: bool = False
    processing_error: str

    user_messages: list[str] = []

    mgr: Manager
    send: Optional[Queue]
    recv: Optional[JoinableQueue]

    def __init__(self):
        self.mgr = Manager()
        self.mgr.scan_dirs()

        self.timer = ui.timer(0.1, callback=self.check_message, active=False)

        # re-scan directories on client connect (triggered by reload)
        app.on_connect(lambda: self.mgr.scan_dirs())

    async def start_processing(self, basenames=None):
        if self.is_processing:
            print('WARN: already processing')
            return

        print("start_processing")

        await self.__start(basenames)

    def stop_processing(self):
        assert self.send is not None
        self.send.put_nowait('stop')

    def skip_file(self):
        assert self.send is not None
        self.send.put_nowait(('skip', self.current_basename))

    async def approve(self, ctdfile: CTDFile, comment=''):
        # TODO raise exception if approving file that is currently processing
        await run.io_bound(move_to_approved_dir, ctdfile, comment)
        self.mgr.scan_dirs()

    def reload_config(self):
        """reload state dependent on the app configuration"""
        self.mgr.load_config()

    def respond_file_error(self, command: str):
        """Respond to a file error holding processing with: retry, abort, ignore"""

        if not self.is_file_error:
            raise Exception('No file error to respond to')

        assert self.send is not None
        self.send.put_nowait((command, self.file_error_base_name))

        self.is_file_error = False
        self.file_error_base_name = ''
        self.file_error_message = ''

    def respond_latitude(self, latitude: float | str):
        """
        Respond with the current file's latitude (float)
        or "skip" / "stop" command
        """
        if not self.is_requesting_latitude:
            raise Exception('Not requesting latitude')

        self.is_requesting_latitude = False

        if isinstance(latitude, str):
            # skip or stop command
            if latitude == 'stop':
                self.stop_processing()
            elif latitude == 'skip':
                self.skip_file()
            else:
                raise Exception(f'Unknown command "{latitude}"')

        else:
            assert self.send is not None
            self.send.put_nowait(('submit_latitude', self.current_basename, latitude))

    def clear_processing_error(self):
        self.is_processing_error = False
        self.processing_error = ''

    def reset_dialog_state(self):
        """Reset dialog state that occurs during processing"""
        self.is_file_error = False
        self.file_error_base_name = None
        self.file_error_message = None
        self.is_requesting_latitude = False

    async def __start(self, basenames=None):
        self.reset_dialog_state()
        self.clear_processing_error()
        self.is_processing = True
        self.progress = 0.0
        self.timer.activate()
        self.user_messages.clear()

        self.send = Queue()
        self.recv = JoinableQueue()

        try:
            await run.io_bound(start_manager, self.recv, self.send, basenames)

        except Exception as e:
            logging.exception('start_manager task exited with error')

            msg = str(e)

            # occurs when LatitudeSpreadsheet is refreshed whil open in Excel.
            # add helpful information about this permissions error
            if isinstance(e, PermissionError) and e.filename.endswith('.xlsx'):
                msg += '\n\nThis error is likely due to an open Excel file. Please close any open Excel files and try again.'

            self.handle_msg_error(msg)


        finally:
            self.is_processing = False
            # wait for all messages to be processed
            # join in separate thread, otherwise it breaks timer that's processing messages.
            await asyncio.to_thread(self.recv.join)

            self.timer.deactivate()

            self.send.close()
            self.send = None
            self.recv.close()
            self.recv = None

    async def check_message(self):
        assert self.recv is not None
        if not self.recv.empty():
            msg = self.recv.get(block=False)
            await self.process_msg(msg)
            self.recv.task_done()

    async def process_msg(self, msg):
        logging.debug("process_msg: %s", msg)
        event_name = msg[0]

        try:
            method = getattr(self, f'handle_msg_{event_name}')
            result = method(*msg[1:])
            if inspect.isawaitable(result):
                await result

        except AttributeError:
            logging.warning(f'no message handler for "{event_name}"', msg)

    def handle_msg_begin(self, num_pending: int):
        self.total_processing = num_pending
        self.num_pending = num_pending
        self.progress = 0
        self.current_basename = ''
        self.current_step = ''

    def handle_msg_start(self, name: str, num: int, num_pending: int):
        self.current_basename = name
        self.num_pending = num_pending
        # minus 1 since num is 1-based index
        self.file_progress_init = (num - 1) / self.total_processing
        self.progress = self.file_progress_init

    def handle_msg_finish(self, name: str, num: int, num_processed: int):
        self.progress = num / self.total_processing
        self.mgr.scan_dirs()

    def handle_msg_process_step(self, step_name: str, step_num: int, num_steps: int):
        self.current_step = step_name

        # width of progressbar allocated to a file
        file_width = 1 / self.total_processing

        self.progress = self.file_progress_init + (step_num / num_steps) * file_width

    def handle_msg_hex_info(self, serial_number: str, cast_date: datetime):
        self.current_serial_number = serial_number
        self.current_cast_date = cast_date

    def handle_msg_done(self):
        self.reset_dialog_state()
        self.progress = 1.0
        self.mgr.scan_dirs()
        ui.notify(f'Processed {self.total_processing} files')

    def handle_msg_usermsg(self, message: str):
        self.user_messages.append(message)

    def handle_msg_request_latitude(self, base_name: str):
        if self.current_basename != base_name:
            raise Exception('base_name does not match current file')

        self.is_requesting_latitude = True

    async def handle_msg_file_error(self, file_name: str, error: str):
        self.is_file_error = True
        self.file_error_base_name = file_name
        self.file_error_message = error

    def handle_msg_error(self, message: str):
        self.is_processing_error = True
        self.processing_error = message
        self.reset_dialog_state()


PROC_STATE = ProcessingState()
