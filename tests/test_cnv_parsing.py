from datetime import datetime
import unittest
from pathlib import Path

from sbe_ctd_proc.parsing.cnv_info import CnvInfo

class TestCnvParsing(unittest.TestCase):

    data_dir: Path
    cnv_4525: CnvInfo
    cnv_7360: CnvInfo
    cnv_WQR: CnvInfo

    def setUp(self):
        self.data_dir = Path(__file__).parent / "data"
        self.assertTrue(self.data_dir.is_dir())

        filepath = self.data_dir / "19plus2_4525_20140618_testCFACLWDB.cnv"
        self.assertTrue(filepath.is_file())

        self.cnv_4525 = CnvInfo(filepath)

        filepath = self.data_dir / "19plusV2_7360_20141014_testCF.cnv"
        self.assertTrue(filepath.is_file())
        self.cnv_7360 = CnvInfo(filepath)

        filepath = self.data_dir / "WQR084CFACLWDB.cnv"
        self.assertTrue(filepath.is_file())
        self.cnv_WQR = CnvInfo(filepath)

    def test_general_info(self):
        cnv = self.cnv_4525
        self.assertEqual(cnv.sections[0]['Temperature SN'], '4525')
        self.assertEqual(cnv.sections[0]['Conductivity SN'], '4525')

        self.assertEqual(cnv.sections[1]['CF0'], "2.637367e+03")

        self.assertEqual(cnv.sections[2]["nquan"], "14")
        self.assertEqual(cnv.sections[2]["interval"], "meters: 1")

        self.assertEqual(cnv.sections[3]["filter_low_pass_tc_A"], "0.500")

    def test_sensors_xml(self):
        xml = self.cnv_4525.get_sensors_xml()

        num_sensors = int(xml.attrib["count"])
        self.assertEqual(num_sensors, 7)

    def test_sensors_free_channel(self):
        # example cnv with a free channel
        cnv_info = self.cnv_7360
        xml = cnv_info.get_sensors_xml()
        num_channels = int(xml.attrib["count"])
        self.assertEqual(num_channels, 8)

        # free channel should be excluded
        sensors_info = cnv_info.get_sensors_info()
        self.assertEqual(len(sensors_info), 7)

    def test_get_sensors_info(self):
        sensors_info = self.cnv_4525.get_sensors_info()
        self.assertEqual(len(sensors_info), 7)

        self.assertDictEqual(sensors_info[0], {
            'channel': 1,
            'type': 'TemperatureSensor',
            'id': 58,
            'sn': '4525',
            'calib_date': '17-may-13'
        })

    def test_colon_separated(self):
        cnv = self.cnv_4525
        # loopedit_surfaceSoak: minDepth = 2.0, maxDepth = 5, useDeckPress = 1
        self.assertEqual(cnv.sections[1]["volt 0"], "offset = -4.684667e-02, slope = 1.248835e+00")
        self.assertEqual(cnv.sections[3]["loopedit_surfaceSoak"], "minDepth = 1.0, maxDepth = 2, useDeckPress = 1")

    def test_get(self):
        cnv = self.cnv_4525
        self.assertEqual(cnv.get("System UpLoad Time"), "Jun 22 2014 14:14:08")
        self.assertEqual(cnv.get("file_type"), "ascii")

        with self.assertRaises(KeyError):
            cnv.get("foobar")

    def test_start_time(self):
        cnv = self.cnv_4525
        starttime, type = cnv.get_start_time()
        # Jun 22 2014 14:14:08 [System UpLoad Time]
        self.assertEqual(starttime, datetime(2014, 6, 22, 14, 14, 8))
        self.assertEqual(type, 'System UpLoad Time')

        # start_time = Jul 15 2015 03:43:07 [Instrument's time stamp, header]
        starttime, type = self.cnv_7360.get_start_time()
        self.assertEqual(starttime, datetime(2015, 7, 15, 3, 43, 7))
        self.assertEqual(type, "Instrument's time stamp, header")

        # start_time = Feb 02 2025 06:49:11 [System UTC, first data scan.]
        starttime, type = self.cnv_WQR.get_start_time()
        self.assertEqual(starttime, datetime(2025, 2, 2, 6, 49, 11))
        self.assertEqual(type, "System UTC, first data scan.")

if __name__ == '__main__':
    unittest.main()
