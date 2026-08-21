"""Render responsive and email-safe reports without external dependencies."""

from __future__ import annotations

from html import escape
from pathlib import Path
from statistics import fmean
from string import Template

from report import ClimateReport, RoomReport, VariableReport


TEMPLATE_DIR = Path("/opt/weekly-climate-report/templates")


COPY = {
    "es": {
        "title": "Clima en casa",
        "summary": "Resumen semanal",
        "rooms": "Habitación a habitación",
        "outside": "Referencia exterior",
        "quality": "Calidad del dato",
        "day": "Día",
        "night": "Noche",
        "mean": "Media",
        "range": "Rango",
        "humidity": "Humedad",
        "coverage": "Cobertura",
        "comparison": "Comparación interanual",
        "no_humidity": "Sin sensor de humedad",
        "no_comparison": "Sin datos comparables",
        "generated": "Generado",
    },
    "en": {
        "title": "Home climate",
        "summary": "Weekly summary",
        "rooms": "Room by room",
        "outside": "Outdoor reference",
        "quality": "Data quality",
        "day": "Day",
        "night": "Night",
        "mean": "Mean",
        "range": "Range",
        "humidity": "Humidity",
        "coverage": "Coverage",
        "comparison": "Year-over-year comparison",
        "no_humidity": "No humidity sensor",
        "no_comparison": "No comparable data",
        "generated": "Generated",
    },
}


def render_full_report(
    report: ClimateReport,
    language: str,
    *,
    template_dir: Path = TEMPLATE_DIR,
) -> str:
    text = COPY.get(language, COPY["en"])
    valid_temps = [room.temperature.overall.mean for room in report.rooms if room.temperature.overall]
    valid_humidity = [
        room.humidity.overall.mean
        for room in report.rooms
        if room.humidity and room.humidity.overall
    ]
    indoor_mean = fmean(valid_temps) if valid_temps else None
    indoor_humidity = fmean(valid_humidity) if valid_humidity else None
    peak_room = max(
        (room for room in report.rooms if room.temperature.overall),
        key=lambda item: item.temperature.overall.maximum,  # type: ignore[union-attr]
        default=None,
    )
    coverage = fmean(room.temperature.coverage for room in report.rooms) if report.rooms else 0
    outdoor = report.outdoor_temperature.overall

    lead = _lead(report, indoor_mean, outdoor.mean if outdoor else None, language)
    kpis = "".join(
        [
            _kpi(text["mean"], _fmt(indoor_mean, "°C"), f"{len(valid_temps)} rooms"),
            _kpi("Peak", _fmt(peak_room.temperature.overall.maximum if peak_room else None, "°C"), peak_room.name if peak_room else "—"),
            _kpi(text["humidity"], _fmt(indoor_humidity, "%", 0), f"{len(valid_humidity)} rooms"),
            _kpi(text["coverage"], f"{coverage:.0%}", f"{report.period_label}"),
        ]
    )
    room_cards = "".join(_room_card(room, text) for room in report.rooms)
    warnings = "".join(f"<li>{escape(item)}</li>" for item in report.warnings) or "<li>No warnings</li>"
    body = f"""
      <header><div class="eyebrow">{escape(text['summary'])}</div><h1>{escape(text['title'])}</h1><p class="subtitle">{escape(report.period_label)}</p><div class="meta"><span>Home Assistant</span><span>{coverage:.0%} {escape(text['coverage'].lower())}</span><span>{escape(text['generated'])}: {escape(report.generated_at)}</span></div></header>
      <section class="hero card"><div><div class="eyebrow">{escape(text['summary'])}</div><p>{escape(lead)}</p></div><aside><b>{_fmt(indoor_mean, '°C')}</b><span>{escape(text['mean'])}</span></aside></section>
      <section class="kpis">{kpis}</section>
      <section><div class="section-head"><div class="eyebrow">{escape(text['outside'])}</div><h2>{escape(text['outside'])}</h2></div>{_outdoor_card(report, text)}</section>
      <section><div class="section-head"><div class="eyebrow">{escape(text['rooms'])}</div><h2>{escape(text['rooms'])}</h2></div><div class="rooms">{room_cards}</div></section>
      <section class="card quality"><h2>{escape(text['quality'])}</h2><ul>{warnings}</ul><p>{escape(text['comparison'])}: {escape(report.comparison_label or text['no_comparison'])}</p></section>
    """
    template = Template((template_dir / "report.html").read_text(encoding="utf-8"))
    return template.safe_substitute(language=language, title=text["title"], body=body)


def render_email_report(
    report: ClimateReport,
    language: str,
    *,
    template_dir: Path = TEMPLATE_DIR,
) -> str:
    text = COPY.get(language, COPY["en"])
    rows = []
    for room in report.rooms:
        rows.append(
            "<tr>"
            f"<td style='padding:10px;border-bottom:1px solid #dfe4dc'><b>{escape(room.name)}</b></td>"
            f"<td style='padding:10px;border-bottom:1px solid #dfe4dc'>{_fmt(_mean(room.temperature), '°C')}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #dfe4dc'>{_fmt(_mean(room.humidity), '%', 0)}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #dfe4dc'>{room.temperature.coverage:.0%}</td>"
            "</tr>"
        )
    summary = f"""
      <p style="font-size:17px;color:#63736f">{escape(report.period_label)}</p>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
        <tr><th align="left">Room</th><th align="left">Temperature</th><th align="left">Humidity</th><th align="left">Coverage</th></tr>
        {''.join(rows)}
      </table>
    """
    template = Template((template_dir / "email.html").read_text(encoding="utf-8"))
    return template.safe_substitute(language=language, title=text["title"], summary=summary)


def _room_card(room: RoomReport, text: dict[str, str]) -> str:
    temperature = room.temperature
    humidity = room.humidity
    day = temperature.daytime
    night = temperature.nighttime
    comparison = room.comparison_temperature
    delta = None
    if temperature.overall and comparison and comparison.overall:
        delta = temperature.overall.mean - comparison.overall.mean
    delta_text = text["no_comparison"] if delta is None else f"{delta:+.1f} °C"
    humidity_text = _fmt(_mean(humidity), "%", 0) if humidity else text["no_humidity"]
    return f"""
      <article class="room card">
        <div class="room-intro"><span class="tag">{temperature.coverage:.0%} {escape(text['coverage'].lower())}</span><h3>{escape(room.name)}</h3><div class="main-value">{_fmt(_mean(temperature), '°C')}</div><p>{escape(text['humidity'])}: {escape(humidity_text)}</p></div>
        <div class="room-body">{_sparkline(temperature)}<div class="ranges"><div><span>{escape(text['day'])}</span><b>{_fmt_summary(day)}</b></div><div><span>{escape(text['night'])}</span><b>{_fmt_summary(night)}</b></div><div><span>{escape(text['comparison'])}</span><b>{escape(delta_text)}</b></div></div></div>
        <div class="daily-wrap">{_daily_table(temperature, humidity)}</div>
      </article>
    """


def _outdoor_card(report: ClimateReport, text: dict[str, str]) -> str:
    temperature = report.outdoor_temperature
    humidity = report.outdoor_humidity
    return f"""
      <article class="outdoor card"><div><span>{escape(text['day'])}</span><b>{_fmt_summary(temperature.daytime)}</b></div><div><span>{escape(text['night'])}</span><b>{_fmt_summary(temperature.nighttime)}</b></div><div><span>{escape(text['humidity'])}</span><b>{_fmt(_mean(humidity), '%', 0)}</b></div><div><span>{escape(text['coverage'])}</span><b>{temperature.coverage:.0%}</b></div></article>
    """


def _daily_table(temperature: VariableReport, humidity: VariableReport | None) -> str:
    humidity_by_day = {item.day: item.summary for item in humidity.daily} if humidity else {}
    cells = []
    for item in temperature.daily:
        humidity_summary = humidity_by_day.get(item.day)
        cells.append(
            f"<td><span>{item.day.strftime('%a %d')}</span><b>{item.summary.mean:.1f}°</b>"
            f"<small>{item.summary.minimum:.1f}–{item.summary.maximum:.1f}° · {_fmt(humidity_summary.mean if humidity_summary else None, '%', 0)}</small></td>"
        )
    return f"<table class='daily'><tr>{''.join(cells)}</tr></table>"


def _sparkline(variable: VariableReport) -> str:
    values = [item.summary.mean for item in variable.daily]
    if len(values) < 2:
        return ""
    low, high = min(values), max(values)
    span = high - low or 1.0
    points = []
    for index, value in enumerate(values):
        x = 10 + index * (280 / (len(values) - 1))
        y = 65 - ((value - low) / span) * 48
        points.append(f"{x:.1f},{y:.1f}")
    return f"<svg viewBox='0 0 300 80' role='img' aria-label='Daily means'><line x1='10' y1='65' x2='290' y2='65'/><polyline points='{' '.join(points)}'/></svg>"


def _kpi(label: str, value: str, foot: str) -> str:
    return f"<article class='kpi card'><span>{escape(label)}</span><b>{escape(value)}</b><small>{escape(foot)}</small></article>"


def _lead(report: ClimateReport, indoor: float | None, outdoor: float | None, language: str) -> str:
    if indoor is None:
        return "No indoor data available." if language == "en" else "No hay datos interiores suficientes."
    difference = indoor - outdoor if outdoor is not None else None
    if language == "en":
        result = f"Indoor rooms averaged {indoor:.1f} °C."
        return result + (f" They were {abs(difference):.1f} °C {'warmer' if difference >= 0 else 'cooler'} than outdoors." if difference is not None else "")
    result = f"Las habitaciones registraron una media de {indoor:.1f} °C."
    return result + (f" Estuvieron {abs(difference):.1f} °C más {'cálidas' if difference >= 0 else 'frescas'} que el exterior." if difference is not None else "")


def _mean(variable: VariableReport | None) -> float | None:
    return variable.overall.mean if variable and variable.overall else None


def _fmt(value: float | None, unit: str, digits: int = 1) -> str:
    return "—" if value is None else f"{value:.{digits}f} {unit}"


def _fmt_summary(summary: object) -> str:
    if summary is None:
        return "—"
    return f"{summary.mean:.1f} °C · {summary.minimum:.1f}–{summary.maximum:.1f} °C"
