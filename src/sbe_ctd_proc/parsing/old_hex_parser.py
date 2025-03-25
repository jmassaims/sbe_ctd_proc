from datetime import datetime
import logging

# OLD code for reference, do not use

# TODO better to use regex (exact indicies brittle)
# Seabird python lib doesn't seem to support extracting hex info.
def parse_hex_OLD(file):
    """Parse serial number and cast date from Hex file

    This is the OLD hex parsing code for reference.
    """
    logging.debug('Parsing hex file: %s', file)

    serial_number = None
    # cast_date should always be found, but this code could have a parsing error.
    cast_date = None

    # encoding option omitted to be more flexible.
    # Previously, this had encoding="utf-8", but we had one file (trip_6169_WQP143)
    # with strange file encoding that caused an error.
    with open(file, "r") as hex_file:
        nmea_checker = False
        for line in hex_file:
            if serial_number is None and "Temperature SN =" in line:
                serial_number = line[-5:].strip()
                logging.debug("serial number from: %s", line.rstrip())

            if "cast" in line:
                try:
                    # If there are multiple casts, an unwanted 'cast' line will be present, so skip it
                    cast_date = datetime.strptime(line[11:22], "%d %b %Y")
                    cast_date_line = line
                except ValueError:
                    pass

            if "SeacatPlus" in line:
                try:
                    # Date parsing for .hex files earlier earlier than 2015
                    cast_date = datetime.strptime(line[40:51], "%d %b %Y")
                    cast_date_line = line
                except ValueError:
                    pass

            if "NMEA UTC (Time) =" in line:
                cast_date = datetime.strptime(line[20:31], "%b %d %Y")
                cast_date_line = line
                nmea_checker = True

            elif "System UTC" in line and nmea_checker != True:
                logging.debug(f"'System UTC' found. nmea_checker={nmea_checker}")
                cast_date = datetime.strptime(line[15:26], "%b %d %Y")
                cast_date_line = line

            # TODO break once have all values? or at "*END*"

        if serial_number == None:
            raise Exception(f"No serial number found in: {file}")

    # TODO show these warnings in App?
    if cast_date is None:
        logging.warning(f"No cast date found in: {file}")
    else:
        logging.debug("cast date from: %s", cast_date_line.rstrip())

    if serial_number is None:
        logging.warning(f"No serial number found in: {file}")

    return (serial_number, cast_date)
