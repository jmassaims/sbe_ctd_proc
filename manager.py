from pathlib import Path
import os
from collections.abc import Mapping
from multiprocessing import Queue

from ctd_file import CTDFile
from process import process_hex_file
from config import CONFIG
from config_util import get_config_dir_path

class Manager:
    """Manages the state of CTDFiles and tracks events.
    Processes each file that needs processing based on current configuration.
    """
    send: Queue

    processing_dir: Path
    destination_dir: Path

    ctdfiles: list[CTDFile]
    ctdfile: Mapping[str, CTDFile]
    "lookup CTDFile by base name"

    pending: set[str]
    processing: set[str]
    processed: set[str]

    def __init__(self, send: Queue = None) -> None:
        self.send = send

        self.raw_path = get_config_dir_path("RAW_PATH")

        # TODO prompt to create if missing?
        self.processing_dir = get_config_dir_path("PROCESSING_PATH")
        self.destination_dir = get_config_dir_path("DESTINATION_PATH")


    def scan_dirs(self):
        """scan directories, set file lists"""
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

    def start(self):
        i = 1
        for base_name in self.pending:
            ctdfile = self.ctdfile[base_name]
            # TODO update manager set() state here
            self.send.put(("start", base_name, i))
            process_hex_file(ctdfile)
            self.send.put(("finish", base_name, i))
            i += 1


def start_manager(send: Queue):
    """Create new instance of Manager and start processing"""
    try:
        manager = Manager(send)
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
