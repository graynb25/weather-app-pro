"""
test_condition_theme.py
=======================

Tests for the condition mapping and palettes in ConditionTheme.
"""

import pytest

from managers.condition_theme import PALETTES, ConditionTheme


@pytest.mark.parametrize("weather_id,expected", [
    (200, "rain"), (202, "rain"), (299, "rain"),
    (300, "rain"), (321, "rain"),
    (500, "rain"), (501, "rain"), (599, "rain"),
    (600, "snow"), (622, "snow"),
    (701, "mist"), (741, "mist"), (781, "mist"),
])
def test_precipitation_and_atmosphere_map(weather_id, expected):
    assert ConditionTheme.from_weather(weather_id, is_day=True) == expected


def test_clear_sky_follows_day_and_night():
    assert ConditionTheme.from_weather(800, is_day=True) == "clear"
    assert ConditionTheme.from_weather(800, is_day=False) == "night"


def test_light_clouds_follow_day_and_night():
    assert ConditionTheme.from_weather(801, is_day=True) == "cloudy"
    assert ConditionTheme.from_weather(802, is_day=False) == "night"
    assert ConditionTheme.from_weather(803, is_day=False) == "cloudy"
    assert ConditionTheme.from_weather(804, is_day=True) == "cloudy"


def test_unknown_id_falls_back_to_rain():
    assert ConditionTheme.from_weather(999, is_day=True) == "rain"


def test_every_condition_has_a_complete_palette():
    required = {"top", "mid", "bottom", "accent"}

    for condition, palette in PALETTES.items():
        assert set(palette.keys()) == required, condition

        for key, value in palette.items():
            assert value.startswith("#"), (condition, key)
            assert len(value) == 7, (condition, key)


def test_palette_lookup_survives_unknown_keys():
    palette = ConditionTheme.palette("not-a-condition")

    assert ConditionTheme.is_known("not-a-condition") is False
    assert set(palette.keys()) == {"top", "mid", "bottom", "accent"}
