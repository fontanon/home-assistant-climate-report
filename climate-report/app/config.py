"""Load and validate Home Assistant app options."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OPTIONS_PATH = Path("/data/options.json")


@dataclass(frozen=True)
class Room:
    name: str
    temperature_entity: str
    humidity_entity: str | None = None


@dataclass(frozen=True)
class Settings:
    timezone: str
    language: str
    report_days: int
    day_start: str
    night_start: str
    comparison: str
    archive_reports: bool
    dry_run: bool
    notifier: str
    weather_entity: str
    rooms: tuple[Room, ...]
    outdoor_temperature_entity: str
    outdoor_humidity_entity: str | None


def load_settings(path: Path = OPTIONS_PATH) -> Settings:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    rooms = tuple(
        Room(
            name=item["name"].strip(),
            temperature_entity=item["temperature_entity"].strip(),
            humidity_entity=(item.get("humidity_entity") or "").strip() or None,
        )
        for item in payload.get("rooms", [])
    )
    outdoor = payload.get("outdoor", {})
    settings = Settings(
        timezone=payload.get("timezone", "Europe/Madrid"),
        language=payload.get("language", "es"),
        report_days=int(payload.get("report_days", 7)),
        day_start=payload.get("day_start", "08:00"),
        night_start=payload.get("night_start", "22:00"),
        comparison=payload.get("comparison", "same_iso_week"),
        archive_reports=bool(payload.get("archive_reports", True)),
        dry_run=bool(payload.get("dry_run", True)),
        notifier=(payload.get("notifier") or "").strip(),
        weather_entity=(payload.get("weather_entity") or "").strip(),
        rooms=rooms,
        outdoor_temperature_entity=(outdoor.get("temperature_entity") or "").strip(),
        outdoor_humidity_entity=(outdoor.get("humidity_entity") or "").strip() or None,
    )
    validate_settings(settings)
    return settings


def validate_settings(settings: Settings) -> None:
    if not settings.rooms:
        raise ValueError("Configure at least one room before generating a report")
    if not settings.outdoor_temperature_entity:
        raise ValueError("Configure an outdoor temperature entity")
    for room in settings.rooms:
        if not room.name or not room.temperature_entity:
            raise ValueError("Every room needs a name and temperature entity")
