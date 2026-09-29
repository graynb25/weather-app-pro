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

## v1.0.2

- Fixed a first-run crash: on a machine with no existing key, the API
  key dialog referenced an unimported dialog class and the app closed
  instead of asking. Found by the clean-machine release test and
  covered by a regression test.
- Re-published v1.0.1, which had shipped with a silent-uninstall data
  loss risk and unreadable attribution links on the dark theme.

---

## v1.0.3

- Fixed the uninstaller runtime error ("Cannot call 'WizardSilent'
  function during Uninstall") that appeared at the end of an
  uninstall: the uninstall phase now uses UninstallSilent(). Verified
  live, the interactive keep-or-delete prompt shows correctly and both
  answers behave.
- Re-published the GitHub release with corrected notes and checksums
  (an earlier scripted publish had silently failed).

---

## v1.0.4

Full findings and next steps in docs/code-review-2026-09.md.

- Added CONTRIBUTING.md: contributor setup, ground rules, test and PR
  expectations. It is the public counterpart of the local agent.md.
- Post-release watch.
- Added docs/code-review-2026-09.md: a full pass over the code, the
  test suite, and the plans at v1.0.3, with next steps in priority
  order.
- Fixed the hourly strip washing out to a flat white band. Rebuilding
  the chips scheduled the old ones for deletion with deleteLater()
  without hiding them, so they kept painting and each rebuild stacked
  another translucent white layer. After three searches the row reached
  Qt's default window color and the hour labels and temperatures became
  unreadable. Old chips are now hidden before they are deleted.
- This release introduced a regression: the fix above was first written
  by reparenting each replaced chip to null, which turns a chip into a
  top-level window, and a small white box then appeared over the hourly
  strip on every search and every unit change. Fixed in v1.0.5, so
  anyone on v1.0.4 should update.
- Fixed the forecast table silently reverting to Fahrenheit when a
  condition was chosen from the menu, because the re-render did not
  pass the current units. A metric user saw the table flip units while
  the hero and the hourly strip stayed in Celsius.
- Fixed the 5-day forecast being bucketed into calendar days using the
  timezone of the computer running the app rather than the city's. The
  weekday labels, the day each row covered, and which entry counted as
  midday all changed with the owner's timezone, so the same city gave
  different forecasts in different zones. Every conversion now uses the
  offset from the payload's city block.
- Fixed a negative Retry-After header crashing a search with the generic
  "something went wrong" message. time.sleep raises on a negative wait,
  and the header handling sat outside the try that wraps the request.
  A negative value now reads as no header at all, as any non-numeric
  value already did.
- Fixed the API key dialog freezing the window for up to ten seconds.
  Validating a key is one HTTP request with a ten second timeout, and it
  ran on the GUI thread. It now runs on its own worker thread behind a
  KeyWorker, and the dialog became a small state machine. The wording of
  every dialog is unchanged.
- Fixed AnimationManager.animation_exists raising NameError, and fixed
  it being unable to return True for the file:// URLs its own getters
  produce. The missing Path import had been masking the second problem.
- Fixed store_key accepting a key containing a control character, which
  in the dotenv file would have been read back on the next start as an
  extra environment variable. Only control characters are refused;
  whether a key works is still decided by validate_key.
- Fixed redact_url only matching a lowercase appid, so text relayed
  from elsewhere with ?APPID= passed through untouched. The function is
  handed text this app did not build, so the match is now case
  insensitive.
- Replaced the nine hardcoded copies of the app title with
  config.APP_TITLE, which existed and was never used.
- Stopped settings logging "Ignored invalid stored value for window" on
  every launch. The window default is null, so a key still holding its
  default is no longer reported as an invalid value. A genuinely bad
  window is still reported.
- A window saved while a second monitor was attached came back off
  screen once that monitor was gone. A restored position is now kept
  when it still overlaps a real screen, so a normal multi monitor layout
  is left exactly as arranged, and pulled back onto the primary screen
  when nothing is visible.
- Fixed a missing Path import in a logging_setup.py annotation. It only
  worked because Python 3.14 defers annotation evaluation.
- The forecast now trims to five days explicitly instead of relying on
  the row loop dropping the sixth, which is what happened for most
  hours of the day because 40 three-hour entries straddle six calendar
  days.
- Fixed two assets that were missing: resources/icons/details had no
  not-available.svg, so the detail icon fallback pointed at nothing and
  now uses the glyph that is on disk; and
  resources/animations/details had no wind.json and no
  not-available.json, so two detail animation mappings resolved to
  nothing. Both files were added.
- Hardened LottieWidget: the animation path is now encoded as a JSON
  string literal instead of being interpolated into JavaScript, and the
  player HTML is resolved through paths.py so a frozen build can find
  it.
- Added 72 tests, from 153 to 225, still under two seconds. New
  coverage: the city-timezone forecast, both sides of the
  Retry-After cap, negative and malformed Retry-After, a server error
  that recovers, timeouts being retried, an HTTPError carrying a real
  key in its text, case-insensitive redaction, the utils conversions
  that previously had no direct test, chips stopping paint on rebuild
  and never becoming windows, units
  surviving a condition change, the key check running off the GUI
  thread, a rejected key not looping, cancelling storing nothing, the
  default window not being logged as invalid, an off-screen window
  being brought back, and a new tests/test_managers.py that asserts
  every mapped asset exists on disk and pins the stylesheet's condition
  accents to the palette table.
- Fixed test_get_forecast_picks_the_entry_closest_to_midday, which built
  its timestamps in machine-local time while declaring a city an hour
  ahead, so it passed by agreeing with the timezone bug above.
- Version 1.0.4.
- Published v1.0.4: the installer and the portable zip, tagged on main
  with the SHA-256 values in the release notes, which match the digests
  GitHub computed for the uploaded assets.

---

## v1.0.5

A one-line fix for the regression v1.0.4 shipped. If you are on
v1.0.4, update to this.

- Fixed a small stray white box appearing over the hourly strip. The
  v1.0.4 fix for the strip washing out to white reparented each
  replaced chip to null, which makes a chip into a top-level window
  that stays visible where the strip sits. The boxes accumulated, 16
  after one rebuild and 48 after three. Only two actions rebuild that
  row, pressing Enter to search and switching units, so it looked like
  a pop-up that came and went rather than a widget leak. Hiding the
  chip stops the painting just as well and never makes it a window, so
  the original washout fix is kept and the box is gone.
- The test that shipped with the first fix asserted the replaced chips
  became parentless, which is the bug rather than the intent. It now
  asserts they stop painting while staying parented, plus a new guard
  that no chip ever becomes a window. The new guard was checked by
  putting the old line back, and it fails.
- Nothing else changed. The interface, the six condition themes, and
  the console design are byte for byte the same, verified by capturing
  all ten states before and after and comparing them pixel by pixel.
- Version 1.0.5.