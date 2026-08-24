from dataclasses import replace
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zoneinfo import ZoneInfo


ROOT = Path(__file__).parents[1]
APP_PATH = ROOT / "climate-report" / "app"
TEMPLATE_PATH = ROOT / "climate-report" / "templates"
sys.path.insert(0, str(APP_PATH))

from archive import save_report  # noqa: E402
from config import Room, Settings  # noqa: E402
from extract import build_report  # noqa: E402
from periods import resolve_periods  # noqa: E402
from render import render_email_report, render_full_report  # noqa: E402
from report import VariableReport  # noqa: E402


class FakeHomeAssistantClient:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str, str]] = []

    def get_statistics(self, entity_ids, start_time, end_time, period="hour"):
        self.calls.append((entity_ids, start_time, end_time))
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        old_scale = start.year == 2025
        result = {}
        for entity_id in entity_ids:
            rows = []
            cursor = start
            while cursor < end:
                hour_wave = abs(13 - cursor.hour) / 12
                if "humidity" in entity_id:
                    mean = 0.55 + hour_wave * 0.08 if old_scale else 55 + hour_wave * 8
                    spread = 0.01 if old_scale else 1
                elif "outdoor" in entity_id:
                    mean = 15 + (1 - hour_wave) * 12
                    spread = 1.5
                else:
                    mean = 21.5 + (1 - hour_wave) * 2
                    spread = 0.4
                rows.append(
                    {
                        "start": cursor.isoformat(),
                        "end": (cursor + timedelta(hours=1)).isoformat(),
                        "min": mean - spread,
                        "max": mean + spread,
                        "mean": mean,
                    }
                )
                cursor += timedelta(hours=1)
            result[entity_id] = rows
        return result

    def get_forecast(self, weather_entity, forecast_type="daily"):
        return {weather_entity: {"forecast": [{"temperature": 26, "condition": "sunny"}]}}


class PipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            timezone="Europe/Madrid",
            language="es",
            report_days=7,
            day_start="08:00",
            night_start="22:00",
            comparison="same_iso_week",
            archive_reports=True,
            dry_run=True,
            push_notifier="",
            email_enabled=False,
            email_to="",
            email_from="",
            smtp_host="",
            smtp_port=587,
            smtp_security="starttls",
            smtp_username="",
            smtp_password="",
            weather_entity="weather.home",
            rooms=(Room("Living room", "sensor.living_temperature", "sensor.living_humidity"),),
            outdoor_temperature_entity="sensor.outdoor_temperature",
            outdoor_humidity_entity="sensor.outdoor_humidity",
        )

    def test_end_to_end_report_generation(self) -> None:
        zone = ZoneInfo("Europe/Madrid")
        generated_at = datetime(2026, 5, 11, 7, 15, tzinfo=zone)
        periods = resolve_periods(
            self.settings.timezone,
            7,
            "same_iso_week",
            now=generated_at,
        )
        client = FakeHomeAssistantClient()
        report = build_report(client, self.settings, periods, generated_at=generated_at)

        self.assertEqual(len(client.calls), 2)
        self.assertEqual(report.rooms[0].temperature.coverage, 1.0)
        self.assertEqual(report.rooms[0].humidity.scale, 1.0)
        assert report.rooms[0].comparison_humidity is not None
        self.assertEqual(report.rooms[0].comparison_humidity.scale, 100.0)
        self.assertEqual(len(report.rooms[0].temperature.daily), 7)

        html = render_full_report(report, "es", template_dir=TEMPLATE_PATH)
        email = render_email_report(
            report,
            "es",
            template_dir=TEMPLATE_PATH,
            report_url="https://example.ui.nabu.casa/app/climate_report",
        )
        self.assertIn("Living room", html)
        self.assertIn("2026-05-04", html)
        self.assertIn("temperature-line", html)
        self.assertIn("humidity-line", html)
        self.assertIn("Living room", email)
        self.assertIn("https://example.ui.nabu.casa/app/climate_report", email)
        self.assertNotIn("{{", html)

        empty_temperature = VariableReport(
            unit="°C",
            overall=None,
            daytime=None,
            nighttime=None,
            daily=(),
            coverage=0.0,
        )
        humidity_only_room = replace(report.rooms[0], temperature=empty_temperature)
        humidity_only_report = replace(report, rooms=(humidity_only_room,))
        humidity_only_html = render_full_report(
            humidity_only_report, "es", template_dir=TEMPLATE_PATH
        )
        self.assertIn("Sin datos de temperatura", humidity_only_html)
        self.assertIn("humidity-line", humidity_only_html)
        self.assertIn("Humedad: 59 %", humidity_only_html)

        with TemporaryDirectory() as temporary:
            target = save_report(report, html, report_dir=Path(temporary))
            self.assertTrue(target.exists())
            self.assertTrue((Path(temporary) / "latest.html").exists())
            payload = json.loads((Path(temporary) / "latest.json").read_text())
            self.assertEqual(payload["rooms"][0]["name"], "Living room")


if __name__ == "__main__":
    unittest.main()
