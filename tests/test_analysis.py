import os
import unittest
from pathlib import Path

from sbe_ctd_proc.analysis import check_for_negatives, create_scan_count_dataframe

class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.data_dir = Path(__file__).parent / "data"
        self.assertTrue(self.data_dir.is_dir())

    def test_check_for_negatives(self):
        filepath = self.data_dir / "19plusV2_7360_20141014_testCF.cnv"
        neg_cols = check_for_negatives(filepath)

        self.assertEqual(len(neg_cols), 1)

        filepath2 = self.data_dir / "19plus2_4525_20140618_testCFACLWDB.cnv"
        neg_cols = check_for_negatives(filepath2)
        self.assertEqual(len(neg_cols), 0)
