# Contributing to Weather App Pro

Thanks for your interest in the project. Weather App Pro is a small
personal project maintained by one person, so the process is light:
keep changes focused, keep secrets out, and keep the writing plain.

## Ground rules

- Never commit or share an API key. `.env` is gitignored. Get your own
  free key at openweathermap.org/appid for local testing, and never
  paste key material into issues, pull requests, or log excerpts.
- Never commit runtime files: `cache.json`, `settings.json`,
  `favorites.json`, `app.lock`, or anything in `logs/`. `.gitignore`
  already excludes them.
- No em dashes anywhere in the project: not in code, comments,
  user-facing strings, documentation, or commit messages. Use a comma,
  colon, or parentheses instead. Short plain sentences beat dense ones.
- Do not change anything in `old/`. It is legacy code kept for reference.
- Development and testing happen on Windows. Running from source on
  other platforms is untested, and building the EXE and installer is
  Windows-only (PyInstaller plus Inno Setup).

## Setup

1. Install Python 3.14 or newer.
2. Create and activate a virtual environment.
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
4. Copy `.env.example` to `.env` and put your own key in it:
   ```text
   OPENWEATHER_API_KEY=your_key_here
   ```
5. Run the app:
   ```bash
   python main.py
   ```

The README's Setup section has more detail, including the note that new
OpenWeatherMap keys can take up to two hours to activate.

## Tests

```bash
python -m pytest
```

- The suites live in `tests/`. They cover the API client (including the
  leak guard), workers, cache, settings, favorites, geocoding, paths,
  logging, condition theming, and smoke-level UI tests.
- Tests never read `.env` and never touch the network. `conftest.py`
  sets a dummy key before anything imports `weather_api`, and HTTP is
  stubbed with requests-mock.
- For coverage: `python -m pytest --cov`. The error paths matter more
  than the percentage.

## Manual GUI checks

Automated tests cover wiring, not looks. If you change the UI, run the
app and check the six condition themes (clear, cloudy, rain, snow,
mist, night) from the Condition menu, the unit toggle, the hourly
strip, the range bars, and the favorites bar. `python test_lottie.py`
renders one animation on its own. `docs/release_checklist.md` has the
full list used before each release.

## How the code is organized

The design is layered, and the dependency points one way: `ui.py` and
the widgets display data, workers run network calls on threads, and
`weather_api.py` and `geocoding.py` talk to OpenWeatherMap. The README
shows the file tree; `docs/architecture.md` and
`docs/coding_standards.md` hold the details. The rules that matter most
in practice:

- Widgets never call the API and never touch file paths. A search goes
  through WeatherWorker on its QThread, never a direct call on the GUI
  thread.
- Errors come from the hierarchy in `errors.py`. Each one carries a
  hand-written `user_message` for the screen and `debug_detail` for the
  log. The UI reads only `user_message`.
- Log request URLs only through `utils.redact_url`. The raw text of a
  requests exception embeds the URL, which contains the key.
- Constants live in `config.py`. Models are dataclasses in
  `weather_model.py`. Unit conversions come from the helpers in
  `utils.py`.
- Asset lookups go through the managers in `managers/` (icons, flags,
  animations, themes). Never hardcode asset paths in UI code.
- New widgets follow the `create_widgets()`, `create_layout()`,
  `apply_styles()` pattern and live in `widgets/`.
- Styling uses QSS object names in `resources/styles/console.qss` plus
  the palettes in `managers/condition_theme.py`, not per-widget
  `setStyleSheet`.

## Finding work

The plans in `docs/` list the known work with a severity scale (S
critical, H high, M medium, L low). `docs/README.md` is the index. For
anything bigger than a small fix, open an issue first and describe the
approach before writing code.

## Pull requests

- One change per pull request.
- Run the full test suite before opening the PR, and say in the
  description that it passed.
- If the change alters documented behavior, update `README.md` and the
  relevant plan in `docs/` in the same change. If it closes a plan
  item, add an entry to `docs/changelog.md`.
- Commit messages: short imperative summary, plain sentences, no em
  dashes. Example: "Fix the first-run key dialog crash".
- Keep the security properties intact: no key on the GUI, no key in
  logs, no technical error text on screen. Changes to `weather_api.py`,
  `weather_worker.py`, or logging must keep the leak guard tests green.

## Bug reports and feature requests

Open a GitHub issue with:

- The app version (the footer chip, or Help, About)
- Your OS and how you installed the app (installer, portable, source)
- Steps to reproduce, what happened, and what you expected
- If relevant, an excerpt from `logs/app.log`. The app already redacts
  the key from logged URLs, but check the excerpt before pasting, and
  never paste the contents of `.env`.

## Releases

The maintainer cuts releases. `build.ps1` runs the tests, generates the
icon and version resource, builds the EXE with PyInstaller, scans the
result for key material, and zips the portable build; the installer
comes from Inno Setup. See `docs/release-plan.md`. Contributors do not
need to build a release.

## License

By contributing, you agree that your contributions are licensed under
the MIT License that covers the project.
