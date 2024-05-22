from datetime import datetime
from pathlib import Path
from config import CONFIG

# TODO better to use regex (exact indicies brittle)
# Seabird python lib doesn't seem to support extracting hex info.
def parse_hex(file):
    """Parse searial number and cast date from Hex file"""
    serial_number = None
    with open(file, "r", encoding="utf-8") as hex_file:
        nmea_checker = False
        for line in hex_file:
            if serial_number is None and "Temperature SN =" in line:
                serial_number = line[-5:].strip()
                print("serial number from:", line.rstrip())

            if "cast" in line:
                try:
                    # If there are multiple casts, an unwanted 'cast' line will be present, so skip it
                    cast_date = datetime.strptime(line[11:22], "%d %b %Y")
                    cast_date_line = line
                except ValueError:
                    pass

            if "SeacatPlus" in line:
                try:
                    # Date parsing for .hex files earlier earlier than 2015
                    cast_date = datetime.strptime(line[40:51], "%d %b %Y")
                    cast_date_line = line
                except ValueError:
                    pass

            if "NMEA UTC (Time) =" in line:
                cast_date = datetime.strptime(line[20:31], "%b %d %Y")
                cast_date_line = line
                nmea_checker = True

            elif "System UTC" in line and nmea_checker != True:
                print(nmea_checker)
                cast_date = datetime.strptime(line[15:26], "%b %d %Y")
                cast_date_line = line

            # TODO break once have all values? or at "*END*"

        if serial_number == None:
            raise Exception(f"No serial number found in: {file}")

    print("cast date from: ", cast_date_line.rstrip())
    return (serial_number, cast_date)


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

    serial_number: str
    """Temperature serial number from hex file"""

    cast_date: datetime

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

    def parse_hex(self):
        """Parse serial number and cast date from hex file.
        Applies the LIVEWIRE_MAPPING if it has an entry for the serial number.
        """
        serial_number, cast_date = parse_hex(self.hex_path)

        # Livewire ctds have different temperature IDs - Adjust them here
        # use CONFIG stored mapping
        try:
            new_id = CONFIG["LIVEWIRE_MAPPING"][serial_number]
            print(f"LIVEWIRE_MAPPING mapped {serial_number} to {new_id}")
            serial_number = new_id
        except KeyError:
            pass

        self.serial_number = serial_number
        self.cast_date = cast_date
