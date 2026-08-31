# Climate Report

Climate Report generates environmental reports from Home Assistant long-term
statistics for scheduled or manually selected date ranges.

## Current milestone

The Ingress UI generates reports, browses dated archives, sends Companion App
notifications and can test or send reports through SMTP. Keep `dry_run` enabled
while validating output; manual test buttons still perform the requested send.

## Example configuration

```yaml
timezone: Europe/Madrid
language: es
report_days: 7
day_start: "08:00"
night_start: "22:00"
comparison: same_iso_week
archive_reports: true
dry_run: true
push_notifier: notify.mobile_app_your_phone
home_assistant_url: https://your-instance.ui.nabu.casa
email_enabled: false
email_to: you@example.com
email_from: reports@example.com
smtp_host: smtp.example.com
smtp_port: 587
smtp_security: starttls
smtp_username: reports@example.com
smtp_password: ""
weather_entity: weather.home
rooms:
  - name: Living room
    temperature_entity: sensor.living_room_temperature
    humidity_entity: sensor.living_room_humidity
    exclude_from_summary: false
  - name: Water heater
    temperature_entity: sensor.water_heater_temperature
    exclude_from_summary: true
outdoor:
  temperature_entity: sensor.outdoor_temperature
  humidity_entity: sensor.outdoor_humidity
```

Entity IDs above are examples. Replace them with entities from your own Home
Assistant installation.

## Manual command

Once installed and running, send this payload through the Home Assistant
`hassio.addon_stdin` action:

```yaml
addon: local_climate_report
input:
  command: generate
```

Generate a historical period by supplying the exclusive end date. This example
reports the seven complete days ending before May 11:

```yaml
addon: local_climate_report
input:
  command: generate
  end_date: "2026-05-11"
```

Keep `dry_run: true` until the generated report and delivery settings have been
reviewed. With dry-run disabled, a configured email and push notification are
sent after successful generation.

## Data access

The app uses Home Assistant's internal API proxy and the automatically supplied
`SUPERVISOR_TOKEN`. It does not require a long-lived access token.

## Dashboard

The compact summary is available inside Ingress at `/summary`. The optional
Climate Report integration creates registered temperature, humidity, coverage,
year-over-year and last-report entities plus a generate button. The optional
`custom:climate-report-card` supports `compact`, `normal` and `detailed` modes.

```yaml
type: custom:climate-report-card
entity: sensor.climate_report_last_report
mode: normal
navigation_path: /app/9d838440_climate_report
```

## Persistent files

Generated files are stored under `reports/` in the app configuration mount:

- `latest.html`: latest full report.
- `latest-email.html`: latest email-safe summary.
- `latest.json`: machine-readable calculations.
- `climate-report-YYYY-MM-DD.html`: archived full report.

They are not committed to this repository.

When `archive_reports` is enabled, dated HTML files appear under **Reportes
archivados** in the app Web UI. Disabling it keeps only `latest.html` and
`latest.json`.

The push notifier must be the Home Assistant Companion action name, normally
`notify.mobile_app_<device>`. SMTP credentials remain in the private app options
and are not included in generated reports.
