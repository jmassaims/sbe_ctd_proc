import unittest
from tempfile import TemporaryFile, mkstemp
from pathlib import Path

from sbe_ctd_proc.audit_log import AuditInfo, AuditLog
from sbe_ctd_proc.ctd_file import CTDFile


class TestAuditLog(unittest.TestCase):

    def setUp(self):
        self.data_dir = Path(__file__).parent / "data"
        self.assertTrue(self.data_dir.is_dir())

        # temp_csv_file = TemporaryFile(suffix=".csv").name
        temp_csv_file = mkstemp(suffix=".csv", text=True)[1]
        self.audit = AuditLog(temp_csv_file, is_empty=True)

    def tearDown(self) -> None:
        self.audit.close()

    def test_one_temp(self):
        hex_file = self.data_dir / "19plus2_4525_20140618_test.hex"
        ctd_file = CTDFile(hex_file)
        ctd_file.parse_hex()
        cnv_file = self.data_dir / "19plus2_4525_20140618_testCFACLWDB.cnv"

        mixin_info: AuditInfo = {
            'con_filename': 'foo.xml',
            'latitude': -19.2,
            'last_command': 'foo.exe'
        } # type: ignore partial dict

        self.audit.log(ctd_file, cnv_file, mixin_info)

    def test_two_temps(self):
        hex_file = self.data_dir / "WQR084.hex"
        ctd_file = CTDFile(hex_file)
        ctd_file.parse_hex()
        cnv_file = self.data_dir / "WQR084CFACLWDB.cnv"

        mixin_info: AuditInfo = {
            'con_filename': 'foo.xml',
            'latitude': -19.2,
            'last_command': 'foo.exe'
        } # type: ignore partial dict

        self.audit.log(ctd_file, cnv_file, mixin_info)


if __name__ == '__main__':
    unittest.main()
