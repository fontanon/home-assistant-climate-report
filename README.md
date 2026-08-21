# Weekly Climate Report for Home Assistant

Generate a weekly temperature and humidity report from Home Assistant long-term
statistics. The project is designed as a community-shareable Home Assistant app
(formerly add-on).

> Early development preview. Do not use it yet for unattended delivery.

## Intended features

- Configurable rooms and indoor/outdoor sensors.
- Day and night summaries.
- Previous-year comparison.
- Local outdoor and weather-provider context.
- Data-quality checks and explicit coverage reporting.
- Responsive full report and email-safe summary.
- Persistent report archive.
- Manual and scheduled execution from Home Assistant.

## Privacy

The repository contains no entity IDs, reports, credentials, webhook URLs, or
measurements from a real home. Installation-specific configuration remains in
Home Assistant's private app options.

## Development status

The development version generates a complete archived report on demand from
long-term statistics. Email delivery and the final Home Assistant scheduling
workflow remain intentionally disabled until installation testing is complete.

See [`weekly-climate-report/DOCS.md`](weekly-climate-report/DOCS.md) for the
planned installation and configuration flow.
