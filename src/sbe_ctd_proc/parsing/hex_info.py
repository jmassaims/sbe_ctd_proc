
from datetime import datetime
from pathlib import Path
import re
from .seabird_info_parser import SeabirdInfoParser

class HexInfo(SeabirdInfoParser):

    # * cast   1 23 Aug 2005 09:59:58 samples 1 to 895, avg = 1, stop = mag switch
    # Groups: cast number, date
    _cast_re = re.compile(r"\* cast\s+(\d+)\s+(\d+\s+\w+\s+\d{2,4}\s+\d{2}:\d{2}:\d{2})")

    def __init__(self, file: str | Path):
        super().__init__(file)

    def get_serial_number(self) -> str | None:
        return self.get("Temperature SN")


    def get_cast_date(self) -> datetime | None:
        # look for usual cast line
        for sec in self.sections:
            for line in sec.unknown_lines:
                if line.startswith("* cast "):
                    m = self._cast_re.match(line)
                    if m:
                        cast_num = m.group(1)
                        date_text = m.group(2)
                        dt = datetime.strptime(date_text, "%d %b %Y %H:%M:%S")
                        return dt

        # fallback



        return None
