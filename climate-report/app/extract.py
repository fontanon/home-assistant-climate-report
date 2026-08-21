"""Transform Home Assistant recorder responses into validated report series."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from config import Settings
from home_assistant import HomeAssistantClient
from metrics import Sample, split_day_night, summarize
from periods import Period, Periods
from quality import humidity_scale, validate_humidity, validate_temperature
from report import ClimateReport, DailySummary, RoomReport, VariableReport


def build_report(
    client: HomeAssistantClient,
    settings: Settings,
    periods: Periods,
    *,
    generated_at: datetime,
) -> ClimateReport:
    entity_kinds = _entity_kinds(settings)
    entity_ids = list(entity_kinds)
    current_raw = client.get_statistics(
        entity_ids, periods.current.start.isoformat(), periods.current.end.isoformat()
    )
    comparison_raw: dict[str, Any] = {}
    if periods.comparison:
        comparison_raw = client.get_statistics(
            entity_ids,
            periods.comparison.start.isoformat(),
            periods.comparison.end.isoformat(),
        )

    zone = ZoneInfo(settings.timezone)
    day_start = time.fromisoformat(settings.day_start)
    night_start = time.fromisoformat(settings.night_start)
    current = _prepare_all(
        current_raw, entity_kinds, periods.current, zone, day_start, night_start
    )
    previous = _prepare_all(
        comparison_raw,
        entity_kinds,
        periods.comparison,
        zone,
        day_start,
        night_start,
    ) if periods.comparison else {}

    rooms = tuple(
        RoomReport(
            name=room.name,
            temperature=current[room.temperature_entity],
            humidity=current.get(room.humidity_entity) if room.humidity_entity else None,
            comparison_temperature=previous.get(room.temperature_entity),
            comparison_humidity=previous.get(room.humidity_entity) if room.humidity_entity else None,
        )
        for room in settings.rooms
    )
    forecast: dict[str, Any] = {}
    warnings: list[str] = []
    if settings.weather_entity:
        try:
            forecast = client.get_forecast(settings.weather_entity)
        except Exception as error:  # Report remains useful without forecast.
            warnings.append(f"Forecast unavailable: {error}")

    for entity_id, variable in current.items():
        if variable.coverage < 0.8:
            warnings.append(f"Low coverage for {entity_id}: {variable.coverage:.0%}")

    return ClimateReport(
        generated_at=generated_at.astimezone(zone).isoformat(),
        period_label=periods.current.label,
        comparison_label=periods.comparison.label if periods.comparison else None,
        rooms=rooms,
        outdoor_temperature=current[settings.outdoor_temperature_entity],
        outdoor_humidity=current.get(settings.outdoor_humidity_entity)
        if settings.outdoor_humidity_entity else None,
        comparison_outdoor_temperature=previous.get(settings.outdoor_temperature_entity),
        comparison_outdoor_humidity=previous.get(settings.outdoor_humidity_entity)
        if settings.outdoor_humidity_entity else None,
        forecast=forecast,
        warnings=tuple(warnings),
    )


def _entity_kinds(settings: Settings) -> dict[str, str]:
    kinds: dict[str, str] = {}
    for room in settings.rooms:
        kinds[room.temperature_entity] = "temperature_indoor"
        if room.humidity_entity:
            kinds[room.humidity_entity] = "humidity"
    kinds[settings.outdoor_temperature_entity] = "temperature_outdoor"
    if settings.outdoor_humidity_entity:
        kinds[settings.outdoor_humidity_entity] = "humidity"
    return kinds


def _prepare_all(
    raw: dict[str, Any],
    kinds: dict[str, str],
    period: Period | None,
    zone: ZoneInfo,
    day_start: time,
    night_start: time,
) -> dict[str, VariableReport]:
    if period is None:
        return {}
    result: dict[str, VariableReport] = {}
    for entity_id, kind in kinds.items():
        rows = raw.get(entity_id, [])
        samples, scale = parse_samples(rows, kind, zone)
        result[entity_id] = make_variable_report(
            samples,
            "%" if kind == "humidity" else "°C",
            period.expected_hours,
            day_start,
            night_start,
            scale,
        )
    return result


def parse_samples(
    rows: Iterable[dict[str, Any]], kind: str, zone: ZoneInfo
) -> tuple[list[Sample], float]:
    items = list(rows)
    scale = 1.0
    if kind == "humidity":
        candidates = [
            float(row[field])
            for row in items
            for field in ("min", "max", "mean")
            if row.get(field) is not None
        ]
        scale = humidity_scale(candidates)

    samples: list[Sample] = []
    for row in items:
        if any(row.get(field) is None for field in ("start", "min", "max", "mean")):
            continue
        validator = validate_humidity if kind == "humidity" else validate_temperature
        kwargs = {"scale": scale} if kind == "humidity" else {"outdoor": kind.endswith("outdoor")}
        minimum = validator(row["min"], **kwargs).value
        maximum = validator(row["max"], **kwargs).value
        mean = validator(row["mean"], **kwargs).value
        if minimum is None or maximum is None or mean is None:
            continue
        start = datetime.fromisoformat(str(row["start"]).replace("Z", "+00:00")).astimezone(zone)
        samples.append(Sample(start, mean, minimum, maximum))
    return samples, scale


def make_variable_report(
    samples: list[Sample],
    unit: str,
    expected_hours: int,
    day_start: time,
    night_start: time,
    scale: float,
) -> VariableReport:
    day, night = split_day_night(samples, day_start, night_start)
    grouped: dict[object, list[Sample]] = defaultdict(list)
    for sample in samples:
        grouped[sample.start.date()].append(sample)
    daily = tuple(
        DailySummary(day=key, summary=summarize(grouped[key]))  # type: ignore[arg-type]
        for key in sorted(grouped)
    )
    return VariableReport(
        unit=unit,
        overall=summarize(samples),
        daytime=summarize(day),
        nighttime=summarize(night),
        daily=daily,
        coverage=len(samples) / expected_hours if expected_hours else 0.0,
        scale=scale,
    )
