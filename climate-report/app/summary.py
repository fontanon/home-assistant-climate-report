"""Build and persist the dashboard-facing report summary."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import fmean
from typing import Any

from report import ClimateReport, RoomReport, VariableReport


SUMMARY_PATH = Path("/config/reports/latest-summary.json")


def build_summary(report: ClimateReport, report_path: str | None) -> dict[str, Any]:
    rooms = [room for room in report.rooms if room.include_in_summary]
    temperatures = [_mean(room.temperature) for room in rooms]
    humidities = [_mean(room.humidity) for room in rooms]
    temperatures = [value for value in temperatures if value is not None]
    humidities = [value for value in humidities if value is not None]
    peaks = [room.temperature.overall.maximum for room in rooms if room.temperature.overall]
    minimums = [room.temperature.overall.minimum for room in rooms if room.temperature.overall]
    temperature_deltas = [_delta(room.temperature, room.comparison_temperature) for room in rooms]
    humidity_deltas = [_delta(room.humidity, room.comparison_humidity) for room in rooms]
    temperature_deltas = [value for value in temperature_deltas if value is not None]
    humidity_deltas = [value for value in humidity_deltas if value is not None]
    return {
        "period": report.period_label,
        "comparison_period": report.comparison_label,
        "generated_at": report.generated_at,
        "mean_temperature": _average(temperatures),
        "mean_humidity": _average(humidities),
        "peak_temperature": max(peaks) if peaks else None,
        "minimum_temperature": min(minimums) if minimums else None,
        "temperature_year_delta": _average(temperature_deltas),
        "humidity_year_delta": _average(humidity_deltas),
        "coverage": _average([room.temperature.coverage for room in rooms]),
        "warnings": list(report.warnings),
        "included_rooms": len(rooms),
        "excluded_rooms": [room.name for room in report.rooms if not room.include_in_summary],
        "report_path": report_path,
    }


def save_summary(summary: dict[str, Any], path: Path = SUMMARY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def load_summary(path: Path = SUMMARY_PATH) -> dict[str, Any] | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _mean(variable: VariableReport | None) -> float | None:
    return variable.overall.mean if variable and variable.overall else None


def _delta(current: VariableReport | None, previous: VariableReport | None) -> float | None:
    current_mean = _mean(current)
    previous_mean = _mean(previous)
    return current_mean - previous_mean if current_mean is not None and previous_mean is not None else None


def _average(values: list[float]) -> float | None:
    return fmean(values) if values else None
