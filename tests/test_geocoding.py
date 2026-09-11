"""
test_geocoding.py
=================

Tests for Geocoder in geocoding.py: parsing, error mapping, key
safety, and input validation.
"""

import logging

import pytest
import requests
import requests_mock

from conftest import DUMMY_API_KEY
from config import GEO_URL
from errors import (InvalidCityError, ApiKeyMissingError, ApiKeyInvalidError,
    RateLimitError, ApiServiceError, NetworkError, ApiDataError)
from geocoding import Geocoder


@pytest.fixture
def geocoder():
    return Geocoder()


SAMPLE_PAYLOAD = [
    {"name": "Springfield", "state": "Illinois", "country": "US",
        "lat": 39.8, "lon": -89.6},
    {"name": "London", "country": "GB", "lat": 51.5, "lon": -0.12},
]


def test_parsing_builds_display_and_query(geocoder, requests_mock):
    requests_mock.get(GEO_URL, status_code=200, json=SAMPLE_PAYLOAD)

    results = geocoder.search("spring")

    assert len(results) == 2

    assert results[0].display == "Springfield, Illinois, US"
    assert results[0].query == "Springfield, US"

    assert results[1].display == "London, GB"
    assert results[1].query == "London, GB"


def test_query_goes_out_with_limit_and_key(geocoder, requests_mock):
    requests_mock.get(GEO_URL, status_code=200, json=SAMPLE_PAYLOAD)

    geocoder.search("spring")

    from urllib.parse import parse_qsl, urlparse

    params = dict(parse_qsl(urlparse(requests_mock.last_request.url).query))

    assert params["q"] == "spring"
    assert params["limit"] == "5"
    assert params["appid"] == DUMMY_API_KEY


def test_no_matches_returns_empty_list(geocoder, requests_mock):
    requests_mock.get(GEO_URL, status_code=200, json=[])

    assert geocoder.search("zzzz") == []


def test_404_counts_as_no_matches(geocoder, requests_mock):
    requests_mock.get(GEO_URL, status_code=404, json={})

    assert geocoder.search("zzzz") == []


@pytest.mark.parametrize("status,expected", [
    (401, ApiKeyInvalidError),
    (429, RateLimitError),
    (503, ApiServiceError),
])
def test_error_statuses_map_to_the_hierarchy(geocoder, requests_mock,
    status, expected):

    requests_mock.get(GEO_URL, status_code=status, json={})

    with pytest.raises(expected):
        geocoder.search("spring")


def test_network_failures_become_network_error(geocoder, requests_mock):
    requests_mock.get(GEO_URL, exc=requests.exceptions.ConnectTimeout)

    with pytest.raises(NetworkError):
        geocoder.search("spring")


def test_missing_key_raises_before_any_request(geocoder, requests_mock):
    geocoder.api_key = None

    with pytest.raises(ApiKeyMissingError):
        geocoder.search("spring")

    assert requests_mock.called is False


def test_non_list_payload_raises_api_data_error(geocoder, requests_mock):
    requests_mock.get(GEO_URL, status_code=200, json={"oops": True})

    with pytest.raises(ApiDataError):
        geocoder.search("spring")


def test_malformed_entries_are_skipped(geocoder, requests_mock):
    requests_mock.get(GEO_URL, status_code=200, json=[
        {"country": "US"},
        "junk",
        {"name": "London", "country": "GB"},
    ])

    results = geocoder.search("l")

    assert [result.display for result in results] == ["London, GB"]


def test_non_json_response_raises_api_data_error(geocoder, requests_mock):
    requests_mock.get(GEO_URL, status_code=200, text="<html>oops</html>")

    with pytest.raises(ApiDataError):
        geocoder.search("spring")


@pytest.mark.parametrize("bad_query", ["", "   ", "L\x00n", "a" * 86])
def test_invalid_query_is_rejected(geocoder, requests_mock, bad_query):
    with pytest.raises(InvalidCityError):
        geocoder.search(bad_query)

    assert requests_mock.called is False


def test_the_key_never_reaches_the_log(geocoder, requests_mock, weather_log):
    requests_mock.get(GEO_URL, status_code=401, json={})

    with pytest.raises(ApiKeyInvalidError):
        geocoder.search("London")

    log_text = "\n".join(weather_log.formatted)

    assert "appid=***" in log_text
    assert DUMMY_API_KEY not in log_text
