"""
test_api.py
===========

Tests for WeatherAPI in weather_api.py.

Covers the phase 1 leak guard (docs/error-handling-and-security.md
item 1.7): a mock returns each failure status, and the dummy key must
appear in neither the raised user_message nor anything written to the
log. Also covers status mapping, input validation, payload validation,
and the success paths.
"""

import logging
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlparse

import pytest
import requests
import requests_mock
from requests_mock import ANY

from conftest import DUMMY_API_KEY, VALID_CURRENT_PAYLOAD, forecast_item

import weather_api
from config import MAX_CITY_LENGTH
from errors import (WeatherAppError, InvalidCityError, ApiKeyMissingError,
    ApiKeyInvalidError, CityNotFoundError, RateLimitError, ApiServiceError,
    NetworkError, ApiDataError)
from weather_api import WeatherAPI


# ---------------------------------------------------------
# Retry timing
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def fast_retries(monkeypatch):
    """
    Record retry sleeps instead of living them, so retry tests stay
    fast and can assert the exact backoff.
    """

    sleeps = []
    monkeypatch.setattr(weather_api, "time", SimpleNamespace(sleep=sleeps.append))
    return sleeps


# ---------------------------------------------------------
# Log capture
# ---------------------------------------------------------

class ListHandler(logging.Handler):
    """
    Capture formatted records from the app's own "weather" logger.

    caplog also collects third-party debug output (requests_mock logs
    the raw request URL, key included, under its own logger name), so
    the leak guard needs a handler scoped to the app's namespace.
    """

    def __init__(self):
        super().__init__()
        self.formatted = []

    def emit(self, record):
        self.formatted.append(self.format(record))


@pytest.fixture
def weather_log():
    handler = ListHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    app_logger = logging.getLogger("weather")
    app_logger.addHandler(handler)

    yield handler

    app_logger.removeHandler(handler)


# ---------------------------------------------------------
# Leak guard (plan item 1.7)
# ---------------------------------------------------------

def test_leak_guard_user_message_and_log_are_key_free(api, requests_mock, weather_log):
    """
    For every failure path, the dummy key must survive in neither the
    user_message nor the log. The positive control proves the redacted
    URL really was logged, so a silent logging change cannot pass this.
    """

    failures = [(401, ApiKeyInvalidError), (404, CityNotFoundError),
        (429, RateLimitError), (500, ApiServiceError)]

    for status, expected_error in failures:
        requests_mock.get(ANY, status_code=status, json={})

        with pytest.raises(WeatherAppError) as raised:
            api.get_current_weather("London")

        assert DUMMY_API_KEY not in raised.value.user_message

    requests_mock.get(ANY,
        exc=requests.exceptions.ConnectTimeout)

    with pytest.raises(NetworkError):
        api.get_current_weather("London")

    log_text = "\n".join(weather_log.formatted)

    assert "appid=***" in log_text
    assert DUMMY_API_KEY not in log_text


def test_leak_guard_forecast_path(api, requests_mock, weather_log):
    requests_mock.get(ANY, status_code=401, json={})

    with pytest.raises(WeatherAppError) as raised:
        api.get_forecast("London")

    log_text = "\n".join(weather_log.formatted)

    assert DUMMY_API_KEY not in raised.value.user_message
    assert "appid=***" in log_text
    assert DUMMY_API_KEY not in log_text


# ---------------------------------------------------------
# Status mapping
# ---------------------------------------------------------

@pytest.mark.parametrize("status,expected_error,expected_message", [
    (401, ApiKeyInvalidError,
     "The API key was rejected. Check OPENWEATHER_API_KEY in .env. "
     "New keys can take up to two hours to activate."),
    (404, CityNotFoundError,
     "City not found. Check the spelling and try again."),
    (429, RateLimitError,
     "Too many requests. Wait a minute and try again."),
    (500, ApiServiceError,
     "The weather service is having problems right now. Try again later."),
    (403, ApiServiceError,
     "The weather service is having problems right now. Try again later."),
])
def test_http_status_maps_to_the_right_error(api, requests_mock,
    status, expected_error, expected_message):

    requests_mock.get(ANY, status_code=status, json={})

    with pytest.raises(expected_error) as raised:
        api.get_current_weather("London")

    assert raised.value.user_message == expected_message


def test_connection_error_becomes_network_error(api, requests_mock):
    requests_mock.get(ANY,
        exc=requests.exceptions.ConnectionError("connection refused"))

    with pytest.raises(NetworkError) as raised:
        api.get_current_weather("London")

    assert raised.value.user_message == (
        "Could not reach the weather service. Check your internet connection.")


def test_timeout_becomes_network_error(api, requests_mock):
    requests_mock.get(ANY, exc=requests.exceptions.Timeout)

    with pytest.raises(NetworkError) as raised:
        api.get_forecast("London")

    assert raised.value.user_message == (
        "The request timed out. Check your internet connection and try again.")


# ---------------------------------------------------------
# Missing key
# ---------------------------------------------------------

def test_missing_key_raises_before_any_request(api, requests_mock):
    api.api_key = None

    requests_mock.get(ANY, status_code=200, json={})

    with pytest.raises(ApiKeyMissingError):
        api.get_current_weather("London")

    with pytest.raises(ApiKeyMissingError):
        api.get_forecast("London")

    assert requests_mock.called is False


# ---------------------------------------------------------
# City input validation
# ---------------------------------------------------------

def test_city_whitespace_is_collapsed(api, requests_mock):
    requests_mock.get(ANY, status_code=200,
        json=VALID_CURRENT_PAYLOAD)

    api.get_current_weather("  London   New   York  ")

    # requests_mock lowercases its .query proxy, so parse the URL.
    params = dict(parse_qsl(urlparse(requests_mock.last_request.url).query))

    assert params["q"] == "London New York"


@pytest.mark.parametrize("bad_city", ["", "   ", "\t\n"])
def test_empty_city_is_rejected(api, requests_mock, bad_city):
    with pytest.raises(InvalidCityError) as raised:
        api.get_current_weather(bad_city)

    assert raised.value.user_message == "Please enter a city name."
    assert requests_mock.called is False


@pytest.mark.parametrize("bad_city", ["London\x00", "London\x1f", "Kyiv\x7f"])
def test_control_characters_are_rejected(api, requests_mock, bad_city):
    with pytest.raises(InvalidCityError) as raised:
        api.get_current_weather(bad_city)

    assert raised.value.user_message == (
        "That does not look like a valid city name.")
    assert requests_mock.called is False


def test_city_at_length_limit_is_accepted(api, requests_mock):
    requests_mock.get(ANY, status_code=200,
        json=VALID_CURRENT_PAYLOAD)

    api.get_current_weather("a" * MAX_CITY_LENGTH)

    assert requests_mock.called is True


def test_city_over_length_limit_is_rejected(api, requests_mock):
    with pytest.raises(InvalidCityError) as raised:
        api.get_current_weather("a" * (MAX_CITY_LENGTH + 1))

    assert raised.value.user_message == "City names are limited to 85 characters."
    assert requests_mock.called is False


# ---------------------------------------------------------
# Payload validation
# ---------------------------------------------------------

@pytest.mark.parametrize("broken_payload", [
    {},
    {"name": "London"},
    {"name": "London", "main": {}, "weather": [{"id": 500, "description": "x"}]},
    {"name": "London", "main": {"temp": 59.0}, "weather": []},
])
def test_malformed_current_payload_raises_api_data_error(api, requests_mock,
    broken_payload, weather_log):

    requests_mock.get(ANY, status_code=200, json=broken_payload)

    with pytest.raises(ApiDataError) as raised:
        api.get_current_weather("London")

    assert raised.value.user_message == (
        "The weather service sent data this app does not understand.")

    # The shape is logged as keys and paths only, never values.
    log_text = "\n".join(weather_log.formatted)

    assert "Unexpected payload shape" in log_text
    assert DUMMY_API_KEY not in log_text


@pytest.mark.parametrize("broken_payload", [
    {},
    {"list": []},
    {"city": {"timezone": 3600}, "list": []},
    {"city": {"timezone": 3600}, "list": [{"dt": 1767763200}]},
])
def test_malformed_forecast_payload_raises_api_data_error(api, requests_mock,
    broken_payload):

    requests_mock.get(ANY, status_code=200, json=broken_payload)

    with pytest.raises(ApiDataError):
        api.get_forecast("London")


def test_non_json_response_raises_api_data_error(api, requests_mock):
    requests_mock.get(ANY, status_code=200, text="<html>oops</html>")

    with pytest.raises(ApiDataError):
        api.get_current_weather("London")


# ---------------------------------------------------------
# Retries (plan item 3.2)
# ---------------------------------------------------------

def test_server_errors_are_retried_with_backoff(api, requests_mock, fast_retries):
    requests_mock.get(ANY, status_code=500, json={})

    with pytest.raises(ApiServiceError):
        api.get_current_weather("London")

    assert len(requests_mock.request_history) == 3
    assert fast_retries == [0.5, 1.0]


def test_connection_errors_are_retried(api, requests_mock, fast_retries):
    requests_mock.get(ANY, exc=requests.exceptions.ConnectionError("down"))

    with pytest.raises(NetworkError):
        api.get_current_weather("London")

    assert len(requests_mock.request_history) == 3
    assert fast_retries == [0.5, 1.0]


def test_retry_after_header_is_honored(api, requests_mock, fast_retries):
    requests_mock.get(ANY, [
        {"status_code": 429, "headers": {"Retry-After": "2"}, "json": {}},
        {"status_code": 200, "json": VALID_CURRENT_PAYLOAD},
    ])

    weather = api.get_current_weather("London")

    assert weather.city == "London"
    assert len(requests_mock.request_history) == 2
    assert fast_retries == [2]


def test_429_without_retry_after_fails_immediately(api, requests_mock):
    requests_mock.get(ANY, status_code=429, json={})

    with pytest.raises(RateLimitError):
        api.get_current_weather("London")

    assert len(requests_mock.request_history) == 1


def test_429_with_huge_retry_after_fails_immediately(api, requests_mock):
    requests_mock.get(ANY, status_code=429,
        headers={"Retry-After": "3600"}, json={})

    with pytest.raises(RateLimitError):
        api.get_current_weather("London")

    assert len(requests_mock.request_history) == 1


# ---------------------------------------------------------
# Success paths
# ---------------------------------------------------------

def test_get_current_weather_builds_the_model(api, requests_mock):
    requests_mock.get(ANY, status_code=200,
        json=VALID_CURRENT_PAYLOAD)

    weather = api.get_current_weather("London")

    assert weather.city == "London"
    assert weather.country == "GB"
    assert weather.temperature_f == pytest.approx(59.0)
    assert weather.temperature_c == pytest.approx(15.0)
    assert weather.description == "Light Rain"
    assert weather.weather_id == 500
    assert weather.humidity == 72
    assert weather.visibility == 10000

    params = dict(parse_qsl(urlparse(requests_mock.last_request.url).query))

    assert params["q"] == "London"
    assert params["appid"] == DUMMY_API_KEY


def test_get_forecast_picks_the_entry_closest_to_midday(api, requests_mock):
    # Local noon for two days, plus a morning entry that must lose.
    monday_noon = int(datetime(2026, 1, 5, 12, 0).timestamp())
    monday_morning = int(datetime(2026, 1, 5, 6, 0).timestamp())
    tuesday_noon = int(datetime(2026, 1, 6, 12, 0).timestamp())

    requests_mock.get(ANY, status_code=200, json={
        "city": {"timezone": 3600},
        "list": [
            forecast_item(monday_morning, 40.0),
            forecast_item(monday_noon, 50.0),
            forecast_item(tuesday_noon, 60.0),
        ],
    })

    forecast, hourly = api.get_forecast("London")

    assert [day.temperature_f for day in forecast] == [50.0, 60.0]
    assert [day.date for day in forecast] == ["2026-01-05", "2026-01-06"]
    assert [day.day for day in forecast] == ["Mon", "Tue"]
    assert forecast[0].temperature_c == pytest.approx(10.0)

    # Every entry is long past, so the strip keeps only the NOW chip.
    assert [chip.hour for chip in hourly] == ["NOW"]


def test_get_hourly_builds_future_chips(api, requests_mock):
    now = datetime.now(timezone.utc)

    # Ten future entries at three-hour steps, in a UTC+1 city.
    entries = [
        forecast_item(int(now.timestamp()) + index * 3 * 3600, 50.0 + index)
        for index in range(10)
    ]

    requests_mock.get(ANY, status_code=200, json={
        "city": {"timezone": 3600},
        "list": entries,
    })

    _, hourly = api.get_forecast("London")

    assert len(hourly) == 8
    assert hourly[0].hour == "NOW"
    assert hourly[0].temperature_f == pytest.approx(50.0)

    # Labels are the city-local hour in 12h form without a leading
    # zero, three hours apart.
    city_tz = timezone(timedelta(hours=1))

    for index, chip in enumerate(hourly[1:], start=1):
        local = (now + timedelta(hours=3 * index)).astimezone(city_tz)
        expected = local.strftime("%I %p").lstrip("0")

        assert chip.hour == expected, (index, chip.hour, expected)
