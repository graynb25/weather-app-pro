"""
conftest.py
===========

Shared pytest fixtures and test-wide setup.

The dummy API key is set BEFORE anything imports weather_api, because
weather_api runs load_dotenv() at import time. load_dotenv() never
overrides an existing environment variable, so the dummy key survives
and the real key in .env can never enter the test process.
"""

import os

import pytest

# ---------------------------------------------------------
# Isolate tests from .env
# ---------------------------------------------------------

DUMMY_API_KEY = "test-dummy-key-12345"

os.environ.setdefault("OPENWEATHER_API_KEY", DUMMY_API_KEY)

import logging

from weather_api import WeatherAPI


class ListHandler(logging.Handler):
    """
    Capture formatted records from the app's own "weather" logger,
    without third-party debug output (requests_mock logs raw request
    URLs, key included, under its own logger name).
    """

    def __init__(self):
        super().__init__()
        self.formatted = []

    def emit(self, record):
        self.formatted.append(self.format(record))


import pytest


@pytest.fixture
def weather_log():
    handler = ListHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    app_logger = logging.getLogger("weather")
    app_logger.addHandler(handler)

    yield handler

    app_logger.removeHandler(handler)


# ---------------------------------------------------------
# Shared mock payloads
# ---------------------------------------------------------

VALID_CURRENT_PAYLOAD = {
    "name": "London",
    "sys": {"country": "GB", "sunrise": 1767763200, "sunset": 1767792000},
    "main": {
        "temp": 59.0,
        "feels_like": 57.2,
        "temp_min": 50.0,
        "temp_max": 64.4,
        "humidity": 72,
        "pressure": 1015,
    },
    "weather": [{"id": 500, "description": "light rain"}],
    "wind": {"speed": 8.0},
    "visibility": 10000,
    "timezone": 3600,
}


def forecast_item(dt: int, temp: float) -> dict:
    return {
        "dt": dt,
        "main": {"temp": temp},
        "weather": [{"id": 802, "description": "scattered clouds"}],
    }


VALID_FORECAST_PAYLOAD = {
    "city": {"timezone": 3600},
    "list": [
        forecast_item(1767763200, 50.0),
        forecast_item(1767849600, 60.0),
    ],
}


@pytest.fixture
def api() -> WeatherAPI:
    """
    A WeatherAPI client holding the dummy key.
    """

    return WeatherAPI()
