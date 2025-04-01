from functools import cached_property
import logging
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

class XmlSection:

    root_name: str
    # ending xml text
    end_text: str

    __lines: list[str]
    __complete: bool

    def __init__(self, root_name: str) -> None:
        self.root_name = root_name
        self.end_text = f'</{root_name}>'
        self.__lines = []
        self.__complete = False

    def add_line(self, text: str):
        if self.__complete:
            raise AssertionError('cannot add line to completed XML')

        self.__lines.append(text)

    @cached_property
    def xml(self) -> ElementTree.Element:
        # this parser does not include Comments
        # may need to use XMLPullParser, or another XML module.
        logging.debug('parsing %s xml', self.root_name)
        return ElementTree.fromstringlist(self.__lines)

    def complete(self):
        self.__complete = True

    def is_complete(self):
        return self.__complete

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

    xml_sections: list[XmlSection]
    # root names corresponding to xml sections
    xml_names: tuple[str, ...]

    # uninteresting text that's ignored
    # values must exactly match entire line with whitespace stripped.
    # ds and dh are maybe "data section" and "data header"? could structure these.
    ignored_text = {"", "*", "* ds", "* dh"}

    # private, static
    # Regex to separate: name [=:] value
    # some lines contain multiple values
    _name_val_re = re.compile(r"[*#]\s+([^=:]+)\s*[=:]\s*(.+)\s*")

    # Regex to check for starting XML element
    # xml element could split across lines, but assuming Seabird doesn't that
    _xml_start_re = re.compile(r"[*#]\s*<([^>\s]+)[^>]*>")

    # special lines that should not be split into name=value
    _weird_line_starts = ['* cast ', '* SeacatPlus ', '* SEACAT PROFILER ']

    def __init__(self, file_path: str | Path):
        self.file_path = file_path
        self.parse_file()

        self.xml_names = tuple(xml.root_name for xml in self.xml_sections)

        for xml in self.xml_sections:
            if not xml.is_complete():
                logging.warning(f'"{xml.root_name}" XML never commpleted! {self.file_path}')

    def parse_file(self):
        section = SeabirdSection()
        self.sections = [section]
        self.xml_sections = []

        xml: XmlSection | None = None

        name_val_re = self._name_val_re
        xml_start_re = self._xml_start_re

        # encoding option omitted to be more flexible.
        # Previously, this had encoding="utf-8", but we had one file (trip_6169_WQP143)
        # with strange file encoding that caused an error.
        with open(self.file_path, 'r') as file:
            for line in file:
                if line.startswith("*END*"):
                    # end of info, this is where data starts.
                    # use seabirdscientific cnv_to_instrument_data instead.
                    break
                elif line.startswith("* S>"):
                    # next section
                    section = SeabirdSection()
                    self.sections.append(section)

                    if xml:
                        logging.warning("XML broken by new section: %s", line)
                        xml = None

                    continue

                else:
                    line = line.strip()

                    if xml is not None:
                        # gather xml lines until end element
                        # cut off the *|# and space
                        # this assumes XML always has at least two leading characters
                        chopped = line[2:].strip()
                        if len(chopped) == 0:
                            # no content on line after chopping
                            continue

                        # Need to guard against weird XML like this:
                        #
                        # * <Headers>
                        # *
                        # * cast   9 30 May 2024 11:49:18 samples 9019 to 10047, avg = 1, stop = mag switch
                        #
                        # So assuming all Seabird XML lines start with < or we exit XML mode.
                        if chopped.startswith('<'):
                            xml.add_line(chopped)
                            # can end multiple elements on same line, so endswith check
                            # * </EventCounters></InstrumentState>
                            # FUTURE more robust to feed xml parser and have it say when done
                            if chopped.endswith(xml.end_text):
                                logging.debug("XML end: %s", line)
                                xml.complete()
                                xml = None

                            continue
                        else:
                            logging.warning("XML broken by line: %s", line)
                            xml = None
                            # keep going, should skip xml_match check but it should fail

                    # check if starting xml
                    xml_match = xml_start_re.match(line)
                    if xml_match:
                        name = xml_match.group(1)
                        logging.debug('XML start "%s": %s', name, line)
                        xml = XmlSection(name)
                        # assuming led by *|#, fix with nested RegEx groups?
                        xml.add_line(line[2:])
                        self.xml_sections.append(xml)

                        # XML ends current section
                        # (this is debatable, maybe XML belongs in sections?)
                        section = SeabirdSection()
                        self.sections.append(section)

                        continue

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

    def get_xml(self, root_name: str) -> ElementTree.Element:
        xmls = [x for x in self.xml_sections if x.root_name == root_name]
        if len(xmls) > 1:
            raise AssertionError(f'multiple "{root_name}" XML sections in: {self.file_path}')
        elif len(xmls) == 0:
            raise KeyError(f'No "{root_name}" section found')

        return xmls[0].xml

    def find_unknown_line(self, start_text: str) -> str | None:
        """Search all sectiions for unknown line starting with given text."""
        for sec in self.sections:
            for line in sec.unknown_lines:
                if line.startswith(start_text):
                    return line

        return None
