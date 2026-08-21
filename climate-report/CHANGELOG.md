# Changelog

## 0.2.0-dev

- Generate complete weekly reports on demand.
- Query current and comparison periods through `recorder.get_statistics`.
- Normalize humidity scale and reject invalid environmental measurements.
- Calculate overall, day, night and daily summaries with DST-aware coverage.
- Render responsive full reports and conservative email summaries.
- Persist HTML and JSON output in the app configuration directory.
- Accept optional historical `end_date` values through the stdin command.

## 0.1.0-dev

- Create community-ready Home Assistant app repository scaffold.
- Add generic room and outdoor configuration.
- Add internal Home Assistant API client foundation.
- Add deterministic quality and metric helpers.
- Add stdin command loop and report template placeholders.
