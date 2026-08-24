from datetime import date, datetime
import sys
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo


APP_PATH = Path(__file__).parents[1] / "climate-report" / "app"
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

    def test_custom_date_range_and_comparison_keep_requested_length(self) -> None:
        periods = resolve_periods(
            "Europe/Madrid",
            7,
            "same_dates",
            start_date=date(2026, 5, 2),
            end_date=date(2026, 5, 12),
        )
        self.assertEqual(periods.current.label, "2026-05-02 – 2026-05-11")
        self.assertEqual(periods.current.expected_hours, 240)
        assert periods.comparison is not None
        self.assertEqual(periods.comparison.label, "2025-05-02 – 2025-05-11")

    def test_custom_range_rejects_reversed_dates(self) -> None:
        with self.assertRaises(ValueError):
            resolve_periods(
                "Europe/Madrid",
                7,
                "none",
                start_date=date(2026, 5, 12),
                end_date=date(2026, 5, 2),
            )
