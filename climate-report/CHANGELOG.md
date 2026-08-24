# Changelog

## 0.5.6

- Add a configurable Home Assistant public URL so email reports always include a direct button to the app Web UI.
- Reuse the same report destination for email and Companion push notifications.
- Add the report button to previously generated emails when they are sent manually.

## 0.5.5

- Open the app's latest report when tapping a Companion push notification.
- Add an email button linking to the latest report through Home Assistant's external URL.
- Resolve the installed app slug dynamically through Supervisor.

## 0.5.4

- Replace browser CSS with a complete Gmail-compatible table layout and inline styles.
- Preserve room, temperature, humidity, comparison and daily details in email.
- Render email-safe temperature and humidity trend sparklines.

## 0.5.3

- Send the complete Web UI report as the email body instead of the compact summary.
- Attach the exact generated HTML so it can be opened without email-client styling restrictions.

## 0.5.2

- Add a back arrow from the Ingress UI to the previous Home Assistant page.
- Explain clearly when email delivery is disabled instead of showing an English error.

## 0.5.1

- Support both legacy Companion notify actions and modern notify entities.
- Replace generic HTTP 400 push failures with a precise unavailable-target error.

## 0.5.0

- Add secondary day, night, range and year-over-year humidity measurements.
- Add a browsable archive of saved reports to the Ingress UI.
- Add Companion App push notifications and a manual push test.
- Add direct SMTP configuration, automatic delivery and manual test/send buttons.
- Clarify archive and delivery options in the app configuration.

## 0.4.1

- Plot daily humidity alongside temperature in every room chart.
- Preserve humidity charts and daily values when temperature data is missing.
- Auto-size the report preview so the Ingress page has a single scrollbar.
- Show temperature and humidity coverage separately.

## 0.4.0

- Add an Ingress form to generate reports for an inclusive custom date range.
- Keep the existing stdin weekly and historical generation commands compatible.

## 0.3.0

- Add a Home Assistant Ingress viewer for the latest generated report.

## 0.2.1

- Use a Python base image so local Supervisor builds do not depend on Alpine
  package-index downloads.
- Publish the project as Climate Report for Home Assistant.

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
