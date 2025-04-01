
from pathlib import Path
import re
from xml.etree import ElementTree

class SeabirdSection():
    """
    Represents a section of Seabird data.
    """

    # key value pairs following standard format
    data: dict

    # lines in the section that didn't match the name = value format
    unknown_lines: list[str]

    def __init__(self):
        self.data = {}
        self.unknown_lines = []

    def safe_set(self, key, value):
        """Throws KeyError if key already exists in this section."""
        if key in self.data:
            raise KeyError(f'key "{key}" already exists in section')

        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __str__(self):
        return (str(self.data), str(self.unknown_lines))

    def __repr__(self):
        return repr(dict(data=self.data, unknown_lines=self.unknown_lines))

    def __contains__(self, key):
        return key in self.data

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)


class SeabirdInfoParser():
    """
    General Seabird header information parser that supports the format of .hex and .cnv files.

    The approach of this parser is to scan the information above the data and structure
    it into the sections and key-value pairs. This tries to be a general parser and does
    not change behavior based on file version; TBD if this strategy works in all cases.

    * dh and ds are currently ignored instead of being interpreted as a section.
    """

    file_path: str | Path

    sections: list[SeabirdSection]

    # Sensor XML
    # Specific to CNV files, but simpler to capture in this base class.
    sensors_xml_lines: list[str]
    sensors_xml: ElementTree.Element

    # uninteresting text that's ignored
    # values must exactly match entire line with whitespace stripped.
    # ds and dh are maybe "data section" and "data header"? could structure these.
    ignored_text = {"", "*", "* ds", "* dh"}

    # private, static
    # Regex to separate: name [=:] value
    # some lines contain multiple values
    _name_val_re = re.compile(r"[*#]\s+([^=:]+)\s*[=:]\s*(.+)\s*")

    # special lines that should not be split into name=value
    _weird_line_starts = ['* cast ', '* SeacatPlus ', '* SEACAT PROFILER ']

    def __init__(self, file: str | Path):
        self.file_path = file
        section = SeabirdSection()
        self.sections = [section]

        xml_lines = None

        name_val_re = self._name_val_re

        # encoding option omitted to be more flexible.
        # Previously, this had encoding="utf-8", but we had one file (trip_6169_WQP143)
        # with strange file encoding that caused an error.
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
                    # use seabirdscientific cnv_to_instrument_data instead.
                    break
                elif line.startswith("* S>"):
                    # next section
                    section = SeabirdSection()
                    self.sections.append(section)
                    continue
                elif line.startswith("# <Sensors"):
                    assert xml_lines is None
                    xml_lines = [line[2:]]
                    # next section
                    section = SeabirdSection()
                    self.sections.append(section)
                else:
                    line = line.strip()

                    if self.is_weird_line(line):
                        section.unknown_lines.append(line)
                        continue

                    m = name_val_re.match(line)
                    if m:
                        # regex consumes most whitespace, but strip to be certain.
                        name = m.group(1).strip()
                        value = m.group(2).strip()
                        section.safe_set(name, value)
                    else:
                        # did not match name [=:] value
                        self.parse_unknown_text(section, line)

    def get_sensors_xml(self) -> ElementTree.Element:
        if not hasattr(self, 'sensors_xml'):
            # this parser does not include Comments
            # may need to use XMLPullParser, or another XML module.
            self.sensors_xml = ElementTree.fromstringlist(self.sensors_xml_lines)

        return self.sensors_xml

    def is_weird_line(self, line: str) -> bool:
        """Special check for lines that match the name [=:] value format but that we want
        to keep in unknown_lines"""
        # cast line is hard to parse after name/value split, so consider it weird/unknown.
        for text in self._weird_line_starts:
            if line.startswith(text):
                return True

        return False

    def parse_unknown_text(self, section: SeabirdSection, line: str):
        """Handle text that doesn't match the name = value format.
        @param section: section to add the unknown line to
        @param line: line text, stripped of whitespace
        """
        if line in self.ignored_text:
            # skip line
            return

        section.unknown_lines.append(line)

    def get(self, name: str) -> str:
        """Get the value of the variable name from any section.
        @throws Exception if name is in multiple sections
        @throws KeyError if name does not exist in any section
        """
        val = None
        for s in self.sections:
            if val is None:
                # get() returns None instead of raising KeyError
                val = s.get(name)
            elif name in s:
                # ambiguous which section's value to use.
                raise AssertionError(f'multiple sections have "{name}" {self.file_path}')

        if val is None:
            raise KeyError(f'"{name}" does not exist in any section. {self.file_path}')

        return val

    def find_unknown_line(self, start_text: str) -> str | None:
        """Search all sectiions for unknown line starting with given text."""
        for sec in self.sections:
            for line in sec.unknown_lines:
                if line.startswith(start_text):
                    return line

        return None
