# Release Plan (v1.0.0)

Ship Weather App Pro as a Windows installer and a portable EXE. This
plan covers everything between "code works in the venv" and "someone
else can install and use it": frozen-app plumbing, the build pipeline,
the installer, user-facing finishing, and verification.

Each item carries one tag covering both severity and effort:

| Level | Meaning |
|-------|---------|
| S     | Release blocker. Broken behavior or a secret risk. Do first. |
| H     | High. The release is wrong or much worse without it. |
| M     | Medium. Worth doing as part of the release. |
| L     | Low. Polish and nice-to-haves. |

## Findings that shape the plan

From inspecting the current code:

1. Every runtime file (logs, cache.json, settings.json,
   favorites.json) and the VERSION read resolve from the module's own
   folder. That works in the venv and fails in a real install: a
   frozen bundle extracts to a temp dir, and Program Files is not
   writable. App data must move to a per-user data directory when
   frozen. Severity: S.
2. `resources/` (icons, styles) is found the same way and must be
   bundled and resolved through `sys._MEIPASS` when frozen. Severity:
   S.
3. PyQtWebEngine is a runtime requirement but nothing in the app
   imports it anymore; only `test_lottie.py` does. Dropping it from
   the runtime requirements cuts the bundle by roughly 100 MB and one
   fragile dependency. Severity: H.
4. `main.py` sets no High DPI attributes. On scaled displays (125,
   150 percent) the window would render blurry for other users.
   Severity: H.
5. The API key loads from `.env` in the working directory. An
   installed app has no project folder, so first-run key setup needs a
   real answer. Severity: H (it is the difference between an
   installable app and a dev artifact).

## Phase 0: Release readiness (code and legal before packaging)

### Legal, licensing, and attribution

Facts this section is built on (verified September 2026 against
openweathermap.org): the free plan requires visible attribution, the
text "Weather data provided by OpenWeather" with a hyperlink to
openweathermap.org, placed where the weather data is displayed; the
free license is ODbL-based; and every user of the app must register
their own OpenWeatherMap account and key (new keys can take up to two
hours to activate, which our 401 message already mentions).

- [x] 0.9 (H) LICENSE file: the MIT license text with the copyright
  holder and year, referenced by the README. This covers the project's
  own code.
- [x] 0.10 (H) THIRD-PARTY-NOTICES file: PyQt5 (GPL v3 or commercial,
  see decision 5), requests (Apache 2.0), python-dotenv (BSD-3), plus
  the OpenWeatherMap data notice. Ships in the installer and the
  portable zip.
- [x] 0.11 (H) Visible OpenWeatherMap attribution in the app: a footer
  line reading "Weather data provided by OpenWeather" that opens
  openweathermap.org when clicked. Required by the free plan terms and
  it belongs on the screen where the data is shown, not only in the
  About dialog.
- [x] 0.12 (M) PRIVACY file and installer page: what the app sends
  (typed city queries and the user's own API key to OpenWeatherMap
  over HTTPS), what never leaves the machine (the key file, settings,
  favorites, cache, logs), and that the developer collects nothing.
  Links to OpenWeatherMap's own privacy terms.
- [x] 0.13 (M) Disclaimer text (in the installer page, the About
  dialog, and the README): weather data comes from OpenWeatherMap with
  no accuracy warranty; do not rely on it for safety-critical
  decisions.
- [ ] 0.14 (M) Installer consent flow (files exist; the Inno Setup wiring lands with 2.1): the Inno Setup license page
  (must accept) carries the MIT license plus a summary of the notices,
  and an info page before it states the free-key requirement, the
  attribution, and the privacy summary. Feeds item 2.1.
- [x] 0.15 (M) Tell users a free OpenWeatherMap account is required:
  the first-run dialog links the signup page, the README says it up
  front, and the key-activation delay is already covered by the 401
  message.
- [x] 0.16 (L) Asset provenance check: the weather icons and the
  Lottie animations are Meteocons by Bas Milius (MIT, no attribution
  required). The country flags are flag-icons by lipis (MIT,
  confirmed by the `id="flag-icons-..."` fingerprint in 271 of 272
  files); the one extra file is the project's own not-available
  placeholder. All recorded in THIRD-PARTY-NOTICES.

- [x] 0.1 (S) Frozen-aware paths. One `paths.py` helper that resolves
  the app data directory (`%LOCALAPPDATA%\WeatherAppPro` for logs,
  cache, settings, favorites) and the read-only resource root
  (`sys._MEIPASS` when frozen, the project root in dev, including
  VERSION). Update logging_setup, cache, settings, favorites, config,
  and the managers to use it. Dev behavior unchanged. Migrates any
  existing dev-machine files on first run.
- [x] 0.2 (S) Secret-free bundle rule, automated (tools/secret_scan.py; wired into build.ps1 in phase 1): a build step that
  asserts no `.env` and no `OPENWEATHER_API_KEY`-looking string exists
  anywhere in the dist tree. Mirrors the git-side check we already
  run.
- [x] 0.3 (H) Move PyQtWebEngine out of `requirements.txt` into
  `requirements-dev.txt`; `test_lottie.py` stays a dev-only harness.
  Update agent.md and README accordingly.
- [x] 0.4 (H) Key management for the installed app: a first-run dialog
  that asks for the key, validates it with one cheap API call, and
  stores it in the app data directory as a dotenv-style file. It never
  goes into settings.json and never into the repo. Portable mode
  (phase 2) reads `.env` next to the EXE first, so the dev workflow is
  unchanged.
- [x] 0.5 (H) High DPI: set `Qt.AA_EnableHighDpiScaling` and
  `Qt.AA_UseHighDpiPixmaps` before creating QApplication. Verify the
  layout at 150 percent scaling.
- [x] 0.6 (M) Pause the sky animation while the window is minimized
  (changeEvent on WindowMinimized) to stop burning CPU on a hidden
  30 fps timer.
- [x] 0.7 (M) Crash path in a windowed build: stdout and stderr are
  None with `--windowed`; sweep for stray `print(` and confirm the
  logger and crash dialog need neither stream.
- [x] 0.8 (L) Single-instance guard (Qt QLockFile in the data
  directory): a second launch focuses the first instead of stacking.

## Phase 1: Build pipeline (the EXE)

- [x] 1.1 (M) A real icon file: generate a multi-size `app.ico`
  (16 to 256 px) from the clear-sky SVG with a small build script
  (Pillow, dev-only dependency). Commit the `.ico`; the window icon
  code keeps using the SVG.
- [x] 1.2 (H) PyInstaller spec: onedir (faster startup than onefile,
  friendlier to antivirus), windowed, icon, bundled resources and
  VERSION, pinned `pyinstaller` in a new `requirements-build.txt`.
- [x] 1.3 (L) Windows version-info resource so file properties show
  the version from the VERSION file.
- [x] 1.4 (M) One build script (`build.ps1`) that: runs the test
  suite, builds the icon, runs PyInstaller, runs the secret scan
  (0.2), and zips the artifact.
- [x] 1.5 (H) EXE smoke test script (launch, data directory, log, and process checks automated; the interactive live-API pass is the clean-machine test in 4.2): launch the built EXE, run a
  search against the live API, cycle the six conditions, force a bad
  city, confirm the error path and that data files landed in the data
  directory.

## Phase 2: Installer

- [x] 2.1 (H) Inno Setup script: app name and version read from the
  VERSION file, Program Files default with per-user option, Start
  Menu and optional desktop shortcuts, uninstall entry.
- [x] 2.2 (M) Uninstaller offers to keep user data (key, settings,
  favorites) and defaults to keeping it. Amended in v1.0.1: silent
  uninstalls (/SUPPRESSMSGBOXES) bypassed the prompt and deleted data;
  they now always keep data.
- [x] 2.3 (M) Portable zip variant: the onedir tree plus a README
  line; `.env` next to the EXE works without any install or admin
  rights.
- [x] 2.4 (L) Verified end to end on this machine (interactive
  install, shortcuts, launch). A clean-VM pass remains part of the
  phase 4 clean-machine test (4.2).

## Phase 3: User-facing finish

- [x] 3.1 (M) About dialog (Help menu or title bar button): app name,
  version from the VERSION file, a short description, the data folder
  path, and an offer to open it. Also carries the OpenWeatherMap
  attribution with a link (items 0.11) and points at the notices file
  (0.10). No repo link while the repo is private.
- [x] 3.2 (H) First-run key setup UX from 0.4: dialog copy, validation
  feedback, and a clear path to change the key later.
- [x] 3.3 (M) README release section: install from the installer, run
  portable, run from source. Refresh public screenshots under
  `docs/screenshots/` (the previews in `instance/` are private on
  purpose).
- [x] 3.4 (L) Keyboard shortcuts pass: Enter already searches; add
  Ctrl+F to focus the search box and F1 for About.
- [x] 3.5 (M) VERSION bump to 1.0.0 and the changelog entry.

## Phase 4: Verify and ship

- [x] 4.1 (H) Full pytest suite green (152 tests) plus the coverage
  report captured at release/coverage-report-v1.0.0.txt (87% total).
- [x] 4.2 (H) Clean-machine manual pass. Completed September 2026 on
  the owner's machine after a full data reset (no VM needed: the app
  bundles its runtime). Walkthrough verified: download from the
  published release, checksum check, install, first-run key setup,
  searches, all features including the hourly strip, favorites, unit
  toggle, auto refresh at the configured interval, and uninstall with
  the keep-or-delete prompt. The pass caught two real bugs that were
  fixed and re-released: the v1.0.2 first-run crash and the v1.0.3
  uninstaller runtime error.
- [x] 4.3 (M) The automatable checklist items executed and filed at
  release/PRE-RELEASE-CHECKS-v1.0.0.txt (the UI and behavior rows are
  the interactive pass in 4.2).
- [x] 4.4 (M) GitHub release published: tag `v1.0.0`, installer and
  portable zip attached, SHA-256 checksums in the notes
  (releases/tag/v1.0.0). The repo and release are private.
- [ ] 4.5 (L) Post-release watch (ongoing): missing-DLL reports,
  antivirus false positives (common for unsigned PyInstaller builds),
  and the first lines of real user logs if anyone shares them.

## Decisions to confirm before starting

Not blockers; defaults are proposed.

1. Version: propose 1.0.0. The feature set (conditions, hourly,
   favorites, settings, autocomplete) reads as a 1.0.
2. Installer default scope: propose per-user install (no admin
   prompt), with per-machine as an option.
3. QtWebEngine leaves the runtime requirements (0.3). The Lottie
   harness stays dev-only.
4. The key file lives in the data directory as `.env`-style plain
   text. Alternatives (Windows Credential Manager) add complexity for
   little gain on a personal machine; noted as a future hardening
   item.
5. PyQt5 licensing: PyQt5 is GPL v3 or commercial. MIT covers this
   project's own code, but the packaged app is built on PyQt5, so
   distributed binaries carry PyQt5's GPL terms. Compliant default:
   keep the source public (this repo) and ship the notices file.
   The GPL-free alternative is migrating to PySide6 (LGPL), which is
   a real code migration and is proposed as a post-1.0 option, not a
   1.0 item.

## Out of scope for this release

- Code signing (no certificate; Windows SmartScreen will warn on
  first run. Accept and document).
- Auto-update.
- macOS and Linux builds (see below).
- `widgets/weather_animation.py` painter overlay (the sky widget
  covers the need).
- The remaining roadmap UX sprint items beyond 3.4 (loading spinner,
  fade transitions).

### macOS and Linux builds: what they would take

PyInstaller cannot cross-compile: a macOS .app/.dmg must be built on
macOS and a Linux AppImage on Linux. The practical route is GitHub
Actions CI (free minutes cover it, even for a private repo, though
macOS runners bill at a 10x minute multiplier). Beyond the build,
each platform is its own workstream: macOS adds an .app bundle plus
Gatekeeper friction for unsigned binaries (signing needs an Apple
Developer account), and Linux needs an AppImage or deb package with a
.desktop entry. Proposed as a separate future plan if non-Windows
users materialize; not a 1.0.x item.

## Build-time dependency additions

- `requirements-build.txt`: pyinstaller (pinned), Pillow (pinned, icon
  generation). Never installed by end users.
- Inno Setup 6 on the build machine only; its script is committed.
