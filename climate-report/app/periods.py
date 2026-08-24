"""Resolve complete reporting and comparison windows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Period:
    start: datetime
    end: datetime
    label: str

    @property
    def expected_hours(self) -> int:
        elapsed = self.end.astimezone(ZoneInfo("UTC")) - self.start.astimezone(ZoneInfo("UTC"))
        return int(elapsed.total_seconds() // 3600)


@dataclass(frozen=True)
class Periods:
    current: Period
    comparison: Period | None


def resolve_periods(
    timezone: str,
    report_days: int,
    comparison: str,
    *,
    now: datetime | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Periods:
    zone = ZoneInfo(timezone)
    local_now = now.astimezone(zone) if now else datetime.now(zone)
    final_date = end_date or local_now.date()
    end = datetime.combine(final_date, time.min, zone)
    start = (
        datetime.combine(start_date, time.min, zone)
        if start_date
        else end - timedelta(days=report_days)
    )
    if start >= end:
        raise ValueError("Report start date must be earlier than end date")
    period_days = (end.date() - start.date()).days
    current = Period(start, end, _date_label(start.date(), (end - timedelta(days=1)).date()))

    previous: Period | None = None
    if comparison == "same_dates":
        previous_start = _replace_year(start, start.year - 1)
        previous_end = previous_start + timedelta(days=period_days)
        previous = Period(
            previous_start,
            previous_end,
            _date_label(previous_start.date(), (previous_end - timedelta(days=1)).date()),
        )
    elif comparison == "same_iso_week":
        iso_year, iso_week, iso_weekday = start.date().isocalendar()
        try:
            previous_date = date.fromisocalendar(iso_year - 1, iso_week, iso_weekday)
        except ValueError:
            previous_date = date.fromisocalendar(iso_year - 1, 52, iso_weekday)
        previous_start = datetime.combine(previous_date, time.min, zone)
        previous_end = previous_start + timedelta(days=period_days)
        previous = Period(
            previous_start,
            previous_end,
            _date_label(previous_start.date(), (previous_end - timedelta(days=1)).date()),
        )
    return Periods(current=current, comparison=previous)


def _replace_year(value: datetime, year: int) -> datetime:
    try:
        return value.replace(year=year)
    except ValueError:  # February 29
        return value.replace(year=year, day=28)


def _date_label(start: date, end: date) -> str:
    return f"{start.isoformat()} – {end.isoformat()}"
