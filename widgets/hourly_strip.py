"""
hourly_strip.py
===============

The hourly strip from the redesign plan: a horizontally scrollable row
of glass chips for the next 24 hours (hour, condition icon, mono
temperature), fed from the forecast data already fetched.

The first chip is NOW and picks up the condition accent through the
same WeatherApp attribute selectors the other accent widgets use.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout

from managers.icon_manager import IconManager

CHIP_SIZE = 64
ICON_SIZE = 28
MAX_CHIPS = 8


class HourChip(QFrame):
    """
    One hour in the strip: hour label, icon, temperature.
    """

    def __init__(self):
        super().__init__()

        self.setObjectName("hourChip")

        self.hour_label = QLabel()
        self.hour_label.setObjectName("hourLabel")

        hour_font = self.hour_label.font()
        hour_font.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        self.hour_label.setFont(hour_font)
        self.hour_label.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(ICON_SIZE, ICON_SIZE)
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.temp_label = QLabel()
        self.temp_label.setObjectName("hourTemp")
        self.temp_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(6)

        layout.addWidget(self.hour_label)
        layout.addWidget(self.icon_label, 0, Qt.AlignCenter)
        layout.addWidget(self.temp_label)

        self.setLayout(layout)

    def update_chip(self, chip, is_now: bool) -> None:
        """
        Fill the chip from an HourData model.
        """

        self.hour_label.setText(chip.hour.upper())

        if is_now:
            self.hour_label.setObjectName("hourNow")
        else:
            self.hour_label.setObjectName("hourLabel")

        self.temp_label.setText(f"{chip.temperature_f:.0f}\u00b0")

        renderer = QSvgRenderer(IconManager.get_icon_path(chip.weather_id))

        pixmap = QPixmap(ICON_SIZE, ICON_SIZE)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        self.icon_label.setPixmap(pixmap)


class HourlyStrip(QFrame):
    """
    The scrollable row of hour chips.
    """

    def __init__(self):
        super().__init__()

        self.setObjectName("hourlyPanel")

        self.chip_row = QHBoxLayout()
        self.chip_row.setContentsMargins(10, 8, 10, 8)
        self.chip_row.setSpacing(8)
        self.chip_row.addStretch()

        chips_widget = QFrame()
        chips_widget.setObjectName("hourlyRow")
        chips_widget.setLayout(self.chip_row)

        scroll = QScrollArea()
        scroll.setObjectName("hourlyScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFixedHeight(CHIP_SIZE + 24)
        scroll.setWidget(chips_widget)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def update_hourly(self, hourly: list, accent: str = "") -> None:
        """
        Rebuild the chips from a list of HourData models.

        The accent parameter is accepted for symmetry with the
        forecast table; the NOW color comes from the stylesheet's
        condition selectors.
        """

        while self.chip_row.count() > 1:
            item = self.chip_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for index, chip in enumerate(hourly[:MAX_CHIPS]):
            widget = HourChip()
            widget.update_chip(chip, is_now=(index == 0))

            self.chip_row.insertWidget(self.chip_row.count() - 1, widget)
