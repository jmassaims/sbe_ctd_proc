from datetime import datetime
import unittest

from sbe_ctd_proc.config import CONFIG
from sbe_ctd_proc.db import OceanDB


class TestOceanDB(unittest.TestCase):

    def setUp(self):
        if not CONFIG.db_enabled:
            self.skipTest('database not enabled by config.toml')

        self.db = OceanDB(CONFIG.db_mdb_file, CONFIG.db_mdw_file, CONFIG.db_user, CONFIG.db_password)

    def test_latitude_lookup(self):
        with self.assertRaises(LookupError):
            self.db.lookup_latitude('foo123_does_not_exist')

        basename, expected_lat = self.db.get_test_basename()

        lat = self.db.lookup_latitude(basename)
        self.assertEqual(lat, expected_lat)

    def test_ctd_data_rec(self):
        # brittle, gets first record from ctd_data table
        basename, expected_lat = self.db.get_test_basename()
        rec = self.db.get_ctd_data(basename)
        self.assertEqual(rec.lat, expected_lat)

        self.assertIsInstance(rec.basename, str)
        self.assertIsInstance(rec.filename, str)
        self.assertIsInstance(rec.lat, float)
        self.assertIsInstance(rec.lon, float)
        self.assertIsInstance(rec.cast_number, int)
        self.assertEqual(rec.cast_number, 1)
        self.assertIsInstance(rec.site, str)
        self.assertIsInstance(rec.station, str)
        self.assertIsInstance(rec.date_first_in_pos, datetime)
