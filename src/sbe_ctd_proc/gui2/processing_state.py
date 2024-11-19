import asyncio
import inspect
from multiprocessing import Queue, JoinableQueue
from datetime import datetime
from typing import Optional

from nicegui import app, run, ui

from ..ctd_file import CTDFile
from ..manager import Manager, start_manager
from ..process import move_to_destination_dir


class ProcessingState:
    """
    State shared across the app independent of user session.
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

    current_basename: str = None
    current_step: str = None
    current_serial_number: str = None
    current_cast_date: datetime = None

    # file error processing is waiting on
    is_file_error: bool = False
    file_error_base_name: str = None
    file_error_message: str = None

    # error that stopped processing
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

    async def start_processing(self):
        if self.is_processing:
            print('WARN: already processing')
            return

        print("start_processing")

        await self.__start()

    def stop_processing(self):
        self.send.put_nowait('stop')

    async def approve(self, ctdfile: CTDFile):
        await run.io_bound(move_to_destination_dir, ctdfile)
        self.mgr.scan_dirs()

    def respond_file_error(self, command: str):
        """Respond to a file error holding processing with: retry, abort, ignore"""

        if not self.is_file_error:
            raise Exception('No file error to respond to')

        self.send.put_nowait((command, self.file_error_base_name))

        self.is_file_error = False
        self.file_error_base_name = ''
        self.file_error_message = ''

    def clear_processing_error(self):
        self.is_processing_error = False
        self.processing_error = ''

    async def __start(self):
        self.is_processing = True
        self.progress = 0.0
        self.timer.activate()
        self.clear_processing_error()
        self.user_messages.clear()

        self.send = Queue()
        self.recv = JoinableQueue()

        try:
            await run.io_bound(start_manager, self.recv, self.send)

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
        if not self.recv.empty():
            msg = self.recv.get(block=False)
            await self.process_msg(msg)
            self.recv.task_done()

    async def process_msg(self, msg):
        print("msg:", msg)
        event_name = msg[0]

        try:
            method = getattr(self, f'handle_msg_{event_name}')
            result = method(*msg[1:])
            if inspect.isawaitable(result):
                await result

        except AttributeError:
            print(f'WARNING: no message handler for "{event_name}"', msg)

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
        self.progress = 1.0
        self.mgr.scan_dirs()
        ui.notify(f'Processed {self.total_processing} files')

    def handle_msg_usermsg(self, message: str):
        self.user_messages.append(message)

    async def handle_msg_file_error(self, file_name: str, error: str):
        self.is_file_error = True
        self.file_error_base_name = file_name
        self.file_error_message = error

    def handle_msg_error(self, message: str):
        self.is_processing_error = True
        self.processing_error = message


PROC_STATE = ProcessingState()
