"""Long-running stdin command loop for the Home Assistant app."""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from datetime import date, datetime, timedelta
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse
from pathlib import Path
from zoneinfo import ZoneInfo

from archive import DEFAULT_REPORT_DIR, save_report
from config import load_settings
from extract import build_report
from home_assistant import HomeAssistantClient
from periods import resolve_periods
from render import render_email_report, render_full_report


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("climate_report")
GENERATE_LOCK = threading.Lock()


def _viewer_page(message: str = "") -> bytes:
    today = date.today()
    start = today - timedelta(days=7)
    notice = f'<p class="notice">{escape(message)}</p>' if message else ""
    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Climate Report</title><style>
body{{margin:0;background:#f4f1e9;color:#17322d;font-family:system-ui,sans-serif}}main{{width:min(1120px,calc(100% - 32px));margin:32px auto}}h1{{font:500 42px Georgia,serif;margin-bottom:8px}}p{{color:#64746f}}form{{display:flex;flex-wrap:wrap;gap:14px;align-items:end;padding:20px;background:#fffdf8;border-radius:18px;box-shadow:0 10px 30px #17322d14}}label{{display:grid;gap:6px;font-size:13px;font-weight:700}}input,button{{font:inherit;padding:10px 12px;border:1px solid #dfe4dc;border-radius:10px}}button{{border-color:#226454;background:#226454;color:white;font-weight:700;cursor:pointer}}.notice{{padding:12px 16px;border-radius:10px;background:#e6f2ec;color:#174b3f}}iframe{{display:block;width:100%;height:600px;margin-top:22px;border:0;border-radius:18px;background:white;overflow:hidden}}
</style></head><body><main><h1>Climate Report</h1><p>Genera un informe manual para cualquier periodo de hasta 366 días.</p>{notice}
<form method="post" action="generate"><label>Fecha inicial<input required type="date" name="start_date" value="{start.isoformat()}"></label><label>Fecha final (incluida)<input required type="date" name="end_date" value="{(today - timedelta(days=1)).isoformat()}"></label><button type="submit">Generar reporte</button></form>
<iframe id="report" src="report" scrolling="no" title="Último reporte"></iframe></main><script>
const frame=document.getElementById('report');
function fitReport(){{try{{frame.style.height=frame.contentDocument.documentElement.scrollHeight+'px'}}catch(error){{}}}}
frame.addEventListener('load',()=>{{fitReport();try{{new ResizeObserver(fitReport).observe(frame.contentDocument.documentElement)}}catch(error){{}}}});
</script></body></html>"""
    return html.encode("utf-8")


class ReportHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") in ("", "/"):
            message = parse_qs(parsed.query).get("message", [""])[0]
            self._send_html(_viewer_page(message))
            return
        if parsed.path.rstrip("/") != "/report":
            self.send_error(404)
            return
        target = DEFAULT_REPORT_DIR / "latest.html"
        if not target.is_file():
            self.send_error(404, "No report has been generated yet")
            return
        self._send_html(target.read_bytes())

    def do_POST(self) -> None:
        if urlparse(self.path).path.rstrip("/") != "/generate":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 4096:
                raise ValueError("Formulario no válido")
            values = parse_qs(self.rfile.read(length).decode("utf-8"))
            start = date.fromisoformat(values["start_date"][0])
            final = date.fromisoformat(values["end_date"][0])
            days = (final - start).days + 1
            if not 1 <= days <= 366:
                raise ValueError("El periodo debe contener entre 1 y 366 días")
            if not GENERATE_LOCK.acquire(blocking=False):
                raise ValueError("Ya hay un reporte en generación")
            try:
                generate({
                    "start_date": start.isoformat(),
                    "end_date_inclusive": final.isoformat(),
                })
            finally:
                GENERATE_LOCK.release()
            message = f"Reporte generado: {start.isoformat()} – {final.isoformat()}"
        except (KeyError, IndexError, UnicodeDecodeError, ValueError) as error:
            message = f"No se pudo generar: {error}"
        self.send_response(303)
        self.send_header("Location", f"./?message={quote(message)}")
        self.end_headers()

    def _send_html(self, payload: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, message: str, *args: object) -> None:
        LOGGER.info("Ingress: " + message, *args)


def start_report_server() -> None:
    port = int(os.environ.get("REPORT_HTTP_PORT", "8099"))
    server = ThreadingHTTPServer(("0.0.0.0", port), ReportHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    LOGGER.info("Report viewer listening on port %d", port)


def generate(command: dict[str, object] | None = None) -> Path:
    command = command or {}
    settings = load_settings()
    LOGGER.info(
        "Configuration valid: %d room(s), %d report day(s), dry_run=%s",
        len(settings.rooms),
        settings.report_days,
        settings.dry_run,
    )
    requested_end = command.get("end_date")
    requested_end_inclusive = command.get("end_date_inclusive")
    if requested_end and requested_end_inclusive:
        raise ValueError("Use end_date or end_date_inclusive, not both")
    end_date = date.fromisoformat(str(requested_end)) if requested_end else None
    if requested_end_inclusive:
        end_date = date.fromisoformat(str(requested_end_inclusive)) + timedelta(days=1)
    requested_start = command.get("start_date")
    start_date = date.fromisoformat(str(requested_start)) if requested_start else None
    zone = ZoneInfo(settings.timezone)
    generated_at = datetime.now(zone)
    periods = resolve_periods(
        settings.timezone,
        settings.report_days,
        settings.comparison,
        now=generated_at,
        start_date=start_date,
        end_date=end_date,
    )
    LOGGER.info("Collecting statistics for %s", periods.current.label)
    report = build_report(
        HomeAssistantClient(), settings, periods, generated_at=generated_at
    )
    html = render_full_report(report, settings.language)
    email_html = render_email_report(report, settings.language)
    target = save_report(report, html, archive=settings.archive_reports)
    email_target = DEFAULT_REPORT_DIR / "latest-email.html"
    email_target.write_text(email_html, encoding="utf-8")
    LOGGER.info("Report written to %s", target)
    if settings.dry_run:
        LOGGER.info("Dry-run enabled; email delivery skipped")
    else:
        LOGGER.warning("Email delivery is not enabled in this milestone; report was archived only")
    return target


def main() -> int:
    start_report_server()
    LOGGER.info("Climate Report is ready; waiting for stdin commands")
    for line in sys.stdin:
        try:
            command = json.loads(line)
            if isinstance(command, str):
                command = json.loads(command)
            if not isinstance(command, dict):
                raise ValueError("Command must be a JSON object")
            if command.get("command") != "generate":
                LOGGER.warning("Ignoring unsupported command: %s", command.get("command"))
                continue
            generate(command)
        except Exception:
            LOGGER.exception("Report command failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
