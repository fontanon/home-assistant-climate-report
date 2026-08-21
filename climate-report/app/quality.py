"""Quality rules for environmental measurements."""

from __future__ import annotations

from dataclasses import dataclass


SENTINELS = {327.67}


@dataclass(frozen=True)
class ValidatedValue:
    value: float | None
    reason: str | None = None


def validate_temperature(value: object, *, outdoor: bool = False) -> ValidatedValue:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ValidatedValue(None, "not_numeric")
    if number in SENTINELS:
        return ValidatedValue(None, "sentinel")
    lower, upper = (-20.0, 55.0) if outdoor else (-10.0, 50.0)
    if not lower <= number <= upper:
        return ValidatedValue(None, "outside_plausible_range")
    return ValidatedValue(number)


def humidity_scale(values: list[float]) -> float:
    """Return 100 only when a complete non-empty series is unambiguously 0..1."""
    if values and all(0.0 <= value <= 1.0 for value in values):
        return 100.0
    return 1.0


def validate_humidity(value: object, *, scale: float = 1.0) -> ValidatedValue:
    try:
        number = float(value) * scale
    except (TypeError, ValueError):
        return ValidatedValue(None, "not_numeric")
    if not 0.0 <= number <= 100.0:
        return ValidatedValue(None, "outside_plausible_range")
    return ValidatedValue(number)
