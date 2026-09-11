"""
test_contrast.py
================

WCAG 2.1 contrast checks for the glass console theme.

Every text color is composited over the real backgrounds it sits on
(glass panels, chips, and the accent pill, each over every gradient
stop of every condition) and must meet WCAG AA:

    4.5:1 for normal text
    3.0:1 for large text (hero values only)

The constants here mirror resources/styles/console.qss and
managers/condition_theme.py. If you tune a color in one place,
update it here too or these tests will tell you why you shouldn't.
"""

import pytest

from managers.condition_theme import PALETTES

# From console.qss: backgrounds
PANEL = (11, 16, 25, 170)        # status line, hero, tiles, forecast panel
CHIP = (11, 16, 25, 180)         # section titles, footer labels
PILL = (4, 8, 16, 150)           # behind the live badge and condition text

# From console.qss: text colors (r, g, b, alpha)
TEXT = (238, 242, 247, 255)          # values, rows, input text
TEXT_SOFT_205 = (238, 242, 247, 205)  # stat titles, hero meta, tags, units
TEXT_SOFT_190 = (238, 242, 247, 190)  # hero alt temperature
TEXT_CHIP = (238, 242, 247, 235)      # section titles and footer text
TEXT_LOCAL_190 = (238, 242, 247, 190)  # search placeholder
BUTTON_TEXT = (16, 21, 29, 255)

AA_NORMAL = 4.5
AA_LARGE = 3.0


def _srgb_to_linear(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _luminance(rgb) -> float:
    r, g, b = (channel / 255 for channel in rgb[:3])
    return (0.2126 * _srgb_to_linear(r)
        + 0.7152 * _srgb_to_linear(g)
        + 0.0722 * _srgb_to_linear(b))


def _composite(fg_rgba, bg_rgb) -> tuple:
    """Alpha composite an rgba color over an opaque rgb color."""
    alpha = fg_rgba[3] / 255

    return tuple(
        round(alpha * fg + (1 - alpha) * bg)
        for fg, bg in zip(fg_rgba[:3], bg_rgb[:3])
    )


def _contrast_ratio(fg_rgb, bg_rgb) -> float:
    light = max(_luminance(fg_rgb), _luminance(bg_rgb))
    dark = min(_luminance(fg_rgb), _luminance(bg_rgb))

    return (light + 0.05) / (dark + 0.05)


def _brightest_stops() -> dict:
    """
    The brightest gradient stop per condition, for text that sits on
    the sky (section titles, footer).
    """

    brightest = {}

    for condition, palette in PALETTES.items():
        stops = [_hex_to_rgb(palette[key]) for key in ("top", "mid", "bottom")]
        brightest[condition] = max(stops, key=_luminance)

    return brightest


def test_text_on_glass_panels_meets_aa():
    for condition, palette in PALETTES.items():
        for stop_name in ("top", "mid", "bottom"):
            panel_bg = _composite(PANEL, _hex_to_rgb(palette[stop_name]))

            values = _contrast_ratio(TEXT[:3], panel_bg)
            soft = _contrast_ratio(
                _composite(TEXT_SOFT_205, panel_bg), panel_bg
            )

            assert values >= AA_NORMAL, (condition, stop_name, values)
            assert soft >= AA_NORMAL, (condition, stop_name, soft)


def test_large_hero_text_meets_large_aa():
    for condition, palette in PALETTES.items():
        for stop_name in ("top", "mid", "bottom"):
            panel_bg = _composite(PANEL, _hex_to_rgb(palette[stop_name]))

            alt = _contrast_ratio(
                _composite(TEXT_SOFT_190, panel_bg), panel_bg
            )

            assert alt >= AA_LARGE, (condition, stop_name, alt)


def test_accent_text_on_the_pill_meets_aa():
    for condition, palette in PALETTES.items():
        accent = _hex_to_rgb(palette["accent"])

        for stop_name in ("top", "mid", "bottom"):
            panel_bg = _composite(PANEL, _hex_to_rgb(palette[stop_name]))
            pill_bg = _composite(PILL, panel_bg)

            ratio = _contrast_ratio(accent, pill_bg)

            assert ratio >= AA_NORMAL, (condition, stop_name, ratio)


def test_button_text_on_accent_meets_aa():
    for condition, palette in PALETTES.items():
        accent = _hex_to_rgb(palette["accent"])

        ratio = _contrast_ratio(BUTTON_TEXT[:3], accent)

        assert ratio >= AA_NORMAL, (condition, ratio)


def test_sky_chips_meet_aa_over_the_brightest_stop():
    for condition, stop_rgb in _brightest_stops().items():
        chip_bg = _composite(CHIP, stop_rgb)

        ratio = _contrast_ratio(
            _composite(TEXT_CHIP, chip_bg), chip_bg
        )

        assert ratio >= AA_NORMAL, (condition, ratio)


def test_search_placeholder_stays_readable():
    for condition, palette in PALETTES.items():
        for stop_name in ("top", "mid", "bottom"):
            input_bg = _composite(PANEL, _hex_to_rgb(palette[stop_name]))

            ratio = _contrast_ratio(
                _composite(TEXT_LOCAL_190, input_bg), input_bg
            )

            assert ratio >= AA_LARGE, (condition, stop_name, ratio)


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")

    return tuple(
        int(hex_color[index:index + 2], 16) for index in (0, 2, 4)
    )
