import unittest
from tempfile import TemporaryFile, mkstemp
from pathlib import Path
from csv import DictReader

from sbe_ctd_proc.audit_log import AuditInfoProcessing, AuditLog
from sbe_ctd_proc.ctd_file import CTDFile


class TestAuditLog(unittest.TestCase):

    def setUp(self):
        self.data_dir = Path(__file__).parent / "data"
        self.assertTrue(self.data_dir.is_dir())

        # tests set CTDFile.approved_dir to this to avoid audit log error.
        self.mock_approved_dir = Path(__file__).parent

    def test_appending(self):
        # temp_csv_file = TemporaryFile(suffix=".csv").name
        temp_csv_file = mkstemp(suffix=".csv", text=True)[1]
        # TODO , replace_rows = True
        # versus log param?
        # why did I create is_empty!?
        audit = AuditLog(temp_csv_file)

        self._write_logs(audit)

        audit.close()

        with open(temp_csv_file, 'r', newline='') as f:
            reader = DictReader(f, dialect='excel')
            rows = [r for r in reader]
            self.assertEqual(len(rows), 3)
            r1, r2, r3 = rows

            self.assertEqual(r1['latitude'], '-19.2')

            self.assertEqual(r2['latitude'], '-19.3')
            self.assertEqual(r2['last_command'], 'foo.exe')

            self.assertEqual(r3['latitude'], '-19.3')
            self.assertEqual(r3['last_command'], 'updated')

    def test_update_rows(self):
        temp_csv_file = mkstemp(suffix=".csv", text=True)[1]
        audit = AuditLog(temp_csv_file, update_rows=True)
        self._write_logs(audit)
        audit.close()

        with open(temp_csv_file, 'r', newline='') as f:
            reader = DictReader(f, dialect='excel')
            rows = [r for r in reader]
            self.assertEqual(len(rows), 2)
            r1, r2 = rows

            self.assertEqual(r1['latitude'], '-19.2')

            self.assertEqual(r2['latitude'], '-19.3')
            self.assertEqual(r2['last_command'], 'updated')

    def test_update_rows_flushing(self):
        temp_csv_file = mkstemp(suffix=".csv", text=True)[1]
        audit = AuditLog(temp_csv_file, update_rows=True, flush_after_log=True)
        self._write_logs(audit)
        audit.close()

        def check_assertions():
            with open(temp_csv_file, 'r', newline='') as f:
                reader = DictReader(f, dialect='excel')
                rows = [r for r in reader]
                self.assertEqual(len(rows), 2)
                r1, r2 = rows

                self.assertEqual(r1['latitude'], '-19.2')

                self.assertEqual(r2['latitude'], '-19.3')
                self.assertEqual(r2['last_command'], 'updated')

        check_assertions()

        # reopen same file, repeat tests with and without flush_after_log
        audit = AuditLog(temp_csv_file, update_rows=True, flush_after_log=True)
        self._write_logs(audit)
        audit.close()
        check_assertions()

        audit = AuditLog(temp_csv_file, update_rows=True, flush_after_log=False)
        self._write_logs(audit)
        audit.close()
        check_assertions()

    def _write_logs(self, audit: AuditLog):
        hex_file = self.data_dir / "19plus2_4525_20140618_test.hex"
        ctd_file = CTDFile(hex_file)
        ctd_file.parse_hex()
        ctd_file.approved_dir = self.mock_approved_dir
        cnv_file = self.data_dir / "19plus2_4525_20140618_testCFACLWDB.cnv"

        mixin_info: AuditInfoProcessing = {
            'con_filename': 'foo.xml',
            'latitude': -19.2,
            'last_command': 'foo.exe'
        } # type: ignore partial dict

        audit.log(ctd_file, cnv_file, mixin_info)

        hex_file = self.data_dir / "WQR084.hex"
        ctd_file = CTDFile(hex_file)
        ctd_file.parse_hex()
        ctd_file.approved_dir = self.mock_approved_dir
        cnv_file = self.data_dir / "WQR084CFACLWDB.cnv"

        mixin_info: AuditInfoProcessing = {
            'con_filename': 'foo.xml',
            'latitude': -19.3,
            'last_command': 'foo.exe',
            'approve_comment': '',
            'approve_date': ''
        }

        audit.log(ctd_file, cnv_file, mixin_info)

        # call a 2nd time to test appends vs update_row behavior
        mixin_info['last_command'] = 'updated'
        audit.log(ctd_file, cnv_file, mixin_info)


if __name__ == '__main__':
    unittest.main()
