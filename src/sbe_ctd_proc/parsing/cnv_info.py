from datetime import datetime
import logging
import re
from pathlib import Path
from io import TextIOWrapper
from typing import TypedDict
from xml.etree import ElementTree

from .seabird_info_parser import SeabirdInfoParser

class SensorInfo(TypedDict):
    type: str
    channel: int
    id: int
    sn: str
    calib_date: str

def sensorinfo_from_element(sensor: ElementTree.Element) -> SensorInfo:
    subelements = [x for x in sensor]

    # All sensors seem to have a comment like:
    # <!-- Count, Pressure, Strain Gauge -->

    # can have an empty sensor element (comment only):
    #   <sensor Channel="5" >
    #     <!-- A/D voltage 1, Free -->
    #   </sensor>
    if len(subelements) == 0:
        channel = int(sensor.attrib['Channel'])
        raise Exception(f'<sensor> channel="{channel}" has no subelements!')

    # Note: there can be a comment with useful info above this element.
    subelement = subelements[0]

    calib_date = subelement.findtext("CalibrationDate")

    return {
        'channel': int(sensor.attrib['Channel']),
        'type': subelement.tag,
        'id': int(subelement.attrib["SensorID"]),
        'sn': subelement.findtext("SerialNumber"),
        'calib_date': calib_date
    }

class CnvInfo(SeabirdInfoParser):
    """Extract information from .cnv file with minimal parsing.
    Methods will perform smarter parsing of different formats.

    seabirdscientific lib has cnv_to_instrument_data, but that doesn't extract general info.
    It only has interval_s, latitude, start_time and the MeasurementSeries data.
    """

    # Jun 22 2014 14:14:08 [System UpLoad Time]
    # 1st group is everything up to opening bracket, 2nd group text in brackets; trims whitespace.
    _start_time_re = re.compile(r"\s*([^\[]+)\s*\[\s*([^\]]*)\s*\]\s*")

    def __init__(self, file: str | Path):
        super().__init__(file)

    def get_sensors_info(self) -> list[SensorInfo]:
        """
        get simplified sensor information.
        excludes free channels.
        """
        xml = self.get_sensors_xml()

        # the count attribute is the number of channels, some <sensor> can be empty.
        # num_channels = int(xml.attrib["count"])
        # we only want the active sensors, so exclude the empty ones by checking len(sensor)

        infos = [
            sensorinfo_from_element(sensor)
            for sensor in xml.iterfind("sensor")
            if len(sensor) > 0
        ]

        return infos

    def get_sensors_xml(self) -> ElementTree.Element:
        for xml in self.xml_sections:
            if xml.root_name == 'Sensors':
                return xml.xml

        raise KeyError(f'Sensors XML not found/parsed in: {self.file_path}')


    def get_start_time(self) -> tuple[datetime, str]:
        """Get the start time and its type
        @throws KeyError if start_time does not exist in anywhere in CNV.
        """
        # Jun 22 2014 14:14:08 [System UpLoad Time]
        start_time_line = self.get("start_time")

        m = self._start_time_re.match(start_time_line)
        if m:
            time = m.group(1).strip()
            time_type = m.group(2).strip()
            logging.debug(f"Extracted start_time line parts: {time} {time_type}")

            dt = datetime.strptime(time, "%b %d %Y %H:%M:%S")
            return (dt, time_type)

        else:
            raise ValueError(f"""Could not parse start_time line value in: {self.file_path}
    {start_time_line}""")
