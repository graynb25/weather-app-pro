# Weather App Pro Roadmap

## Version 1.0

- [x] Current Weather
- [x] 5-Day Forecast
- [x] Dark Theme
- [x] Light Theme
- [x] SVG Icons
- [x] Lottie Animations

---

## Hardening

Detail lives in docs/error-handling-and-security.md.

- [x] Exception hierarchy and safe error messages
- [x] API key leak fix, redaction, and leak guard test
- [x] Rotating file logging
- [x] Payload and city input validation
- [x] pytest scaffolding and first suites
- [x] Background network worker
- [x] Retries with backoff
- [x] Last result cache
- [x] Quiet auto refresh

---

## Code review, September 2026

Detail lives in docs/code-review-2026-09.md. Closed items from that
pass; the open work is in the review's next-steps section.

- [x] Hourly strip no longer washes out to white on rebuild
- [x] Forecast table keeps the selected units across a theme change
- [x] Forecast days and midday use the city timezone, not the owner's
- [x] Negative and malformed Retry-After no longer escape as a crash
- [x] API key check moved off the GUI thread
- [x] AnimationManager.animation_exists works and handles file URLs
- [x] store_key refuses a key carrying a control character
- [x] redact_url matches the key parameter case insensitively
- [x] App title comes from config.APP_TITLE
- [x] Settings no longer logs its own default on every launch
- [x] A restored window off every screen is brought back
- [x] Missing animation and icon fallback assets added
- [x] 225 tests, from 153
- [ ] CI workflow (the plan has wanted this since the project went public)
- [ ] Leak guard sees INFO and DEBUG records, not just ERROR
- [ ] test_contrast.py reads its colours from console.qss
- [ ] Regenerate or delete the stale coverage_report.txt
- [ ] Repair the changelog: two v1.0.3 sections, no v1.0.2
- [ ] Reconcile the four phase numbering schemes
- [ ] Resolve the checkboxes marked done with no artifact behind them
- [ ] Decide the fate of the dead code listed in the review

---

## UI Sprint

- [x] Hero redesign
- [x] Detail card redesign
- [x] Forecast redesign
- [ ] Responsive layouts (the one real UI gap; see the review)

---

## UX Sprint

- [ ] Loading animation
- [ ] Fade transitions
- [ ] Better error dialogs
- [ ] Keyboard shortcuts

---

## Features

- [x] Favorite Cities
- [ ] Recent Searches
- [x] Hourly Forecast
- [ ] Air Quality
- [ ] UV Index
- [ ] Moon Phase
- [ ] Weather Alerts

---

## Release

Detail lives in docs/release-plan.md (phase 6). Shipped in v1.0.0.

- [x] Installer
- [x] EXE
- [x] App icon file for the binary (window icon shipped in v0.11)
- [x] About dialog
- [x] Documentation