"""
test_range_bar.py
=================

Tests for the range bar mapping math in range_bar.py.
"""

import pytest

from widgets.range_bar import segment_fractions


def test_day_range_maps_inside_the_week():
    start, end = segment_fractions(12, 21, week_lo=9, week_hi=25)

    assert start == pytest.approx((12 - 9) / 16)
    assert end == pytest.approx((21 - 9) / 16)


def test_extremes_span_the_full_track():
    start, end = segment_fractions(9, 25, week_lo=9, week_hi=25)

    assert start == pytest.approx(0.0)
    assert end == pytest.approx(1.0)


def test_degenerate_week_collapses_to_the_middle():
    start, end = segment_fractions(18, 18, week_lo=18, week_hi=18)

    assert start == pytest.approx(0.45)
    assert end == pytest.approx(0.55)


def test_inverted_day_range_is_repaired():
    # Bad data: lo above hi. The segment must stay valid and ordered.
    start, end = segment_fractions(21, 12, week_lo=9, week_hi=25)

    assert start <= end
