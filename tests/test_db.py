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
