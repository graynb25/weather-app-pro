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
import os

import paths

from PyQt5.QtCore import Qt, QEvent, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QKeySequence, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (QWidget, QMainWindow, QLabel, QPushButton,
    QLineEdit, QVBoxLayout, QGridLayout, QActionGroup, QAction,
    QHBoxLayout, QFrame, QLayout, QScrollArea, QCompleter, QMessageBox,
    QShortcut)
from PyQt5.QtCore import QStringListModel
from geocoding import Geocoder

from config import APP_VERSION, SUGGEST_DEBOUNCE_MS
from favorites import Favorites
from weather_api import WeatherAPI
from weather_worker import WeatherWorker, SuggestWorker
from geocoding import store_key, validate_key
from cache import WeatherCache
from errors import WeatherAppError
from managers.condition_theme import ConditionTheme
from managers.icon_manager import IconManager
from managers.flag_manager import FlagManager
from managers.theme_manager import ThemeManager
from settings import REFRESH_MINUTES, Settings
from utils import (meters_to_km, meters_to_miles, miles_per_hour_to_kmh,
    unix_to_local_time)
from datetime import datetime, timedelta, timezone
from widgets.sky_widget import SkyWidget
from widgets.favorites_bar import FavoritesBar
from widgets.hourly_strip import HourlyStrip
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

    # Carries the autocomplete query to the suggest worker.
    suggest_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # Weather API object
        self.weather_api = WeatherAPI()

        # Persisted user settings: units, condition mode, refresh
        # interval, window geometry. Never holds the API key.
        self.settings = Settings()
        self.units = self.settings.get("units")

        # Persisted saved cities
        self.favorites = Favorites()

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
        self._last_hourly = None

        # Errors stay on the status line for half a minute before the
        # elapsed-time line takes the status back.
        self._error_until = None

        # Background search: the worker lives on its own thread so the
        # window never freezes while a request is in flight
        self.weather_thread = QThread()
        self.weather_worker = WeatherWorker(self.weather_api)
        self.weather_worker.moveToThread(self.weather_thread)

        # Autocomplete: a debounce timer batches typing, then a second
        # worker thread asks the geocoding API. Failures stay quiet.
        self.suggest_thread = QThread()
        self.suggest_worker = SuggestWorker(Geocoder())
        self.suggest_worker.moveToThread(self.suggest_thread)

        self.suggest_timer = QTimer()
        self.suggest_timer.setSingleShot(True)

        self.suggest_model = QStringListModel()

        self.completer = QCompleter(self.suggest_model, self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)

        self._suggestions = {}
        self._suggest_query = ""


        # Build the window
        self.create_widgets()
        self.create_menu()
        self.create_layout()
        self.connect_signals()
        self.apply_styles()

        self.weather_thread.start()
        self.suggest_thread.start()

        # Restore the saved window geometry when it is usable; the
        # first-show fit only runs when there is nothing to restore.
        saved = self.settings.get("window")

        if saved is not None:
            x, y, width, height = saved

            self.resize(width, height)
            self.move(x, y)
            self._window_size_fitted = True
            self._geometry_restored = True

        # Show the last successful search when starting offline
        cached = self.weather_cache.load()

        if cached is not None:
            weather, forecast, hourly, fetched_at = cached

            self.weather_data = weather
            self.fetched_at = datetime.fromtimestamp(fetched_at)

            self.display_weather(weather)
            self.display_forecast(forecast)
            self.display_hourly(hourly)

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
        self.city_input.setCompleter(self.completer)

        popup = self.completer.popup()

        if popup is not None:
            popup.setObjectName("suggestPopup")

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
        # Empty state: example cities
        # -----------------------------

        self.examples_row = QWidget()
        self.examples_row.setObjectName("examplesRow")

        examples_layout = QHBoxLayout(self.examples_row)
        examples_layout.setContentsMargins(0, 0, 0, 0)
        examples_layout.setSpacing(10)

        try_hint = QLabel("Try:")
        try_hint.setObjectName("stationLabel")
        examples_layout.addWidget(try_hint)

        for example in ("London", "Tokyo", "Bogota"):
            chip = QPushButton(example)
            chip.setObjectName("cityChip")
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(
                lambda checked=False, name=example: self.search_favorite(name)
            )
            examples_layout.addWidget(chip)

        examples_layout.addStretch()

        # -----------------------------
        # Favorites bar
        # -----------------------------

        self.favorites_bar = FavoritesBar()
        self.favorites_bar.set_cities(self.favorites.get())
        self.favorites_bar.set_add_enabled(False)

        # -----------------------------
        # Hourly strip and forecast table
        # -----------------------------

        self.hourly_strip = HourlyStrip()
        self.forecast_table = ForecastTable()

        # -----------------------------
        # Footer
        # -----------------------------

        self.status_label = QLabel()
        self.status_label.setObjectName("footerLabel")

        self.version_label = QLabel(APP_VERSION)
        self.version_label.setObjectName("footerLabel")

        # OpenWeatherMap's free plan requires visible attribution on
        # the screen where the data is shown. The link color is set
        # inline: rich-text links default to the palette's blue.
        self.attribution_label = QLabel(
            '<a href="https://openweathermap.org/">'
            '<span style="color:#dfe8f2;">'
            "Weather data provided by OpenWeather</span></a>"
        )
        self.attribution_label.setObjectName("footerLabel")
        self.attribution_label.setOpenExternalLinks(True)

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

        stored_mode = self.settings.get("condition_mode")

        if stored_mode in self.condition_actions:
            self.condition_mode = stored_mode
            self.condition_actions[stored_mode].setChecked(True)

            if stored_mode != "auto":
                self.current_condition = stored_mode
        else:
            self.condition_actions["auto"].setChecked(True)

        # -----------------------------------------------------
        # Settings menu
        # -----------------------------------------------------

        settings_menu = menu_bar.addMenu("Settings")

        self.units_group = QActionGroup(self)

        self.imperial_action = QAction("Imperial units", self)
        self.metric_action = QAction("Metric units", self)

        for action in (self.imperial_action, self.metric_action):
            action.setCheckable(True)
            self.units_group.addAction(action)
            settings_menu.addAction(action)

        settings_menu.addSeparator()

        refresh_menu = settings_menu.addMenu("Auto refresh")

        self.refresh_group = QActionGroup(self)
        self.refresh_actions = {}

        for minutes in REFRESH_MINUTES:
            action = QAction(f"{minutes} minutes", self)
            action.setCheckable(True)

            self.refresh_group.addAction(action)
            refresh_menu.addAction(action)

            action.triggered.connect(
                lambda checked, value=minutes: self.set_refresh_minutes(value)
            )

            self.refresh_actions[minutes] = action

        units_action = (
            self.imperial_action if self.units == "imperial"
            else self.metric_action
        )
        units_action.setChecked(True)

        self.imperial_action.triggered.connect(
            lambda: self.set_units("imperial")
        )
        self.metric_action.triggered.connect(
            lambda: self.set_units("metric")
        )

        self.refresh_actions[
            self.settings.get("refresh_minutes")
        ].setChecked(True)

        # -----------------------------------------------------
        # Help menu
        # -----------------------------------------------------

        help_menu = menu_bar.addMenu("Help")

        self.about_action = QAction("&About Weather App Pro", self)
        self.about_action.setShortcut("F1")
        help_menu.addAction(self.about_action)

        self.about_action.triggered.connect(self.show_about)

        # API key management lives in Settings so an installed copy
        # can replace a saved key without touching files by hand.
        api_key_action = QAction("API &key...", self)
        api_key_action.triggered.connect(self.offer_key_setup)
        settings_menu.addAction(api_key_action)

        # Ctrl+F jumps to the search box.
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.focus_search)

    def set_units(self, units: str) -> None:
        """
        Switch the display units and refresh everything on screen.

        The API always fetches imperial; the models carry both units,
        so this is pure display state.
        """

        if units == self.units:
            return

        self.units = units
        self.settings.set("units", units)

        if self.weather_data is not None:
            self.display_weather(self.weather_data)

            if self._last_forecast is not None:
                self.display_forecast(self._last_forecast)

            if self._last_hourly is not None:
                self.display_hourly(self._last_hourly)

    def set_refresh_minutes(self, minutes: int) -> None:
        """
        Persist a new auto refresh interval and apply it live.
        """

        self.settings.set("refresh_minutes", minutes)

        if self.refresh_timer.isActive():
            self.refresh_timer.start(minutes * 60_000)

    def set_condition_mode(self, mode: str) -> None:
        """
        Apply a condition mode: "auto" or a pinned condition key.

        With no weather on screen yet, a pinned choice applies right
        away so the menu always gives visible feedback; "auto" simply
        waits for the first search.
        """

        self.condition_mode = mode
        self.settings.set("condition_mode", mode)

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

        if self._last_hourly is not None:
            self.hourly_strip.update_hourly(self._last_hourly, self.units)

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
        main_layout.addWidget(self.favorites_bar)

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

        hero_box = QVBoxLayout()
        hero_box.setContentsMargins(0, 0, 0, 0)
        hero_box.setSpacing(6)
        hero_box.addLayout(hero_layout)
        hero_box.addWidget(self.examples_row, 0, Qt.AlignHCenter)

        hero_panel = QFrame()
        hero_panel.setObjectName("heroPanel")
        hero_panel.setLayout(hero_box)

        main_layout.addWidget(hero_panel)

        # Hourly strip
        main_layout.addWidget(self._micro_title("Next 24 hours"))
        main_layout.addWidget(self.hourly_strip)

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
        footer_layout.addWidget(self.version_label)
        footer_layout.addSpacing(12)
        footer_layout.addWidget(self.attribution_label)
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
        self._console_content = content

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

        # Typing queues a debounced autocomplete query.
        self.city_input.textEdited.connect(self.queue_suggestions)
        self.suggest_timer.timeout.connect(self.emit_suggestions)

        self.suggest_requested.connect(self.suggest_worker.suggest)
        self.suggest_worker.suggestions_ready.connect(self.on_suggestions)
        self.suggest_worker.suggest_failed.connect(self.on_suggest_failed)

        self.completer.activated.connect(self.on_suggestion_activated)

        # Update the displayed clock every second.
        self.timer.timeout.connect(self.update_clock)

        # The signal hops threads safely; the worker never touches widgets.
        self.search_requested.connect(self.weather_worker.search)
        self.weather_worker.search_done.connect(self.on_search_done)
        self.weather_worker.search_failed.connect(self.on_search_failed)

        # Quietly repeat the last search on a fixed interval.
        self.refresh_timer.timeout.connect(self.auto_refresh)

        # Favorites: click searches, plus saves, right click removes.
        self.favorites_bar.city_clicked.connect(self.search_favorite)
        self.favorites_bar.add_requested.connect(self.add_current_city)
        self.favorites_bar.remove_requested.connect(self.remove_favorite)

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

    # ---------------------------------------------------------
    # Autocomplete
    # ---------------------------------------------------------

    def queue_suggestions(self, text: str) -> None:
        """
        Batch typing: restart the debounce on every keystroke.
        """

        cleaned = text.strip()

        if len(cleaned) < 2:
            self.suggest_timer.stop()
            self.suggest_model.setStringList([])
            self._suggestions = {}
            return

        self._suggest_query = cleaned
        self.suggest_timer.start(SUGGEST_DEBOUNCE_MS)

    def emit_suggestions(self) -> None:
        """
        The debounce fired: ask the geocoder on its worker thread.
        """

        self.suggest_requested.emit(self._suggest_query)

    def on_suggestions(self, query: str, results: list) -> None:
        """
        Fill the popup, unless the user has typed something else since
        the request went out.
        """

        if query != self.city_input.text().strip():
            return

        self._suggestions = {result.display: result for result in results}

        self.suggest_model.setStringList(list(self._suggestions.keys()))

    def on_suggest_failed(self, query: str, error: WeatherAppError) -> None:
        """
        Suggestions are best effort: failures stay in the log and the
        popup simply does not open.
        """

        logger.warning("Autocomplete unavailable: %s",
            error.debug_detail or error.user_message)

    def on_suggestion_activated(self, display: str) -> None:
        """
        Fill the search box with the picked suggestion's disambiguated
        query.
        """

        result = self._suggestions.get(display)

        if result is not None:
            self.city_input.setText(result.query)

    def search_favorite(self, city: str) -> None:
        """
        Search a saved city and show it in the box.
        """

        self.city_input.setText(city)
        self.begin_search(city, auto=False)

    def add_current_city(self) -> None:
        """
        Save the city currently on screen.
        """

        if self.weather_data is None:
            return

        city = self.weather_data.city

        if self.favorites.contains(city):
            self.display_error(f"{city} is already in favorites.")
            return

        if not self.favorites.add(city):
            self.display_error(
                f"Favorites are full ({Favorites.MAX_FAVORITES} cities)."
            )
            return

        self.favorites_bar.set_cities(self.favorites.get())
        self.status_label.setText(f"Added {city} to favorites.")

    def remove_favorite(self, city: str) -> None:
        """
        Remove a saved city.
        """

        if self.favorites.remove(city):
            self.favorites_bar.set_cities(self.favorites.get())
            self.status_label.setText(f"Removed {city} from favorites.")

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

    def on_search_done(self, weather, forecast, hourly) -> None:
        """
        Handle a successful background search.
        """

        self.weather_data = weather
        self.fetched_at = datetime.now()

        self.weather_cache.save(weather, forecast, hourly)

        self.display_weather(weather, refresh_timestamp=True)
        self.display_forecast(forecast)
        self.display_hourly(hourly)

        self.search_button.setEnabled(True)

        self.refresh_timer.start(
            self.settings.get("refresh_minutes") * 60_000
        )

        # If the filled console is taller than the window (it should
        # not be, but fonts and metrics vary), grow to fit rather
        # than make the owner scroll.
        QTimer.singleShot(0, self._fit_height)

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

        # Keep the error visible for half a minute before the
        # elapsed-time line takes the status back.
        self._error_until = datetime.now() + timedelta(seconds=30)

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

    def _make_app_icon(self):
        """
        Render the clear-sky SVG into a square app icon.
        """

        renderer = QSvgRenderer(IconManager.get_icon_path(800))

        pixmap = QPixmap(256, 256)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    def display_weather(self, weather, refresh_timestamp: bool = False) -> None:
        """
        Fill every panel from a WeatherData model.

        A fresh fetch stamps the fetch time; re-displays (unit toggle,
        cached startup) keep the original timestamp so the elapsed-time
        line stays honest.
        """

        self.weather_data = weather

        if refresh_timestamp or self.fetched_at is None:
            self.fetched_at = datetime.now()

        # The plus chip needs a city on screen to add.
        self.favorites_bar.set_add_enabled(True)

        condition = self.resolve_condition(weather)
        self.apply_condition(condition)
        accent = ConditionTheme.accent(condition)

        self.load_weather_icon(weather.weather_id)
        self.load_flag(weather.country)

        self.station_label.setText(
            f"STATION: {weather.city.upper()}, {weather.country.upper()}"
        )

        self.live_badge.setText(f"\u25cf LIVE  {weather.description.upper()}")

        if self.units == "metric":
            self.temperature_label.setText(
                f"{weather.temperature_c:.0f}\u00b0C"
            )
            self.celsius_label.setText(
                f"{weather.temperature_f:.0f}\u00b0F"
            )

            self.feels_label.setText(
                f"FEELS LIKE {weather.feels_like_c:.0f}\u00b0"
            )
            self.minmax_label.setText(
                f"H {weather.temp_max_c:.0f}\u00b0   "
                f"L {weather.temp_min_c:.0f}\u00b0"
            )

            self.wind_tile.set_value(
                f"{miles_per_hour_to_kmh(weather.wind_speed):.0f}", "km/h"
            )
            self.visibility_tile.set_value(
                f"{meters_to_km(weather.visibility):.0f}", "km"
            )
        else:
            self.temperature_label.setText(
                f"{weather.temperature_f:.0f}\u00b0F"
            )
            self.celsius_label.setText(
                f"{weather.temperature_c:.0f}\u00b0C"
            )

            self.feels_label.setText(
                f"FEELS LIKE {weather.feels_like_f:.0f}\u00b0"
            )
            self.minmax_label.setText(
                f"H {weather.temp_max_f:.0f}\u00b0   "
                f"L {weather.temp_min_f:.0f}\u00b0"
            )

            self.wind_tile.set_value(f"{weather.wind_speed:.0f}", "mph")
            self.visibility_tile.set_value(
                f"{meters_to_miles(weather.visibility):.0f}", "mi"
            )

        self.condition_text.setText(weather.description.upper())

        self.examples_row.setVisible(False)

        self.humidity_tile.set_value(f"{weather.humidity}", "%")
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

        self.update_clock()

    def display_forecast(self, forecast: list) -> None:
        """
        Display the 5-day forecast table.

        The table needs the active accent, which display_weather
        resolves before this is called.
        """

        self._last_forecast = forecast

        if self._forecast_accent is not None:
            self.forecast_table.update_forecast(
                forecast, self._forecast_accent, self.units
            )

    def display_hourly(self, hourly: list) -> None:
        """
        Display the hourly strip chips.
        """

        self._last_hourly = hourly

        if self._forecast_accent is not None:
            self.hourly_strip.update_hourly(hourly, self.units)

    def display_error(self, message: str) -> None:
        """
        Display an error message.
        """

        self.status_label.setText(message)

    def update_clock(self) -> None:

        """
         Update the local clock, the city clock, and the elapsed-time
         status line every second.
         """

        now = datetime.now()

        # The owner's local time. Always ticks, even before the first
        # search, in 12h format like the city clock.
        self.local_clock_label.setText(now.strftime("%I:%M:%S %p"))

        # Let error messages breathe for half a minute before the
        # elapsed-time line takes the status back.
        if self._error_until is not None and now < self._error_until:
            return

        self._error_until = None

        if self.weather_data is None or self.fetched_at is None:
            self.time_label.setText("--:--")
            return

        city_time = datetime.now(timezone(
            timedelta(seconds=self.weather_data.timezone)
        ))

        self.time_label.setText(city_time.strftime("%I:%M:%S %p"))

        self.status_label.setText(
            f"Updated {self.weather_data.city} \u00b7 {self._elapsed_text(now)}"
        )

    def _elapsed_text(self, now: datetime) -> str:
        """
        Human wording for how long ago the last search ran.
        """

        seconds = int((now - self.fetched_at).total_seconds())

        if seconds < 60:
            return "just now"

        minutes = seconds // 60

        if minutes < 60:
            return "1 min ago" if minutes == 1 else f"{minutes} min ago"

        hours = minutes // 60

        return "1 hr ago" if hours == 1 else f"{hours} hr ago"

    # ---------------------------------------------------------
    # Help and key management
    # ---------------------------------------------------------

    def show_about(self) -> None:
        """
        Show the About dialog: version, attribution, licenses, and the
        data folder with an offer to open it.
        """

        box = QMessageBox(self)
        box.setWindowTitle("About Weather App Pro")
        box.setTextFormat(Qt.RichText)
        box.setText(self._about_text())

        open_button = box.addButton("Open data folder", QMessageBox.ActionRole)
        box.addButton(QMessageBox.Ok)

        box.exec()

        if box.clickedButton() is open_button:
            os.startfile(str(paths.data_dir()))

    def _about_text(self) -> str:
        """
        The About dialog's text (plain HTML).
        """

        return (
            f"<h3>Weather App Pro {APP_VERSION}</h3>"
            "<p>A desktop weather console powered by OpenWeatherMap.</p>"
            "<p>Weather data provided by "
            '<a href="https://openweathermap.org/">'
            '<span style="color:#dfe8f2;">OpenWeather</span></a> '
            "(openweathermap.org). Free plan terms require this "
            "attribution.</p>"
            "<p>License: MIT (see LICENSE). Third-party software and "
            "assets: THIRD-PARTY-NOTICES.md.</p>"
            "<p>Your data folder:<br>"
            f"<code>{paths.data_dir()}</code></p>"
        )

    def focus_search(self) -> None:
        """
        Ctrl+F: put the cursor in the search box.
        """

        self.city_input.setFocus()
        self.city_input.selectAll()

    def offer_key_setup(self) -> None:
        """
        Ask for a free OpenWeatherMap API key, validate it with one
        cheap call, and store it in the data directory.

        Runs on first start and any time from the Settings menu; the
        user can skip it and the app keeps warning until a working key
        exists.
        """

        first_run = not self.weather_api.api_key_exists()

        if first_run:
            message = (
                "Weather App Pro needs a free OpenWeatherMap API key.\n"
                "Create one at openweathermap.org/appid and paste it below.\n"
                "(New keys can take up to two hours to activate.)"
            )
        else:
            message = (
                "Enter a new OpenWeatherMap API key.\n"
                "It replaces the key saved in the data folder."
            )

        while True:
            key, accepted = QInputDialog.getText(
                self,
                "Weather App Pro: API key",
                message,
            )

            key = key.strip()

            if not accepted or not key:
                return

            if validate_key(key):
                store_key(key)
                os.environ["OPENWEATHER_API_KEY"] = key
                self.weather_api.api_key = key

                QMessageBox.information(
                    self,
                    "Weather App Pro",
                    "API key saved. You are ready to search.",
                )
                return

            message = (
                "That key was rejected.\n"
                "Check it on openweathermap.org (new keys can take up to two\n"
                "hours to activate), then try again."
            )

            retry = QMessageBox.question(
                self,
                "Weather App Pro",
                message + "\n\nTry again?",
            )

            if retry != QMessageBox.Yes:
                return

    # ---------------------------------------------------------
    # Shutdown
    # ---------------------------------------------------------

    def changeEvent(self, event) -> None:
        """
        Pause the sky scene while minimized; resume on restore.
        """

        super().changeEvent(event)

        if event.type() == QEvent.WindowStateChange:
            minimized = bool(self.windowState() & Qt.WindowMinimized)
            self.sky.set_paused(minimized)

    def closeEvent(self, event) -> None:
        """
        Stop the background thread before the window goes away.
        """

        self.refresh_timer.stop()
        self.timer.stop()

        self.settings.set("window", [
            self.x(), self.y(), self.width(), self.height()
        ])

        self.suggest_timer.stop()

        self.weather_thread.quit()
        self.weather_thread.wait(2000)

        self.suggest_thread.quit()
        self.suggest_thread.wait(2000)

        event.accept()

    # ---------------------------------------------------------
    # Styles
    # ---------------------------------------------------------

    def apply_styles(self) -> None:
        """
        Apply the glass console stylesheet and window defaults.
        """

        self.setWindowTitle(f"Weather App Pro {APP_VERSION}")
        self.setWindowIcon(self._make_app_icon())
        self.setMinimumSize(820, 620)

        # The window grows to fit the whole console on first show (see
        # showEvent), so nothing needs scrolling on a normal screen.
        # Shorter screens clamp and the scroll area takes over.
        self.resize(1010, 930)
        self._window_size_fitted = False
        self._geometry_restored = False

        # Defaults before the first search: a short hint and three
        # clickable example cities in the hero.
        self.temperature_label.setText("--\u00b0F")
        self.celsius_label.setText("--\u00b0C")
        self.condition_text.setText("SEARCH FOR A CITY")
        self.feels_label.setText("")
        self.minmax_label.setText("")
        self.live_badge.setText("\u25cf OFFLINE")
        self.local_clock_label.setText("--:--:-- --")
        self.time_label.setText("--:--")
        self.status_label.setText("Ready")

        self.examples_row.setVisible(True)

        self.time_label.setAlignment(Qt.AlignRight)

        # The glass console theme. Accent colors follow the condition
        # through the dynamic property set in apply_condition.
        theme = ThemeManager.load_theme("console")

        self.setStyleSheet(theme)

        # The completer popup is a top-level window, so the window
        # stylesheet does not reach it: hand it the theme directly.
        popup = self.completer.popup()

        if popup is not None:
            popup.setObjectName("suggestPopup")
            popup.setStyleSheet(theme)

        self.apply_condition(self.current_condition)

    def showEvent(self, event) -> None:
        """
        On first show, size the window to the console's measured
        height, clamped to the screen.

        The comfortable height depends on real font metrics and the
        title bar, neither of which are known before showing.
        """

        super().showEvent(event)

        if self._window_size_fitted:
            return

        self._window_size_fitted = True

        self._fit_height(grow_only=False)

    def _fit_height(self, grow_only: bool = True) -> None:
        """
        Resize the window to exactly fit the console content.

        Never exceeds the screen; with grow_only it also never shrinks,
        so a window the owner resized smaller stays put unless the
        content genuinely no longer fits.
        """

        needed = (
            self._console_content.sizeHint().height()
            + self.menuBar().height()
            + 2
        )

        frame_extra = self.frameGeometry().height() - self.height()

        if frame_extra > 0:
            needed += frame_extra

        available = self.screen().availableGeometry()

        target = min(needed, available.height())

        if not grow_only or target > self.height():
            self.resize(self.width(), target)

        if not self._geometry_restored:
            frame = self.frameGeometry()
            frame.moveCenter(available.center())
            self.move(frame.topLeft())
