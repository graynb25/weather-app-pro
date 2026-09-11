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

    # WeatherData and the list of ForecastData for the same search.
    search_done = pyqtSignal(object, object)

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
            forecast = self.weather_api.get_forecast(city)

        except WeatherAppError as error:
            self.search_failed.emit(error)
            return

        except Exception:
            # A bug in our own code. The trace goes to the log; the
            # user gets the generic message.
            logger.exception("Unexpected failure during the search for '%s'.", city)

            self.search_failed.emit(WeatherAppError(UNEXPECTED_ERROR_MESSAGE))
            return

        self.search_done.emit(weather, forecast)
