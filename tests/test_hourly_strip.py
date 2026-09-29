"""
test_hourly_strip.py
====================

Tests for HourlyStrip in widgets/hourly_strip.py.
"""

from weather_model import HourData
from widgets.hourly_strip import HourChip, HourlyStrip

from PyQt5.QtWidgets import QApplication


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
    Old chips must stop painting before they are freed, without ever
    becoming windows of their own.

    deleteLater() leaves the widget drawing at its old position until
    the event loop delivers the deferred delete, so each rebuild
    stacked another translucent layer and the row washed out to white.
    Hiding fixes that.

    Reparenting to null would also stop the painting, but it turns the
    chip into a top-level window that stays visible as a stray white
    box over the strip, on every search and every unit change. Those
    are the only actions that rebuild this row, which is why the
    symptom looked like a pop-up that came and went.
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

    for chip in old_chips:
        assert chip.isHidden(), "a replaced chip is still painting"
        assert chip.parent() is not None, \
            "a replaced chip was turned into a top-level window"

    # The row holds exactly the new set plus the trailing stretch.
    assert strip.chip_row.count() == len(sample_hourly()) + 1


def test_rebuilding_never_turns_a_chip_into_a_window(qtbot):
    """
    The regression guard for the stray white box.

    Reparenting a chip to null makes it a top-level window that stays
    visible over the strip, on every search and every unit change. A
    chip must never become a window, however many times the row is
    rebuilt. Only the chips this strip created are checked, so the
    assertion cannot be disturbed by other windows in the session.
    """

    strip = HourlyStrip()
    qtbot.addWidget(strip)

    seen = []

    for _ in range(5):
        strip.update_hourly(sample_hourly())
        # Hidden chips stay parented until their deferred delete runs,
        # so this grows on purpose: it collects every chip ever made.
        seen.extend(strip.findChildren(HourChip))
        QApplication.processEvents()

    assert seen

    for chip in seen:
        assert chip.isWindow() is False, "a chip became a top-level window"
