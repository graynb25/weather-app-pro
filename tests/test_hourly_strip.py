"""
test_hourly_strip.py
====================

Tests for HourlyStrip in widgets/hourly_strip.py.
"""

from weather_model import HourData
from widgets.hourly_strip import HourlyStrip


def sample_hourly() -> list:
    return [
        HourData(hour="NOW", temperature_f=85.0, temperature_c=29.4,
            weather_id=800),
        HourData(hour="3 PM", temperature_f=84.0, temperature_c=28.9,
            weather_id=800),
        HourData(hour="6 PM", temperature_f=81.0, temperature_c=27.2,
            weather_id=801),
    ]


def test_strip_builds_one_chip_per_hour(qtbot):
    strip = HourlyStrip()
    qtbot.addWidget(strip)

    strip.update_hourly(sample_hourly())

    # The layout keeps a trailing stretch, hence the offset.
    assert strip.chip_row.count() == len(sample_hourly()) + 1

    first = strip.chip_row.itemAt(0).widget()

    assert first.hour_label.text() == "NOW"
    assert first.temp_label.text() == "85°"
    assert not first.icon_label.pixmap().isNull()

    second = strip.chip_row.itemAt(1).widget()

    assert second.hour_label.text() == "3 PM"


def test_strip_clears_old_chips(qtbot):
    strip = HourlyStrip()
    qtbot.addWidget(strip)

    strip.update_hourly(sample_hourly())
    strip.update_hourly(sample_hourly()[:1])

    assert strip.chip_row.count() == 2


def test_strip_ignores_empty_updates(qtbot):
    strip = HourlyStrip()
    qtbot.addWidget(strip)

    strip.update_hourly([])

    assert strip.chip_row.count() == 1  # just the stretch
