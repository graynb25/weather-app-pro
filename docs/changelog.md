# Changelog

## v0.1

- Initial project structure.
- OpenWeather integration.
- Current weather.
- Forecast support.

---

## v0.2

- Added managers.
- Added reusable widgets.
- Added DetailCard.
- Added ForecastCard.

---

## v0.3

- Added SVG detail icons.
- Added Lottie weather animations.
- Added Light/Dark themes.

---

## v0.4

- Added errors.py, an exception hierarchy where every error carries a
  hand-written user message plus debug detail for the log.
- Rewrote the API error path in weather_api.py: HTTP statuses map to typed
  errors, both endpoints check the API key up front, and payloads are
  validated before models are built.
- Closed the API key leak: URLs are redacted through utils.redact_url before
  they can reach a log, and the leak guard test holds for every status.
- Added city input validation: whitespace collapsing, control character
  rejection, and the API's 85 character limit.
- Added logging_setup.py: rotating file log at logs/app.log, optional console
  mirror through WEATHER_CONSOLE_LOG.
- Added the pytest scaffolding (requirements-dev.txt, pytest.ini, tests/) and
  37 tests covering status mapping, the leak guard, validation, and redaction.
- Used the utils conversion helpers everywhere instead of inline math.

---

## Upcoming

- UI redesign.
- Refactor ui.py.
- Background network worker and retries (phase 3).