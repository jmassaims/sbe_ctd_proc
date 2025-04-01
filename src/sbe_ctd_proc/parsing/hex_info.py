from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
import re
from .seabird_info_parser import SeabirdInfoParser

# Concerns and possible future enhancements:
# - do both 'NMEA UTC (Time)' and 'NMEA UTC' date keys exist in Seabird files?
# - have any of these date keys changed value slightly over the years?
# - UTC timezone conversion. automatic if key contains "UTC"?

@dataclass
class DateInfo:
    """Information about a date retrieved from a Seabird file"""
    # parsed datetime value
    datetime: datetime
    # date name/key such as 'SeacatPlus', 'cast', 'SEACAT PROFILER'
    key: str
    # the raw line(s) where this date was parsed from
    line: str

class HexInfo(SeabirdInfoParser):

    # * cast   1 23 Aug 2005 09:59:58 samples 1 to 895, avg = 1, stop = mag switch
    # Groups: cast number, date
    _cast_re = re.compile(r"\* cast\s+(\d+)\s+(\d+\s+\w+\s+\d{2,4}\s+\d{2}:\d{2}:\d{2})")
    # * cast 0  09/11  10:37:19   samples 0 to 316  stop = switch off
    # Groups: cast number, date MM/DD, time
    _cast2_re = re.compile(r"\* cast\s+(\d+)\s+(\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})")

    # * SeacatPlus V 1.4D  SERIAL NO. 4525    22 Jun 2014  14:13:50
    # Groups: version, serial number, date+time
    _seacatplus_re = re.compile(r"\* SeacatPlus\s+V\s+([\d\.]+\w*)\s+SERIAL NO\.\s+(\d+)\s+(\d+\s+\w+\s+\d+\s+\d{2}:\d{2}:\d{2})")

    # * SEACAT PROFILER V2.1a SN 597   09/17/08  08:53:28.144
    # Groups: version, serial number, date+time
    _seacat_profiler_re = re.compile(r"\* SEACAT PROFILER\s+V([\d\.]+\w*)\s+SN\s+(\d+)\s+(\d+/\d+/\d+\s+\d{2}:\d{2}:\d{2}\.\d{3})")


    _next_date_keys = [
        'NMEA UTC (Time)',
        'System UTC',
        'SEACAT PROFILER',
        'SeacatPlus',
        'System UpLoad Time'
    ]

    # use date from another line if cast line not found.
    cast_date_fallback = True

    def __init__(self, file: str | Path):
        super().__init__(file)

    def get_serial_number(self) -> str | None:
        return self.get("Temperature SN")


    def get_cast_date(self) -> DateInfo:
        """
        Find and parse the cast date.

        Attempts to get the date from the cast line. If that fails and
        cast_date_fallback is True, then the next best date is used in this order:
        1. cast
        2. NMEA UTC (Time)
        3. System UTC
        4. SEACAT PROFILER
        5. SeacatPlus
        6. System UpLoad Time

        @returns DateInfo
        @throws KeyError if no dates or cast date line not found (depending on cast_date_fallback)
        @throws ValueError if parsing date failed.
        """
        di = None
        # look for usual cast line
        try:
            di = self._get_simple_cast_date()
        except KeyError as e:
            if self.cast_date_fallback:
                logging.debug("Attempting cast date fallback, no cast line in: %s", self.file_path)
            else:
                raise e
        except ValueError:
            # 1st cast line RegEx failed, try combined cast date
            # this will raise ValueError if it does not match.
            di = self._get_combined_cast_date()

        if di is None:
            if self.cast_date_fallback:
                di = self._find_next_best_date()
            else:
                # code path logic error above.
                raise AssertionError("cast line parsing failed and cast_date_fallback is False!?")


        logging.debug(f"cast date {di.datetime} from: {di.line}")
        return di

    def get_all_dates(self) -> dict[str, datetime]:
        """Get all known dates in the file"""
        d = {}
        # TODO
        return d

    def _get_simple_cast_date(self) -> DateInfo:
        """
        Get the cast date from the cast line.

        Succeeds only if this cast line has month, date, and year.

        @throws KeyError if cast line not found
        @throws ValueError if failed to parse line or it's missing year.
        @returns (datetime, line)
        """
        line = self.find_unknown_line("* cast ")
        if line:
            # cast line can have very different formats:
            # * cast  11 22 Sep 2015 17:55:29 samples 13335 to 14765, avg = 1, stop = mag switch
            # * cast 0  09/11  10:37:19   samples 0 to 316  stop = switch off
            m = self._cast_re.match(line)
            if m:
                cast_num = m.group(1)
                date_text = m.group(2)
                dt = datetime.strptime(date_text, "%d %b %Y %H:%M:%S")
                return DateInfo(dt, 'cast', line)
            else:
                raise ValueError("Regex did not match cast line")

        else:
            raise KeyError('cast line not found')

    def _get_combined_cast_date(self, line: str | None = None) -> DateInfo:
        """
        Attempt to combine a partial MM/DD date in the cast line with another date line.
        Returns type indicating the other date it combined with, e.g. 'cast+SEABIRD PROFILER'
        @param line the line to parse, otherwise searchs for unknown line: * cast
        @returns DateInfo (line attr will be both lines with newline char between)
        @throws KeyError if cast line not found
        @throws ValueError if regex did not match
        """
        if line is None:
            line = self.find_unknown_line("* cast ")
            if line is None:
                raise KeyError('cast line not found')

        # this regex only matches a MM/DD cast line
        m = self._cast2_re.match(line)
        if m:
            cast_num = m.group(1)
            date_text = m.group(2)
            time_text = m.group(3)

            next_date = self._find_next_best_date()

            year = next_date.datetime.year
            dt = datetime.strptime(f'{date_text}/{year} {time_text}', '%m/%d/%Y %H:%M:%S')
            return DateInfo(dt, f'cast+{next_date.key}', f'{line}\n{next_date.line}')
        else:
            raise ValueError("Regex did not match cast line")

    def _find_next_best_date(self) -> DateInfo:
        """
        Get the next date that should be closest to the cast date.

        Iterates through _next_date_keys, default order is:
        1. NMEA UTC (Time)
        2. System UTC
        3. SEACAT PROFILER
        4. SeacatPlus
        5. System UpLoad Time

        @throws KeyError if none of these dates exist or parse
        """

        for date_key in self._next_date_keys:
            try:
                return self._get_date(date_key)
            except ValueError:
                logging.warning(f'"{date_key}" regex failed to match')
            except KeyError:
                pass

        raise KeyError('None of the dates were found!')

    def _get_date(self, key: str) -> DateInfo:
        """Unified way to get simple or weird dates by known keys."""
        if key == 'SEACAT PROFILER':
            return self._get_seacatprofiler_date()
        elif key == 'SeacatPlus':
            return self._get_seacatplus_date()
        else:
            return self._get_simple_date(key)

    def _get_simple_date(self, key: str, format="%b %d %Y %H:%M:%S") -> DateInfo:
        """
        Get a simple date where the entire value is the date+time text.

        Example: * NMEA UTC (Time) = Feb 02 2025  06:47:06
        Known keys: 'NMEA UTC (Time)', 'System UTC', 'System UpLoad Time'
        @throws KeyError if key not found
        @throws ? if date parsing failed
        """
        value = self.get(key)
        # though can have extra space between date and time.
        # TODO probably timezone issues here. Should be UTC if in key text?
        dt = datetime.strptime(value, format)
        # TODO ideally would lookup the raw line instead of recreating
        return DateInfo(dt, key, f'RECREATED * {key} = {value}')

    def _get_seacatplus_date(self) -> DateInfo:
        """
        Get datetime from the SeacatPlus line.

        Date style used in .hex files earlier than 2015.

        @throws KeyError if SeacatPlus line not found
        @throws ValueError if line found but Regex did not match
        @returns (datetime, line)
        """
        line = self.find_unknown_line("* SeacatPlus")
        if line:
            m = self._seacatplus_re.match(line)
            if m:
                datetext = m.group(3)
                dt = datetime.strptime(datetext, "%d %b %Y %H:%M:%S")
                return DateInfo(dt, 'SeacatPlus', line)

            else:
                raise ValueError('Regex did not match SeacatPlus line "{line}" in file: {self.hex_path}')

        else:
            raise KeyError('SeacatPlus line not found')

    def _get_seacatprofiler_date(self) -> DateInfo:
        """
        Get the datetime from the SEACAT PROFILER line.
        * SEACAT PROFILER V2.1a SN 597   09/17/08  08:53:28.144
        @returns (datetime, line)
        @throws KeyError if SEACAT PROFILER line not found
        """
        line = self.find_unknown_line("* SEACAT PROFILER")
        if line is None:
            raise KeyError('SEACAT PROFILER line not found')

        m = self._seacat_profiler_re.match(line)
        if m:
            datetext = m.group(3)
            dt = datetime.strptime(f'{datetext}000', "%m/%d/%y %H:%M:%S.%f")
            return DateInfo(dt,'SEACAT PROFILER', line)

        else:
            raise ValueError("Regex did not match SEACAT PROFILER line")
