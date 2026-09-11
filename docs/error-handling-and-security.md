# Error Handling, Security, and Logging Plan

Phases 1 and 3 of the roadmap. Read `docs/README.md` first for the severity
legend and phase order.

## Current state (problems found by inspection)

These are observations from the code as of September 2026. Line numbers will
drift as the code changes; the descriptions are what matters.

1. **The API key can reach the UI.** `weather_api.py` calls
   `response.raise_for_status()` (lines 85 and 152). The `HTTPError` message
   that `requests` builds includes the full request URL, and that URL contains
   `appid=<key>`. `ui.py` then does `display_error(str(error))` (line 589), so
   a rejected key or a misspelled city can print the API key into the status
   label. Any future log statement would capture it too. Severity: S.

2. **Raw exceptions reach the user.** `get_weather()` in `ui.py` catches
   `Exception` and shows `str(error)`. Beyond the key leak, the user sees
   programmer text such as "HTTPSConnectionPool host timed out". Severity: S.

3. **No exception hierarchy.** Empty city and missing key raise bare
   `ValueError`. Network problems surface as `requests` types. The UI cannot
   tell "user typed a bad city" from "our code broke". Severity: S.

4. **No logging anywhere.** When something fails, the message lives in the
   status label until the next search overwrites it. There is no file, no
   timestamps, no stack traces. Severity: S (you cannot diagnose field
   problems without this).

5. **`get_forecast()` skips its own checks.** It never verifies that the API
   key exists (only `get_current_weather()` does) and it indexes the response
   without checking fields, so a malformed payload raises `KeyError`. It is
   also called right after `get_current_weather()` with the same city, which
   doubles the failure surface for one search. Severity: H.

6. **Network calls run on the GUI thread.** One search triggers two blocking
   requests, each allowed 10 seconds (`config.REQUEST_TIMEOUT`). During that
   window the window is frozen and the search button still accepts clicks.
   Severity: H.

7. **Response fields are trusted.** `data["main"]["temp"]`,
   `data["weather"][0]["id"]`, `data["sys"]["country"]` and friends are indexed
   directly. A change in payload shape crashes instead of degrading. Severity: H.

8. **Input is only stripped.** City names go straight from `QLineEdit` into
   the query string. No length cap, no whitespace collapsing, no control
   character rejection. Severity: M.

9. **No retry, no backoff, no handling of 429.** The free tier allows 60 calls
   per minute; a transient 500 or a rate limit looks identical to a hard
   failure. Severity: M.

10. **No caching or offline behavior.** A failed request leaves the previous
    result on screen with no indication it is stale, and there is no way to
    start the app and see anything without a live request. Severity: M.

11. **`config.REFRESH_INTERVAL` is unused.** When auto refresh gets built, it
    must not spam errors or repeat the leak above. Severity: M.

12. **Conversion duplication.** `weather_api.py` computes Celsius inline while
    `utils.fahrenheit_to_celsius` exists. Not a failure mode, just drift
    waiting to happen. Severity: L.

## Rules that apply from now on

These are binding for all future code, not just for this plan:

- User-facing error text is written by hand and hardcoded. It never comes from
  exception text, URLs, response bodies, or f-string interpolations of those.
- The API key never appears in a message, a log line, or a stored file. If a
  URL must be logged, pass it through a redaction helper that strips the
  `appid` parameter first.
- Every failure is logged (with stack trace) and then shown to the user as a
  short, plain, human-written sentence.

## Phase 1: Critical fixes

### 1.1 Create `errors.py` with an exception hierarchy (S)

```
WeatherAppError(Exception)        base class, carries user_message
  InvalidCityError                empty or malformed input
  ApiKeyMissingError              OPENWEATHER_API_KEY not set
  ApiKeyInvalidError              API returned 401
  CityNotFoundError               API returned 404
  RateLimitError                  API returned 429
  ApiServiceError                 API returned 5xx or unknown status
  NetworkError                    timeout, connection failure
  ApiDataError                    200 response with an unexpected shape
```

Each exception is constructed with a safe, human-written user message plus
optional debug detail. The debug detail is for logs only; the UI reads
`user_message` and nothing else.

### 1.2 Map requests failures to the hierarchy in `weather_api.py` (S)

Wrap both `get_current_weather()` and `get_forecast()` in one shared private
method that:

- checks the key exists up front (fixes problem 5),
- catches `requests.exceptions.Timeout` and `ConnectionError`, raises
  `NetworkError`,
- catches `HTTPError`, inspects `response.status_code`, raises the matching
  exception from 1.1,
- validates the payload shape (item 1.4) before returning models.

Add `errors.py` messages matching OpenWeatherMap semantics:

| Status | User message |
|--------|--------------|
| 401    | "The API key was rejected. Check OPENWEATHER_API_KEY in .env. New keys can take up to two hours to activate." |
| 404    | "City not found. Check the spelling and try again." |
| 429    | "Too many requests. Wait a minute and try again." |
| 5xx    | "The weather service is having problems right now. Try again later." |

### 1.3 Rewrite the UI error path (S)

`get_weather()` in `ui.py`:

- catches `WeatherAppError` and calls `display_error(error.user_message)`,
- catches `Exception`, logs it with `logger.exception()`, and shows a generic
  "Something went wrong. See the log for details." message.

### 1.4 Validate response payloads (H)

Before building `WeatherData` or `ForecastData`, check that the fields the app
actually uses exist. On a miss, raise `ApiDataError` and log the JSON top-level
keys (keys only, never values) so shape changes are diagnosable.

### 1.5 Logging bootstrap (S)

New file `logging_setup.py`, called from `main.py` before the window is built:

- `logging.getLogger("weather")` as the single namespace; modules use
  `logging.getLogger(__name__)` under it,
- `RotatingFileHandler` writing to `logs/app.log`, 1 MB per file, 5 backups,
  DEBUG level,
- optional console handler at INFO, enabled by a flag or env var,
- format: `%(asctime)s %(levelname)s %(name)s: %(message)s`,
- add `logs/` to `.gitignore`.

Nothing in the app logs request params, response bodies, or anything derived
from them without redaction (item 1.6).

### 1.6 Redaction helper (H)

`utils.py` gets `redact_url(url: str) -> str` that replaces the `appid`
parameter value with `***`. Every place a URL could reach a log uses it. A
small unit test asserts the key substring cannot survive the function.

### 1.7 Leak guard test (S, needs phase 2 scaffolding)

A pytest case that points the API client at a mock returning 401 (and each
other status) with a dummy key, then asserts the dummy key appears in neither
the raised exception's `user_message` nor anything written to the log handler.

### 1.8 Input validation (H)

In `weather_api.py` before the request: collapse whitespace, reject empty
strings, reject control characters, cap length at 85 characters (the API's
documented maximum for the `q` parameter). Raises `InvalidCityError`.

## Phase 2: Test scaffolding

See `testing-plan.md`. Listed here because 1.7 depends on it.

- S: add pytest, pytest-qt, requests-mock, pytest-cov to a dev requirements
  file, plus `pytest.ini`.
- S: isolate tests from `.env`. Importing `weather_api` currently runs
  `load_dotenv()` at module import, so `conftest.py` must set a dummy
  `OPENWEATHER_API_KEY` in the environment before the first import, or the
  `load_dotenv()` call moves into a function called by `main.py`.

## Phase 3: Robustness

### 3.1 Move network calls off the GUI thread (H)

Run the API calls in a `QThread` or a `QThreadPool` worker. The search button
disables while a request is in flight and re-enables on completion or failure.
Results and errors come back through signals. Keep `weather_api.py` free of Qt
imports so it stays testable; the worker owns the call and emits the result.

### 3.2 Retries with backoff (M)

Mount `HTTPAdapter` with `urllib3.util.Retry` (2 retries, exponential
backoff) for connection errors and 5xx. Honor `Retry-After` on 429 before
giving up. Retries log at INFO with the redacted URL.

### 3.3 Cache the last successful result (M)

Write the last `WeatherData` and forecast to a local JSON file (plain data
only; never the API key). On startup or on a failed request, load it and show
it with a "last updated" marker so the app works offline.

### 3.4 Quiet auto refresh (M, blocks the REFRESH_INTERVAL feature)

When auto refresh is implemented, a failed background refresh logs a warning
and updates a small "updated X ago / failed at HH:MM" note. It must not pop
dialogs or overwrite a good display with an error.

### 3.5 First-run key check (M)

Check for the API key at startup in `main.py` and show a clear message (a
dialog or a status message) instead of failing on the first search. The
message names the variable, never its value.

### 3.6 Defensive JSON IO for favorites and settings (M)

When those features are implemented: wrap file reads against missing or
corrupt files, write to a temp file then rename, and never store the API key
in either file.

### 3.7 Global crash hook (L)

`sys.excepthook` plus a Qt message handler that logs uncaught errors and shows
one friendly dialog, so a crash leaves a trace behind.

### 3.8 Use `utils` conversions everywhere (L)

Replace the inline Celsius math in `weather_api.py` with
`utils.fahrenheit_to_celsius`.

## Checklist

- [x] 1.1 errors.py hierarchy
- [x] 1.2 status code mapping in weather_api.py
- [x] 1.3 UI error path rewrite
- [x] 1.4 payload validation
- [x] 1.5 logging_setup.py and logs/ gitignore
- [x] 1.6 redact_url helper
- [x] 1.7 leak guard test
- [x] 1.8 input validation
- [x] 2.1 pytest scaffolding
- [x] 2.2 tests isolated from .env
- [x] 3.1 background network worker
- [x] 3.2 retries with backoff
- [x] 3.3 last result cache
- [x] 3.4 quiet auto refresh (blocks REFRESH_INTERVAL feature)
- [x] 3.5 first-run key check
- [ ] 3.6 defensive favorites/settings IO (when implemented)
- [x] 3.7 global crash hook
- [x] 3.8 utils conversions used everywhere

Phase 1, the pytest scaffolding, and phase 3 (except 3.6, which waits
for the favorites and settings features) were completed in September
2026. See docs/changelog.md v0.4 and v0.5. The tests live in tests/
and run with `python -m pytest` after installing requirements-dev.txt.

Implementation notes for phase 3:

- The retries in weather_api.py are an explicit loop rather than an
  adapter-mounted urllib3.Retry, with identical semantics. The adapter
  approach cannot be tested through requests_mock, and the leak guard
  must see every failure path.
- Auto refresh starts only after the first successful search and
  repeats that city. A failed refresh keeps the previous display and
  only updates the status label.
- The cache file is cache.json in the project root, written through a
  temp file plus rename. It is gitignored and never holds the key.
