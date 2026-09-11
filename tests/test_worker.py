"""
test_worker.py
==============

Tests for WeatherWorker in weather_worker.py.

The worker's search slot is called directly (no event loop, no second
thread): PyQt emits signals synchronously to directly connected
callables, so results are captured without any threading.
"""

import pytest
import requests_mock

from conftest import VALID_CURRENT_PAYLOAD, VALID_FORECAST_PAYLOAD

from config import BASE_URL, CURRENT_WEATHER_ENDPOINT, FORECAST_ENDPOINT
from errors import CityNotFoundError, UNEXPECTED_ERROR_MESSAGE
from weather_worker import WeatherWorker

CURRENT_URL = BASE_URL + CURRENT_WEATHER_ENDPOINT
FORECAST_URL = BASE_URL + FORECAST_ENDPOINT


@pytest.fixture
def worker(api):
    """
    A WeatherWorker with recorders wired to both of its signals.
    """

    worker = WeatherWorker(api)

    worker.done = []
    worker.failed = []

    worker.search_done.connect(lambda w, f: worker.done.append((w, f)))
    worker.search_failed.connect(worker.failed.append)

    return worker


def mock_success(requests_mock) -> None:
    requests_mock.get(CURRENT_URL, status_code=200,
        json=VALID_CURRENT_PAYLOAD)
    requests_mock.get(FORECAST_URL, status_code=200,
        json=VALID_FORECAST_PAYLOAD)


def test_successful_search_emits_done(worker, requests_mock):
    mock_success(requests_mock)

    worker.search("London")

    assert len(worker.done) == 1
    assert worker.failed == []

    weather, forecast = worker.done[0]

    assert weather.city == "London"
    assert forecast[0].temperature_f == 50.0


def test_failed_search_emits_the_app_error(worker, requests_mock):
    requests_mock.get(CURRENT_URL, status_code=404, json={})

    worker.search("Atlantis")

    assert worker.done == []

    error = worker.failed[0]

    assert isinstance(error, CityNotFoundError)
    assert error.user_message == "City not found. Check the spelling and try again."


def test_unexpected_failure_is_wrapped(worker, api, monkeypatch):
    def boom(city):
        raise RuntimeError("bug in our own code")

    monkeypatch.setattr(api, "get_current_weather", boom)

    worker.search("London")

    error = worker.failed[0]

    assert error.user_message == UNEXPECTED_ERROR_MESSAGE
