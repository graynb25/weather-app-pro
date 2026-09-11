"""
forecast_table.py
=================

The 5-day forecast table from the glass console design: one row per
day with the day name, a condition icon, a hi/lo range bar against the
week range, and the temperatures.

Feeds from the same list of ForecastData the app already receives, so
no extra API call. The accent color follows the active condition.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from managers.icon_manager import IconManager
from widgets.range_bar import RangeBar

ROW_COUNT = 5

ROW_GRID = (56, 34)


class ForecastRow(QFrame):
    """
    One day inside the forecast table.
    """

    def __init__(self, index: int):
        super().__init__()

        self.setObjectName("forecastRow")

        if index == 0:
            # The first row is today; QSS gives it a soft tint.
            self.setProperty("today", True)

        self.day_label = QLabel()
        self.day_label.setObjectName("forecastDay")

        day_font = self.day_label.font()
        day_font.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        self.day_label.setFont(day_font)

        self.icon_label = QLabel()

        # Reserved at full icon size so the row height is identical
        # before and after the first search; otherwise the window
        # grows taller once icons appear.
        self.icon_label.setMinimumSize(30, 30)

        self.range_bar = RangeBar()

        self.values_label = QLabel()
        self.values_label.setObjectName("forecastValues")

        row = QHBoxLayout()
        row.setContentsMargins(18, 12, 18, 12)
        row.setSpacing(16)

        row.addWidget(self.day_label, 0, Qt.AlignVCenter)
        row.addWidget(self.icon_label, 0, Qt.AlignVCenter)
        row.addWidget(self.range_bar, 1, Qt.AlignVCenter)
        row.addWidget(self.values_label, 0, Qt.AlignVCenter)

        self.setLayout(row)

    def update_day(self, day, accent: str, week_lo: float, week_hi: float,
        units: str = "imperial") -> None:
        """
        Fill the row from a ForecastData model, hi/lo in the
        selected unit.
        """

        if units == "metric":
            day_lo, day_hi = day.temp_min_c, day.temp_max_c
        else:
            day_lo, day_hi = day.temp_min_f, day.temp_max_f

        self.day_label.setText(day.day.upper())
        self.values_label.setText(
            f"{day_hi:.0f}\u00b0  /  {day_lo:.0f}\u00b0"
        )

        self.range_bar.set_data(
            day_lo,
            day_hi,
            week_lo,
            week_hi,
            accent,
        )

        renderer = QSvgRenderer(IconManager.get_icon_path(day.weather_id))

        pixmap = QPixmap(30, 30)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        self.icon_label.setPixmap(pixmap)


class ForecastTable(QFrame):
    """
    The full 5-day forecast table.
    """

    def __init__(self):
        super().__init__()

        self.setObjectName("forecastPanel")

        self.rows = [ForecastRow(index) for index in range(ROW_COUNT)]

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        for row in self.rows:
            layout.addWidget(row)

        self.setLayout(layout)

    def update_forecast(self, forecast: list, accent: str,
        units: str = "imperial") -> None:
        """
        Fill all rows from a list of ForecastData models, in the
        selected unit.

        The bars scale against the week's full range so the five days
        are comparable at a glance. The list is always the same length
        in practice, but short data only fills the rows it has.
        """

        if not forecast:
            return

        if units == "metric":
            low_field, high_field = "temp_min_c", "temp_max_c"
        else:
            low_field, high_field = "temp_min_f", "temp_max_f"

        week_lo = min(getattr(day, low_field) for day in forecast)
        week_hi = max(getattr(day, high_field) for day in forecast)

        for row, day in zip(self.rows, forecast):
            row.update_day(day, accent, week_lo, week_hi, units)
