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
    push_notifier: str
    email_enabled: bool
    email_to: str
    email_from: str
    smtp_host: str
    smtp_port: int
    smtp_security: str
    smtp_username: str
    smtp_password: str
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
        push_notifier=(payload.get("push_notifier") or payload.get("notifier") or "").strip(),
        email_enabled=bool(payload.get("email_enabled", False)),
        email_to=(payload.get("email_to") or "").strip(),
        email_from=(payload.get("email_from") or "").strip(),
        smtp_host=(payload.get("smtp_host") or "").strip(),
        smtp_port=int(payload.get("smtp_port", 587)),
        smtp_security=payload.get("smtp_security", "starttls"),
        smtp_username=(payload.get("smtp_username") or "").strip(),
        smtp_password=payload.get("smtp_password") or "",
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
    if settings.email_enabled:
        if not settings.email_to or not settings.email_from or not settings.smtp_host:
            raise ValueError("Email requires recipient, sender and SMTP host")
        if settings.smtp_security not in {"starttls", "ssl", "none"}:
            raise ValueError("Unsupported SMTP security mode")
