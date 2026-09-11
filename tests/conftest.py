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

from weather_api import WeatherAPI


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
