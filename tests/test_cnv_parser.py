import unittest
import os
from pathlib import Path

from sbe_ctd_proc.cnv_parser import CnvInfoRaw

class TestParsing(unittest.TestCase):

    data_dir: Path
    cnv_info: CnvInfoRaw

    def setUp(self):
        self.data_dir = Path(os.path.dirname(__file__)) / "data"
        self.assertTrue(self.data_dir.is_dir())

        filepath = self.data_dir / "19plus2_4525_20140618_testCFACLWDB.cnv"
        self.assertTrue(filepath.is_file())

        self.cnv_info = CnvInfoRaw(filepath)

    def test_general_info(self):
        cnv = self.cnv_info
        self.assertEqual(cnv.sections[0]['Temperature SN'], '4525')
        self.assertEqual(cnv.sections[0]['Conductivity SN'], '4525')

        self.assertEqual(cnv.sections[1]['CF0'], "2.637367e+03")

        self.assertEqual(cnv.sections[2]["nquan"], "14")
        self.assertEqual(cnv.sections[2]["interval"], "meters: 1")

        self.assertEqual(cnv.sections[3]["filter_low_pass_tc_A"], "0.500")

    def test_sensors_xml(self):
        xml = self.cnv_info.get_sensors_xml()

        num_sensors = int(xml.attrib["count"])
        self.assertEqual(num_sensors, 7)

    def test_get_sensors_info(self):
        sensors_info = self.cnv_info.get_sensors_info()
        self.assertEqual(len(sensors_info), 7)

        self.assertDictEqual(sensors_info[0], {
            'channel': 1,
            'type': 'TemperatureSensor',
            'id': 58,
            'sn': '4525',
            'calib_date': '17-may-13'
        })


if __name__ == '__main__':
    unittest.main()
