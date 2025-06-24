from datetime import datetime, timedelta
import logging
from pathlib import Path
from seabirdscientific.instrument_data import MeasurementSeries

from ..config import CONFIG

from .negative_value_checker import check_for_negatives

class DataChecker:
    """
    simplifies interface to data checking and scanning and tracks related information.
    """

    problem_count: int

    checked_for_negatives: bool = False
    scanned_bin_file: Path
    negative_cols: list[MeasurementSeries]
    check_for_negatives_error: Exception | None

    checked_cast_dates: bool = False
    file_cast_date: datetime
    db_cast_date: datetime
    date_diff_seconds: float
    # consider a problem if dates more than this many seconds apart
    date_diff_limit: int
    check_cast_dates_error: Exception | None

    def __init__(self) -> None:
        self.problem_count = 0
        self.check_for_negatives_error = None
        self.check_cast_dates_error = None

        # hours to seconds (may be nan)
        self.date_diff_limit = CONFIG.date_difference_limit * 3600

    def check_for_negatives(self, bin_file: Path):
        try:
            self.scanned_bin_file = bin_file
            self.negative_cols = check_for_negatives(bin_file)
            self.problem_count += len(self.negative_cols)
            self.checked_for_negatives = True
        except Exception as e:
            logging.exception('check_for_negatives error')
            self.problem_count += 1
            self.check_for_negatives_error = e

    def check_cast_dates(self, file_cast_date: datetime, db_cast_date: datetime):
        try:
            self.file_cast_date = file_cast_date
            self.db_cast_date = db_cast_date

            assert db_cast_date.tzinfo is not None
            if file_cast_date.tzinfo is None:
                # assuming that this zoneless cast date is in the same timezone as the
                # date from the database
                file_cast_date = file_cast_date.replace(tzinfo=db_cast_date.tzinfo)

            diff = self.date_diff_seconds = (db_cast_date - file_cast_date).total_seconds()
            if self.date_diff_limit and diff > self.date_diff_limit:
                self.problem_count += 1

            self.checked_cast_dates = True

        except Exception as e:
            logging.exception('check_cast_dates error')
            self.problem_count += 1
            self.check_cast_dates_error = e
