# Code Review, September 2026

A full pass over the app as it stood at v1.0.3: code, tests, and the
plans in `docs/`. Every finding below was reproduced before it was
written down, and every fix in section 2 has a regression test.

Scope note: **the design was not touched.** All six condition palettes,
the glass console layout, the stylesheet, and every icon are byte for
byte the same. Section 4 explains how that was verified.

## Severity scale

Same scale as the rest of `docs/`.

| Level | Meaning |
|-------|---------|
| S | Critical. Broken behavior, or a security or secret leak risk. |
| H | High. A clear bug or a major usability gap. |
| M | Medium. Worth doing, not urgent. |
| L | Low. Polish and nice-to-haves. |

## Summary

- 9 real defects were found and fixed, all with a regression test.
- 2 further defects were found by the new tests while writing them.
- The suite grew from 153 tests to 225, and stays under two seconds.
- No S severity issue is open. The key-leak work from v0.4 still holds.
- 20 documentation defects are listed in section 5. Several are
  checkboxes marked done with no artifact behind them.
- Five roadmap features (recent searches, air quality, UV index, moon
  phase, weather alerts) have no plan and no code at all.

---

## 1. What was fixed

### 1.1 (H) The hourly strip washed out to white after a few searches

`widgets/hourly_strip.py`, `update_hourly()`.

The rebuild took the old chips out of the layout and called
`deleteLater()` on them. `deleteLater()` only *schedules* the delete.
Until the event loop delivers it, the widget is still a live child of
the scroll area, still visible, still painting at the same position.

Each chip is `rgba(255, 255, 255, 22)` over a dark panel, so every
rebuild stacked another 8.6 percent white layer on the row. Measured on
the chip row, one search per repolish:

| searches | chip row color |
|----------|----------------|
| 1 (correct) | `#343e4d` dark glass |
| 2 | `#d3d7d9` pale |
| 3 | `#f5f6f6` near white |
| 4 and up | `#fafafa` flat white |

`#fafafa` is Qt's default window color. The hour labels
(`rgba(238, 242, 247, 205)`) and the temperatures were light grey on
white, so the whole strip became unreadable. Picking any condition from
the menu, or searching twice, was enough to trigger it.

The fix detaches before deleting:

```python
if widget is not None:
    widget.setParent(None)
    widget.deleteLater()
```

`setParent(None)` stops the painting immediately; `deleteLater()` still
frees the object. The chip row now holds `#343e4d` across every
repolish, which is the correct first-render value, so nothing about the
look changed.

`widgets/favorites_bar.py` uses the same `deleteLater()` pattern and was
checked for the same defect. It does not have it: the city chips are
opaque enough that the stacking is invisible, and only three chips are
ever live. Left alone.

### 1.2 (H) Choosing a condition silently switched the forecast to Fahrenheit

`ui.py`, `apply_condition()`.

The method re-rendered the forecast table to recolor the range bars, but
called `update_forecast()` without the units argument, and the default is
`"imperial"`. A metric user who picked a condition from the menu, or
toggled anything that re-applied a condition, saw the table flip back
to Fahrenheit while the hero and the hourly strip stayed in Celsius.

Reproduced: table read `19°  /  13°`, then after `Condition > Night` it
read `66°  /  56°` with `self.units` still `metric`.

The fix passes `self.units`, matching what `display_forecast()` already
did.

### 1.3 (H) The 5-day forecast was bucketed in the owner's timezone

`weather_api.py`, `get_forecast()`.

The daily rows and the "closest to midday" pick both used
`datetime.fromtimestamp(item["dt"])` with no timezone, so they used the
**machine's** local zone. The city offset was read, but only for the
hourly chip labels.

For a city at UTC-11, one forecast entry at 23:00 UTC lands on:

| owner in | buckets as | distance from midday |
|----------|-----------|----------------------|
| London (UTC+0) | Tue 2026-09-29 | 11h |
| Sydney (UTC+11) | Wed 2026-09-30 | 2h |
| Los Angeles (UTC-8) | Tue 2026-09-29 | 3h |

So the weekday labels, which calendar day each row covered, and which
entry was treated as midday all changed with the timezone of the
computer running the app. The same city gave different forecasts to two
users in different zones. The city block already carries the offset, so
the fix pins every conversion to it.

`test_get_forecast_picks_the_entry_closest_to_midday` was building its
timestamps in machine-local time while declaring a `timezone: 3600` city,
so it passed by agreeing with the bug. It now pins its entries to city
time, and a new test covers the UTC-11 case.

### 1.4 (H) A negative Retry-After header crashed the search

`weather_api.py`, `_retry_after_seconds()`.

`float(raw)` accepted a negative number, and `time.sleep(-5)` raises
`ValueError`. The 429 handling sits outside the `try` that wraps
`requests.get`, so the `ValueError` escaped the request handling, landed
in the worker's catch-all, and the user saw "Something went wrong. See
the log for details." instead of "Too many requests. Wait a minute and
try again."

A negative header now reads as no header at all, which is the existing
behaviour for a value that is not a plain number. Both sides of the
`RETRY_AFTER_CAP_SECONDS` boundary are now tested, which the old suite
did not do: it only probed `3600`, twenty times past the cap.

### 1.5 (H) The API key dialog froze the window for up to ten seconds

`ui.py`, `offer_key_setup()`, and a new `KeyWorker` in
`weather_worker.py`.

Validating a key is one `requests.get` with a ten second timeout. It ran
directly in the dialog's accept handler, on the GUI thread, which is the
exact thing `agent.md` section 4 forbids. The window was unresponsive for
the whole wait, with no wait cursor and no way out.

The check now runs on its own `QThread` behind a `KeyWorker`, and the
dialog became a small state machine: ask, check, then store the key or
offer a retry. `offer_key_setup()` holds a nested `QEventLoop` so it
still returns only when the flow is finished, which is what `main.py`
and the existing test rely on.

The wording of every dialog is unchanged. A test asserts the check runs
on a thread that is not the GUI thread, which is the invariant the module
docstring claims but nothing checked.

### 1.6 (M) `AnimationManager.animation_exists()` raised NameError

`managers/animation_manager.py`.

The method called `Path(...)` and the module never imported `Path`, so
every call raised. The `NameError` was masking a second defect: the
getters return a `file://` URL, and `Path("file:///C:/...")` never
exists, so even with the import the method could never have returned
`True` for the manager's own output. Both are fixed.

### 1.7 (M) `store_key()` accepted a key that could inject a second variable

`geocoding.py`.

The key is written into a dotenv file. A pasted key containing a newline
would produce a second `NAME=value` line, which python-dotenv would read
as a real environment variable on the next start. A key holding any
control character is now refused.

Only control characters are refused. Whether a key actually works is
decided by `validate_key`, so an unusual but legitimate key format is
not rejected on a guess.

### 1.8 (M) `redact_url()` only matched a lowercase `appid`

`utils.py`.

The function is handed text the app did not build, such as an exception
message relayed from something that rewrote the parameter name, but the
regex was case sensitive. `?APPID=secret` passed through untouched. The
match is now case insensitive, with tests for all three casings and a
check that an unrelated 32 character hex value is left alone.

### 1.9 (M) The app title was hardcoded nine times

`ui.py`, `main.py`, `crash_hooks.py`.

`config.APP_TITLE` existed and was never used. The string appeared in
the window title, the About dialog, the key dialog, three message boxes,
and the single-instance warning. All of them now read the constant, which
is what `agent.md` section 4 requires.

### 1.10 (M) Settings logged a warning on every single launch

`settings.py`.

`DEFAULTS["window"]` is `None`, `save()` writes it as `null`, and
`load()` then validated `None` against a four-integer list shape and
logged "Ignored invalid stored value for window" on every start. A key
still holding its default is not an invalid value and is now skipped. A
genuinely bad window, such as `[0, 0, 10, 10]`, is still reported.

### 1.11 (M) A window from a detached monitor came back off screen

`ui.py`, `onscreen_position()`.

The stored geometry was trusted blindly. There was no screen bounds
check anywhere in `settings.py` or `ui.py`. A position is now kept when
it still overlaps a real screen, which leaves an ordinary multi monitor
layout exactly as the owner arranged it, and pulled back onto the primary
screen when nothing is visible. Previously this relied entirely on the
window manager to clamp, which is not something to depend on.

### 1.12 (L) A missing `Path` import in a type annotation

`logging_setup.py`. The `log_file: Path = LOG_FILE` annotation named a
type that was never imported. It only worked because Python 3.14 defers
annotation evaluation, so it was a latent `NameError` on any older
interpreter. Imported.

### 1.13 (L) The forecast relied on `zip()` to drop a sixth day

`weather_api.py`. The endpoint returns 40 three-hour entries, which
straddles **six** calendar days for most hours of the day (measured: 6
days at every request hour except 06:00 UTC). The table has five rows,
so the sixth was dropped by `zip()` truncating rather than on purpose.
`FORECAST_DAYS` now trims it explicitly, and a test pins the count and
the ordering.

### 1.14 (L) Two assets were missing, and two fallbacks pointed at nothing

Found by the new manager tests, not by hand.

- `resources/icons/details/` has no `not-available.svg`, so
  `IconManager.get_detail_icon()` returned a path that did not exist for
  any unknown name. The fallback now points at the glyph that is on disk
  in the weather folder, which is the pattern the other folders use.
- `resources/animations/details/` had no `wind.json` and no
  `not-available.json`, so two entries in `DETAIL_ANIMATIONS` and the
  unknown-name fallback all resolved to nothing. Both files were added
  from the weather folder, matching the existing per-folder convention.

## 2. Dead code and duplication found

Not fixed, listed so it can be decided on.

| Where | Finding |
|-------|---------|
| `utils.py` | `meters_per_second_to_mph` and `meters_per_second_to_kmh` are never called by anything. The API is queried in imperial, so the m/s helpers lost their caller. |
| `config.py` | `REFRESH_INTERVAL` is superseded by the persisted refresh interval and is never read. |
| `managers/theme_manager.py` | `DEFAULT_THEME = "light"` points at a stylesheet that has been unused since v0.6. `available_themes()` is never called. |
| `forecast_card.py` | `ForecastCard` is unused. `agent.md` marks it legacy. |
| `widgets/detail_card.py` | `DetailCard` is unused, and is the only caller of `get_detail_icon`. |
| `widgets/lottie_widget.py` | Unused by the app. `app.spec` excludes PyQtWebEngine, so it cannot work in a frozen build at all. |
| `utils/svg_utils.py` | An empty file with no plan entry, no README mention and no `agent.md` entry. |

Two of these were hardened rather than deleted: `lottie_widget.py` was
building a JavaScript string literal by interpolation, which a quote or
backslash in a path would break, and it resolved its player HTML with
`Path(__file__).resolve().parent.parent` instead of `paths.py`, so it
would not have found the file in a frozen build. Both are fixed. The
file stays, since `test_lottie.py` still uses it.

## 3. Test suite findings

The suite was 153 tests and 87 percent coverage. It is now 225 tests.
Full detail is in `docs/testing-plan.md`; the findings that matter most:

### 3.1 The leak guard could not see most log records

The `weather_log` fixture attaches a handler to the `weather` logger, but
the effective level of that logger is `WARNING` and no fixture ever
lowers it. A handler therefore receives only ERROR records. The guard
proves the key never reaches an ERROR line, and it carries a positive
control that redaction really ran, which is the strongest test in the
suite. But it is blind to every INFO and DEBUG record, including the
`logger.info` calls that log retried URLs.

A guard that can be defeated by changing a log level from INFO to
ERROR-and-back is a gap worth closing. Set the level to DEBUG in the
fixture, restore it after.

### 3.2 The documented main leak vector was untested

`weather_api.py` and `geocoding.py` both state that exception text from
`requests` is never logged as-is, because `HTTPError` embeds the request
URL, which carries the key. The generic `except RequestException` arm
that does `logger.error("Request failed: %s", redact_url(str(error)))`
had no coverage, and the only transport failures the suite injected
(`ConnectTimeout`, `ConnectionError("down")`) contain no URL, so
`redact_url` was a no-op on them. Now fixed and tested: a mocked
`HTTPError` carrying a real `appid=` in its text, asserting both the
message and the log are key free while `appid=***` is present.

### 3.3 `test_contrast.py` is disconnected from the stylesheet it protects

The six WCAG tests hardcode eleven colour constants as hand copies. They
never open `resources/styles/console.qss`, although the stylesheet's own
header says the alphas are verified there and must be kept in sync.

`console.qss` hardcodes six accent hexes that duplicate
`PALETTES[...]["accent"]` in `ConditionTheme`. Change the rain accent in
the stylesheet to anything and all six contrast tests still pass while
the real search button, live badge and condition text are wrong.

`tests/test_managers.py` now pins the two together. The remaining gap is
that the panel and text colours are still hand copies.

### 3.4 Tests that cannot fail

- `test_leak_guard_user_message_and_log_are_key_free` builds a list of
  `(status, expected_error)` pairs and never uses `expected_error`, then
  asserts `pytest.raises(WeatherAppError)`, the base class. Any error type
  passes. The types are only pinned by a separate test.
- `assert not pixmap.isNull()` on an allocated pixmap is always true,
  even after `fill(Qt.transparent)`, so a missing or blank SVG passes.
  Two tests use it. The real invariant is that pixels were painted.
- `test_worker.py:63` asserts a disjunction that every possible chip
  label satisfies.
- `test_ctrl_f_shortcut_is_wired` calls the method and asserts nothing.
- `test_store_key_writes_a_dotenv_line` asserted a temp file did not
  exist, for a function that never creates one. Removed.

### 3.5 Whole areas with no coverage at all

- `main.py` at 0 percent, including the single-instance lock, the High
  DPI attributes, and the first-run key setup call.
- `crash_hooks.py` at 0 percent, including the code that mutates
  `sys.excepthook` and installs a global Qt message handler. This is the
  riskiest untested code in the project.
- `SuggestWorker` failure paths.
- Auto refresh, in full. It is a shipped feature and
  `docs/error-handling-and-security.md` item 3.4 specifies its required
  behavior, and no test calls `auto_refresh()`.
- The search overlap guard, the debounce restart, `closeEvent`'s thread
  shutdown and geometry save, and the minimize pause.
- The right-click-to-remove feature on a favorite chip.
- `main.py` and `crash_hooks.py` are both release-plan items marked
  complete with zero coverage and no row in `release_checklist.md`.

### 3.6 `coverage_report.txt` is stale and misleading

It is gitignored, nothing regenerates it, and it disagrees with itself:
the header says 152 tests, the per-file rows sum to 153, and the real
number is now 225. The headline `TOTAL 87%` counts the test files
themselves, 1044 of 3075 measured statements, plus four dead modules at
zero. `docs/testing-plan.md` sets a target of 90 percent for `utils.py`,
`weather_api.py` and `managers/`; `icon_manager.py` was at 66,
`animation_manager.py` at 0, `theme_manager.py` at 88, `utils.py` at 89,
and nothing flagged the miss.

## 4. How the design was verified unchanged

The owner asked that the look stay exactly as it is, so the change was
checked rather than assumed.

A harness in the temp folder builds the real `WeatherApp` with sample
data, entirely offline: a dummy `OPENWEATHER_API_KEY` is set before
`weather_api` is imported so python-dotenv never loads the real key,
`paths` is redirected at a throwaway directory so the project's
`settings.json`, `favorites.json` and `cache.json` are never touched,
and no HTTP call is made. The window uses `WA_DontShowOnScreen`, so
nothing appears on the owner's desktop.

Ten captures are taken: the empty state, all six condition palettes,
metric units, the minimum window size, and a long city name.

The harness has to be deterministic to be useful, and two things were
not. `SkyWidget` seeds its particles from the global `random` module, and
its 33 ms timer advances a phase counter, so an unseeded build is not
reproducible at all. Once the seed and the phase are pinned and the
timer is stopped immediately before each grab, two runs of the same code
differ by 52 to 102 pixels, all of it the last digit of a clock.

The comparison then ran the **original** code, captured with the same
harness, against the fixed code. The original was captured by stashing
the change set, re-running, and restoring it, so both sides went through
identical code.

Result, per capture, over 1,267,550 pixels:

| Capture | Differing pixels | Where |
|---------|------------------|-------|
| empty state | 0 | none, bit identical |
| clear, cloudy, rain, snow | 565 | clocks and the Updated tile only |
| mist | 584 | as above, plus 3 at a cloud edge |
| night | 607 | as above, plus 22 on the hero glyph and 13 on a range bar |
| metric rain | 581 | clocks and the Updated tile only |
| narrow 820x620 | 134 | clocks only |
| long city name | 581 | clocks and the Updated tile only |

Every remaining pixel was located individually. Rows 77-84 are the local
clock, rows 770-783 the Updated tile, rows 1214-1222 the footer city
clock: all of them legitimately differ because the time moved. The 35
stragglers on the night theme were magnified and sampled: the hero glyph
is pixel identical, and the differences are a single channel moving by 1
of 255 where a twinkling star shows through the translucent glass.

No stylesheet rule was edited, no palette value was edited, and no
layout code was edited. The one visual change is that the hourly strip
now stays dark instead of washing to white, which is the bug fix itself.

## 5. Documentation defects

Twenty findings, none of which are in the app. Grouped by how much they
hurt.

### 5.1 Checked as done with no artifact behind them

- `release-plan.md` 4.3 is `[x]` for checklist output filed at
  `release/PRE-RELEASE-CHECKS-v1.0.0.txt`. The file does not exist and the
  string appears nowhere else in the repo. Worse, `release/` is
  gitignored, so the coverage report backing 4.1 would not survive a
  clean clone either.
- `release-plan.md` 1.5 is `[x]` for an EXE smoke test script. There is no
  such script. `build.ps1` never launches the built binary and `tools/`
  holds only the asset generator and the secret scan.
- `release_checklist.md` has all 30 items unticked, including things
  verified shipped: `LICENSE`, `PRIVACY.md`, `THIRD-PARTY-NOTICES.md`,
  the README install section, and the screenshots. Either it was never
  run or it was run and never updated.
- `redesign-modernization.md` 5.1 settings persistence and 5.2 favorites
  are `[ ]` while `roadmap.md` marks favorites `[x]`. Both shipped in
  v0.8 and v0.9.
- `error-handling-and-security.md` 3.6 defensive favorites IO is `[ ]`
  and its own body text is written in the future tense, while the code
  and nine tests already exist.
- `release-plan.md` 0.14 is `[ ]` for the installer consent flow, which
  is implemented in `weatherapp.iss` and generated by `build.ps1`.
- `testing-plan.md` says "Status: largely complete" and then has all
  nine checklist items unticked. It also says the app "has zero
  automated coverage today", which was true in September 2026 and is now
  wrong by a factor of 225.
- `roadmap.md` "Version 1.0" still lists Dark Theme, Light Theme and
  Lottie Animations as shipped features. All three were retired in v0.6.
  `README.md` also still advertises Lottie animations and PyQtWebEngine
  as runtime technologies, though `requirements.txt` has neither.
- `roadmap.md` lists Keyboard Shortcuts as `[ ]` while `release-plan.md`
  3.4 marks it `[x]` and the code has Ctrl+F, F1 and Enter.

### 5.2 The changelog is corrupted

`docs/changelog.md` has **two** `## v1.0.3` sections describing the same
bug, and **no `v1.0.2` entry at all**, even though
`release/RELEASE-NOTES-v1.0.2.md` exists and the release plan describes
the v1.0.2 first-run crash and the v1.0.3 uninstaller error as two
separate releases.

### 5.3 Promises with no owner anywhere

- The transcript records an agreed refactor of `ui.py`, which was still
  the right call at the time. It is not in any plan, and the "Upcoming"
  section of the changelog that used to name it no longer does. `ui.py`
  is 1,600 lines and still assembles, displays and converts.
- `docs/testing-plan.md` has a "CI (later)" section describing a GitHub
  Actions workflow. The project has been on GitHub since 2026-09-10 and
  there is no `.github/` directory. Nothing catches a regression between
  releases.
- The transcript's lesson about keeping `requirements.txt` in step with
  what the environment actually has is in no plan, no checklist row, and
  no test. It cost a broken fresh install once already.
- `utils/svg_utils.py` is an empty placeholder with no plan entry, no
  README mention and no `agent.md` entry.
- The installer uninstall logic shipped two regressions, silent data loss
  in v1.0.1 and a `WizardSilent` error in v1.0.3, with no regression
  test and no checklist row.

### 5.4 Structural problems

- **Phase numbering does not line up.** `docs/README.md` defines phases 1
  to 6 with release as phase 6. `release-plan.md` uses its own 0 to 4.
  The changelog follows 0 to 3. `roadmap.md` says "phase 6". Same work,
  four numbering schemes, no reconciliation note.
- **`docs/README.md` predicts its own drift.** It notes that
  `roadmap.md` and the plan documents track the same work and suggests
  consolidating if keeping them in sync gets old. It got old; the
  contradictions in 5.1 are the result.
- **`agent.md` is gitignored but is the only accurate architecture
  document.** `docs/README.md` points at it for the tree that matches
  disk, and `CONTRIBUTING.md` names it as authority. A cloner gets
  `docs/architecture.md`, which lists `models/`, `services/` and
  `styles/` folders that do not exist, a `WeatherService` class that does
  not exist, a `Services` layer in `coding_standards.md` that does not
  exist, and a widget set and theme list that were retired in v0.6.
- **`testing-plan.md` describes a mechanism that changed.** It cites
  `Path(__file__).resolve()` in the managers as the reason tests run from
  any working directory. `theme_manager.py` now uses
  `paths.resources_root()`. The conclusion still holds, the stated reason
  does not, and `agent.md` repeats the stale claim.
- **The no-em-dash rule has the weakest enforcement of any rule in the
  project.** It appears in `agent.md`, `CONTRIBUTING.md`,
  `docs/README.md` and the release checklist, and the repo is currently
  clean. Nothing checks it: no pre-commit hook, no lint step, no CI.
  The same is true of the "no unused imports" and "no debug prints"
  rows. A one-line grep in the release checklist would cover all three.

## 6. Next steps, in order

### 6.1 Do now (small, and the rest depends on it)

1. **Add a GitHub Actions workflow.** Windows, Python 3.14, install both
   requirements files, `pytest -q`, and a grep for em dashes, TODO and
   `print(`. The plan has wanted this since the project went public and
   it is what turns every other item below from a hope into a check.
2. **Regenerate or delete `coverage_report.txt`.** It is stale, it
   disagrees with itself, and it is not tracked, so nobody can audit it.
3. **Fix the leak guard's blind spot.** Set the `weather` logger to DEBUG
   in the `weather_log` fixture and restore it afterwards, so the guard
   sees INFO records too.
4. **Connect `test_contrast.py` to `console.qss`.** Parse the stylesheet
   for the values the tests hand copy. The manager test now pins the six
   accents; the panel and text colours still drift silently.

### 6.2 Then, next release

5. **Repair `docs/changelog.md`.** Merge the duplicate v1.0.3 sections and
   write the missing v1.0.2 entry.
6. **Reconcile the four phase numbering schemes**, then either consolidate
   `roadmap.md` into the plan documents or state which one is
   authoritative. The contradictions in 5.1 come from having two.
7. **Fix the `[x]` items with no artifact** (5.1): produce the release
   checklist output and the EXE smoke script, or uncheck them. An
   unchecked item is honest; a checked one with no file is not.
8. **Refresh `README.md`**: the planned-features section, the Lottie and
   WebEngine claims, the project structure tree, which is missing
   `paths.py`, `app.spec`, `build.ps1`, `installer/`, `tools/` and the
   legal files, and the build section, which still says the installer
   comes later.
9. **Give `docs/architecture.md` a rewrite** against what is on disk, so
   the public repo is not dependent on a gitignored file.
10. **Plan or drop the orphaned roadmap features.** Recent Searches, Air
    Quality, UV Index, Moon Phase and Weather Alerts are `[ ]` with no
    plan, no endpoint, no model field and no test. Moon Phase is worth a
    note: a grep for "moon" finds only the decorative moon in the sky
    scene and two resource files, so it is easy to mistake for existing
    work.

### 6.3 Engineering work still open

11. **Responsive layouts (H, the one real gap in the UI).**
    `roadmap.md` has this unticked and it is genuinely unimplemented.
    The measurement grid is a fixed `index // 4, index % 4`, so the tiles
    are always four across, `_fit_height()` only ever adjusts height, and
    there is no `resizeEvent` and no breakpoint. It survives only because
    `setMinimumSize(820, 620)` and a vertical scroll area cover the
    overflow.
12. **The save-failure paths** in `cache.py`, `settings.py` and
    `favorites.py` are all at 0 percent, while their docstrings promise
    that a write failure is logged and swallowed. A read-only data
    directory is the normal state under Program Files and is untested.
13. **Startup with corrupt runtime files.** Each store survives a bad
    file on its own, but no test constructs `WeatherApp()` with all
    three corrupt, which is the claim the docstrings actually make.
14. **`ui.py` is 1,600 lines and does three jobs.** The transcript agreed
    on this refactor and it is now unowned. `coding_standards.md` asks
    for methods under about 40 lines; `create_widgets` is 152,
    `create_layout` 150, `display_weather` 94, and nothing enforces it.
15. **Decide the fate of the dead code** in section 2, or accept it as
    deliberate. `animation_manager.py` and `lottie_widget.py` cannot work
    in a frozen build at all, since `app.spec` excludes PyQtWebEngine.

### 6.4 Worth considering, not urgent

16. **No cancel for an in-flight search.** The button disables and the
    worker retries with backoff, so a rate-limited search can leave the
    button disabled for well over a minute with no way out.
17. **`apply_condition()` repolishes every descendant widget** on every
    search, and `display_weather` calls it, so a unit toggle or a theme
    change triggers a full-window stylesheet re-evaluation. It works, and
    it was the amplifier for 1.1, but it is a lot of work per search.
18. **A missing `visibility` renders as `0 mi`.** Every other field is
    required and raises `ApiDataError`; `visibility` alone falls back to
    zero, so a payload without it looks like genuinely zero visibility.
    This was left alone deliberately: making the field required would
    turn a partial display into a total failure, and the safer fix is a
    visible placeholder, which is a design decision, not a bug fix.
19. **API-supplied strings reach labels that render rich text.** The city
    name and the description go into `QLabel.setText` under Qt's default
    `Qt::AutoText`, so markup in a payload would be rendered. A
    `setTextFormat(Qt.PlainText)` on those three labels would close it
    with no visual change to normal data.
20. **The console content is wider than the default window.** Measured at
    1,210 px against a 1,010 px window once a flag and a real station
    name are present, with the horizontal scrollbar disabled, so the
    overflow is unreachable rather than scrollable. It is only visible
    with a long city name, and the minimum window size is 820 px, so this
    is a latent problem rather than a daily one, but item 11 covers it.

## 7. Reproducing this review

The harness and the diagnostics live outside the repository, in the
temp folder, so nothing in `docs/` depends on them:

- `shoot_baseline.py` builds the window offline and captures the ten
  screenshots described in section 4.
- `diff_shots.py` compares two capture sets and reports differing pixels
  inside and outside the clock regions.
- `locate.py` reports the row and column bands of the differing pixels,
  which is what turned "607 pixels differ" into "the last digit of a
  clock, and one star behind the glass".

To re-run the suite, note that the project's `.venv` currently points
at a Python 3.14.7 that has been uninstalled, so `build.ps1` and
`python -m pytest` both fail. Rebuild the venv before the next release.
