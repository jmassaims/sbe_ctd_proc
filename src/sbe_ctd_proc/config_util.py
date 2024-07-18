import os
from pathlib import Path
from datetime import datetime

from .config import CONFIG

def get_config_dir_path(name: str) -> Path:
    val = CONFIG[name]
    path = Path(val)
    if not path.exists():
        raise FileNotFoundError(f"Missing directory: {val}")

    if not path.is_dir():
        raise FileNotFoundError(f"Not a directory: {val}")

    return path

# Test: test_config_util
def get_config_dir(serial_number: str, cast_date: datetime) -> Path:
    """get the config folder for the given serial number and cast date"""

    sn_config_path = os.path.join(CONFIG["CTD_CONFIG_PATH"], serial_number)
    print(f"Checking configuration directory {sn_config_path} for subdirectory relevant to {cast_date} cast date.")

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
