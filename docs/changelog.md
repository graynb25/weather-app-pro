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

## v0.5

- Moved all network calls off the GUI thread: searches run through a
  WeatherWorker on a QThread, results and typed errors come back through
  signals, and the search button disables while a request is in flight.
- Added retries with exponential backoff for connection errors, timeouts,
  and 5xx responses. A 429 is retried only when Retry-After asks for a
  sane wait.
- Added cache.py: the last successful search is stored as plain JSON and
  shown at startup or after a failed request, with an "as of" note.
- Added quiet auto refresh on config.REFRESH_INTERVAL: repeats the last
  successful city every 10 minutes and never pops dialogs or replaces a
  good display with an error.
- Added a first-run API key check in main.py that names the missing
  variable instead of failing on the first search.
- Added crash_hooks.py: uncaught exceptions and Qt messages are logged
  with stack traces, and a crash shows one friendly dialog.

---

## v0.6

- Redesigned the app as the "glass console": the data console layout on
  glass panels over an animated condition sky, per the reviewed preview
  (instance/preview/05-glass-console.html, local only).
- Added managers/condition_theme.py: six condition palettes (clear,
  cloudy, rain, snow, mist, night) chosen from the weather id plus day
  or night. The Condition menu follows the weather on Auto or pins any
  condition.
- Added widgets/sky_widget.py: the painted full-window gradient and the
  ambient scene per condition (drifting sun or moon, twinkling stars,
  falling rain, drifting snow, cloud and mist blobs).
- Added widgets/range_bar.py and widgets/forecast_table.py: the 5-day
  forecast is now a table with hi/lo temperature range bars scaled
  against the week range. ForecastData grew real daily min and max,
  aggregated from the API's 3-hourly entries.
- Added widgets/stat_tile.py: the measurement tiles (humidity, wind,
  visibility, pressure, sunrise, sunset, condition, updated).
- Replaced the light and dark theme menu with condition theming
  (resources/styles/console.qss). The old theme sheets stay on disk
  unused, and Lottie is no longer embedded in the main window
  (test_lottie.py still uses it).

---

## v0.7

- Added the hourly strip (widgets/hourly_strip.py): glass chips for the
  next 24 hours with hour, condition icon, and monospace temperature.
  The first chip is NOW and picks up the condition accent.
- get_forecast() now returns daily and hourly data from the same
  payload, labeled with the forecast's city timezone; no second API
  call. ForecastData gained an HourData sibling model.
- The worker signal, cache file, and startup display carry the hourly
  chips. Caches from before the strip load with an empty strip.

---

## v0.8

- Added settings.py: persisted user settings in settings.json
  (gitignored), with defensive IO and validated keys. Stores units,
  condition mode, auto refresh interval, and window geometry.
- Added the unit toggle: a Settings menu switches imperial and metric
  across the hero, tiles, hourly strip, and forecast instantly. The API
  always fetches imperial; the toggle is display state.
- The condition menu choice and the auto refresh interval now persist.
- The window position and size are restored on the next start.

---

## v0.9

- Added favorites (favorites.py, widgets/favorites_bar.py): a row of
  saved-city chips under the search bar. Click a chip to search it,
  right click to remove it, and the plus chip saves the city currently
  on screen. Capped at 10, deduped case-insensitively, persisted on
  every change with defensive IO.
- Added the VERSION file and a version chip in the footer center. The
  window title carries the version too.

---

## v0.10

- Added search autocomplete (geocoding.py, SuggestWorker): typing
  queues a debounced query (300 ms) to the OpenWeatherMap geocoding
  API on its own thread, and a styled popup lists up to five matches
  as city, state, country. Picking one fills the search box with the
  disambiguated query.
- Suggestion failures are best effort: they are logged with the key
  redacted and the popup simply stays closed. Stale answers for an
  older query are dropped.
- The geocoder reuses the errors hierarchy and key-safety rules; 404
  counts as no matches.

---

## v0.11

- Fixed the autocomplete popup: it is a top-level window, so the
  window stylesheet never reached it. The theme is now applied to the
  popup directly and it renders as a dark glass list.
- Added the app icon (rendered from the clear-sky SVG) and the window
  title version.
- The window centers itself on first show; a saved geometry restores
  exactly and skips the centering.
- Added the empty state: a "Search for a city" badge plus three
  clickable example cities (London, Tokyo, Bogota) in the hero.
- The footer status line now shows "Updated {city} . X ago" using the
  last fetch time. Errors hold the line for half a minute before it
  takes over.

---

## v0.12

- Release-readiness work (release plan phase 0):
- paths.py: frozen-aware filesystem locations. Runtime files move to
  %LOCALAPPDATA%\WeatherAppPro when frozen; running from source is
  unchanged.
- First-run API key setup: the app asks for a free OpenWeatherMap key,
  validates it with one cheap call, and stores it in the data
  directory. The key file is loaded at startup.
- High DPI scaling enabled; the app renders sharply on scaled
  displays.
- Single-instance guard: a second launch focuses the message instead
  of stacking windows.
- The sky scene pauses while the window is minimized.
- PyQtWebEngine moved to the dev requirements; the runtime no longer
  needs it.
- tools/secret_scan.py: the release gate that checks a build tree for
  key material.
- LICENSE (MIT), THIRD-PARTY-NOTICES, and PRIVACY added; the weather
  icons and animations are Meteocons by Bas Milius (MIT).

---

## v0.13

- Build pipeline (release plan phase 1): requirements-build.txt
  (PyInstaller 6.22.2, Pillow 12.3.0), tools/make_release_assets.py
  (multi-size app.ico from the clear-sky SVG, Windows version
  resource from the VERSION file), app.spec (onedir, windowed, no
  QtWebEngine), and build.ps1 (tests, assets, build, secret scan,
  portable zip).
- The built EXE is about 105 MB onedir (43 MB zipped), shows the sun
  icon and file version in Explorer, stores data in
  %LOCALAPPDATA%\WeatherAppPro, and passes the secret scan.

---

## v0.14

- Installer (release plan phase 2): an Inno Setup build in build.ps1
  produces WeatherAppPro-setup-<version>.exe with a must-accept
  license page (MIT plus the notices summary), an info page (free-key
  requirement, privacy summary, disclaimer), per-user or per-machine
  scope chosen at install time, Start Menu and optional desktop
  shortcuts, and an uninstaller that asks before deleting user data
  (default: keep).
- Portable zip now carries a README-portable.txt explaining the .env
  option and the data folder.
- The LICENSE copyright holder is "Weather App Pro".

---

## v1.0.0

- Release polish (release plan phase 3): an About dialog (Help menu or
  F1) with the version, the OpenWeatherMap attribution and link, the
  license and notices pointers, and an open-data-folder button.
- Settings menu gained "API key..." so an installed copy can replace
  a saved key without editing files.
- Visible footer attribution: "Weather data provided by OpenWeather",
  required by the free plan terms.
- Ctrl+F focuses the search box.
- README gained install instructions and public screenshots
  (docs/screenshots/).
- Version 1.0.0.

---

## v1.0.1

- Fixed a data-loss risk: a silent uninstall (running the uninstaller
  with /SUPPRESSMSGBOXES, or scripted removals) deleted the user data
  folder without asking. Silent uninstalls now always keep data;
  interactive uninstalls still ask, with keep as the default.
- The OpenWeatherMap attribution links (footer and About dialog) are
  light-colored for readability on the dark theme.
- Refreshed the README screenshots.

---

## v1.0.3

- Fixed the uninstaller runtime error ("Cannot call 'WizardSilent'
  function during Uninstall"): the uninstall phase must use
  UninstallSilent(). Verified live: the interactive keep-or-delete
  prompt now shows correctly and both answers behave.

---

## v1.0.3

- Fixed the uninstaller runtime error ("Cannot call 'WizardSilent'
  function during Uninstall") that appeared at the end of an
  uninstall. The uninstall phase now uses UninstallSilent().
- Re-published the GitHub release with corrected notes and checksums
  (an earlier scripted publish had silently failed).

---

## Upcoming

- Post-release watch.