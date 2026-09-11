# Redesign and Modernization Plan

Phases 4 and 5 of the roadmap. This document first records what mainstream
weather apps do, then maps each idea onto this codebase with a severity.

Working visual previews of four full redesign styles live in
`instance/preview/` (local only, gitignored): open the HTML files in a
browser. The owner reviewed them in September 2026 and chose a mix of
the Data Console layout with the Living Gradient sky, built as
`05-glass-console.html`, now implemented in the app (see changelog
v0.6). Real screenshots of the running app are in
`instance/preview/app-screens/`.

## What other weather apps do

Findings from looking at current weather app UI patterns (Apple Weather, Google
Weather, and popular design showcases; sources listed at the end).

1. **Hero card.** The current conditions own the top of the screen: one huge
   temperature number, the condition name, and the location, usually over a
   gradient background that reflects the weather. Everything else is secondary.
2. **Hourly strip.** A horizontally scrollable row of chips, each showing an
   hour, a small icon, and a temperature, covering roughly the next 12 to 24
   hours. Users read this more often than the daily forecast.
3. **Card groups.** Details (wind, humidity, UV, pressure, visibility,
   sunrise/sunset) live in small rounded cards on a grid, not in one long list.
4. **Dynamic backgrounds.** Gradients or animated scenes change with the
   condition and the time of day (day blue, night navy, storm gray).
5. **Calm typography.** One font family, a strong size hierarchy, generous
   spacing, thin weights for secondary text.
6. **One-line summary.** A single sentence ("Light rain starting in 20 min")
   near the hero. Apple Weather does this well.
7. **Search with autocomplete.** As-you-type suggestions with country and
   region disambiguation instead of requiring exact spelling.

This app already has the bones of several of these: detail cards on a grid,
Lottie animations for conditions, condition themes sitting unused in
`resources/styles/`, and drop shadows via `apply_shadow()`. The plan below is
mostly about wiring and hierarchy, not rebuilding.

## Phase 4: Modernization

### 4.1 Wire the condition themes (done)

Replaced the light and dark menu with a Condition menu. The manual
light/dark sheets are retired; conditions come from
`managers/condition_theme.py`, which maps the weather id plus day or
night to one of six palettes (clear, cloudy, rain, snow, mist, night).
Auto follows the searched weather; the menu can pin any condition.

### 4.2 Hero layout rework (done)

The hero is now the console layout: a large monospace temperature with
the condition SVG icon at its left, and the condition name, feels like,
and hi/lo block on the right, all on a glass panel.

### 4.3 Hourly strip (H)

The `/forecast` endpoint already returns 3-hourly entries. Add a
horizontally scrollable strip (`QScrollArea` with a row of small chips: hour, icon,
temperature) showing the next 12 to 24 hours. Reuse the forecast data
already fetched (no second request; parse the same payload into an
hourly model list). Not part of the chosen glass console preview, so
this stays open as an optional addition.

### 4.4 Spacing and card polish (done)

The glass console theme (`resources/styles/console.qss`) defines one
panel radius, one glass background, and shared spacing.

### 4.5 Typography pass (done)

Segoe UI for prose, Consolas for values, and a size scale in
`console.qss` (hero, value, body, micro). Micro labels get letter
spacing through `QFont` since QSS has no `letter-spacing`.

### 4.6 Dynamic background gradient (done)

`widgets/sky_widget.py` paints the full-window gradient per condition
and hosts the ambient scene: drifting sun or moon with a radial glow,
twinkling stars, falling rain streaks, drifting snow, and slow cloud
or mist blobs. One `QTimer` drives the scene at roughly 30 frames per
second.

### 4.7 Unit toggle (M)

A menu action to switch between imperial and metric, refreshing the current
display immediately (models carry both F and C, so most of this is display
state). Persist it once settings exist (phase 5). Note that `DEFAULT_UNITS`
currently only affects the API request; the UI shows both units everywhere,
which the toggle replaces.

### 4.8 Search autocomplete (M)

Use the OpenWeatherMap geocoding endpoint (free, separate from `/weather`):
debounced (300 ms) requests while typing, show up to five suggestions with
city, state, and country, fill the search box on selection. Needs the same
background-worker treatment as searches (error-handling plan item 3.1) and the
same key-safety rules.

### 4.9 Window and system polish (L)

Minimum window size, centered first show, an application icon, a HiDPI check
on the icons, and a proper empty state before the first search (a short hint
plus two or three example cities).

### 4.10 Footer status improvements (L)

Show "Updated 5 minutes ago" using the timestamp of the last successful fetch,
and restore it after errors instead of leaving the error text as the last word.

## Phase 5: Planned features

These use the placeholder files that already exist. Implementation order:
settings first (favorites and refresh both want persisted state).

### 5.1 Settings (settings.py, settings.json) (M)

Persist units, theme choice, window geometry, and the auto refresh interval.
Wrap IO per error-handling plan item 3.6, store plain data only, and keep the
API key out of this file forever.

### 5.2 Favorites (favorites.py, favorites.json) (M)

A row of city chips under the search bar; clicking one fetches it. Add and
remove through a context menu. Cap the count (10 is plenty) and persist on
change, not on close.

### 5.3 Auto refresh (done)

Shipped in v0.5 with quiet failure handling: the last successful city is
re-fetched every `config.REFRESH_INTERVAL` (10 minutes). Interval
configuration moves into settings when 5.1 lands.

### 5.4 weather_animation.py: painter-based effects (done, via SkyWidget)

The painter-effects idea shipped inside `widgets/sky_widget.py` as the
condition scene (rain, snow, stars, clouds, sun and moon) rather than as
a separate overlay stub. The empty `weather_animation.py` placeholder
remains reserved for future full-window overlays on top of the sky.

### 5.5 Pytest coverage for new features (goes without saying)

Every feature above lands with tests in the suites defined in
`testing-plan.md` (model parsing for hourly data, settings and favorites IO
edge cases, autocomplete debounce logic as a pure function).

## Sources

- [Design for the User: Lessons from Weather Apps (UX Collective)](https://uxdesign.cc/design-for-the-user-lessons-from-weather-apps-c4f8d37bcf44)
- [Weather App Design Patterns for Hourly, Daily, and Radar Views](https://hira.wb.gov.in/guides/weather-app-design-patterns-for-hourly-daily-and-radar-views/)
- [Weather App UI Design: Beautiful and User-Friendly Interfaces](https://downloadfreebie.com/weather-app-ui-design/)
- [Hourly Weather UI showcase (Dribbble)](https://dribbble.com/search/hourly-weather)
- [Weather Forecast App UI case studies (Behance)](https://www.behance.net/search/projects/weather%2520forecast%2520app%2520ui%2520design)
- [OpenWeatherMap Current Weather API (for the geocoding and forecast endpoints)](https://openweathermap.org/current)

## Checklist

- [x] 4.1 condition themes wired
- [x] 4.2 hero layout rework
- [ ] 4.3 hourly strip
- [x] 4.4 spacing and card polish
- [x] 4.5 typography pass
- [x] 4.6 dynamic background gradient
- [ ] 4.7 unit toggle
- [ ] 4.8 search autocomplete
- [ ] 4.9 window and system polish
- [ ] 4.10 footer status improvements
- [ ] 5.1 settings persistence
- [ ] 5.2 favorites
- [x] 5.3 auto refresh
- [x] 5.4 painter-based weather effects
- [ ] 5.5 tests for each new feature
