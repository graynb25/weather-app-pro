# Testing Plan (pytest)

Phase 2 of the roadmap. Status: planned, not started. Nothing in this document
exists in the codebase yet; `test_lottie.py` is a manual GUI harness, not an
automated test.

## Stack

| Package | Purpose |
|---------|---------|
| pytest | Test runner |
| pytest-qt | Qt widget tests without a real user (`qtbot`) |
| requests-mock | Stub OpenWeatherMap HTTP responses without network access |
| pytest-cov | Coverage reporting |

These go in a `requirements-dev.txt` (or a `dev` extra) so the app itself
stays lean. `pytest.ini` or `[tool.pytest.ini_options]` sets the test paths
and adds `-q` by default.

## Ground rules

1. **Tests never read `.env`.** This extends the rule in `agent.md`. All API
   keys in tests are dummy strings (`"test-key-123"`). See the isolation note
   below.
2. **No network in tests.** Every HTTP interaction goes through
   `requests-mock`.
3. **No Qt event loop for logic tests.** Only UI tests use `qtbot`; managers,
   models, utils, and `weather_api.py` stay Qt-free and fast.
4. **Windows paths are exercised as-is.** Path-building code in the managers
   uses `Path(__file__).resolve()`, so tests run from any working directory.

### Isolating tests from .env

`weather_api.py` calls `load_dotenv()` at module import time, so the first
`import weather_api` in a test session would load the real `.env` if one
exists. Two acceptable fixes, pick one when implementing:

- Preferred: move `load_dotenv()` out of module scope into a function (for
  example `WeatherAPI.__init__` or a `main.py` bootstrap call).
- Alternative: `conftest.py` sets `OPENWEATHER_API_KEY=dummy` via
  `os.environ.setdefault` before any project import, accepting that `.env`
  values may still load.

Optionally also run pytest with dotenv loading disabled by monkeypatching
`load_dotenv` in a top-level fixture, and add a test asserting that a missing
key raises `ApiKeyMissingError` with a safe message.

## Suites to write

All items here are severity S unless marked otherwise, because the app has
zero automated coverage today.

### tests/test_utils.py
- `fahrenheit_to_celsius`: 32 to 0, 212 to 100, negative values, rounding
  behavior at the call site (rounding happens in the UI, utils returns floats).
- `meters_per_second_to_mph` / `_kmh`: zero, typical values.
- `meters_to_miles` / `meters_to_km`: zero, typical values.
- `unix_to_local_time`: positive and negative UTC offsets, output format
  `HH:MM AM/PM`.

### tests/test_weather_model.py
- `WeatherData` and `ForecastData` construct with all fields.
- Defaults and types match the dataclass definitions (guards against silent
  field drift).

### tests/test_weather_api.py
Use `requests-mock` for the two endpoints. Fixture JSON files live in
`tests/fixtures/` (hand-written samples shaped like real payloads; real
responses contain no key material, but hand-written ones keep tests stable).

- Success: current weather parses into a filled `WeatherData` (city, country,
  both unit fields, description title-cased, weather_id).
- Success: forecast groups 3-hourly entries per day and picks the entry
  closest to midday; sorted by date. Craft a payload where the midday rule
  matters (for example entries at 09:00, 12:00, 15:00 and another day with
  only 06:00 and 18:00).
- Empty city raises `InvalidCityError`.
- Missing key raises `ApiKeyMissingError` (fix the `get_forecast` gap first,
  see error-handling plan item 1.2).
- Status mapping: 401 to `ApiKeyInvalidError`, 404 to `CityNotFoundError`,
  429 to `RateLimitError`, 500 to `ApiServiceError`, each with the intended
  user message and no exception text from `requests`.
- Timeout and connection error raise `NetworkError`.
- Malformed payloads (missing `main`, empty `weather` list, missing `sys`)
  raise `ApiDataError`.
- Leak guard (the important one): with `appid=test-key-123`, assert the string
  `test-key-123` appears in no `user_message` of any raised exception.
- Input validation (after item 1.8): long input, control characters,
  whitespace collapsing.

### tests/test_managers.py
- `IconManager.get_icon_path` and `AnimationManager.get_weather_animation`
  return existing files for representative condition ids (2xx thunderstorm,
  3xx drizzle, 5xx rain, 6xx snow, 7xx atmosphere, 800 clear) and a defined
  fallback for an unknown id.
- `FlagManager.get_flag_path` returns an existing file for a common code and
  handles lowercase input.
- `ThemeManager`: `load_theme("light")` returns text, an unknown name falls
  back to the default, `available_themes()` includes every `.qss` file.

### tests/test_ui.py (pytest-qt, smoke level)
- The window constructs without errors and shows its default state.
- Empty search shows "Please enter a city." and does not call the API.
- With `WeatherAPI` methods monkeypatched to return a stub `WeatherData`, a
  search populates labels and forecast cards.
- With the API raising `CityNotFoundError`, the status label shows the user
  message.
- Theme menu action switches the stylesheet.

Smoke level means: verify wiring, not pixel layout. Keep these few and fast.

## Coverage targets

- `utils.py`, `weather_api.py`, `managers/`: 90 percent or better (all pure
  logic).
- `ui.py`, widgets: covered by smoke tests, no numeric target.
- Track with `pytest --cov`. Do not chase 100 percent; chase the error paths,
  since those are what phase 1 is about.

## CI (later)

Once the project lives in git, add a GitHub Actions workflow:
windows-latest, Python 3.14, install `-r requirements.txt` and the dev
requirements, run `pytest --cov`. Keep `agent.md` untracked (it already is,
via `.gitignore`), and make sure no test writes into `logs/` during CI.

## Checklist

- [ ] Dev requirements file and pytest.ini
- [ ] conftest.py with dummy key and .env isolation
- [ ] tests/test_utils.py
- [ ] tests/test_weather_model.py
- [ ] tests/test_weather_api.py including leak guard
- [ ] tests/fixtures sample payloads
- [ ] tests/test_managers.py
- [ ] tests/test_ui.py smoke tests
- [ ] Coverage run and report
