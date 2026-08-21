"""Persist generated reports and machine-readable snapshots."""

from __future__ import annotations

import json
from pathlib import Path

from report import ClimateReport


DEFAULT_REPORT_DIR = Path("/config/reports")


def save_report(
    report: ClimateReport,
    html: str,
    *,
    report_dir: Path = DEFAULT_REPORT_DIR,
    archive: bool = True,
) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    start = report.period_label.split(" ", 1)[0]
    target = report_dir / (f"weekly-climate-report-{start}.html" if archive else "latest.html")
    target.write_text(html, encoding="utf-8")
    (report_dir / "latest.html").write_text(html, encoding="utf-8")
    (report_dir / "latest.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return target
