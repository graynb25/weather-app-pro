"""
test_managers.py
================

Tests for the manager classes in managers/. These are the only place
that knows where an asset lives, so each test also asserts that the
returned path exists on disk. A mapping that points at a missing file
looks fine in code and renders as an empty space in the window.
"""

from pathlib import Path

import pytest

from managers.animation_manager import AnimationManager
from managers.condition_theme import (ConditionTheme, DEFAULT_CONDITION,
    PALETTES)
from managers.flag_manager import FlagManager
from managers.icon_manager import IconManager
from managers.theme_manager import ThemeManager


# ---------------------------------------------------------
# Icons
# ---------------------------------------------------------

@pytest.mark.parametrize("weather_id, expected", [
    (200, "thunderstorms.svg"),
    (232, "thunderstorms.svg"),
    (300, "drizzle.svg"),
    (321, "drizzle.svg"),
    (500, "rain.svg"),
    (531, "rain.svg"),
    (600, "snow.svg"),
    (622, "snow.svg"),
    (701, "fog.svg"),
    (741, "fog.svg"),
    (762, "volcano.svg"),
    (771, "wind.svg"),
    (781, "fog.svg"),
    (800, "clear-day.svg"),
    (801, "cloudy.svg"),
    (804, "cloudy.svg"),
    (999, "not-available.svg"),
])
def test_weather_icon_paths_exist(weather_id, expected):
    path = IconManager.get_icon_path(weather_id)

    assert path.endswith(expected)
    assert Path(path).exists()


def test_detail_icon_paths_exist():
    for name in IconManager.DETAIL_ICONS:
        assert Path(IconManager.get_detail_icon(name)).exists()

    assert Path(IconManager.get_detail_icon("no-such-detail")).exists()


# ---------------------------------------------------------
# Flags
# ---------------------------------------------------------

def test_flag_path_falls_back_for_an_unknown_country():
    known = FlagManager.get_flag_path("GB")
    unknown = FlagManager.get_flag_path("ZZ")

    assert Path(known).exists()
    assert Path(unknown).name == "not-available.svg"
    assert Path(unknown).exists()


def test_flag_lookup_ignores_case():
    assert FlagManager.get_flag_path("gb") == FlagManager.get_flag_path("GB")


# ---------------------------------------------------------
# Themes
# ---------------------------------------------------------

def test_console_theme_loads():
    text = ThemeManager.load_theme("console")

    assert "console" in text or "Glass" in text


def test_unknown_theme_falls_back_to_the_default():
    assert ThemeManager.load_theme("no-such-theme") == \
        ThemeManager.load_theme(ThemeManager.DEFAULT_THEME)

    assert ThemeManager.theme_exists("no-such-theme") is False


def test_every_shipped_theme_loads():
    for name in ThemeManager.available_themes():
        assert ThemeManager.theme_exists(name) is True
        assert ThemeManager.load_theme(name).strip()


# ---------------------------------------------------------
# Animations
# ---------------------------------------------------------

def test_animation_exists_reports_true_for_a_real_file():
    """
    This method used Path() without importing it, so every call raised
    NameError. A helper that cannot be called is worse than no helper.
    """

    path = AnimationManager.get_weather_animation(800)

    assert AnimationManager.animation_exists(path) is True


def test_animation_exists_reports_false_for_a_missing_file():
    assert AnimationManager.animation_exists(
        "no/such/animation.json"
    ) is False


@pytest.mark.parametrize("weather_id", [200, 300, 500, 600, 701, 762, 771,
    800, 801, 900])
def test_weather_animation_files_exist(weather_id):
    # The manager returns a file:// URL, so strip the scheme.
    url = AnimationManager.get_weather_animation(weather_id)

    assert url.startswith("file://")
    assert AnimationManager.animation_exists(url) is True


def test_detail_animation_files_exist():
    for name in AnimationManager.DETAIL_ANIMATIONS:
        url = AnimationManager.get_detail_animation(name)

        assert AnimationManager.animation_exists(url) is True

    assert AnimationManager.animation_exists(
        AnimationManager.get_detail_animation("no-such-detail")
    ) is True


# ---------------------------------------------------------
# Condition theme and the stylesheet it feeds
# ---------------------------------------------------------

def test_every_condition_id_maps_to_a_real_palette_key():
    for weather_id in range(1000):
        for is_day in (True, False):
            assert ConditionTheme.from_weather(weather_id, is_day) in PALETTES


def test_an_unknown_condition_falls_back_to_the_default_palette():
    assert ConditionTheme.palette("no-such-condition") == \
        PALETTES[DEFAULT_CONDITION]

    assert ConditionTheme.accent("no-such-condition") == \
        PALETTES[DEFAULT_CONDITION]["accent"]


def test_accent_comes_from_the_palette():
    for key, palette in PALETTES.items():
        assert ConditionTheme.accent(key) == palette["accent"]


def test_every_palette_entry_is_complete():
    for key, palette in PALETTES.items():
        assert set(palette) == {"top", "mid", "bottom", "accent"}, key

        for name, value in palette.items():
            assert value.startswith("#"), (key, name)
            assert len(value) == 7, (key, name)


def test_the_stylesheet_covers_every_palette_key():
    """
    console.qss recolors the search button, live badge, condition text
    and NOW chip through one selector per condition. A palette added
    to the table without those rules would silently keep the default
    blue, so the two lists are pinned to each other.
    """

    from managers.theme_manager import ThemeManager

    qss = (ThemeManager.STYLE_FOLDER / "console.qss").read_text(
        encoding="utf-8"
    )

    for key, palette in PALETTES.items():
        selector = f'WeatherApp[condition="{key}"]'

        assert selector in qss, key
        assert palette["accent"] in qss, key
