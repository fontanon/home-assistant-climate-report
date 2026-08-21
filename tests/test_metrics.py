from datetime import datetime, time
import sys
from pathlib import Path
import unittest


APP_PATH = Path(__file__).parents[1] / "climate-report" / "app"
sys.path.insert(0, str(APP_PATH))

from metrics import Sample, coverage, split_day_night, summarize  # noqa: E402


class MetricsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.samples = [
            Sample(datetime(2026, 5, 4, 7), 20.0, 19.0, 21.0),
            Sample(datetime(2026, 5, 4, 8), 22.0, 21.0, 23.0),
            Sample(datetime(2026, 5, 4, 21), 24.0, 23.0, 25.0),
            Sample(datetime(2026, 5, 4, 22), 23.0, 22.0, 24.0),
        ]

    def test_summarize(self) -> None:
        result = summarize(self.samples)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.mean, 22.25)
        self.assertEqual(result.minimum, 19.0)
        self.assertEqual(result.maximum, 25.0)
        self.assertEqual(result.samples, 4)

    def test_split_day_night(self) -> None:
        day, night = split_day_night(self.samples, time(8), time(22))
        self.assertEqual(len(day), 2)
        self.assertEqual(len(night), 2)

    def test_coverage(self) -> None:
        self.assertEqual(coverage(84, 168), 0.5)


if __name__ == "__main__":
    unittest.main()
