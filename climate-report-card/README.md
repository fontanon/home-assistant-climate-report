# Climate Report Card

Lovelace summary card for Climate Report. It displays mean temperature and
humidity, coverage, warnings and year-over-year deltas, then navigates to the
latest report through Home Assistant Ingress.

```yaml
type: custom:climate-report-card
entity: sensor.climate_report_last_report
mode: normal
navigation_path: /app/9d838440_climate_report
```

`mode` can be `compact`, `normal` or `detailed`.
