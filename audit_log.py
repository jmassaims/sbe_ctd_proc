

from typing import TypedDict


class LogData(TypedDict):
    """Data structure with information from .cnd file"""
    # which name? hex? file in
    filename: str
    xmlcon_file: str
    cast_date: str
    lat: str
    lon: str
    # TODO logreq from DB
    temp_sn: str
    cond_sn: str
    # "meters: 1"
    interval: str
    sensors_count: int
