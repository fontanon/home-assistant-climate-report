# Weekly Climate Report

This development preview generates weekly environmental reports from Home
Assistant long-term statistics.

## Current milestone

The app generates and archives complete HTML reports. It intentionally does not
send email yet; keep `dry_run` enabled while validating output.

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
notifier: ""
weather_entity: weather.home
rooms:
  - name: Living room
    temperature_entity: sensor.living_room_temperature
    humidity_entity: sensor.living_room_humidity
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
addon: local_weekly_climate_report
input:
  command: generate
```

Generate a historical period by supplying the exclusive end date. This example
reports the seven complete days ending before May 11:

```yaml
addon: local_weekly_climate_report
input:
  command: generate
  end_date: "2026-05-11"
```

Keep `dry_run: true` until the generated report has been reviewed.

## Data access

The app uses Home Assistant's internal API proxy and the automatically supplied
`SUPERVISOR_TOKEN`. It does not require a long-lived access token.

## Persistent files

Generated files are stored under `reports/` in the app configuration mount:

- `latest.html`: latest full report.
- `latest-email.html`: latest email-safe summary.
- `latest.json`: machine-readable calculations.
- `weekly-climate-report-YYYY-MM-DD.html`: archived full report.

They are not committed to this repository.
