import sys
from pathlib import Path
import unittest


APP_PATH = Path(__file__).parents[1] / "climate-report" / "app"
sys.path.insert(0, str(APP_PATH))

from quality import humidity_scale, validate_humidity, validate_temperature  # noqa: E402


class QualityTest(unittest.TestCase):
    def test_rejects_dragino_sentinel(self) -> None:
        self.assertIsNone(validate_temperature(327.67).value)

    def test_detects_fractional_humidity_series(self) -> None:
        self.assertEqual(humidity_scale([0.42, 0.55, 0.61]), 100.0)
        self.assertAlmostEqual(validate_humidity(0.55, scale=100).value or 0, 55.0)

    def test_does_not_scale_mixed_humidity(self) -> None:
        self.assertEqual(humidity_scale([0.55, 55.0]), 1.0)


if __name__ == "__main__":
    unittest.main()
