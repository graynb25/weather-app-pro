"""
forecast_card.py
================

Reusable widget for displaying one day's weather forecast.

Each card displays:
    - Day of the week
    - Weather icon
    - Temperature
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QFrame

from managers.icon_manager import IconManager
from weather_model import ForecastData

class ForecastCard(QFrame):
    """
    Displays one day's forecast.
    """

    def __init__(self):
        super().__init__()

        self.setObjectName("forecastCard")

        self.create_widgets()
        self.create_layout()
        self.apply_styles()

    def create_widgets(self):
        self.day_label = QLabel("Mon")
        self.icon_label = QLabel()
        self.temperature_label = QLabel("--°")

    def create_layout(self):
        layout = QVBoxLayout()

        layout.addWidget(
            self.day_label,
            alignment=Qt.AlignCenter
        )
        layout.addWidget(
            self.icon_label,
            alignment=Qt.AlignCenter
        )
        layout.addWidget(
            self.temperature_label,
            alignment=Qt.AlignCenter
        )
        self.setLayout(layout)

    def apply_styles(self):
        """
        Apply non-theme styling.
        """

        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(115, 175)

    def load_weather_icon(self, weather_id: int) -> None:
        """
        Load the appropriate SVG weather icon.
        """

        icon_path = IconManager.get_icon_path(weather_id)

        renderer = QSvgRenderer(icon_path)

        pixmap = QPixmap(70, 70)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignCenter)

    def update_forecast(self, forecast: ForecastData) -> None:
        """
            Update the card using a ForecastData object.
            """

        self.day_label.setText(forecast.day)

        self.load_weather_icon(
            forecast.weather_id
        )

        self.temperature_label.setText(
            f"{forecast.temperature_f:.0f}°F\n"
            f"{forecast.temperature_c:.0f}°C"
        )