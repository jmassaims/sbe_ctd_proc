import unittest
from datetime import datetime
from pathlib import Path

from sbe_ctd_proc.config import CONFIG
from sbe_ctd_proc.ctd_file import CTDFile
from sbe_ctd_proc.parsing import HexInfo

# TODO choose testing hex files (diff versions), commit
class TestHexParsing(unittest.TestCase):

    def setUp(self):
        self.data_dir = Path(__file__).parent / "data"

        # Mutating CONFIG shared among tests.
        # Ideally would have mock CONFIG scoped to this test.
        CONFIG.livewire_mapping['4409'] = '123'

    def test_parse_hex(self):
        hex_file = self.data_dir / "19plus1_4409_20030312_test.hex"
        info = HexInfo(hex_file)

        sn = info.get_serial_number()
        self.assertEqual(sn, "4409")

        cast_date = info.get_cast_date()
        self.assertEqual(cast_date, datetime(2005, 8, 23, 9, 59, 58))

    def test_time(self):
        # * SeacatPlus V 1.4D  SERIAL NO. 4525    24 Sep 2015  15:39:44
        hex_file = self.data_dir / "19plus2_4525_20150914_test.hex"
        info = HexInfo(hex_file)

        sn = info.get_serial_number()
        self.assertEqual(sn, "4525")

        cast_date = info.get_cast_date()
        # should use the cast line
        # * cast  11 22 Sep 2015 17:55:29 samples ...
        self.assertEqual(cast_date, datetime(2015, 9, 22, 17, 55, 29))

    # FIXME fallback date
    def test_no_date(self):
        hex_file = self.data_dir / "19plus2_4525_20140618_test.hex"
        info = HexInfo(hex_file)

        sn = info.get_serial_number()
        self.assertEqual(sn, "4525")

        cast_date = info.get_cast_date()
        self.assertIsNone(cast_date)

    def test_mapping(self):
        hex_file = self.data_dir / "19plus1_4409_20030312_test.hex"
        info = HexInfo(hex_file)

        sn = info.get_serial_number()
        self.assertEqual(sn, "4409")

        cast_date = info.get_cast_date()
        self.assertEqual(cast_date, datetime(2005, 8, 23, 9, 59, 58))

        # when we create a CTDFile, the livewire mapping (4409 -> 123) should be used.
        ctdfile = CTDFile(hex_file)
        ctdfile.parse_hex()
        self.assertEqual(ctdfile.serial_number, "123")

    def test_dualtemp(self):
        # TODO WQR084.hx
        pass


if __name__ == '__main__':
    unittest.main()
