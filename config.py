# config.py

from pathlib import Path

# The app version, kept in the VERSION file next to this module and
# bumped with every release. Displayed in the footer and window title.
try:
    _version = (Path(__file__).resolve().parent / "VERSION").read_text(
        encoding="utf-8"
    ).strip()
except OSError:
    _version = "0.0.0"

APP_VERSION = f"v{_version}"

BASE_URL = "https://api.openweathermap.org/data/2.5"

GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"

GEO_LIMIT = 5                 # suggestions per autocomplete query

SUGGEST_DEBOUNCE_MS = 300     # idle time after typing before suggesting

CURRENT_WEATHER_ENDPOINT = "/weather"
FORECAST_ENDPOINT = "/forecast"

REQUEST_TIMEOUT = 10

RETRY_ATTEMPTS = 2               # retries after the first attempt
RETRY_BACKOFF_SECONDS = 0.5      # doubles with each retry
RETRY_AFTER_CAP_SECONDS = 30     # never wait longer than this on a 429

MAX_CITY_LENGTH = 85           # OpenWeatherMap's limit for the q parameter

REFRESH_INTERVAL = 600000      # 10 minutes in milliseconds

DEFAULT_UNITS = "imperial"     # "metric" or "imperial"

APP_TITLE = "Weather App Pro"