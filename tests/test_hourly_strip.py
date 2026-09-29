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


def test_replaced_chips_stop_painting_immediately(qtbot):
    """
    Old chips must be detached, not only scheduled for deletion.

    deleteLater() leaves the widget a live child of the scroll area
    still painting at the same position until the event loop delivers
    the deferred delete. Because each chip is a translucent white over
    a dark panel, every rebuild stacked another layer and the strip
    washed out to white after a few searches. Detaching is what stops
    the stacking.
    """

    strip = HourlyStrip()
    qtbot.addWidget(strip)

    strip.update_hourly(sample_hourly())

    old_chips = [
        strip.chip_row.itemAt(index).widget()
        for index in range(strip.chip_row.count() - 1)
    ]

    assert old_chips

    strip.update_hourly(sample_hourly())

    # No old chip may still be parented into the row, which is what
    # keeps it from painting on top of the new ones.
    still_attached = [
        chip for chip in old_chips if chip.parent() is not None
    ]

    assert still_attached == []

    # The row holds exactly the new set plus the trailing stretch.
    assert strip.chip_row.count() == len(sample_hourly()) + 1
