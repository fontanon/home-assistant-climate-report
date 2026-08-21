from datetime import date, datetime
import sys
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo


APP_PATH = Path(__file__).parents[1] / "weekly-climate-report" / "app"
sys.path.insert(0, str(APP_PATH))

from periods import resolve_periods  # noqa: E402


class PeriodsTest(unittest.TestCase):
    def test_last_complete_week_and_iso_comparison(self) -> None:
        periods = resolve_periods(
            "Europe/Madrid",
            7,
            "same_iso_week",
            now=datetime(2026, 5, 11, 7, 15, tzinfo=ZoneInfo("Europe/Madrid")),
        )
        self.assertEqual(periods.current.start.date(), date(2026, 5, 4))
        self.assertEqual(periods.current.end.date(), date(2026, 5, 11))
        assert periods.comparison is not None
        self.assertEqual(periods.comparison.start.date(), date(2025, 5, 5))

    def test_expected_hours_respects_dst(self) -> None:
        periods = resolve_periods(
            "Europe/Madrid", 7, "none", end_date=date(2026, 3, 30)
        )
        self.assertEqual(periods.current.expected_hours, 167)
