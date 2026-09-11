"""
test_settings.py
================

Tests for Settings in settings.py: defensive IO, validation, and
persistence.
"""

import json

from settings import DEFAULTS, Settings


def test_missing_file_uses_defaults(tmp_path):
    settings = Settings(tmp_path / "settings.json")

    assert settings.get("units") == "imperial"
    assert settings.get("condition_mode") == "auto"
    assert settings.get("refresh_minutes") == 10
    assert settings.get("window") is None


def test_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(path)

    settings.set("units", "metric")
    settings.set("condition_mode", "night")
    settings.set("refresh_minutes", 30)
    settings.set("window", [100, 50, 1010, 930])

    reloaded = Settings(path)

    assert reloaded.get("units") == "metric"
    assert reloaded.get("condition_mode") == "night"
    assert reloaded.get("refresh_minutes") == 30
    assert reloaded.get("window") == [100, 50, 1010, 930]


def test_invalid_values_are_rejected(tmp_path):
    settings = Settings(tmp_path / "settings.json")

    settings.set("units", "kelvin")
    settings.set("refresh_minutes", 7)
    settings.set("condition_mode", "rainbow")
    settings.set("window", [0, 0, 10, 10])

    assert settings.get("units") == "imperial"
    assert settings.get("refresh_minutes") == 10
    assert settings.get("condition_mode") == "auto"
    assert settings.get("window") is None


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{ not json", encoding="utf-8")

    settings = Settings(path)

    assert settings.values == DEFAULTS


def test_legacy_empty_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("", encoding="utf-8")

    settings = Settings(path)

    assert settings.values == DEFAULTS


def test_non_dict_root_falls_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    settings = Settings(path)

    assert settings.values == DEFAULTS


def test_unknown_and_invalid_stored_keys_are_dropped(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({
        "units": "metric",
        "api_key": "should-never-be-kept",
        "refresh_minutes": "soon",
    }), encoding="utf-8")

    settings = Settings(path)

    assert settings.get("units") == "metric"
    assert settings.get("refresh_minutes") == 10
    assert "api_key" not in settings.values


def test_save_leaves_no_temp_file(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(path)

    settings.set("units", "metric")

    names = sorted(item.name for item in tmp_path.iterdir())

    assert names == ["settings.json"]
