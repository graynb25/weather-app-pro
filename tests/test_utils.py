"""
test_utils.py
=============

Tests for the pure helpers in utils.py, with most of the weight on
redact_url, since it is the last thing standing between the API key and
a log file.
"""

from datetime import datetime, timezone

import pytest

from conftest import DUMMY_API_KEY
from utils import redact_url


@pytest.mark.parametrize("url", [
    # appid first
    f"https://api.openweathermap.org/data/2.5/weather?appid={DUMMY_API_KEY}&q=London",
    # appid in the middle
    f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={DUMMY_API_KEY}&units=imperial",
    # appid last
    f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={DUMMY_API_KEY}",
    # appid is the only parameter
    f"https://api.openweathermap.org/data/2.5/weather?appid={DUMMY_API_KEY}",
])
def test_redact_url_strips_the_key(url):
    result = redact_url(url)

    assert DUMMY_API_KEY not in result
    assert "appid=***" in result


def test_redact_url_keeps_other_parameters():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={DUMMY_API_KEY}&units=imperial"

    result = redact_url(url)

    assert "q=London" in result
    assert "units=imperial" in result


def test_redact_url_leaves_clean_urls_alone():
    url = "https://api.openweathermap.org/data/2.5/weather?q=London&units=imperial"

    assert redact_url(url) == url


@pytest.mark.parametrize("url", [
    f"https://api.openweathermap.org/data/2.5/weather?APPID={DUMMY_API_KEY}&q=London",
    f"https://api.openweathermap.org/data/2.5/weather?AppId={DUMMY_API_KEY}&q=London",
    f"https://api.openweathermap.org/data/2.5/weather?q=London&APPID={DUMMY_API_KEY}",
])
def test_redact_url_ignores_the_case_of_the_parameter(url):
    """
    redact_url is also handed text this app did not build, such as an
    exception message relayed from something that rewrote the
    parameter name, so the match must not be case sensitive.
    """

    result = redact_url(url)

    assert DUMMY_API_KEY not in result
    assert "***" in result


def test_redact_url_leaves_other_hex_values_alone():
    """
    Only the key parameter is touched. A 32 character hex value that
    belongs to something else must survive. The value is built at
    runtime so the release secret scan does not find a key-shaped
    literal sitting in the test file.
    """

    other_value = ("0123456789abcdef" * 2)

    url = f"https://example.com/thing?station={other_value}&appid={DUMMY_API_KEY}"

    result = redact_url(url)

    assert other_value in result
    assert DUMMY_API_KEY not in result


def test_unix_to_local_time_uses_the_city_offset():
    from utils import unix_to_local_time

    # 2026-01-05 12:00 UTC.
    stamp = int(datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc).timestamp())

    assert unix_to_local_time(stamp, 0) == "12:00 PM"
    assert unix_to_local_time(stamp, 3600) == "01:00 PM"
    assert unix_to_local_time(stamp, -11 * 3600) == "01:00 AM"


@pytest.mark.parametrize("temp_f, expected_c", [
    (32, 0.0),
    (212, 100.0),
    (-40, -40.0),
    (98.6, 37.0),
])
def test_fahrenheit_to_celsius(temp_f, expected_c):
    from utils import fahrenheit_to_celsius

    assert fahrenheit_to_celsius(temp_f) == pytest.approx(expected_c)


def test_speed_and_distance_helpers():
    from utils import (meters_to_km, meters_to_miles,
        miles_per_hour_to_kmh)

    assert miles_per_hour_to_kmh(1.0) == pytest.approx(1.609344)
    assert meters_to_miles(1609.34) == pytest.approx(1.0)
    assert meters_to_km(10_000) == pytest.approx(10.0)
