"""
range_bar.py
============

The hi/lo temperature bar from the glass console forecast table.

Each bar shows where one day's temperatures sit inside the week's
range: a dim track with an accent gradient segment. The mapping math
is kept in a helper so tests can check it without painting.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QLinearGradient, QPainter
from PyQt5.QtWidgets import QWidget

TRACK_HEIGHT = 6.0
TRACK_RADIUS = 3.0
SEGMENT_MIN_WIDTH = 5.0

GRADIENT_FROM = "#4a90d9"


def segment_fractions(day_lo: float, day_hi: float,
    week_lo: float, week_hi: float) -> tuple[float, float]:
    """
    Map one day's range into 0 to 1 fractions of the week range.

    Degenerate week ranges (all five days identical) collapse onto the
    middle of the track instead of dividing by zero.
    """

    span = week_hi - week_lo

    if span <= 0:
        return 0.45, 0.55

    start = (day_lo - week_lo) / span
    end = (day_hi - week_lo) / span

    # A day can report a lo above its own hi on bad data; keep the
    # segment valid either way.
    start, end = min(start, end), max(start, end)

    return max(0.0, start), min(1.0, end)


class RangeBar(QWidget):
    """
    One painted hi/lo bar for the forecast table.
    """

    def __init__(self):
        super().__init__()

        self.setObjectName("rangeBar")

        self._start = 0.0
        self._end = 1.0
        self._accent = "#6fb3ff"

        self.setFixedHeight(12)

    def set_data(self, day_lo: float, day_hi: float,
        week_lo: float, week_hi: float, accent: str) -> None:
        """
        Update the bar's day range, the week range it sits in, and the
        condition accent color.
        """

        self._start, self._end = segment_fractions(
            day_lo, day_hi, week_lo, week_hi
        )

        self._accent = accent

        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        center = self.height() / 2.0

        track = QRectF(0, center - TRACK_HEIGHT / 2, width, TRACK_HEIGHT)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 36))
        painter.drawRoundedRect(track, TRACK_RADIUS, TRACK_RADIUS)

        x0 = self._start * width
        x1 = self._end * width

        if x1 - x0 < SEGMENT_MIN_WIDTH:
            midpoint = (x0 + x1) / 2
            x0 = midpoint - SEGMENT_MIN_WIDTH / 2
            x1 = midpoint + SEGMENT_MIN_WIDTH / 2

        gradient = QLinearGradient(QPointF(x0, 0), QPointF(x1, 0))
        gradient.setColorAt(0.0, QColor(GRADIENT_FROM))
        gradient.setColorAt(1.0, QColor(self._accent))

        segment = QRectF(x0, center - TRACK_HEIGHT / 2, x1 - x0, TRACK_HEIGHT)
        painter.setBrush(gradient)
        painter.drawRoundedRect(segment, TRACK_RADIUS, TRACK_RADIUS)

        painter.end()
