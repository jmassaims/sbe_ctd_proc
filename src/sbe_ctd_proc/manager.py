import threading
from contextlib import AbstractContextManager
from pathlib import Path
import os
from collections.abc import Mapping, Callable
from multiprocessing import Queue
from typing import Optional

from .audit_log import AuditLog
from .ctd_file import CTDFile
from .process import process_hex_file
from .config import CONFIG
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

    def scan_dirs(self):
        """scan directories, set file lists"""
        with self._scan_lock:
            self.hex_files = list(self.raw_path.glob("*.hex"))
            total_count = len(self.hex_files)
            self.hex_count = total_count
            print(f"{total_count} hex files in {self.raw_path}")

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

            # TODO what should be done with processing? option to delete it?
            self.pending = base_names - processed - processing

        if self.on_change:
            self.on_change()

    def start(self):
        # copy pending set since we mutate it
        pending = list(self.pending)

        i = 0
        file_num = 1 # 1-based index
        while i < len(pending):
            if not self.recv.empty():
                msg = self.recv.get()
                if msg == 'stop':
                    print('stopping')
                    break
                else:
                    print('Unknown message:', msg)

            base_name = pending[i]
            ctdfile = self.ctdfile[base_name]

            response = None
            try:
                self.process_file(ctdfile, file_num)
            except Exception as e:
                self.send.put(("file_error", base_name, str(e)))
                # expecting App to respond with abort, retry, ignore
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
        process_hex_file(ctdfile, audit=self.audit_log, send=self.send)

        self.processed.add(base_name)
        self.send.put(("finish", base_name, file_num, len(self.processed)))


def start_manager(send: Queue, recv: Queue):
    """Create new instance of Manager and start processing"""
    try:
        # TODO auditlog_path from config
        with Manager(send, recv, auditlog_path="sbe_ctd_auditlog.csv") as manager:
            manager.scan_dirs()

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
