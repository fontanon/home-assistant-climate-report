"""Long-running stdin command loop for the Home Assistant app."""

from __future__ import annotations

import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from archive import DEFAULT_REPORT_DIR, save_report
from config import load_settings
from extract import build_report
from home_assistant import HomeAssistantClient
from periods import resolve_periods
from render import render_email_report, render_full_report


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("climate_report")


def generate(command: dict[str, object] | None = None) -> Path:
    command = command or {}
    settings = load_settings()
    LOGGER.info(
        "Configuration valid: %d room(s), %d report day(s), dry_run=%s",
        len(settings.rooms),
        settings.report_days,
        settings.dry_run,
    )
    requested_end = command.get("end_date")
    end_date = date.fromisoformat(str(requested_end)) if requested_end else None
    zone = ZoneInfo(settings.timezone)
    generated_at = datetime.now(zone)
    periods = resolve_periods(
        settings.timezone,
        settings.report_days,
        settings.comparison,
        now=generated_at,
        end_date=end_date,
    )
    LOGGER.info("Collecting statistics for %s", periods.current.label)
    report = build_report(
        HomeAssistantClient(), settings, periods, generated_at=generated_at
    )
    html = render_full_report(report, settings.language)
    email_html = render_email_report(report, settings.language)
    target = save_report(report, html, archive=settings.archive_reports)
    email_target = DEFAULT_REPORT_DIR / "latest-email.html"
    email_target.write_text(email_html, encoding="utf-8")
    LOGGER.info("Report written to %s", target)
    if settings.dry_run:
        LOGGER.info("Dry-run enabled; email delivery skipped")
    else:
        LOGGER.warning("Email delivery is not enabled in this milestone; report was archived only")
    return target


def main() -> int:
    LOGGER.info("Climate Report is ready; waiting for stdin commands")
    for line in sys.stdin:
        try:
            command = json.loads(line)
            if command.get("command") != "generate":
                LOGGER.warning("Ignoring unsupported command: %s", command.get("command"))
                continue
            generate(command)
        except Exception:
            LOGGER.exception("Report command failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
