import logging
import os
from pathlib import Path
from datetime import datetime

from .config import CONFIG

# Test: test_config_util
def get_config_dir(serial_number: str, cast_date: datetime, config_dir: Path | None = None) -> Path:
    """get the config folder for the given serial number and cast date.

    @param config_dir: use this config directory instead of CONFIG.ctd_config_path
    """

    if cast_date is None:
        # it may be possible to process without a cast date, but for our purposes
        # the cast date is required and when not parsed should be supplied
        # via another method like the database or spreadsheet.
        raise ValueError("cannot get config dir with out cast_date?")

    config_dir = config_dir or CONFIG.ctd_config_path
    if config_dir is None:
        raise ValueError("psa config directory missing")

    sn_config_path = config_dir / serial_number

    logging.debug(f"Checking configuration directory {sn_config_path} for subdirectory relevant to {cast_date} cast date.")

    config_folder = None
    for folder in os.scandir(sn_config_path):
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
    """
    xmlcon_files = list(config_folder.glob("*.xmlcon"))
    if len(xmlcon_files) != 1:
        raise Exception(f"Expected one .xmlcon file in: {config_folder}")
    os.listdir()
    return xmlcon_files[0]
