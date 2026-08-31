"""Render responsive and email-safe reports without external dependencies."""

from __future__ import annotations

from html import escape
from pathlib import Path
from statistics import fmean
from string import Template

from report import ClimateReport, RoomReport, VariableReport


TEMPLATE_DIR = Path("/opt/climate-report/templates")


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
        "no_temperature": "Sin datos de temperatura",
        "excluded": "Fuera del resumen general",
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
        "no_temperature": "No temperature data",
        "excluded": "Excluded from home summary",
    },
}


def render_full_report(
    report: ClimateReport,
    language: str,
    *,
    template_dir: Path = TEMPLATE_DIR,
) -> str:
    text = COPY.get(language, COPY["en"])
    summary_rooms = [room for room in report.rooms if room.include_in_summary]
    valid_temps = [room.temperature.overall.mean for room in summary_rooms if room.temperature.overall]
    valid_humidity = [
        room.humidity.overall.mean
        for room in summary_rooms
        if room.humidity and room.humidity.overall
    ]
    indoor_mean = fmean(valid_temps) if valid_temps else None
    indoor_humidity = fmean(valid_humidity) if valid_humidity else None
    peak_room = max(
        (room for room in summary_rooms if room.temperature.overall),
        key=lambda item: item.temperature.overall.maximum,  # type: ignore[union-attr]
        default=None,
    )
    coverage = fmean(room.temperature.coverage for room in summary_rooms) if summary_rooms else 0
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
    report_url: str | None = None,
) -> str:
    text = COPY.get(language, COPY["en"])
    summary_rooms = [room for room in report.rooms if room.include_in_summary]
    valid_temps = [room.temperature.overall.mean for room in summary_rooms if room.temperature.overall]
    valid_humidity = [room.humidity.overall.mean for room in summary_rooms if room.humidity and room.humidity.overall]
    indoor_mean = fmean(valid_temps) if valid_temps else None
    indoor_humidity = fmean(valid_humidity) if valid_humidity else None
    coverage = fmean(room.temperature.coverage for room in summary_rooms) if summary_rooms else 0
    outdoor = report.outdoor_temperature.overall
    lead = _lead(report, indoor_mean, outdoor.mean if outdoor else None, language)
    peak = max(
        (room for room in summary_rooms if room.temperature.overall),
        key=lambda room: room.temperature.overall.maximum,  # type: ignore[union-attr]
        default=None,
    )
    kpis = "".join([
        _email_kpi(text["mean"], _fmt(indoor_mean, "°C")),
        _email_kpi("Pico", _fmt(peak.temperature.overall.maximum if peak else None, "°C")),
        _email_kpi(text["humidity"], _fmt(indoor_humidity, "%", 0)),
        _email_kpi(text["coverage"], f"{coverage:.0%}"),
    ])
    rooms = "".join(_email_room_card(room, text) for room in report.rooms)
    outdoor_card = f"""
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #dfe4dc;border-radius:16px;background:#fffdf8">
        <tr>{_email_stat(text['day'], _fmt_summary(report.outdoor_temperature.daytime))}{_email_stat(text['night'], _fmt_summary(report.outdoor_temperature.nighttime))}{_email_stat(text['humidity'], _fmt(_mean(report.outdoor_humidity), '%', 0))}{_email_stat(text['coverage'], f'{report.outdoor_temperature.coverage:.0%}')}</tr>
      </table>"""
    summary = f"""
      <p style="margin:0;color:#226454;font-size:11px;font-weight:bold;letter-spacing:1.5px;text-transform:uppercase">{escape(text['summary'])}</p>
      <h1 style="margin:8px 0 4px;color:#17322d;font-family:Georgia,serif;font-size:48px;font-weight:normal;line-height:1">{escape(text['title'])}</h1>
      <p style="margin:0 0 24px;color:#64746f;font-size:16px">{escape(report.period_label)}</p>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:14px;border-radius:18px;background:#226454;color:#ffffff">
        <tr><td style="padding:26px"><p style="margin:0;font-family:Georgia,serif;font-size:23px;line-height:1.35">{escape(lead)}</p></td><td width="180" align="center" style="padding:20px;border-left:1px solid #ffffff33"><b style="font-family:Georgia,serif;font-size:34px">{_fmt(indoor_mean, '°C')}</b></td></tr>
      </table>
      <table role="presentation" width="100%" cellspacing="8" cellpadding="0" style="margin-bottom:28px"><tr>{kpis}</tr></table>
      <p style="margin:0 0 10px;color:#226454;font-size:11px;font-weight:bold;letter-spacing:1.3px;text-transform:uppercase">{escape(text['outside'])}</p>
      {outdoor_card}
      <h2 style="margin:32px 0 14px;color:#17322d;font-family:Georgia,serif;font-size:30px;font-weight:normal">{escape(text['rooms'])}</h2>
      {rooms}
      <div style="margin-top:24px;padding:20px;border:1px solid #dfe4dc;border-radius:16px;background:#fffdf8;color:#64746f;font-size:12px"><b style="color:#17322d">{escape(text['quality'])}</b><br>{'<br>'.join(escape(item) for item in report.warnings) or 'Sin avisos'}<br>{escape(text['comparison'])}: {escape(report.comparison_label or text['no_comparison'])}</div>
      {f'<p style="margin:28px 0;text-align:center"><a href="{escape(report_url)}" style="display:inline-block;padding:14px 22px;border-radius:10px;background:#226454;color:#ffffff;font-weight:bold;text-decoration:none">Abrir último reporte en Home Assistant</a></p>' if report_url else ''}
    """
    template = Template((template_dir / "email.html").read_text(encoding="utf-8"))
    return template.safe_substitute(language=language, title=text["title"], summary=summary)


def _email_kpi(label: str, value: str) -> str:
    return f"<td width='25%' style='padding:14px;border:1px solid #dfe4dc;border-radius:12px;background:#fffdf8'><span style='display:block;color:#64746f;font-size:9px;text-transform:uppercase'>{escape(label)}</span><b style='display:block;margin-top:7px;color:#17322d;font-family:Georgia,serif;font-size:22px'>{escape(value)}</b></td>"


def _email_stat(label: str, value: str) -> str:
    return f"<td width='25%' style='padding:14px;border-right:1px solid #dfe4dc'><span style='display:block;color:#64746f;font-size:9px;text-transform:uppercase'>{escape(label)}</span><b style='display:block;margin-top:6px;color:#17322d;font-size:12px'>{escape(value)}</b></td>"


def _email_room_card(room: RoomReport, text: dict[str, str]) -> str:
    temperature = room.temperature
    humidity = room.humidity
    comparison_delta = None
    if temperature.overall and room.comparison_temperature and room.comparison_temperature.overall:
        comparison_delta = temperature.overall.mean - room.comparison_temperature.overall.mean
    humidity_delta = None
    if humidity and humidity.overall and room.comparison_humidity and room.comparison_humidity.overall:
        humidity_delta = humidity.overall.mean - room.comparison_humidity.overall.mean
    temperature_value = _fmt(_mean(temperature), "°C") if temperature.overall else text["no_temperature"]
    humidity_value = _fmt(_mean(humidity), "%", 0) if humidity else text["no_humidity"]
    daily = _email_daily_row(temperature, humidity)
    return f"""
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:16px;border:1px solid #dfe4dc;border-radius:16px;background:#fffdf8">
        <tr><td width="210" valign="top" style="padding:20px;background:#edf3ed"><span style="color:#64746f;font-size:9px">Temp. {temperature.coverage:.0%}{f' · Hum. {humidity.coverage:.0%}' if humidity else ''}{f' · {escape(text["excluded"])}' if not room.include_in_summary else ''}</span><h3 style="margin:6px 0;color:#17322d;font-family:Georgia,serif;font-size:25px;font-weight:normal">{escape(room.name)}</h3><b style="color:#17322d;font-family:Georgia,serif;font-size:27px;font-weight:normal">{escape(temperature_value)}</b><p style="margin:7px 0 0;color:#397e91;font-size:12px">{escape(text['humidity'])}: {escape(humidity_value)}</p></td>
        <td valign="top" style="padding:18px"><div style="margin-bottom:12px;color:#226454;font-family:monospace;font-size:18px;letter-spacing:2px">Temp. {_email_sparkline(temperature)}</div>{f'<div style="margin-bottom:12px;color:#397e91;font-family:monospace;font-size:18px;letter-spacing:2px">Hum. {_email_sparkline(humidity)}</div>' if humidity else ''}<table role="presentation" width="100%" cellspacing="4" cellpadding="0"><tr>{_email_stat(text['day'], _fmt_summary(temperature.daytime))}{_email_stat(text['night'], _fmt_summary(temperature.nighttime))}{_email_stat(text['comparison'], text['no_comparison'] if comparison_delta is None else f'{comparison_delta:+.1f} °C')}</tr>{f'<tr>{_email_stat("Hum. día", _fmt_summary_unit(humidity.daytime, "%", 0))}{_email_stat("Hum. noche", _fmt_summary_unit(humidity.nighttime, "%", 0))}{_email_stat("Hum. comp.", text["no_comparison"] if humidity_delta is None else f"{humidity_delta:+.0f} pp")}</tr>' if humidity and humidity.overall else ''}</table></td></tr>
        <tr><td colspan="2" style="padding:10px 14px;border-top:1px solid #dfe4dc">{daily}</td></tr>
      </table>"""


def _email_daily_row(temperature: VariableReport, humidity: VariableReport | None) -> str:
    temperatures = {item.day: item.summary for item in temperature.daily}
    humidities = {item.day: item.summary for item in humidity.daily} if humidity else {}
    days = sorted(set(temperatures) | set(humidities))
    if not days:
        return ""
    width = max(1, 100 // len(days))
    cells = "".join(
        f"<td width='{width}%' style='padding:6px;border-right:1px solid #dfe4dc'><span style='display:block;color:#64746f;font-size:8px'>{day.strftime('%a %d')}</span><b style='display:block;color:#17322d;font-size:13px'>{_fmt(temperatures[day].mean if day in temperatures else None, '°C')}</b><small style='color:#397e91'>{_fmt(humidities[day].mean if day in humidities else None, '%', 0)}</small></td>"
        for day in days
    )
    return f"<table role='presentation' width='100%' cellspacing='0' cellpadding='0'><tr>{cells}</tr></table>"


def _email_sparkline(variable: VariableReport | None) -> str:
    if not variable or len(variable.daily) < 2:
        return "—"
    values = [item.summary.mean for item in variable.daily]
    low, high = min(values), max(values)
    span = high - low or 1.0
    blocks = "▁▂▃▄▅▆▇█"
    return "".join(blocks[min(7, round((value - low) / span * 7))] for value in values)


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
    temperature_text = _fmt(_mean(temperature), "°C") if temperature.overall else text["no_temperature"]
    humidity_coverage = f" · {escape(text['humidity'])} {humidity.coverage:.0%}" if humidity and humidity.overall else ""
    humidity_delta = None
    if humidity and humidity.overall and room.comparison_humidity and room.comparison_humidity.overall:
        humidity_delta = humidity.overall.mean - room.comparison_humidity.overall.mean
    humidity_stats = ""
    if humidity and humidity.overall:
        humidity_stats = f"""
          <div class="humidity-ranges">
            <div><span>{escape(text['humidity'])} · {escape(text['day'])}</span><b>{_fmt_summary_unit(humidity.daytime, '%', 0)}</b></div>
            <div><span>{escape(text['humidity'])} · {escape(text['night'])}</span><b>{_fmt_summary_unit(humidity.nighttime, '%', 0)}</b></div>
            <div><span>{escape(text['humidity'])} · {escape(text['comparison'])}</span><b>{text['no_comparison'] if humidity_delta is None else f'{humidity_delta:+.0f} pp'}</b></div>
          </div>"""
    return f"""
      <article class="room card">
        <div class="room-intro"><span class="tag">Temp. {temperature.coverage:.0%}{humidity_coverage}</span>{f'<span class="tag">{escape(text["excluded"])}</span>' if not room.include_in_summary else ''}<h3>{escape(room.name)}</h3><div class="main-value">{escape(temperature_text)}</div><p>{escape(text['humidity'])}: {escape(humidity_text)}</p></div>
        <div class="room-body">{_sparkline(temperature, humidity, text)}<div class="ranges"><div><span>{escape(text['day'])}</span><b>{_fmt_summary(day)}</b></div><div><span>{escape(text['night'])}</span><b>{_fmt_summary(night)}</b></div><div><span>{escape(text['comparison'])}</span><b>{escape(delta_text)}</b></div></div>{humidity_stats}</div>
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
    temperature_by_day = {item.day: item.summary for item in temperature.daily}
    humidity_by_day = {item.day: item.summary for item in humidity.daily} if humidity else {}
    cells = []
    for day in sorted(set(temperature_by_day) | set(humidity_by_day)):
        temperature_summary = temperature_by_day.get(day)
        humidity_summary = humidity_by_day.get(day)
        cells.append(
            f"<td><span>{day.strftime('%a %d')}</span><b>{_fmt(temperature_summary.mean if temperature_summary else None, '°C')}</b>"
            f"<small>{_fmt_range(temperature_summary)} · {_fmt(humidity_summary.mean if humidity_summary else None, '%', 0)}</small></td>"
        )
    return f"<table class='daily'><tr>{''.join(cells)}</tr></table>"


def _sparkline(temperature: VariableReport, humidity: VariableReport | None, text: dict[str, str]) -> str:
    temperature_values = {item.day: item.summary.mean for item in temperature.daily}
    humidity_values = {item.day: item.summary.mean for item in humidity.daily} if humidity else {}
    days = sorted(set(temperature_values) | set(humidity_values))
    if len(days) < 2:
        return ""
    temperature_chart = _series_chart(days, temperature_values, "°C", "temperature", "left")
    humidity_chart = _series_chart(days, humidity_values, "%", "humidity", "right")
    lines = temperature_chart + humidity_chart
    legend = "<div class='chart-legend'>"
    if temperature_chart:
        legend += "<span class='temperature-key'>Temperatura</span>"
    if humidity_chart:
        legend += f"<span class='humidity-key'>{escape(text['humidity'])}</span>"
    legend += "</div>"
    return f"<div class='chart'>{legend}<svg viewBox='0 0 340 100' role='img' aria-label='Daily temperature and humidity means'><line x1='34' y1='76' x2='306' y2='76'/>{lines}</svg></div>"


def _series_chart(
    days: list[object],
    values: dict[object, float],
    unit: str,
    css_class: str,
    axis: str,
) -> str:
    present = list(values.values())
    if len(present) < 2:
        return ""
    low, high = min(present), max(present)
    span = high - low or 1.0
    points: list[tuple[float, float, float]] = []
    for index, day in enumerate(days):
        if day not in values:
            continue
        x = 34 + index * (272 / (len(days) - 1))
        y = 76 - ((values[day] - low) / span) * 54
        points.append((x, y, values[day]))
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points)
    label_offset = -7 if css_class == "temperature" else 12
    digits = 1 if unit == "°C" else 0
    vertices = "".join(
        f"<circle class='chart-point {css_class}' cx='{x:.1f}' cy='{y:.1f}' r='2.2'/>"
        f"<text class='chart-label {css_class}' x='{x:.1f}' y='{y + label_offset:.1f}' text-anchor='middle'>{value:.{digits}f}{unit}</text>"
        for x, y, value in points
    )
    axis_x = 30 if axis == "left" else 310
    anchor = "end" if axis == "left" else "start"
    extrema = (
        f"<text class='axis-label {css_class}' x='{axis_x}' y='25' text-anchor='{anchor}'>{high:.{digits}f}{unit}</text>"
        f"<text class='axis-label {css_class}' x='{axis_x}' y='78' text-anchor='{anchor}'>{low:.{digits}f}{unit}</text>"
    )
    return f"<polyline class='{css_class}-line' points='{polyline}'/>{vertices}{extrema}"


def _fmt_range(summary: object) -> str:
    if summary is None:
        return "—"
    return f"{summary.minimum:.1f}–{summary.maximum:.1f} °C"


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


def _fmt_summary_unit(summary: object, unit: str, digits: int = 1) -> str:
    if summary is None:
        return "—"
    return f"{summary.mean:.{digits}f} {unit} · {summary.minimum:.{digits}f}–{summary.maximum:.{digits}f} {unit}"
