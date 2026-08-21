"""Serializable report model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any

from metrics import Summary


@dataclass(frozen=True)
class DailySummary:
    day: date
    summary: Summary


@dataclass(frozen=True)
class VariableReport:
    unit: str
    overall: Summary | None
    daytime: Summary | None
    nighttime: Summary | None
    daily: tuple[DailySummary, ...]
    coverage: float
    scale: float = 1.0


@dataclass(frozen=True)
class RoomReport:
    name: str
    temperature: VariableReport
    humidity: VariableReport | None
    comparison_temperature: VariableReport | None = None
    comparison_humidity: VariableReport | None = None


@dataclass(frozen=True)
class ClimateReport:
    generated_at: str
    period_label: str
    comparison_label: str | None
    rooms: tuple[RoomReport, ...]
    outdoor_temperature: VariableReport
    outdoor_humidity: VariableReport | None
    comparison_outdoor_temperature: VariableReport | None
    comparison_outdoor_humidity: VariableReport | None
    forecast: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
