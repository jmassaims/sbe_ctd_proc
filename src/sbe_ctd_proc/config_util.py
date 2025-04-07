import logging
import os
from pathlib import Path
from datetime import datetime

from .config import CONFIG

# Test: test_config_util
def get_config_dir(serial_number: str | None, cast_date: datetime | None, config_dir: Path | None = None) -> Path:
    """get the config folder for the given serial number and cast date.

    serial_number and cast_date accept None for code conveience; this raises ValueError.
    @param serial_number
    @param cast_date
    @param config_dir: use this config directory instead of CONFIG.ctd_config_path
    @throws ValueError if params or config values invalid/missing
    """

    if cast_date is None:
        # it may be possible to process without a cast date, but for our purposes
        # the cast date is required and when not parsed should be supplied
        # via another method like the database or spreadsheet.
        raise ValueError("cast date required to get config dir")

    if serial_number is None:
        raise ValueError('serial number required to get config dir')

    config_dir = config_dir or CONFIG.ctd_config_path
    if config_dir is None:
        raise ValueError("psa config directory missing")

    sn_config_path = config_dir / serial_number
    if not sn_config_path.is_dir():
        raise Exception(f'CTD config directory not found for serial number {serial_number}: {sn_config_path}')

    logging.debug(f"Checking configuration directory {sn_config_path} for subdirectory relevant to {cast_date} cast date.")

    config_folder = None
    for folder in sn_config_path.iterdir():
        if not folder.is_dir():
            continue

        folder_date = datetime.strptime(folder.name[-8:], "%Y%m%d")

        if folder_date <= cast_date:
            config_folder = folder

    if config_folder is None:
        raise Exception(f"No config folder found for serial_number={serial_number}, cast_date={cast_date}")

    return Path(config_folder)

def get_xmlcon(config_folder: Path) -> Path:
    """get the .xmlcon file Path from the folder.
    Error if folder does not contain one .xmlcon file.
    @returns Path to xmlcon file in the given directory
    @throws AssertionError if zero or multiple xmlcons found.
    """
    path = None
    for xmlcon_file in config_folder.glob("*.xmlcon"):
        if not xmlcon_file.is_file():
            continue

        if path is not None:
            raise AssertionError(f'multiple .xmlcon files in: {config_folder}')

        path = xmlcon_file

    if path is None:
        raise AssertionError(f"No .xmlcon files in: {config_folder}")

    return path
