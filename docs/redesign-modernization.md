# Redesign and Modernization Plan

Phases 4 and 5 of the roadmap. This document first records what mainstream
weather apps do, then maps each idea onto this codebase with a severity.

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

### 4.1 Wire the condition themes (H)

`sunny.qss`, `cloudy.qss`, `rainy.qss`, and `snowy.qss` exist but
`change_theme()` only offers light and dark. After a successful search, map
`weather_id` to a condition theme (same id ranges as IconManager: 2xx
thunderstorm, 3xx/5xx rain, 6xx snow, 7xx fog or mist, 800 clear) and apply it,
keeping the manual light/dark menu choice as the base when no condition theme
fits. The menu needs a third choice: "Auto (match weather)".

### 4.2 Hero layout rework (H)

Rework `create_hero_layout()` so the temperature is the visual anchor: large
type (roughly 72pt), the Lottie animation beside or behind it, city and flag
above, description and min/max below in lighter text. Use the existing panels
and QSS object names; this is a layout and typography change, not new widgets.

### 4.3 Hourly strip (H)

The `/forecast` endpoint already returns 3-hourly entries. Add a horizontally
scrollable strip (`QScrollArea` with a row of small chips: hour, icon,
temperature) showing the next 12 to 24 hours. Reuse `ForecastCard` styling at
a smaller size, and feed it from the same API call the daily forecast already
makes (no second request; parse the same payload into an hourly model list).

### 4.4 Spacing and card polish (M)

Apply a consistent 8pt spacing grid, rounded corners, and hover states through
QSS. Keep shadows subtle. Cards should share one radius and one padding value
via `main.qss` instead of per-widget numbers.

### 4.5 Typography pass (M)

Pick one font family (Segoe UI Variable on Windows, with a fallback), define a
size scale in `main.qss` (display, title, body, caption), and stop mixing font
sizes per widget.

### 4.6 Dynamic background gradient (M)

With sunrise, sunset, and the city timezone already in `WeatherData`, set a
background gradient per condition plus day/night. Implement it as a QSS class
on the main panel or a `paintEvent` on a background widget, driven by a small
mapping (condition to palette) in one place.

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

### 5.3 Auto refresh (M)

Enable `config.REFRESH_INTERVAL` with a `QTimer` re-fetching the current city.
Only works after error-handling plan item 3.4 (quiet failures) is done.
Interval configurable in settings.

### 5.4 weather_animation.py: painter-based effects (L)

Implement a light `QPainter` overlay for ambient effects (drifting clouds,
rain streaks, snow dots) as a cheaper alternative to Lottie for background
use, keeping Lottie for the hero and detail icons. Start with one effect
(rain) to prove the timer and performance budget, then decide whether the rest
are worth it.

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

- [ ] 4.1 condition themes wired
- [ ] 4.2 hero layout rework
- [ ] 4.3 hourly strip
- [ ] 4.4 spacing and card polish
- [ ] 4.5 typography pass
- [ ] 4.6 dynamic background gradient
- [ ] 4.7 unit toggle
- [ ] 4.8 search autocomplete
- [ ] 4.9 window and system polish
- [ ] 4.10 footer status improvements
- [ ] 5.1 settings persistence
- [ ] 5.2 favorites
- [ ] 5.3 auto refresh
- [ ] 5.4 painter-based weather effects
- [ ] 5.5 tests for each new feature
