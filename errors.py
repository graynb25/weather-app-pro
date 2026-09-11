"""
errors.py
=========

Exception hierarchy for Weather App Pro.

Responsibilities:
    - Define one exception type per failure the app can explain
    - Carry a safe, hand-written message for the user
    - Carry optional debug detail for the log file

The UI reads user_message and nothing else. The debug detail exists so
the log can say what actually happened without ever showing that text
to the user.
"""

# Shown when something failed that the app has no specific story for.
UNEXPECTED_ERROR_MESSAGE = "Something went wrong. See the log for details."


class WeatherAppError(Exception):
    """
    Base class for every error the app raises on purpose.

    Attributes:
        user_message: Short plain sentence, safe to show in the UI.
        debug_detail: Extra context for the log file. Never shown
            to the user, never derived from exception text or URLs.
    """

    def __init__(self, user_message: str, debug_detail: str = ""):
        super().__init__(user_message)

        self.user_message = user_message
        self.debug_detail = debug_detail


class InvalidCityError(WeatherAppError):
    """The city input is empty, too long, or contains unusable characters."""


class ApiKeyMissingError(WeatherAppError):
    """OPENWEATHER_API_KEY is not set, so no request can be made."""


class ApiKeyInvalidError(WeatherAppError):
    """The API returned 401. The key was rejected or is not active yet."""


class CityNotFoundError(WeatherAppError):
    """The API returned 404 for the searched city."""


class RateLimitError(WeatherAppError):
    """The API returned 429. The request quota is used up for now."""


class ApiServiceError(WeatherAppError):
    """The API returned 5xx, or a status this app does not handle."""


class NetworkError(WeatherAppError):
    """The request timed out or the connection failed before a response."""


class ApiDataError(WeatherAppError):
    """The API answered 200 but the payload does not have the expected shape."""
