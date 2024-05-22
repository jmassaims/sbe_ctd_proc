import os
from pathlib import Path
from datetime import datetime
from config import CONFIG

def get_config_dir_path(name: str) -> Path:
    val = CONFIG[name]
    path = Path(val)
    if not path.exists():
        raise FileNotFoundError(f"Missing directory: {val}")

    if not path.is_dir():
        raise FileNotFoundError(f"Not a directory: {val}")

    return path

def get_config_dir(serial_number: str, cast_date: datetime):
    """get the config folder for the given serial number and cast date"""

    # try
    subfolders = [
        f.path
        for f in os.scandir(os.path.join(CONFIG["CTD_CONFIG_PATH"], serial_number))
        if f.is_dir()
    ]

    # TODO:review why was this exception allowed?
    # Exception handling for incompatible config file
    #except FileNotFoundError as e:
    #    print("WARNING: Config file path incompatible.")

    print(f"Checking configuration directory for subdirectory relevant to {cast_date} cast date.")
    subfolder_date_list = []

    # FIXME dependent on alphasort, this code is brittle
    # i.e. SBE prefixes just happen to have dates after the previous style dir names.
    # for folder in subfolders:
    #     folder_date = datetime.strptime(folder[-8:], "%Y%m%d")
    #     subfolder_date_list.append(folder_date)
    # subfolder_date_list.sort()
    #
    # print(subfolder_date_list)

    # FIXME confusing code, what's the intention here?
    found_config = 0
    for folder in subfolders:
        folder_date = datetime.strptime(folder[-8:], "%Y%m%d")
        # find date range our cast fits into
        print(f"Checking {folder_date} configuration directory.")
        if folder_date < cast_date:
            temp_folder = folder
        else:
            config_folder = temp_folder
            break
        if found_config == 0:
            config_folder = folder

    print("Configuration Folder Selected: ", config_folder)
    return config_folder

def get_xmlcon(config_folder: str) -> Path:
    """get the .xmlcon file Path from the folder.
    Error if folder does not contain one .xmlcon file.
    """
    xmlcon_files = list(Path(config_folder).glob("*.xmlcon"))
    if len(xmlcon_files) != 1:
        raise Exception(f"Expected one .xmlcon file in: {config_folder}")

    return xmlcon_files[0]
