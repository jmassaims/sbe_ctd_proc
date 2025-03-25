
from datetime import datetime
import logging
from pathlib import Path
import re
from .seabird_info_parser import SeabirdInfoParser

class HexInfo(SeabirdInfoParser):

    # * cast   1 23 Aug 2005 09:59:58 samples 1 to 895, avg = 1, stop = mag switch
    # Groups: cast number, date
    _cast_re = re.compile(r"\* cast\s+(\d+)\s+(\d+\s+\w+\s+\d{2,4}\s+\d{2}:\d{2}:\d{2})")

    # * SeacatPlus V 1.4D  SERIAL NO. 4525    22 Jun 2014  14:13:50
    # Groups: version, serial number, date+time
    _seacatplus_re = re.compile(r"\* SeacatPlus\s+V\s+([\d\.]+\w*)\s+SERIAL NO\.\s+(\d+)\s+(\d+\s+\w+\s+\d+\s+\d{2}:\d{2}:\d{2})")

    def __init__(self, file: str | Path):
        super().__init__(file)

    def get_serial_number(self) -> str | None:
        return self.get("Temperature SN")


    def get_cast_date(self) -> tuple[datetime, str]:
        """Find and parse the cast date.
        1. * cast
        2. SeacatPlus
        3. NMEA UTC (Time)
        4. System UTC

        @returns datetime, line type
        @throws ValueError if could not determine cast date.
        """

        # look for usual cast line
        for sec in self.sections:
            for line in sec.unknown_lines:
                if line.startswith("* cast "):
                    m = self._cast_re.match(line)
                    if m:
                        cast_num = m.group(1)
                        date_text = m.group(2)
                        dt = datetime.strptime(date_text, "%d %b %Y %H:%M:%S")
                        logging.debug(f"cast date {dt} from: {line}")
                        return dt, 'cast'

        # fallback to other dates
        for name in ['NMEA UTC (Time)', 'System UTC']:
            try:
                value = self.get(name)
                if value:
                    # both of these use same date format: Feb 02 2025 06:47:06
                    # though can have extra space between date and time.
                    # TODO probably timezone issues here. Should be UTC?
                    dt = datetime.strptime(value, "%b %d %Y %H:%M:%S")
                    logging.debug(f'cast date {dt} from: {line}')
                    return dt, name

            except KeyError:
                continue

        for sec in self.sections:
            for line in sec.unknown_lines:
                if line.startswith("* SeacatPlus"):
                    # Date parsing for .hex files earlier than 2015
                    m = self._seacatplus_re.match(line)
                    if m:
                        datetext = m.group(3)
                        dt = datetime.strptime(datetext, "%d %b %Y %H:%M:%S")
                        logging.debug(f"cast date {dt} from: {line}")
                        return dt, 'SeacatPlus'

                    else:
                        raise ValueError('Regex did not match SeacatPlus line "{line}" in file: {self.hex_path}')

        raise ValueError(f"Could not determine cast date: {self.file_path}")
