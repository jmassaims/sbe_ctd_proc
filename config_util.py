from pathlib import Path
from config import CONFIG

def get_config_dir_path(name: str) -> Path:
    val = CONFIG[name]
    path = Path(val)
    if not path.exists():
        raise FileNotFoundError(f"Missing directory: {val}")

    if not path.is_dir():
        raise FileNotFoundError(f"Not a directory: {val}")

    return path
