import os
from pathlib import Path
import unittest

from sbe_ctd_proc.latitude_spreadsheet import LatitudeSpreadsheet

class TestLatitudeSpreadsheet(unittest.TestCase):
    lat_spreadsheet: LatitudeSpreadsheet

    def setUp(self):
        self.data_dir = Path(os.path.dirname(__file__)) / 'data'
        path = self.data_dir / 'latitude_lookup_example.xlsx'
        self.assertTrue(path.exists())

        self.lat_spreadsheet = LatitudeSpreadsheet(path)

    def test_lookup(self):
        lat = self.lat_spreadsheet.lookup_latitude('WQN080')
        self.assertEqual(-19.1613333, lat)

        lat = self.lat_spreadsheet.lookup_latitude('WQM001')
        self.assertEqual(-23.1574833, lat)


if __name__ == '__main__':
    unittest.main()
