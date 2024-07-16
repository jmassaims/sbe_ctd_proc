import unittest
from datetime import datetime

from sbe_ctd_proc.config_util import get_config_dir

class TestConfigUtil(unittest.TestCase):

    def test_between_date(self):
        cast_date = datetime(2013, 1, 1)
        dir = get_config_dir("6180", cast_date)
        self.assertEqual('6180', dir.parts[-2])
        self.assertEqual('NRS1_6180_20121009', dir.name)

    def test_exact_date(self):
        cast_date = datetime(2017, 9, 29)
        dir = get_config_dir("6180", cast_date)
        self.assertEqual('6180', dir.parts[-2])
        self.assertEqual('SBE19plusV2_6180_20170929', dir.name)

    def test_before_date(self):
        cast_date = datetime(2009, 1, 1)
        with self.assertRaises(Exception):
            dir = get_config_dir("6180", cast_date)

    def test_afterlast_date(self):
        cast_date = datetime(2025, 1, 1)
        dir = get_config_dir("6180", cast_date)
        self.assertEqual('6180', dir.parts[-2])
        self.assertEqual('SBE19plusV2_6180_20191230', dir.name)

if __name__ == '__main__':
    unittest.main()
