"""
test_key_setup.py
=================

Tests for the first-run key helpers in geocoding.py: validate_key and
store_key.
"""

import pytest
import requests

import geocoding
from conftest import DUMMY_API_KEY
from config import GEO_URL
from geocoding import store_key, validate_key


@pytest.fixture
def key_file(tmp_path, monkeypatch):
    """
    Redirect the key file into the test's tmp directory.
    """

    path = tmp_path / "data" / ".env"
    path.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(geocoding.paths, "key_file", lambda: path)

    return path


def test_validate_key_accepts_a_working_key(requests_mock):
    requests_mock.get(GEO_URL, status_code=200, json=[])

    assert validate_key(DUMMY_API_KEY) is True


def test_validate_key_rejects_a_bad_key(requests_mock):
    requests_mock.get(GEO_URL, status_code=401, json={})

    assert validate_key(DUMMY_API_KEY) is False


def test_validate_key_treats_network_trouble_as_invalid(requests_mock):
    requests_mock.get(GEO_URL, exc=requests.exceptions.ConnectTimeout)

    assert validate_key(DUMMY_API_KEY) is False


def test_store_key_writes_a_dotenv_line(key_file):
    store_key(DUMMY_API_KEY)

    assert key_file.read_text(encoding="utf-8") == (
        "OPENWEATHER_API_KEY=" + DUMMY_API_KEY + "\n"
    )


def test_store_key_refuses_a_key_with_a_newline(key_file):
    """
    The file is dotenv format, so a key carrying a newline would be
    read back on the next start as extra variables. The app's own
    dotted key file must stay a single line.
    """

    with pytest.raises(ValueError):
        store_key("abc\nWEATHER_CONSOLE_LOG=1")

    assert not key_file.exists()


def test_store_key_refuses_a_key_with_a_carriage_return(key_file):
    with pytest.raises(ValueError):
        store_key("abc\rWEATHER_CONSOLE_LOG=1")

    assert not key_file.exists()


def test_store_key_accepts_a_key_with_a_hyphen(key_file):
    """
    Only control characters are refused. Whether a key works is
    decided by validate_key, not by guessing at the key format.
    """

    store_key("abc-123_def")

    assert key_file.read_text(encoding="utf-8") == (
        "OPENWEATHER_API_KEY=abc-123_def\n"
    )
