# Improvement Plans

This folder holds the project's documentation: the owner's reference docs plus
the working plans for improving Weather App Pro. Plans list items with a
severity and group them into phases. Work proceeds roughly in phase order, but
items from later phases can jump the queue if they are small and useful.

## Severity scale

| Level | Meaning |
|-------|---------|
| S     | Critical. Broken behavior, or a security or secret leak risk. Fix before anything else. |
| H     | High. A clear bug or a major usability gap. |
| M     | Medium. Worth doing, not urgent. |
| L     | Low. Polish and nice-to-haves. |

## Phase order

| Phase | Focus | Plan document |
|-------|-------|---------------|
| 1 | Error handling, exceptions, secret leak prevention, logging | error-handling-and-security.md |
| 2 | pytest suites and fixtures | testing-plan.md |
| 3 | Responsiveness and robustness (threads, retries, caching) | error-handling-and-security.md |
| 4 | UI modernization (themes, hero layout, hourly strip) | redesign-modernization.md |
| 5 | Planned features (favorites, settings, weather animations) | redesign-modernization.md |
| 6 | Release: frozen-app plumbing, EXE, installer, About, ship | release-plan.md |

Phases 1 and 2 overlap by design: the leak guard tests in phase 1 need the
test setup from phase 2. It is fine to build the test scaffolding first.

`roadmap.md` tracks the same work from the version and sprint angle: its UI
Sprint is phase 4, its UX Sprint items map to phases 1, 3, and 4, and its
Features section is phase 5. Update both views when items finish, or move
item tracking into one place if keeping two in sync gets old.

## Documents

### Plans (kept current as work happens)

- [error-handling-and-security.md](error-handling-and-security.md)
  Current failure modes with file and line references, the exception
  hierarchy, safe message rules, logging setup, and the phase 1 and 3 items.
- [testing-plan.md](testing-plan.md)
  Test stack, the suites to write, fixtures, coverage targets, and the
  rule that tests never read `.env`.
- [redesign-modernization.md](redesign-modernization.md)
  What mainstream weather apps do, what to adopt here, and the phase 4 and 5
  items including favorites, settings, and painter-based animations.
- [release-plan.md](release-plan.md)
  The phase 6 release sprint: frozen-app plumbing (data directory,
  bundled resources), legal and attribution (LICENSE, notices, privacy,
  the OpenWeatherMap attribution requirement), the build pipeline and
  secret scan, the Inno Setup installer and portable zip, the About
  dialog and first-run key setup, and verification. Items tagged
  S/H/M/L.

### Project reference (owner's docs)

- [roadmap.md](roadmap.md)
  Version history and feature sprints: UI Sprint, UX Sprint, Features,
  Release.
- [architecture.md](architecture.md)
  The intended architecture and data flow. Note: its folder tree uses target
  names (`models/`, `services/`, `styles/`) that do not exist as folders yet.
  Today those roles are filled by `weather_model.py`, `weather_api.py`, and
  `resources/styles/`. See `agent.md` section 3 for the tree that matches
  disk today.
- [coding_standards.md](coding_standards.md)
  Style rules: responsibilities per layer, comment and docstring rules.
  Treat this as the source of truth for code style; `agent.md` section 4
  summarizes the same rules with more concrete examples.
- [changelog.md](changelog.md)
  Version-by-version changes.
- [release_checklist.md](release_checklist.md)
  Pre-release checks for code, UI, testing, packaging, and docs.

## Status tracking

Each plan document ends with a checklist. Mark items `[x]` when the work is
merged into the app, add a matching entry to `changelog.md`, and note it in
`roadmap.md` when it closes a sprint item. When a plan item changes behavior
described in `README.md` or `agent.md`, update those files in the same change.
