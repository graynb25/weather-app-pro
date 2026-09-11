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

## Phase 0: Release readiness (code changes before packaging)

- [ ] 0.1 (S) Frozen-aware paths. One `paths.py` helper that resolves
  the app data directory (`%LOCALAPPDATA%\WeatherAppPro` for logs,
  cache, settings, favorites) and the read-only resource root
  (`sys._MEIPASS` when frozen, the project root in dev, including
  VERSION). Update logging_setup, cache, settings, favorites, config,
  and the managers to use it. Dev behavior unchanged. Migrates any
  existing dev-machine files on first run.
- [ ] 0.2 (S) Secret-free bundle rule, automated: a build step that
  asserts no `.env` and no `OPENWEATHER_API_KEY`-looking string exists
  anywhere in the dist tree. Mirrors the git-side check we already
  run.
- [ ] 0.3 (H) Move PyQtWebEngine out of `requirements.txt` into
  `requirements-dev.txt`; `test_lottie.py` stays a dev-only harness.
  Update agent.md and README accordingly.
- [ ] 0.4 (H) Key management for the installed app: a first-run dialog
  that asks for the key, validates it with one cheap API call, and
  stores it in the app data directory as a dotenv-style file. It never
  goes into settings.json and never into the repo. Portable mode
  (phase 2) reads `.env` next to the EXE first, so the dev workflow is
  unchanged.
- [ ] 0.5 (H) High DPI: set `Qt.AA_EnableHighDpiScaling` and
  `Qt.AA_UseHighDpiPixmaps` before creating QApplication. Verify the
  layout at 150 percent scaling.
- [ ] 0.6 (M) Pause the sky animation while the window is minimized
  (changeEvent on WindowMinimized) to stop burning CPU on a hidden
  30 fps timer.
- [ ] 0.7 (M) Crash path in a windowed build: stdout and stderr are
  None with `--windowed`; sweep for stray `print(` and confirm the
  logger and crash dialog need neither stream.
- [ ] 0.8 (L) Single-instance guard (Qt QLockFile in the data
  directory): a second launch focuses the first instead of stacking.

## Phase 1: Build pipeline (the EXE)

- [ ] 1.1 (M) A real icon file: generate a multi-size `app.ico`
  (16 to 256 px) from the clear-sky SVG with a small build script
  (Pillow, dev-only dependency). Commit the `.ico`; the window icon
  code keeps using the SVG.
- [ ] 1.2 (H) PyInstaller spec: onedir (faster startup than onefile,
  friendlier to antivirus), windowed, icon, bundled resources and
  VERSION, pinned `pyinstaller` in a new `requirements-build.txt`.
- [ ] 1.3 (L) Windows version-info resource so file properties show
  the version from the VERSION file.
- [ ] 1.4 (M) One build script (`build.ps1`) that: runs the test
  suite, builds the icon, runs PyInstaller, runs the secret scan
  (0.2), and zips the artifact.
- [ ] 1.5 (H) EXE smoke test script: launch the built EXE, run a
  search against the live API, cycle the six conditions, force a bad
  city, confirm the error path and that data files landed in the data
  directory.

## Phase 2: Installer

- [ ] 2.1 (H) Inno Setup script: app name and version read from the
  VERSION file, Program Files default with per-user option, Start
  Menu and optional desktop shortcuts, uninstall entry.
- [ ] 2.2 (M) Uninstaller offers to keep user data (key, settings,
  favorites) and defaults to keeping it.
- [ ] 2.3 (M) Portable zip variant: the onedir tree plus a README
  line; `.env` next to the EXE works without any install or admin
  rights.
- [ ] 2.4 (L) Verify a clean Windows profile can run the installer
  with no admin prompt in per-user mode and no missing runtime
  messages.

## Phase 3: User-facing finish

- [ ] 3.1 (M) About dialog (Help menu or title bar button): app name,
  version from the VERSION file, a short description, the data folder
  path, and an offer to open it. No repo link while the repo is
  private.
- [ ] 3.2 (H) First-run key setup UX from 0.4: dialog copy, validation
  feedback, and a clear path to change the key later.
- [ ] 3.3 (M) README release section: install from the installer, run
  portable, run from source. Refresh public screenshots under
  `docs/screenshots/` (the previews in `instance/` are private on
  purpose).
- [ ] 3.4 (L) Keyboard shortcuts pass: Enter already searches; add
  Ctrl+F to focus the search box and F1 for About.
- [ ] 3.5 (M) VERSION bump to 1.0.0 and the changelog entry.

## Phase 4: Verify and ship

- [ ] 4.1 (H) Full pytest suite green plus a coverage report captured
  for the release notes.
- [ ] 4.2 (H) Clean-machine manual pass (fresh Windows user or VM):
  install, first run, key setup, search, all six condition themes,
  favorites, unit toggle, auto refresh, offline cache behavior,
  uninstall. Follow `release_checklist.md`.
- [ ] 4.3 (M) `release_checklist.md` executed and filed with the
  release (it was refreshed alongside this plan).
- [ ] 4.4 (M) GitHub release: tag `v1.0.0`, installer and portable zip
  attached, SHA-256 checksums in the notes. The repo is private, so
  the release is too.
- [ ] 4.5 (L) Post-release watch: missing-DLL reports, antivirus
  false positives (common for unsigned PyInstaller builds), and the
  first lines of real user logs if anyone shares them.

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

## Out of scope for this release

- Code signing (no certificate; Windows SmartScreen will warn on
  first run. Accept and document).
- Auto-update.
- macOS or Linux builds.
- `widgets/weather_animation.py` painter overlay (the sky widget
  covers the need).
- The remaining roadmap UX sprint items beyond 3.4 (loading spinner,
  fade transitions).

## Build-time dependency additions

- `requirements-build.txt`: pyinstaller (pinned), Pillow (pinned, icon
  generation). Never installed by end users.
- Inno Setup 6 on the build machine only; its script is committed.
