"""
weather_worker.py
=================

Runs weather searches off the GUI thread.

Responsibilities:
    - Call WeatherAPI from a background thread
    - Report results and typed errors back through signals
    - Never touch a widget

ui.py moves an instance of this class onto a QThread and talks to it
through the search_requested signal. weather_api.py stays free of Qt
imports so it can be tested headlessly; this module owns the threading.
"""

import logging

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from errors import WeatherAppError, UNEXPECTED_ERROR_MESSAGE

logger = logging.getLogger(f"weather.{__name__}")


class WeatherWorker(QObject):
    """
    Executes one search at a time on its own thread.
    """

    # WeatherData, the daily forecast, and the hourly chips for the
    # same search.
    search_done = pyqtSignal(object, object, object)

    # Always a WeatherAppError, never a bare exception.
    search_failed = pyqtSignal(object)

    def __init__(self, weather_api):
        super().__init__()

        self.weather_api = weather_api

    @pyqtSlot(str)
    def search(self, city: str) -> None:
        """
        Fetch current weather and forecast for one city.

        Any failure is converted into a WeatherAppError so the UI only
        ever has one error shape to handle.
        """

        try:
            weather = self.weather_api.get_current_weather(city)
            forecast, hourly = self.weather_api.get_forecast(city)

        except WeatherAppError as error:
            self.search_failed.emit(error)
            return

        except Exception:
            # A bug in our own code. The trace goes to the log; the
            # user gets the generic message.
            logger.exception("Unexpected failure during the search for '%s'.", city)

            self.search_failed.emit(WeatherAppError(UNEXPECTED_ERROR_MESSAGE))
            return

        self.search_done.emit(weather, forecast, hourly)


class SuggestWorker(QObject):
    """
    Executes autocomplete queries on its own thread.

    Failures are reported but stay quiet: the UI logs them and leaves
    the popup alone, since suggestions are best effort.
    """

    # The query the results belong to (stale answers are dropped by
    # the UI) and the list of GeoResult objects.
    suggestions_ready = pyqtSignal(str, list)

    suggest_failed = pyqtSignal(str, object)

    def __init__(self, geocoder):
        super().__init__()

        self.geocoder = geocoder

    @pyqtSlot(str)
    def suggest(self, query: str) -> None:
        try:
            results = self.geocoder.search(query)

        except WeatherAppError as error:
            logger.warning("Suggestions for '%s' failed: %s",
                query, error.debug_detail or error.user_message)

            self.suggest_failed.emit(query, error)
            return

        except Exception:
            logger.exception("Unexpected failure suggesting '%s'.", query)

            self.suggest_failed.emit(
                query, WeatherAppError(UNEXPECTED_ERROR_MESSAGE)
            )
            return

        self.suggestions_ready.emit(query, results)
