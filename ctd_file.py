from config import CONFIG
from pathlib import Path


class CTDFile:
    """high-level utility class with the different paths for a CTD file."""

    hex_path: Path
    "Path of the raw hex file"

    base_file_name: str
    "hex file name without extension"

    processing_dir: Path
    """Path of directory where this file is processed.
    directory may not exist.
    """

    destination_dir: Path
    """Path of directory where this file is processed.
    directory may not exist.
    """

    def __init__(self, hex_path: Path) -> None:
        if not hex_path.is_file():
            raise FileNotFoundError(f"not a file: {hex_path}")

        ext = hex_path.suffix

        # double-check to be safe
        if ext != ".hex":
            raise Exception(f"expected {hex_path} to have .hex extension")

        self.base_file_name = hex_path.stem
        self.hex_path = hex_path

        self.processing_dir = Path(CONFIG["PROCESSING_PATH"]) / self.base_file_name
        self.destination_dir = Path(CONFIG["DESTINATION_PATH"]) / self.base_file_name
