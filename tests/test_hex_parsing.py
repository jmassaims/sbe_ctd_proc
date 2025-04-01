import unittest
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import Element

from sbe_ctd_proc.config import CONFIG
from sbe_ctd_proc.ctd_file import CTDFile
from sbe_ctd_proc.parsing import HexInfo

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

        di = info.get_cast_date()
        self.assertEqual(di.key, 'cast')
        self.assertEqual(di.datetime, datetime(2005, 8, 23, 9, 59, 58))

    def test_time(self):
        # * SeacatPlus V 1.4D  SERIAL NO. 4525    24 Sep 2015  15:39:44
        hex_file = self.data_dir / "19plus2_4525_20150914_test.hex"
        info = HexInfo(hex_file)

        sn = info.get_serial_number()
        self.assertEqual(sn, "4525")

        di = info.get_cast_date()
        # should use the cast line
        # * cast  11 22 Sep 2015 17:55:29 samples ...
        self.assertEqual(di.key, 'cast')
        self.assertEqual(di.datetime, datetime(2015, 9, 22, 17, 55, 29))

    def test_WQR084(self):
        hex_file = self.data_dir / "WQR084.hex"
        info = HexInfo(hex_file)

        sn = info.get_serial_number()
        self.assertEqual(sn, "5530")

        di = info.get_cast_date()
        # this file does not have a cast line, 2 other date lines:
        # * NMEA UTC (Time) = Feb 02 2025  06:47:06
        # * System UTC = Feb 02 2025 06:49:11
        # old hex parser would use the NMEA line.
        self.assertEqual(di.key, 'NMEA UTC (Time)')
        self.assertEqual(di.datetime, datetime(2025, 2, 2, 6, 47, 6))

    def test_SeacatPlus_date(self):
        hex_file = self.data_dir / "19plus2_4525_20140618_test.hex"
        info = HexInfo(hex_file)

        sn = info.get_serial_number()
        self.assertEqual(sn, "4525")

        di = info.get_cast_date()
        # this file has no cast line

        # test direct dates
        di = info._get_seacatplus_date()
        self.assertEqual(di.key, 'SeacatPlus')
        self.assertEqual(di.datetime, datetime(2014, 6, 22, 14, 13, 50))

        di = info._get_simple_date('System UpLoad Time')
        self.assertEqual(di.key, 'System UpLoad Time')
        self.assertEqual(di.datetime, datetime(2014, 6, 22, 14, 14, 8))

        di = info.get_cast_date()
        self.assertEqual(di.key, 'SeacatPlus')
        self.assertEqual(di.datetime, datetime(2014, 6, 22, 14, 13, 50))

    def test_seacat_profiler(self):
        hex_file = self.data_dir / "trip_4859_WQM222.hex"
        info = HexInfo(hex_file)

        sn = info.get_serial_number()
        self.assertEqual(sn, "597")

        # verify result of lower-level get date methods
        di = info._get_seacatprofiler_date()
        self.assertEqual(di.key, 'SEACAT PROFILER')
        self.assertEqual(di.datetime, datetime(2008, 9, 17, 8, 53, 28, 144_000))

        di = info._get_simple_date('System UpLoad Time')
        self.assertEqual(di.key, 'System UpLoad Time')
        self.assertEqual(di.datetime, datetime(2009, 3, 16, 10, 19, 24))

        # get cast date combination
        # for this file, the cast line only has MM/DD, so year is obtained from another line
        di = info.get_cast_date()
        self.assertEqual(di.key, 'cast+SEACAT PROFILER')
        self.assertEqual(di.datetime, datetime(2008, 9, 11, 10, 37, 19))

    def test_8288_extra_xml(self):
        """test hex file with other XML sections"""
        hex_file = self.data_dir / 'trip_8288_FTZ362.hex'
        info = HexInfo(hex_file)

        self.assertTupleEqual(info.xml_names, ('ApplicationData', 'InstrumentState', 'Headers'))

        cast_date = info.get_cast_date()
        self.assertEqual(cast_date.key, 'cast')
        self.assertEqual(cast_date.datetime, datetime(2024, 5, 30, 11, 49, 18))

        app_data = info.get_xml('ApplicationData')
        version = app_data.find('Seaterm232/SoftwareVersion')
        assert isinstance(version, Element)
        self.assertEqual(version.text, '2.8.0.119')

        instr_state = info.get_xml('InstrumentState')
        hardware_data = instr_state.find('HardwareData')
        assert isinstance(hardware_data, Element)
        self.assertEqual(hardware_data.attrib['DeviceType'], 'SBE19plus')

    def test_mapping(self):
        hex_file = self.data_dir / "19plus1_4409_20030312_test.hex"
        info = HexInfo(hex_file)

        original_serial_number = info.get_serial_number()
        self.assertEqual(original_serial_number, "4409")

        di = info.get_cast_date()
        self.assertEqual(di.key, 'cast')
        self.assertEqual(di.datetime, datetime(2005, 8, 23, 9, 59, 58))

        # when we create a CTDFile, the livewire mapping (4409 -> 123) should be used.
        ctdfile = CTDFile(hex_file)
        ctdfile.parse_hex()
        self.assertEqual(ctdfile.serial_number, "123")

    def test_dualtemp(self):
        # TODO WQR084.hx
        pass


if __name__ == '__main__':
    unittest.main()
