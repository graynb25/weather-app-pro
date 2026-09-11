"""
ui.py
======

Main user interface for Weather App Pro: the glass console design.

Responsibilities
----------------
- Build the graphical interface
- Respond to button clicks
- Display weather information
- Update the live clock
- Show errors through hand-written, safe messages
- Run searches on a background worker thread
- Auto refresh the last search on an interval
- Drive the condition themed sky and accent colors

This file does NOT communicate directly with the
OpenWeatherMap API. All API requests go through
weather_worker.py on its own thread.

Design source: instance/preview/05-glass-console.html (local preview).
"""

import logging

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (QWidget, QMainWindow, QLabel, QPushButton,
    QLineEdit, QVBoxLayout, QGridLayout, QActionGroup, QAction,
    QHBoxLayout, QFrame, QLayout, QScrollArea)

from weather_api import WeatherAPI
from weather_worker import WeatherWorker
from cache import WeatherCache
from config import REFRESH_INTERVAL
from errors import WeatherAppError
from managers.condition_theme import ConditionTheme
from managers.icon_manager import IconManager
from managers.flag_manager import FlagManager
from managers.theme_manager import ThemeManager
from utils import meters_to_miles, unix_to_local_time
from datetime import datetime, timedelta, timezone
from widgets.sky_widget import SkyWidget
from widgets.stat_tile import StatTile
from widgets.forecast_table import ForecastTable

logger = logging.getLogger(f"weather.{__name__}")

HERO_ICON_SIZE = 84
FLAG_HEIGHT = 22


class WeatherApp(QMainWindow):
    """
    Main application window.
    """

    # Carries the search text to the worker thread. Signals are the
    # only safe way across a thread boundary.
    search_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # Weather API object
        self.weather_api = WeatherAPI()

        # Stores the latest weather response
        self.weather_data = None

        # When the on-screen weather was fetched (None until first search)
        self.fetched_at = None

        # Updates the city clock every second
        self.timer = QTimer()

        # Repeats the last search on a fixed interval
        self.refresh_timer = QTimer()

        # Condition mode: "auto" follows the weather, anything else is
        # a manual condition key chosen in the menu
        self.condition_mode = "auto"
        self.current_condition = ConditionTheme.DEFAULT_CONDITION

        # Last successful search, kept on disk for offline starts
        self.weather_cache = WeatherCache()

        # True when the in-flight request came from the auto refresher
        self._search_is_auto = False

        # Accent color of the active condition, fed to the forecast
        # table's range bars when a forecast arrives
        self._forecast_accent = None
        self._last_forecast = None

        # Background search: the worker lives on its own thread so the
        # window never freezes while a request is in flight
        self.weather_thread = QThread()
        self.weather_worker = WeatherWorker(self.weather_api)
        self.weather_worker.moveToThread(self.weather_thread)

        # Build the window
        self.create_widgets()
        self.create_menu()
        self.create_layout()
        self.connect_signals()
        self.apply_styles()

        self.weather_thread.start()

        # Show the last successful search when starting offline
        cached = self.weather_cache.load()

        if cached is not None:
            weather, forecast, fetched_at = cached

            self.weather_data = weather
            self.fetched_at = datetime.fromtimestamp(fetched_at)

            self.display_weather(weather)
            self.display_forecast(forecast)

            self.status_label.setText(
                f"Showing saved weather for {weather.city} "
                f"from {self.fetched_at:%I:%M %p}."
            )

        self.timer.start(1000)

    # ---------------------------------------------------------
    # Widgets
    # ---------------------------------------------------------

    def create_widgets(self):
        """
        Create every widget used in the application.

        No layouts are created here.
        No signals are connected here.

        This method ONLY creates widgets.
        """

        # -----------------------------
        # Status line
        # -----------------------------

        self.status_line = QFrame()
        self.status_line.setObjectName("statusLine")

        self.flag_label = QLabel()
        self.station_label = QLabel("STATION: --")
        self.station_label.setObjectName("stationLabel")

        # The owner's local clock. Ticks every second like the city
        # clock, in 12h format with a small LOCAL tag.
        self.local_clock_label = QLabel("--:--")
        self.local_clock_label.setObjectName("localClock")

        self.local_tag_label = QLabel("LOCAL")
        self.local_tag_label.setObjectName("localTag")

        local_tag_font = self.local_tag_label.font()
        local_tag_font.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        self.local_tag_label.setFont(local_tag_font)

        self.live_badge = QLabel()
        self.live_badge.setObjectName("liveBadge")

        # -----------------------------
        # Search
        # -----------------------------

        self.city_input = QLineEdit()
        self.city_input.setObjectName("searchInput")
        self.city_input.setPlaceholderText("City name, 85 characters max")

        self.search_button = QPushButton("GET WEATHER")
        self.search_button.setObjectName("searchButton")

        # -----------------------------
        # Hero
        # -----------------------------

        self.glyph_label = QLabel()

        self.temperature_label = QLabel()
        self.temperature_label.setObjectName("heroTemp")

        self.celsius_label = QLabel()
        self.celsius_label.setObjectName("heroAlt")

        self.condition_text = QLabel()
        self.condition_text.setObjectName("conditionText")

        self.feels_label = QLabel()
        self.feels_label.setObjectName("heroMeta")

        self.minmax_label = QLabel()
        self.minmax_label.setObjectName("heroMeta")

        # -----------------------------
        # Measurement tiles
        # -----------------------------

        self.humidity_tile = StatTile("Humidity")
        self.wind_tile = StatTile("Wind")
        self.visibility_tile = StatTile("Visibility")
        self.pressure_tile = StatTile("Pressure")
        self.sunrise_tile = StatTile("Sunrise")
        self.sunset_tile = StatTile("Sunset")
        self.condition_tile = StatTile("Condition")
        self.updated_tile = StatTile("Updated")

        # -----------------------------
        # Forecast table
        # -----------------------------

        self.forecast_table = ForecastTable()

        # -----------------------------
        # Footer
        # -----------------------------

        self.status_label = QLabel()
        self.status_label.setObjectName("footerLabel")

        self.time_label = QLabel()
        self.time_label.setObjectName("footerLabel")

    def _micro_title(self, text: str) -> QLabel:
        """
        Create a spaced uppercase section title.
        """

        label = QLabel(text.upper())
        label.setObjectName("sectionTitle")

        font = label.font()
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.4)
        label.setFont(font)

        return label

    # ---------------------------------------------------------
    # Menu
    # ---------------------------------------------------------

    def create_menu(self) -> None:
        """
        Create the condition menu.

        Auto follows the searched weather; the other choices pin one
        condition so its sky and accent can be previewed any time.
        """

        menu_bar = self.menuBar()

        condition_menu = menu_bar.addMenu("Condition")

        self.condition_group = QActionGroup(self)

        self.condition_actions = {}

        for key in ("auto", "clear", "cloudy", "rain", "snow", "mist", "night"):
            action = QAction(key.capitalize(), self)
            action.setCheckable(True)

            self.condition_group.addAction(action)
            condition_menu.addAction(action)

            action.triggered.connect(
                lambda checked, chosen=key: self.set_condition_mode(chosen)
            )

            self.condition_actions[key] = action

        self.condition_actions["auto"].setChecked(True)

    def set_condition_mode(self, mode: str) -> None:
        """
        Apply a condition mode: "auto" or a pinned condition key.

        With no weather on screen yet, a pinned choice applies right
        away so the menu always gives visible feedback; "auto" simply
        waits for the first search.
        """

        self.condition_mode = mode

        if self.weather_data is not None:
            self.apply_condition(self.resolve_condition(self.weather_data))
        elif mode != "auto":
            self.apply_condition(mode)

    def resolve_condition(self, weather) -> str:
        """
        Work out the active condition for a weather result.
        """

        if self.condition_mode != "auto":
            return self.condition_mode

        now = datetime.now(timezone.utc).timestamp()
        is_day = weather.sunrise <= now <= weather.sunset

        return ConditionTheme.from_weather(weather.weather_id, is_day)

    def apply_condition(self, condition: str) -> None:
        """
        Paint the sky and recolor the accent widgets for a condition.

        The condition reaches QSS as a dynamic property on the window;
        repolishing makes the attribute selectors re-evaluate.
        """

        self.current_condition = condition

        self.sky.set_condition(condition)

        self.setProperty("condition", condition)

        style = self.style()
        for widget in self.sky.findChildren(QWidget):
            style.unpolish(widget)
            style.polish(widget)

        style.unpolish(self)
        style.polish(self)

        # Keep the range bars on the active accent, even when the
        # condition was pinned from the menu after a search.
        self._forecast_accent = ConditionTheme.accent(condition)

        if self._last_forecast is not None:
            self.forecast_table.update_forecast(
                self._last_forecast, self._forecast_accent
            )

    # ---------------------------------------------------------
    # Layout
    # ---------------------------------------------------------

    def create_layout(self) -> None:
        """
        Create and organize the application's layouts.
        """

        # The sky is the central widget: it paints the background and
        # hosts every panel.
        self.sky = SkyWidget()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 26, 30, 20)
        main_layout.setSpacing(17)

        # Status line
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(18, 11, 18, 11)
        status_layout.setSpacing(8)

        status_layout.addWidget(self.flag_label)
        status_layout.addSpacing(6)
        status_layout.addWidget(self.station_label)
        status_layout.addStretch()
        status_layout.addWidget(self.local_clock_label)
        status_layout.addSpacing(4)
        status_layout.addWidget(self.local_tag_label)
        status_layout.addSpacing(10)
        status_layout.addWidget(self.live_badge)

        self.status_line.setLayout(status_layout)
        main_layout.addWidget(self.status_line)

        # Search
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        search_layout.addWidget(self.city_input, 1)
        search_layout.addWidget(self.search_button)

        main_layout.addLayout(search_layout)

        # Hero
        hero_layout = QHBoxLayout()
        hero_layout.setContentsMargins(28, 24, 28, 24)
        hero_layout.setSpacing(32)

        hero_layout.addWidget(
            self.glyph_label, 0, Qt.AlignVCenter
        )

        temps_layout = QVBoxLayout()
        temps_layout.setSpacing(0)

        temps_layout.addWidget(self.temperature_label)
        temps_layout.addWidget(self.celsius_label)

        hero_layout.addLayout(temps_layout, 0)
        hero_layout.setAlignment(temps_layout, Qt.AlignVCenter)
        hero_layout.addStretch()

        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(4)

        meta_layout.addWidget(self.condition_text, 0, Qt.AlignRight)
        meta_layout.addWidget(self.feels_label, 0, Qt.AlignRight)
        meta_layout.addWidget(self.minmax_label, 0, Qt.AlignRight)

        hero_layout.addLayout(meta_layout, 0)
        hero_layout.setAlignment(meta_layout, Qt.AlignVCenter)

        hero_panel = QFrame()
        hero_panel.setObjectName("heroPanel")
        hero_panel.setLayout(hero_layout)

        main_layout.addWidget(hero_panel)

        # Measurements
        main_layout.addWidget(self._micro_title("Measurements"))

        grid = QGridLayout()
        grid.setSpacing(12)

        tiles = [
            self.humidity_tile, self.wind_tile,
            self.visibility_tile, self.pressure_tile,
            self.sunrise_tile, self.sunset_tile,
            self.condition_tile, self.updated_tile,
        ]

        for index, tile in enumerate(tiles):
            grid.addWidget(tile, index // 4, index % 4)

        main_layout.addLayout(grid)

        # Forecast
        main_layout.addWidget(
            self._micro_title("5-Day Forecast, hi / lo against the week range")
        )

        main_layout.addWidget(self.forecast_table)

        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(2, 8, 2, 2)
        footer_layout.setSpacing(10)

        footer_layout.addWidget(self.status_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.time_label)

        main_layout.addLayout(footer_layout)

        # The console content scrolls when the window is shorter than
        # its comfortable height, instead of Qt crushing the flexible
        # rows (which collapsed labels to zero height on short
        # screens).
        content = QWidget()
        content.setObjectName("consoleContent")
        content.setLayout(main_layout)

        scroll = QScrollArea()
        scroll.setObjectName("consoleScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(content)

        sky_layout = QVBoxLayout(self.sky)
        sky_layout.setContentsMargins(0, 0, 0, 0)
        sky_layout.addWidget(scroll)

        self.setCentralWidget(self.sky)

    # ---------------------------------------------------------
    # Signals
    # ---------------------------------------------------------

    def connect_signals(self) -> None:
        """
        Connect Qt signals to their corresponding methods.
        """

        # Clicking the button requests weather.
        self.search_button.clicked.connect(self.get_weather)

        # Pressing Enter inside the text box also requests weather.
        self.city_input.returnPressed.connect(self.get_weather)

        # Update the displayed clock every second.
        self.timer.timeout.connect(self.update_clock)

        # The signal hops threads safely; the worker never touches widgets.
        self.search_requested.connect(self.weather_worker.search)
        self.weather_worker.search_done.connect(self.on_search_done)
        self.weather_worker.search_failed.connect(self.on_search_failed)

        # Quietly repeat the last search on a fixed interval.
        self.refresh_timer.timeout.connect(self.auto_refresh)

    # ---------------------------------------------------------
    # Search flow
    # ---------------------------------------------------------

    def get_weather(self) -> None:
        """
        Retrieve weather information for the city entered by
        the user.
        """

        city = self.city_input.text().strip()

        # Make sure something was entered.
        if not city:
            self.display_error("Please enter a city.")
            return

        self.begin_search(city, auto=False)

    def begin_search(self, city: str, auto: bool) -> None:
        """
        Run one search on the worker thread.

        The search button disables until the worker reports back, so
        two requests can never overlap.
        """

        self._search_is_auto = auto

        self.search_button.setEnabled(False)
        self.status_label.setText("Searching...")

        self.search_requested.emit(city)

    def auto_refresh(self) -> None:
        """
        Repeat the last successful search without user action.

        A failed refresh keeps the previous display and only notes the
        failure in the status label, never a dialog.
        """

        if self.weather_data is None or not self.search_button.isEnabled():
            return

        self.begin_search(self.weather_data.city, auto=True)

    def on_search_done(self, weather, forecast) -> None:
        """
        Handle a successful background search.
        """

        self.weather_data = weather
        self.fetched_at = datetime.now()

        self.weather_cache.save(weather, forecast)

        self.display_weather(weather)
        self.display_forecast(forecast)

        self.search_button.setEnabled(True)

        self.refresh_timer.start(REFRESH_INTERVAL)

    def on_search_failed(self, error: WeatherAppError) -> None:
        """
        Handle a failed background search.

        The user sees the error's hand-written message. When older
        weather is already on screen, a note says when it is from.
        """

        self.search_button.setEnabled(True)

        if self._search_is_auto:
            logger.warning("Auto refresh failed: %s",
                error.debug_detail or error.user_message)

            message = f"Auto refresh failed at {datetime.now():%I:%M %p}."
        else:
            logger.warning("Search failed: %s",
                error.debug_detail or error.user_message)

            message = error.user_message

        if self.weather_data is not None and self.fetched_at is not None:
            message += f" Showing saved weather from {self.fetched_at:%I:%M %p}."

        self.display_error(message)

    # ---------------------------------------------------------
    # Display
    # ---------------------------------------------------------

    def load_weather_icon(self, weather_id: int) -> None:
        """
        Render the condition SVG into the hero glyph.
        """

        renderer = QSvgRenderer(IconManager.get_icon_path(weather_id))

        pixmap = QPixmap(HERO_ICON_SIZE, HERO_ICON_SIZE)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        self.glyph_label.setPixmap(pixmap)

    def load_flag(self, country_code: str) -> None:
        """
        Render the country flag into the status line, keeping the
        flag's own aspect ratio so it is never squashed.
        """

        renderer = QSvgRenderer(FlagManager.get_flag_path(country_code))

        source = renderer.defaultSize()

        if source.height() > 0:
            width = max(1, round(FLAG_HEIGHT * source.width() / source.height()))
        else:
            width = FLAG_HEIGHT

        pixmap = QPixmap(width, FLAG_HEIGHT)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        self.flag_label.setPixmap(pixmap)

    def display_weather(self, weather) -> None:
        """
        Fill every panel from a WeatherData model.
        """

        condition = self.resolve_condition(weather)
        self.apply_condition(condition)
        accent = ConditionTheme.accent(condition)

        self.load_weather_icon(weather.weather_id)
        self.load_flag(weather.country)

        self.station_label.setText(
            f"STATION: {weather.city.upper()}, {weather.country.upper()}"
        )

        self.live_badge.setText(f"\u25cf LIVE  {weather.description.upper()}")

        self.temperature_label.setText(f"{weather.temperature_f:.0f}\u00b0F")
        self.celsius_label.setText(f"{weather.temperature_c:.0f}\u00b0C")

        self.condition_text.setText(weather.description.upper())
        self.feels_label.setText(f"FEELS LIKE {weather.feels_like_f:.0f}\u00b0")
        self.minmax_label.setText(
            f"H {weather.temp_max_f:.0f}\u00b0   L {weather.temp_min_f:.0f}\u00b0"
        )

        self.humidity_tile.set_value(f"{weather.humidity}", "%")
        self.wind_tile.set_value(f"{weather.wind_speed:.0f}", "mph")
        self.visibility_tile.set_value(
            f"{meters_to_miles(weather.visibility):.0f}", "mi"
        )
        self.pressure_tile.set_value(f"{weather.pressure}", "hPa")
        self.sunrise_tile.set_value(
            unix_to_local_time(weather.sunrise, weather.timezone)
        )
        self.sunset_tile.set_value(
            unix_to_local_time(weather.sunset, weather.timezone)
        )
        self.condition_tile.set_value(f"{weather.weather_id}")

        fetched = self.fetched_at or datetime.now()
        self.updated_tile.set_value(f"{fetched:%I:%M %p}", "local")

        self._forecast_accent = accent

        self.status_label.setText(f"Weather updated for {weather.city}")

        self.update_clock()

    def display_forecast(self, forecast: list) -> None:
        """
        Display the 5-day forecast table.

        The table needs the active accent, which display_weather
        resolves before this is called.
        """

        self._last_forecast = forecast

        if self._forecast_accent is not None:
            self.forecast_table.update_forecast(forecast, self._forecast_accent)

    def display_error(self, message: str) -> None:
        """
        Display an error message.
        """

        self.status_label.setText(message)

    def update_clock(self) -> None:

        """
         Update the local clock and the city clock every second.
         """

        # The owner's local time. Always ticks, even before the first
        # search, in 12h format like the city clock.
        self.local_clock_label.setText(datetime.now().strftime("%I:%M:%S %p"))

        if self.weather_data is None:
            self.time_label.setText("--:--")
            return

        city_time = datetime.now(timezone(
            timedelta(seconds=self.weather_data.timezone)
        ))

        self.time_label.setText(city_time.strftime("%I:%M:%S %p"))

    # ---------------------------------------------------------
    # Shutdown
    # ---------------------------------------------------------

    def closeEvent(self, event) -> None:
        """
        Stop the background thread before the window goes away.
        """

        self.refresh_timer.stop()
        self.timer.stop()

        self.weather_thread.quit()
        self.weather_thread.wait(2000)

        event.accept()

    # ---------------------------------------------------------
    # Styles
    # ---------------------------------------------------------

    def apply_styles(self) -> None:
        """
        Apply the glass console stylesheet and window defaults.
        """

        self.setWindowTitle("Weather App Pro")
        self.setMinimumSize(820, 620)
        self.resize(1010, 860)

        # Defaults before the first search
        self.temperature_label.setText("--\u00b0F")
        self.celsius_label.setText("--\u00b0C")
        self.condition_text.setText("SEARCH FOR A CITY")
        self.feels_label.setText("FEELS LIKE --\u00b0")
        self.minmax_label.setText("H --\u00b0   L --\u00b0")
        self.live_badge.setText("\u25cf OFFLINE")
        self.local_clock_label.setText("--:--:-- --")
        self.status_label.setText("Ready")

        self.time_label.setAlignment(Qt.AlignRight)

        # The glass console theme. Accent colors follow the condition
        # through the dynamic property set in apply_condition.
        self.setStyleSheet(ThemeManager.load_theme("console"))

        self.apply_condition(self.current_condition)
