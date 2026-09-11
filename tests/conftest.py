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


@pytest.fixture
def api() -> WeatherAPI:
    """
    A WeatherAPI client holding the dummy key.
    """

    return WeatherAPI()
