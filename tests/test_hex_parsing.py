import unittest
from datetime import datetime
from pathlib import Path

from sbe_ctd_proc.config import CONFIG
from sbe_ctd_proc.ctd_file import parse_hex, CTDFile

# TODO choose testing hex files (diff versions), commit
class TestHexParsing(unittest.TestCase):

    def setUp(self):
        self.data_dir = Path(__file__).parent / "data"

        # Mutating CONFIG shared among tests.
        # Ideally would have mock CONFIG scoped to this test.
        CONFIG.livewire_mapping['4409'] = '123'

    def test_parse_hex(self):
        hex_file = self.data_dir / "19plus1_4409_20030312_test.hex"
        sn, cast_date = parse_hex(hex_file)
        self.assertEqual(sn, "4409")
        self.assertEqual(cast_date, datetime(2005, 8, 23))

    def test_time(self):
        # * SeacatPlus V 1.4D  SERIAL NO. 4525    24 Sep 2015  15:39:44
        hex_file = self.data_dir / "19plus2_4525_20150914_test.hex"
        sn, cast_date = parse_hex(hex_file)
        self.assertEqual(sn, "4525")
        # should use the cast line
        # * cast  11 22 Sep 2015 17:55:29 samples ...
        self.assertEqual(cast_date, datetime(2015, 9, 22))

    def test_mapping(self):
        hex_file = self.data_dir / "19plus1_4409_20030312_test.hex"
        sn, cast_date = parse_hex(hex_file)
        self.assertEqual(sn, "4409")

        # when we create a CTDFile, the livewire mapping (4409 -> 123) should be used.
        ctdfile = CTDFile(hex_file)
        ctdfile.parse_hex()
        self.assertEqual(ctdfile.serial_number, "123")
        self.assertEqual(cast_date, datetime(2005, 8, 23))

    def test_dualtemp(self):
        # TODO WQR084.hx
        pass


if __name__ == '__main__':
    unittest.main()
