import logging
import threading
from contextlib import AbstractContextManager
from pathlib import Path
import os
from collections.abc import Mapping, Callable
from multiprocessing import Queue
from typing import Optional

from .audit_log import AuditLog
from .ctd_file import CTDFile, hex_path_to_base_name
from .process import process_hex_file
from .config import CONFIG

class Manager(AbstractContextManager):
    """Manages the state of CTDFiles and tracks events.
    Processes each file that needs processing based on current configuration.
    """
    send: Optional[Queue]
    recv: Optional[Queue]

    raw_dir: Path
    processing_dir: Path
    destination_dir: Path

    # All CTD files in any of the directories
    ctdfiles: list[CTDFile]
    ctdfile: Mapping[str, CTDFile]
    "lookup CTDFile by base name"

    # basenames in each status
    pending: set[str]
    processing: set[str]
    processed: set[str]

    audit_log: Optional[AuditLog]

    # Alternate latitude lookup method (spreadsheet or database).
    # raises LookupError if not found or multiple found.
    # if None, Manager defaults to "ask" via send/recv messages.
    lookup_latitude: Optional[Callable[[str], float]]

    # callback when file info changes.
    # hacky, only works for the last client
    on_change: Optional[Callable] = None

    _scan_lock = threading.Lock()

    def __init__(
            self,
            send: Optional[Queue] = None,
            recv: Optional[Queue] = None,
            auditlog_path: Optional[Path] = None,
            lookup_latitude: Optional[Callable[[str], float]] = None
        ) -> None:

        self.send = send
        self.recv = recv

        self.raw_dir = CONFIG.raw_path

        # TODO prompt to create if missing?
        self.processing_dir = CONFIG.processing_path
        self.destination_dir = CONFIG.destination_path

        print('Manager auditlog_path', auditlog_path)
        self.audit_log = AuditLog(auditlog_path) if auditlog_path else None

        self.lookup_latitude = lookup_latitude

    def __exit__(self, *exc_details):
        self.cleanup()

    def cleanup(self):
        if self.audit_log:
            self.audit_log.close()

    def scan_dirs(self):
        """
        scan directories, set file collections: hex_files, pending, processing, processed.

        This sets pending to all files in raw that are not processing or processed.
        """
        with self._scan_lock:
            # start with the done CTD files
            self.ctdfiles = ctdfiles = self.__scan_done_dir()
            # generate initial lookup table
            self.ctdfile = ctdfile_lookup =  dict((f.base_file_name, f) for f in ctdfiles)

            self.processed = set(f.base_file_name for f in ctdfiles)

            # add processing CTD files not in done
            self.processing = set()
            for proc_ctdfile in self.__scan_processing_dir():
                if proc_ctdfile.base_file_name in ctdfile_lookup:
                    logging.warning('Done AND Processing!? %s', proc_ctdfile.base_file_name)
                else:
                    ctdfiles.append(proc_ctdfile)
                    self.processing.add(proc_ctdfile.base_file_name)
                    ctdfile_lookup[proc_ctdfile.base_file_name] = proc_ctdfile

            # breakdown of status for files in the raw directory.
            raw_status_counts = {
                'pending': 0,
                'processing': 0,
                'processed': 0,
                'done': 0
            }

            self.pending = set()
            raw_hex_count = 0
            for raw_hex in self.raw_dir.glob("*.hex"):
                base_name = hex_path_to_base_name(raw_hex)
                raw_hex_count += 1

                existing = ctdfile_lookup.get(base_name, None)
                if existing:
                    # already processing or done
                    raw_status_counts[existing.status()] += 1
                else:
                    # not done or processing
                    raw_ctdfile = CTDFile(raw_hex)
                    assert raw_ctdfile.base_file_name == base_name  # being paranoid
                    ctdfiles.append(raw_ctdfile)
                    self.pending.add(base_name)
                    ctdfile_lookup[base_name] = raw_ctdfile

                    raw_status_counts['pending'] += 1
                    # sanity check
                    if not raw_ctdfile.status() == 'pending':
                        logging.warning(f'File should be pending but is {raw_ctdfile.status()}: {raw_ctdfile}')


            n_done = len(self.processed)
            n_processing = len(self.processing)
            logging.info(f'CTDfile scan status: done={n_done}, processing={n_processing}, all raw={raw_hex_count}')
            logging.info(f'Status breakdown of files in raw: {raw_status_counts}')

        if self.on_change:
            self.on_change()

    def __scan_processing_dir(self) -> list[CTDFile]:
        """Scan processing dir for CTDfile processing directories.

        * directory immediately under processing
        * contains a hex file

        @returns list of hex file paths
        """
        ctdfiles: list[CTDFile] = []
        for ctd_dir in self.processing_dir.iterdir():
            if ctd_dir.is_dir():
                # look specifically for convention of hex with name matching directory
                # TODO consider warning if other hex files?
                hex = ctd_dir / f'{ctd_dir.name}.hex'
                if hex.exists():
                    ctdfile = CTDFile(hex)
                    ctdfiles.append(ctdfile)
                    logging.debug('Added processing CTDFile %s', ctdfile)

                    status = ctdfile.status()
                    if status != 'processing' and status != 'processed':
                        logging.warning(f'File status is {status} instead of processed/processing: {ctdfile}')
                else:
                    logging.warning('Processing dir ignored, no hex file: %s', hex)

        return ctdfiles

    def __scan_done_dir(self) -> list[CTDFile]:
        ctdfiles: list[CTDFile] = []
        for ctd_dir in self.destination_dir.iterdir():
            if not ctd_dir.is_dir():
                # ignore files
                continue

            done_raw = ctd_dir / 'raw'
            if not done_raw.is_dir():
                logging.warning('Unexpected directory structure, no raw %s', done_raw)
                continue

            hex = done_raw / f'{ctd_dir.name}.hex'
            #hexs = list(done_raw.glob('*.hex'))
            #assert len(hexs) == 1

            if hex.exists():
                ctdfile = CTDFile(hex)
                ctdfiles.append(ctdfile)
                logging.debug('Added done CTDfile %s', ctdfile)

                if not ctdfile.status() == 'done':
                    logging.warning(f'File status is {ctdfile.status()} instead of done: {ctdfile}')
            else:
                logging.warning('Done dir ignored, no hex file: %s', hex)

        return ctdfiles

    def set_pending(self, basenames: list[str]):
        """
        Set specific files to process. After this, pending will only include files in the given basenames.
        However, only raw or processing files are considered,
        must be called after scan_dirs()
        """

        basenames_set = set(basenames)

        logging.debug('set pending files: %s', basenames)

        # warn about any that are processed
        # user should move these to allow processing.
        match_processed = self.processed & basenames_set
        if match_processed:
            # TODO user message
            logging.warning(f'{len(match_processed)} selected files ignored. already processed: {match_processed}')

        # after scan_dirs(), valid files to process are those in pending or processing
        valid = self.pending | self.processing

        # Currently, hex files need to be in raw directory.
        # FUTURE could be more flexible and take Paths, no reason to restrict location.
        unknown = basenames_set - valid - match_processed
        if unknown:
            print('WARN: selected unknown files', unknown)

        self.pending = valid & basenames_set
        logging.info(f'{len(self.pending)} files pending: {self.pending}')


    def start(self):
        assert self.send is not None
        assert self.recv is not None

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
                logging.exception(f'Error processing f{base_name}')
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
        assert self.send is not None

        base_name = ctdfile.base_file_name

        try:
            self.pending.remove(base_name)
        except KeyError:
            # may happen when retrying a file
            pass

        self.processing.add(base_name)

        self.send.put(("start", base_name, file_num, len(self.pending)))

        if self.lookup_latitude is not None:
            # attempt to get latitude from spreadsheet/database (depending on config)
            try:
                latitude = self.lookup_latitude(base_name)
            except LookupError:
                print(f"WARNING: missing latitude for {base_name}. Fallback to asking user for latitude.")
                latitude = self.request_latitude(base_name)
        else:
            # default to asking if alternate method not configured.
            latitude = self.request_latitude(base_name)

        ctdfile.latitude = latitude

        process_hex_file(ctdfile, audit=self.audit_log, send=self.send, exist_ok=True)

        self.processed.add(base_name)
        self.send.put(("finish", base_name, file_num, len(self.processed)))

    def check_stop_message(self):
        """Check for stop message from the app.
        If received, raises StopProcessing"""
        if self.recv and not self.recv.empty():
            msg = self.recv.get()
            if msg == 'stop':
                raise StopProcessing()
            else:
                print('Unknown message:', msg)

    def request_latitude(self, base_name: str) -> float:
        """
        Request latitude from the GUI process
        Blocks until reply received.
        """

        assert self.send is not None
        assert self.recv is not None

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
    """Create new instance of Manager using current config and start processing.
    Refreshes config services before starting.
    """

    CONFIG.refresh_services()

    if basenames is not None and len(basenames) == 0:
        basenames = None

    try:
        with Manager(send, recv, auditlog_path=CONFIG.auditlog_file, lookup_latitude=CONFIG.lookup_latitude) as manager:
            manager.scan_dirs()

            if basenames:
                manager.set_pending(basenames)

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
