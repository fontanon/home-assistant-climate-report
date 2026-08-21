"""Long-running stdin command loop for the Home Assistant app."""

from __future__ import annotations

import json
import logging
import sys

from config import load_settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("weekly_climate_report")


def generate() -> None:
    settings = load_settings()
    LOGGER.info(
        "Configuration valid: %d room(s), %d report day(s), dry_run=%s",
        len(settings.rooms),
        settings.report_days,
        settings.dry_run,
    )
    # Data extraction and rendering land in the next implementation milestone.
    LOGGER.info("Generation scaffold completed; no email was sent")


def main() -> int:
    LOGGER.info("Weekly Climate Report is ready; waiting for stdin commands")
    for line in sys.stdin:
        try:
            command = json.loads(line)
            if command.get("command") != "generate":
                LOGGER.warning("Ignoring unsupported command: %s", command.get("command"))
                continue
            generate()
        except Exception:
            LOGGER.exception("Report command failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
