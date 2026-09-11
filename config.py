# config.py

BASE_URL = "https://api.openweathermap.org/data/2.5"

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