"""
test_utils.py
=============

Tests for the pure helpers in utils.py, focused on redact_url.
"""

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
