import threading
from contextlib import AbstractContextManager
from pathlib import Path
import os
from collections.abc import Mapping, Callable
from multiprocessing import Queue
from typing import Optional

from .audit_log import AuditLog
from .ctd_file import CTDFile
from .db import get_db
from .process import process_hex_file
from .config_util import get_config_dir_path

class Manager(AbstractContextManager):
    """Manages the state of CTDFiles and tracks events.
    Processes each file that needs processing based on current configuration.
    """
    send: Queue
    recv: Queue

    processing_dir: Path
    destination_dir: Path

    ctdfiles: list[CTDFile]
    ctdfile: Mapping[str, CTDFile]
    "lookup CTDFile by base name"

    pending: set[str]
    processing: set[str]
    processed: set[str]

    audit_log: Optional[AuditLog]

    # callback when file info changes.
    # hacky, only works for the last client
    on_change: Optional[Callable] = None

    _scan_lock = threading.Lock()

    def __init__(self, send: Queue = None, recv: Queue = None, auditlog_path = None) -> None:
        self.send = send
        self.recv = recv

        self.raw_path = get_config_dir_path("RAW_PATH")

        # TODO prompt to create if missing?
        self.processing_dir = get_config_dir_path("PROCESSING_PATH")
        self.destination_dir = get_config_dir_path("DESTINATION_PATH")

        if auditlog_path:
            self.audit_log = AuditLog(auditlog_path)

    def __exit__(self, *exc_details):
        self.cleanup()

    def cleanup(self):
        if self.audit_log:
            self.audit_log.close()

    def scan_dirs(self, basenames: list[str] | None = None):
        """
        scan directories, set file collections: hex_files, pending, processing, processed.

        """
        with self._scan_lock:
            self.hex_files = list(self.raw_path.glob("*.hex"))
            total_count = len(self.hex_files)
            self.hex_count = total_count
            print(f"{total_count} hex files in {self.raw_path}")

            # FIXME currently assuming all files in every state are also in pending directory
            # However, user could change pending directory, or move hex files
            self.ctdfiles = [CTDFile(f) for f in self.hex_files]
            base_names = set(f.base_file_name for f in self.ctdfiles)
            self.ctdfile = dict((f.base_file_name, f) for f in self.ctdfiles)

            processed = set(os.listdir(self.destination_dir))
            processing = set(os.listdir(self.processing_dir))

            # Check for unknown and unexpected situations.

            # unknown - doesn't match a hex file in raw
            unknown_processed = processed - base_names
            if unknown_processed:
                print(f"Processed not matching hex file: {unknown_processed}")

            unknown_processing = processing - base_names
            if unknown_processing:
                print(f"Processing not matching hex file: {unknown_processing}")


            # processed and processing
            unexpected_processing = processed & processing
            if unexpected_processing:
                print(f"Files both processing and processed: {unexpected_processing}")

            processed.intersection_update(base_names)
            self.processed = processed
            if processed:
                print(f"{len(processed)} files already processed:\n{processed}")

            processing.intersection_update(base_names)
            self.processing = processing
            if processing:
                print(f"{len(processing)} files already processing?\n{processing}")

            self.pending = base_names - processed - processing

            if basenames:
                self._set_pending(basenames)

        if self.on_change:
            self.on_change()

    def _set_pending(self, basenames: list[str]):
        """
        Set specific files to process. After this, pending will only include files in the given basenames.
        However, only raw or processing files are considered,
        must be called after scan_dirs()
        """

        basenames_set = set(basenames)

        # warn about any that are processed
        match_processed = self.processed & basenames_set
        if match_processed:
            # TODO user message
            print('WARN: selected files already processed', match_processed)

        print('pending explicitly set', basenames)

        # after scan_dirs(), valid files to process are those in pending or processing
        valid = self.pending | self.processing

        unknown = basenames_set - valid - match_processed
        if unknown:
            print('WARN: selected unknown files', unknown)

        self.pending = valid & basenames_set
        print('valid pending', self.pending)


    def start(self):
        # copy pending set since we mutate it
        pending = list(self.pending)

        i = 0
        file_num = 1 # 1-based index
        while i < len(pending):
            base_name = pending[i]

            response = None
            try:
                self.check_stop_message()
                ctdfile = self.ctdfile[base_name]
                self.process_file(ctdfile, file_num)

            except SkipFile:
                print(f'skip file "{base_name}"')
                response = "ignore"
            except StopProcessing:
                print('Stop processing')
                break
            except Exception as e:
                self.send.put(("file_error", base_name, str(e)))
                # expecting App to respond with abort, retry, ignore
                # both GUIs use these same commands.
                msg = self.recv.get()
                response, app_base_name = msg

                # sanity check that we're talking about the same file
                if app_base_name != base_name:
                    raise Exception("App response refers to a different file!")

                if response == "abort":
                    raise e

            if response is None or response == "ignore":
                file_num += 1
            elif response == "retry":
                # continue now, don't increment i
                continue
            else:
                raise Exception(f"Unknown response '{response}'")

            i += 1

    def process_file(self, ctdfile: CTDFile, file_num: int):
        base_name = ctdfile.base_file_name

        try:
            self.pending.remove(base_name)
        except KeyError:
            # may happen when retrying a file
            pass

        self.processing.add(base_name)

        self.send.put(("start", base_name, file_num, len(self.pending)))

        # attempt to get latitude from primary source
        latitude = None
        oceandb = get_db()
        if oceandb is not None:
            latitude = oceandb.get_latitude(base_name)

        if latitude is None:
            # database disabled or latitude missing for this file, request latitude input
            print(f"WARNING: database missing latitude for file {base_name}. Manual latitude input required.")
            latitude = self.request_latitude(base_name)

        if latitude is not None:
            # TODO validate latitude value
            latitude = latitude.strip()
            ctdfile.latitude = latitude

        process_hex_file(ctdfile, audit=self.audit_log, send=self.send, exist_ok=True)

        self.processed.add(base_name)
        self.send.put(("finish", base_name, file_num, len(self.processed)))

    def check_stop_message(self):
        """Check for stop message from the app.
        If received, raises StopProcessing"""
        if not self.recv.empty():
            msg = self.recv.get()
            if msg == 'stop':
                raise StopProcessing()
            else:
                print('Unknown message:', msg)

    def request_latitude(self, base_name: str) -> str:
        """
        Request latitude from the GUI process
        Blocks until reply received.
        """

        self.send.put(("request_latitude", base_name))
        msg = self.recv.get()
        command = msg[0]
        if msg == 'stop':
            raise StopProcessing()
        else:
            name = msg[1]
            if name != base_name:
                raise Exception('message reply refers to different file')

            if command == 'skip':
                raise SkipFile()
            elif command == 'submit_latitude':
                lat = msg[2]
                return lat

            else:
                raise Exception(f'unexpected message {msg}')


def start_manager(send: Queue, recv: Queue, basenames: list[str] | None = None):
    """Create new instance of Manager and start processing"""

    if basenames is not None and len(basenames) == 0:
        basenames = None

    try:
        # TODO auditlog_path from config
        with Manager(send, recv, auditlog_path="sbe_ctd_auditlog.csv") as manager:
            manager.scan_dirs(basenames)

            if manager.pending:
                print(f"Starting to process {len(manager.pending)} files")
                send.put(("begin", len(manager.pending)))
                manager.start()
                send.put(("done",))
            else:
                print("No files need to be processed.")
                send.put(("usermsg", "No files need to be processed."))

    except Exception as e:
        send.put(("error", str(e)))
        raise e

class StopProcessing(Exception):
    """Raise to stop processing after current file"""
    pass

class SkipFile(Exception):
    """Raise to skip over the current file"""
    pass
