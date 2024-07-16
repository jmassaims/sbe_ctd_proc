import sys
import os
import unittest
from datetime import datetime
from pathlib import Path

if __package__ is None:
    # Add project root to sys path when this file is run directly.
    project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.append(project_root)

from sbe_ctd_proc.ctd_file import parse_hex, CTDFile

from sbe_ctd_proc.config_util import get_config_dir
# FIXME separate testing config or files
from sbe_ctd_proc.config import CONFIG

# TODO choose testing hex files (diff versions), commit
class TestParsing(unittest.TestCase):

    def setUp(self):
        self.config_dir = CONFIG["CTD_CONFIG_PATH"]
        self.raw = raw = Path(CONFIG["RAW_PATH"])

    def test_parse_hex(self):
        hex_file = self.raw / "19plus1_4409_20030312_test.hex"
        sn, cast_date = parse_hex(hex_file)
        self.assertEqual(sn, "4409")
        self.assertEqual(cast_date, datetime(2005, 8, 23))

    def test_time(self):
        # * SeacatPlus V 1.4D  SERIAL NO. 4525    24 Sep 2015  15:39:44
        hex_file = self.raw / "19plus2_4525_20150914_test.hex"
        sn, cast_date = parse_hex(hex_file)
        self.assertEqual(sn, "4525")
        # should use the cast line
        # * cast  11 22 Sep 2015 17:55:29 samples ...
        self.assertEqual(cast_date, datetime(2015, 9, 22))

    def test_mapping(self):
        hex_file = self.raw / "19plus1_4409_20030312_test.hex"
        sn, cast_date = parse_hex(hex_file)
        self.assertEqual(sn, "4409")

        CONFIG["LIVEWIRE_MAPPING"]["4409"] = "123"
        ctdfile = CTDFile(hex_file)
        ctdfile.parse_hex()
        self.assertEqual(ctdfile.serial_number, "123")
        self.assertEqual(cast_date, datetime(2005, 8, 23))


if __name__ == '__main__':
    unittest.main()
