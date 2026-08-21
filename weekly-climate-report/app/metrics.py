"""Deterministic calculations used by the report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from statistics import fmean
from typing import Iterable


@dataclass(frozen=True)
class Sample:
    start: datetime
    mean: float
    minimum: float
    maximum: float


@dataclass(frozen=True)
class Summary:
    mean: float
    minimum: float
    maximum: float
    samples: int


def summarize(samples: Iterable[Sample]) -> Summary | None:
    items = list(samples)
    if not items:
        return None
    return Summary(
        mean=fmean(item.mean for item in items),
        minimum=min(item.minimum for item in items),
        maximum=max(item.maximum for item in items),
        samples=len(items),
    )


def split_day_night(
    samples: Iterable[Sample], day_start: time, night_start: time
) -> tuple[list[Sample], list[Sample]]:
    day: list[Sample] = []
    night: list[Sample] = []
    for sample in samples:
        target = day if day_start <= sample.start.timetz().replace(tzinfo=None) < night_start else night
        target.append(sample)
    return day, night


def coverage(valid_samples: int, expected_samples: int) -> float:
    if expected_samples <= 0:
        raise ValueError("expected_samples must be positive")
    return valid_samples / expected_samples
