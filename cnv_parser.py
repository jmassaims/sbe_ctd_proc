import re
from io import TextIOWrapper
from xml.etree import ElementTree


class CnvInfoRaw:
    """Extract information from .cnv file with minimal parsing.
    Methods will perform smarter parsing of different formats.

    seabird sbs lib has cnv_to_instrument_data, but that doesn't extract general info.
    It only has interval_s, latitude, start_time and the MeasurementSeries data.
    """

    sections: list[dict]

    # unstructured text that may be interesting
    # TODO associate these with their section
    unknown_text: list[str]

    sensors_xml_lines: list[str]
    sensors_xml: ElementTree.Element

    # uninteresting text that's ignored
    ignored_text = {"", "*", "* ds", "* dh"}

    def __init__(self, file: str):
        # separate name = value
        name_val_re = re.compile(r"[*#]\s+([^=]+)\s*=\s*(.+)\s*")

        info = {}
        self.sections = [info]
        self.unknown_text = []

        xml_lines = None

        with open(file, 'r') as cnv:
            for line in cnv:
                if xml_lines is not None:
                    # gather xml lines until </Sensors>
                    xml_lines.append(line[2:])
                    if line.startswith("# </Sensors>"):
                        self.sensors_xml_lines = xml_lines
                        self.sensors_xml_text = "".join(xml_lines)
                        xml_lines = None

                elif line.startswith("*END*"):
                    # end of info, this is where data starts.
                    # use sbs.process cnv_to_instrument_data instead.
                    break
                elif line.startswith("* S>"):
                    # next section
                    info = {}
                    self.sections.append(info)
                    continue
                elif line.startswith("# <Sensors"):
                    assert xml_lines is None
                    xml_lines = [line[2:]]
                    # next section
                    info = {}
                    self.sections.append(info)
                else:
                    m = name_val_re.match(line)
                    if m:
                        # regex consumes most whitespace, but strip to be certain.
                        info[m.group(1).strip()] = m.group(2).strip()
                    else:
                        self.parse_unknown_text(line.strip())

    def get_sensors_xml(self) -> ElementTree.Element:
        if not hasattr(self, 'sensors_xml'):
            self.sensors_xml = ElementTree.fromstringlist(self.sensors_xml_lines)

        return self.sensors_xml

    def parse_unknown_text(self, line: str):
        if line in self.ignored_text:
            return

        self.unknown_text.append(line)


# TEST
path = r"c:\Users\awhite\data\CTD\processed\19plus2_4525_20120905_test\done\19plus2_4525_20120905_testCFACLWDB.cnv"
ci = CnvInfoRaw(path)

xml = ci.get_sensors_xml()
num_sensors = xml.attrib["count"]
print(f"{num_sensors} sensors")

for sensor in xml.iterfind("sensor"):
    subelements = [x for x in sensor]
    if len(subelements) != 1:
        raise Exception("expected 1 subelement of <sensor>")

    subelement = subelements[0]

    channel = sensor.attrib['Channel']
    type = subelement.tag
    id = subelement.attrib["SensorID"]

    sn = subelement.findtext("SerialNumber")
    calib_date = subelement.findtext("CalibrationDate")

    print(type, channel, id, sn, calib_date)
