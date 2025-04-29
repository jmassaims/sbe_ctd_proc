import logging
from datetime import datetime
from pathlib import Path

from .parsing import HexInfo

from .config import CONFIG

def hex_path_to_base_name(hex_path: Path) -> str:
    """Get the base name used for directory names from the hex filename."""
    return hex_path.stem

def FileStatus(Enum):
    """CTD file status"""
    RAW = 'raw'
    PROCESSING = 'processing'
    APPROVED = 'approved'

class CTDFile:
    """high-level utility class with the different paths for a CTD file."""

    hex_path: Path
    """
    Path of the hex file
    in the directory corresponding to it status. done, processing, raw
    """

    base_file_name: str
    "hex file name without extension"

    latitude: float | None
    "latitude for this file. set externally"

    processing_dir: Path
    """Path of directory where this file is processed.
    directory may not exist.
    """

    approved_dir: Path
    """Path of directory where this file is processed.
    directory may not exist.
    """

    serial_number: str | None
    """Temperature serial number from hex file"""

    processing_cnvs: list[Path]

    destination_cnvs: list[Path]

    # should always be present, but could be None if parsing failed to extract cast date.
    cast_date: datetime | None
    cast_date_type: str | None

    info: HexInfo

    def __init__(self, hex_path: Path) -> None:
        if not hex_path.is_file():
            raise FileNotFoundError(f"not a file: {hex_path}")

        ext = hex_path.suffix

        # double-check to be safe
        if ext != ".hex":
            raise Exception(f"expected {hex_path} to have .hex extension")

        self.base_file_name = hex_path_to_base_name(hex_path)
        self.hex_path = hex_path
        self.latitude = None

        if hasattr(CONFIG, 'processing_dir') and hasattr(CONFIG, 'approved_dir'):
            self.processing_dir = CONFIG.processing_dir / self.base_file_name
            self.approved_dir = CONFIG.approved_dir / self.base_file_name
        else:
            # this is expected for testing but shouldn't happen when running App with a good config
            logging.warning("CTDFile processing_dir, approved_dir attrs not set due to missing CONFIG attribute(s)")

    def parse_hex(self):
        """Parse serial number and cast date from hex file.
        Applies the LIVEWIRE_MAPPING if it has an entry for the serial number.
        """
        if hasattr(self, 'info'):
            # avoid parsing multiple times
            return

        self.info = HexInfo(self.hex_path)

        serial_number = self.info.get_serial_number()
        if serial_number is None:
            logging.warning(f"No serial number found in: {self.hex_path}")

        try:
            di = self.info.get_cast_date()
            self.cast_date = di.datetime
            self.cast_date_type = di.key
        except ValueError:
            logging.warning(f"No cast date found in: {self.hex_path}")
            self.cast_date = None
            self.cast_date_type = None

        # Livewire ctds have different temperature IDs - Adjust them here
        # use CONFIG stored mapping
        try:
            new_id = CONFIG.livewire_mapping[serial_number]
            print(f"LIVEWIRE_MAPPING mapped {serial_number} to {new_id}")
            serial_number = new_id
        except KeyError:
            pass

        self.serial_number = serial_number

    def refresh_dirs(self):
        """
        Rescan CNVs in the processing and destionation directories.
        """
        if self.approved_dir.exists():
            self.destination_cnvs = list(self.approved_dir.joinpath('done').glob('*.cnv'))
        else:
            self.destination_cnvs = []

        if self.processing_dir.exists():
            # TODO 'done' subdir?
            self.processing_cnvs = list(self.processing_dir.glob('*.cnv'))
        else:
            self.processing_cnvs = []

    def get_step_count(self) -> tuple[int, int]:
        """get the number of steps completed and the total steps.
        Depends on state from refresh_dirs and calls that method if not called yet."""
        if not hasattr(self, 'processing_cnvs'):
            self.refresh_dirs()

        total = 8

        if self.approved_dir.exists():
            if self.processing_dir.exists():
                raise Exception('processing and done!?')

            return len(self.destination_cnvs), total

        elif self.processing_dir.exists():
            return len(self.processing_cnvs), total

        else:
            return 0, total

    def status(self):
        """Determine if pending, processing, processed, done
        unknown if both processing and done.
        """
        if self.approved_dir.exists():
            if self.processing_dir.exists():
                return 'unknown'
            else:
                return 'done'
        elif self.processing_dir.exists():
            steps, total = self.get_step_count()
            if steps == total:
                return 'processed'
            else:
                return 'processing'
        else:
            return 'pending'

    def __repr__(self) -> str:
        return f'CTDFile(hex_path="{self.hex_path}")'
