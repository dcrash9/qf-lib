import unittest
from unittest import TestCase

import pandas as pd

from qf_lib.common.utils.miscellaneous.consecutive_duplicates import drop_consecutive_duplicates, Method
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.testing_tools.containers_comparison import assert_series_equal


class TestConsecutiveDuplicates(TestCase):
    def setUp(self):
        samples = [1, 2, 2, 3, 3, 3]
        dates = pd.date_range(start='2018-05-13', periods=len(samples))
        self.test_series = QFSeries(data=samples, index=dates)

    def test_drop_consecutive_duplicates_keep_first(self):
        expected_series_with_no_duplicates = self.test_series.iloc[[0, 1, 3]]
        actual_series_with_no_duplicates = drop_consecutive_duplicates(self.test_series, Method.KEEP_FIRST)
        assert_series_equal(expected_series_with_no_duplicates, actual_series_with_no_duplicates)

    def test_drop_consecutive_duplicates_keep_last(self):
        expected_series_with_no_duplicates = self.test_series.iloc[[0, 2, 5]]
        actual_series_with_no_duplicates = drop_consecutive_duplicates(self.test_series, Method.KEEP_LAST)
        assert_series_equal(expected_series_with_no_duplicates, actual_series_with_no_duplicates)

    def test_correct_behaviour_when_there_are_no_duplicates(self):
        no_duplicates_series = self.test_series.iloc[[0, 1, 3]]
        actual_series = drop_consecutive_duplicates(no_duplicates_series, Method.KEEP_FIRST)
        assert_series_equal(no_duplicates_series, actual_series)

        actual_series = drop_consecutive_duplicates(no_duplicates_series, Method.KEEP_LAST)
        assert_series_equal(no_duplicates_series, actual_series)


if __name__ == '__main__':
    unittest.main()
