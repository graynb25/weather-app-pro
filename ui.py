"""
ui.py
======

Main user interface for Weather App Pro.

Responsibilities
----------------
- Build the graphical interface
- Respond to button clicks
- Display weather information
- Update the live clock
- Show errors through hand-written, safe messages

This file does NOT communicate directly with the
OpenWeatherMap API. All API requests go through
weather_api.py.
"""

import logging

from PyQt5.QtWidgets import (QWidget, QMainWindow, QLabel, QPushButton,
    QLineEdit, QVBoxLayout, QGridLayout, QActionGroup,
    QHBoxLayout, QFrame, QLayout, QGraphicsDropShadowEffect, QMenuBar, QAction)

from weather_api import WeatherAPI
from errors import WeatherAppError
from utils import meters_to_miles, unix_to_local_time
from datetime import datetime, timedelta, timezone
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt, QTimer
from managers.icon_manager import IconManager
from managers.flag_manager import FlagManager
from managers.theme_manager import ThemeManager
from forecast_card import ForecastCard
from weather_model import WeatherData, ForecastData
from widgets.lottie_widget import LottieWidget
from managers.animation_manager import AnimationManager
from widgets.detail_card import DetailCard

logger = logging.getLogger(f"weather.{__name__}")



class WeatherApp(QMainWindow):
    """
    Main application window.
    """

    def __init__(self):
        super().__init__()

        # Weather API object
        self.weather_api = WeatherAPI()

        # Stores the latest weather response
        self.weather_data = None

        # Updates the city clock every second
        self.timer = QTimer()

        # Current application theme
        self.current_theme = "light"

        # Build the window
        self.create_widgets()
        self.create_menu()
        self.create_layout()
        self.connect_signals()
        self.apply_styles()

        self.timer.start(1000)

    def load_weather_icon(self, weather_id: int) -> None:
        """
        Load and display the correct weather icon.
        """

        icon_path = IconManager.get_icon_path(weather_id)

        renderer = QSvgRenderer(icon_path)

        pixmap = QPixmap(140, 140)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignCenter)


    def load_flag(self, country_code: str) -> None:
        """
        Load and display a country flag.
        """

        flag_path = FlagManager.get_flag_path(country_code)

        renderer = QSvgRenderer(flag_path)

        pixmap = QPixmap(36, 36)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        self.flag_label.setPixmap(pixmap)


    def create_widgets(self):
        """
        Create every widget used in the application.

        No layouts are created here.
        No signals are connected here.

        This method ONLY creates widgets.
        """

        # -----------------------------
        # Search
        # -----------------------------

        self.flag_label = QLabel()
        self.city_label = QLabel("Enter City")
        self.city_input = QLineEdit()
        self.search_button = QPushButton("Get Weather")

        # -----------------------------
        # Main Weather
        # -----------------------------

        self.temperature_label = QLabel()
        self.celsius_label = QLabel()
        self.hero_animation = LottieWidget()
        self.hero_animation.setFixedSize(260, 260)
        self.description_label = QLabel()
        self.minmax_label = QLabel()

        # -----------------------------
        # Weather Details
        # -----------------------------

        self.feels_like_card = DetailCard()
        self.humidity_card = DetailCard()
        self.wind_card = DetailCard()
        self.visibility_card = DetailCard()
        self.pressure_card = DetailCard()
        self.sunrise_card = DetailCard()
        self.sunset_card = DetailCard()

        # -------------------------------------------------
        # Configure Detail Cards
        # -------------------------------------------------

        self.feels_like_card.set_title("Feels Like")
        self.feels_like_card.set_icon("feels_like")
        self.humidity_card.set_title("Humidity")
        self.humidity_card.set_icon("humidity")
        self.wind_card.set_title("Wind")
        self.wind_card.set_icon("wind")
        self.visibility_card.set_title("Visibility")
        self.visibility_card.set_icon("visibility")
        self.pressure_card.set_title("Pressure")
        self.pressure_card.set_icon("pressure")
        self.sunrise_card.set_title("Sunrise")
        self.sunrise_card.set_icon("sunrise")
        self.sunset_card.set_title("Sunset")
        self.sunset_card.set_icon("sunset")

        # -----------------------------
        # Forecast Cards
        # -----------------------------

        self.forecast_cards = []
        self.forecast_title = QLabel("5-Day Forecast")


        for _ in range(5):
            self.forecast_cards.append(
                ForecastCard()
            )

        # -----------------------------
        # Footer
        # -----------------------------

        self.time_label = QLabel()
        self.status_label = QLabel()

        self.city_label.setObjectName("city_label")
        self.city_input.setObjectName("city_input")
        self.search_button.setObjectName("search_button")

        self.temperature_label.setObjectName("temperature_label")
        self.celsius_label.setObjectName("celsius_label")
        self.hero_animation.setObjectName("hero_animation")
        self.description_label.setObjectName("description_label")
        self.minmax_label.setObjectName("minmax_label")

        self.forecast_title.setObjectName("forecast_title")

        self.status_label.setObjectName("status_label")
        self.time_label.setObjectName("time_label")

    def create_menu(self) -> None:
        """
        Create the application's menu bar.
        """

        menu_bar = self.menuBar()

        # -----------------------------------------------------
        # Theme Menu
        # -----------------------------------------------------

        theme_menu = menu_bar.addMenu("Theme")

        # Create the action group (only one theme can be selected)
        self.theme_group = QActionGroup(self)

        # Create actions
        self.light_theme_action = QAction("Light", self)
        self.dark_theme_action = QAction("Dark", self)

        # Make them checkable
        self.light_theme_action.setCheckable(True)
        self.dark_theme_action.setCheckable(True)

        # Add them to the group
        self.theme_group.addAction(self.light_theme_action)
        self.theme_group.addAction(self.dark_theme_action)

        # Set the default theme
        self.light_theme_action.setChecked(True)

        # Add to the menu
        theme_menu.addAction(self.light_theme_action)
        theme_menu.addAction(self.dark_theme_action)

        # Connect actions
        self.light_theme_action.triggered.connect(
            lambda: self.change_theme("light")
        )

        self.dark_theme_action.triggered.connect(
            lambda: self.change_theme("dark")
        )


    def create_layout(self) -> None:
        """
        Create and organize the application's layouts.
        """

        # =====================================================
        # Main Vertical Layout
        # =====================================================

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(24)

        # Header
        main_layout.addLayout(
            self.create_header_layout()
        )

        # Current search
        main_layout.addLayout(
            self.create_search_layout()
        )

        # Current weather
        hero_panel = self.create_panel(
            self.create_hero_layout(),
            "heroPanel"
        )

        hero_panel.setMaximumHeight(320)
        main_layout.addWidget(hero_panel)
        self.apply_shadow(hero_panel)


        # =====================================================
        # Weather Details Grid
        # =====================================================

        details_panel = self.create_panel(
            self.create_details_layout(),
            "detailsPanel"
        )

        details_panel.setMaximumHeight(360)
        main_layout.addWidget(details_panel)
        self.apply_shadow(details_panel)

        # =====================================================
        # Forecast Layout
        # =====================================================

        forecast_panel = self.create_panel(
            self.create_forecast_layout(),
            "forecastPanel"
        )

        forecast_panel.setMaximumHeight(320)
        main_layout.addWidget(forecast_panel)
        self.apply_shadow(forecast_panel)

        # =====================================================
        # Footer Layout
        # =====================================================

        main_layout.addLayout(
            self.create_footer_layout()
        )

        # =====================================================
        # Set Main Layout
        # =====================================================

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def create_panel(self, layout: QLayout, object_name: str) -> QFrame:
        """
        Create a reusable panel that wraps a layout
        inside a QFrame.
        """

        frame = QFrame()
        frame.setObjectName(object_name)
        frame.setLayout(layout)

        return frame

    def apply_shadow(self, widget) -> None:
        """
        Apply a subtle drop shadow to a widget.
        """

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 40))
        widget.setGraphicsEffect(shadow)


    def create_header_layout(self) -> QHBoxLayout:
        """
        Create the header containing the country flag
        and city name.
        """

        # =====================================================
        # Header Layout (Flag + City Name)
        # =====================================================

        # =====================================================
        # Search Section
        # =====================================================

        layout = QHBoxLayout()

        layout.addStretch()

        layout.addWidget(
            self.flag_label,
            alignment=Qt.AlignVCenter
        )

        layout.addSpacing(8)

        layout.addWidget(
            self.city_label,
            alignment=Qt.AlignVCenter
        )

        layout.addStretch()

        return layout

    def create_search_layout(self) -> QHBoxLayout:
        """
        Create the search section.
        """

        layout = QHBoxLayout()

        layout.addWidget(self.city_input)
        layout.addWidget(self.search_button)

        return layout

    def create_hero_layout(self) -> QVBoxLayout:
        """
        Create the main weather display.
        """

        # =====================================================
        # Main Hero Layout
        # =====================================================

        hero_layout = QHBoxLayout()

        hero_layout.setContentsMargins(20, 20, 20, 20)
        hero_layout.setSpacing(30)

        # =====================================================
        # Left Column (Animation)
        # =====================================================

        animation_layout = QVBoxLayout()

        animation_layout.addStretch()

        animation_layout.addWidget(
            self.hero_animation,
            alignment=Qt.AlignCenter
        )

        animation_layout.addStretch()

        # =====================================================
        # Right Column (Weather Info)
        # =====================================================

        info_layout = QVBoxLayout()

        info_layout.setSpacing(8)

        info_layout.addStretch()

        info_layout.addWidget(self.temperature_label)
        info_layout.addWidget(self.celsius_label)
        info_layout.addWidget(self.description_label)
        info_layout.addWidget(self.minmax_label)

        info_layout.addStretch()

        # =====================================================
        # Assemble Hero
        # =====================================================

        hero_layout.addLayout(animation_layout, 2)
        hero_layout.addLayout(info_layout, 3)

        return hero_layout

    def create_details_layout(self) -> QGridLayout:
        """
        Create the weather details section.
        """

        layout = QGridLayout()

        layout.setContentsMargins(20, 20, 20, 20)
        layout.setHorizontalSpacing(30)
        layout.setVerticalSpacing(28)

        # ---------- Row 1 ----------

        layout.addWidget(self.feels_like_card, 0, 0)
        layout.addWidget(self.humidity_card, 0, 1)
        layout.addWidget(self.wind_card, 0, 2)
        layout.addWidget(self.visibility_card, 0, 3)

        # ---------- Row 2 ----------

        layout.addWidget(self.pressure_card, 1, 0)
        layout.addWidget(self.sunrise_card, 1, 1)
        layout.addWidget(self.sunset_card, 1, 2)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)

        return layout

    def create_forecast_layout(self) -> QVBoxLayout:
        """
        Create the five-day forecast section.
        """

        layout = QVBoxLayout()

        layout.setSpacing(12)
        layout.setContentsMargins(10, 10, 10, 10)

        layout.addWidget(
            self.forecast_title,
            alignment=Qt.AlignCenter
        )

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        cards_layout.addStretch()

        for card in self.forecast_cards:
            cards_layout.addWidget(card)

        cards_layout.addStretch()
        layout.addLayout(cards_layout)

        return layout

    def create_footer_layout(self) -> QHBoxLayout:
        """
        Create the footer section.
        """

        layout = QHBoxLayout()
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.time_label)
        return layout


    def connect_signals(self) -> None:
        """
        Connect Qt signals to their corresponding methods.

        Signals are events generated by widgets, such as
        button clicks, pressing Enter, or timer timeouts.
        """

        # -----------------------------------------------------
        # Search Controls
        # -----------------------------------------------------

        # Clicking the button requests weather.
        self.search_button.clicked.connect(self.get_weather)

        # Pressing Enter inside the text box also requests weather.
        self.city_input.returnPressed.connect(self.get_weather)

        # -----------------------------------------------------
        # Timer
        # -----------------------------------------------------

        # Update the displayed clock every second.
        self.timer.timeout.connect(self.update_clock)

    def get_weather(self) -> None:
        """
        Retrieve weather information for the city entered by
        the user.
        """

        # -----------------------------------------------------
        # Read the city entered by the user
        # -----------------------------------------------------

        city = self.city_input.text().strip()

        # Make sure something was entered.
        if not city:
            self.display_error("Please enter a city.")
            return

        # -----------------------------------------------------
        # Request weather data
        # -----------------------------------------------------

        try:
            # -----------------------------------------------------
            # Retrieve current weather and forecast
            # -----------------------------------------------------

            weather = self.weather_api.get_current_weather(city)
            forecast = self.weather_api.get_forecast(city)

            # -----------------------------------------------------
            # Save the latest weather response
            # -----------------------------------------------------

            self.weather_data = weather

            # -----------------------------------------------------
            # Update the interface
            # -----------------------------------------------------

            self.display_weather(weather)
            self.display_forecast(forecast)

        except WeatherAppError as error:
            # user_message is hand-written in errors.py, so nothing from
            # the API, the URL, or the exception can reach the screen.
            logger.warning("Search for '%s' failed: %s",
                city, error.debug_detail or error.user_message)

            self.display_error(error.user_message)

        except Exception:
            # Unknown territory. Keep the trace in the log, show the
            # user nothing technical.
            logger.exception("Unexpected failure during the search for '%s'.", city)

            self.display_error("Something went wrong. See the log for details.")

    def change_theme(self, theme_name: str) -> None:
        """
        Apply the selected application theme.
        """

        self.current_theme = theme_name

        self.setStyleSheet(
            ThemeManager.load_theme(theme_name)
        )

        if theme_name == "light":
            self.light_theme_action.setChecked(True)
        else:
            self.dark_theme_action.setChecked(True)

    def display_weather(self, weather: WeatherData) -> None:


        self.city_label.setText(
            f"{weather.city}, {weather.country}"
        )

        self.load_flag(weather.country)

        self.temperature_label.setText(
            f"{weather.temperature_f:.0f}°F"
        )

        self.celsius_label.setText(
            f"{weather.temperature_c:.0f}°C"
        )

        self.hero_animation.set_animation(
            AnimationManager.get_weather_animation(
                weather.weather_id
            )
        )

        self.description_label.setText(
            weather.description
        )

        self.minmax_label.setText(
            f"Min: {weather.temp_min_f:.0f}°F / "
            f"{weather.temp_min_c:.0f}°C    "
            f"Max: {weather.temp_max_f:.0f}°F / "
            f"{weather.temp_max_c:.0f}°C"
        )

        # =====================================================
        # Update Weather Details
        # =====================================================

        self.feels_like_card.set_value(
            f"{weather.feels_like_f:.0f}°F\n{weather.feels_like_c:.0f}°C"
        )

        self.humidity_card.set_value(
            f"{weather.humidity}%"
        )

        self.wind_card.set_value(
            f"{weather.wind_speed:.1f} mph"
        )

        self.visibility_card.set_value(
            f"{meters_to_miles(weather.visibility):.1f} mi"
        )

        self.pressure_card.set_value(
            f"{weather.pressure} hPa"
        )

        # =====================================================
        # Sunrise / Sunset
        # =====================================================

        self.sunrise_card.set_value(
            unix_to_local_time(weather.sunrise, weather.timezone)
        )

        self.sunset_card.set_value(
            unix_to_local_time(weather.sunset, weather.timezone)
        )

        # =====================================================
        # Footer
        # =====================================================

        self.status_label.setText(
            f"Weather updated for {weather.city}"
        )

        self.update_clock()

    def display_forecast(self,forecast: list[ForecastData]) -> None:
        """
        Display the 5-day forecast.
        """

        for card, day in zip(self.forecast_cards, forecast):
            card.update_forecast(day)


    def display_error(self, message: str) -> None:
        """
        Display an error message.
        """

        self.status_label.setText(message)


    def update_clock(self) -> None:

        """
         Update the displayed local time for the selected city.
         """

        if self.weather_data is None:
            self.time_label.setText("--:--")
            return

        city_timezone = timezone(
            timedelta(seconds=self.weather_data.timezone)
        )

        city_time = datetime.now(city_timezone)

        self.time_label.setText(
            city_time.strftime("%I:%M:%S %p")
        )


    def apply_styles(self) -> None:
        """
        Apply the application's default stylesheet.

        Later, this method will load either the light or dark
        theme from external .qss files.
        """

        # -----------------------------------------------------
        # Window
        # -----------------------------------------------------

        self.setWindowTitle("Weather App Pro")
        self.resize(500, 700)

        # -----------------------------------------------------
        # Widget Alignment
        # -----------------------------------------------------

        self.city_label.setAlignment(Qt.AlignCenter)

        self.temperature_label.setAlignment(Qt.AlignCenter)
        self.description_label.setAlignment(Qt.AlignCenter)
        self.minmax_label.setAlignment(Qt.AlignCenter)
        self.celsius_label.setAlignment(Qt.AlignCenter)

        self.time_label.setAlignment(Qt.AlignRight)

        # -----------------------------------------------------
        # Default Text
        # -----------------------------------------------------

        self.temperature_label.setText("--°F")
        self.celsius_label.setText("--°C")
        self.description_label.setText("Search for a city")

        self.status_label.setText("Ready")

        # -----------------------------------------------------
        # Style Sheet
        # -----------------------------------------------------


        self.change_theme(self.current_theme)



