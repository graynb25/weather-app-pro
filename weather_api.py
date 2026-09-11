"""
weather_api.py
==============

Handles all communication with the OpenWeatherMap API.

Responsibilities:
    - Get current weather
    - Get 5-day forecast
    - Validate city input and API response payloads
    - Translate transport and HTTP failures into the errors hierarchy
    - Hide API implementation details from the UI

Secret rules (see docs/error-handling-and-security.md):
    - URLs are only ever logged through utils.redact_url
    - Exception text from the requests library is never logged as-is,
      because HTTPError embeds the request URL, which contains the key
    - User-facing text is hand-written in errors.py, never interpolated

Author: Gray Nelson
Project: Weather App Pro
"""

import logging
import os
from collections.abc import Callable
from datetime import datetime
from typing import NoReturn

import requests
from dotenv import load_dotenv

from config import (BASE_URL, CURRENT_WEATHER_ENDPOINT, FORECAST_ENDPOINT,
    REQUEST_TIMEOUT, DEFAULT_UNITS, MAX_CITY_LENGTH)

from weather_model import WeatherData, ForecastData
from errors import (InvalidCityError, ApiKeyMissingError,
    ApiKeyInvalidError, CityNotFoundError, RateLimitError, ApiServiceError,
    NetworkError, ApiDataError)
from utils import redact_url, fahrenheit_to_celsius

from requests.exceptions import (
    ConnectionError,
    Timeout,
    HTTPError,
    RequestException,
)

logger = logging.getLogger(f"weather.{__name__}")

# ---------------------------------------------------------
# Load environment variables (.env)
# ---------------------------------------------------------

load_dotenv()

# ---------------------------------------------------------
# Hand-written user messages and status mapping
# ---------------------------------------------------------

MESSAGE_INVALID_CITY_EMPTY = "Please enter a city name."
MESSAGE_INVALID_CITY_CHARS = "That does not look like a valid city name."
MESSAGE_INVALID_CITY_LENGTH = "City names are limited to 85 characters."

MESSAGE_KEY_MISSING = (
    "No API key found. Set OPENWEATHER_API_KEY in .env and restart the app."
)
MESSAGE_NETWORK = "Could not reach the weather service. Check your internet connection."
MESSAGE_TIMEOUT = "The request timed out. Check your internet connection and try again."
MESSAGE_SERVICE = "The weather service is having problems right now. Try again later."
MESSAGE_BAD_PAYLOAD = "The weather service sent data this app does not understand."

# Whitespace the city input is allowed to contain; str.split() collapses
# these. Every other control character is rejected outright.
COMMON_WHITESPACE = " \t\n\r\f\v"

# OpenWeatherMap statuses with their own meaning. Everything else falls
# back to ApiServiceError.
STATUS_ERRORS = {
    401: (
        ApiKeyInvalidError,
        "The API key was rejected. Check OPENWEATHER_API_KEY in .env. "
        "New keys can take up to two hours to activate.",
    ),
    404: (
        CityNotFoundError,
        "City not found. Check the spelling and try again.",
    ),
    429: (
        RateLimitError,
        "Too many requests. Wait a minute and try again.",
    ),
}

# ---------------------------------------------------------
# Payload shape
# ---------------------------------------------------------

# Fields the app actually reads. A tuple step walks a dict key, an
# int step indexes a list (for example weather[0]). Only field names
# are ever logged, never values.
CURRENT_REQUIRED_FIELDS = (
    ("name",),
    ("weather", 0, "id"),
    ("weather", 0, "description"),
    ("main", "temp"),
    ("main", "feels_like"),
    ("main", "temp_min"),
    ("main", "temp_max"),
    ("main", "humidity"),
    ("main", "pressure"),
    ("wind", "speed"),
    ("sys", "country"),
    ("sys", "sunrise"),
    ("sys", "sunset"),
    ("timezone",),
)

FORECAST_LIST_FIELD = ("list",)

FORECAST_ITEM_FIELDS = (
    ("dt",),
    ("main", "temp"),
    ("weather", 0, "id"),
    ("weather", 0, "description"),
)


def _path_exists(data: dict, path: tuple) -> bool:
    """
    Check that a (possibly nested) field exists in a payload.

    Dict keys and list indexes interleave, for example
    ("weather", 0, "id") reads data["weather"][0]["id"].
    """

    node = data

    for step in path:
        if isinstance(step, int):
            if not isinstance(node, list) or len(node) <= step:
                return False
        else:
            if not isinstance(node, dict) or step not in node:
                return False

        node = node[step]

    return True


class WeatherAPI:
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")


    def api_key_exists(self) -> bool:
        return bool(self.api_key)

    # ---------------------------------------------------------
    # City input
    # ---------------------------------------------------------

    def _validate_city(self, city: str) -> str:
        """
        Normalize and validate a city name before it reaches a request.

        Returns:
            The city with collapsed inner whitespace.

        Raises:
            InvalidCityError: If the input is empty, has control
                characters, or exceeds the API's documented length.
        """

        cleaned = " ".join(city.split())

        if not cleaned:
            logger.info("Rejected an empty city name.")
            raise InvalidCityError(MESSAGE_INVALID_CITY_EMPTY)

        # Control characters are checked on the raw input. Some of them
        # count as whitespace for str.split() and would vanish in the
        # collapse, so only tab, newline, and friends are allowed through.
        if any(
            (ord(ch) < 32 or ord(ch) == 127)
            and ch not in COMMON_WHITESPACE
            for ch in city
        ):
            logger.info("Rejected a city name with control characters.")
            raise InvalidCityError(MESSAGE_INVALID_CITY_CHARS)

        if len(cleaned) > MAX_CITY_LENGTH:
            logger.info("Rejected a city name over %s characters.", MAX_CITY_LENGTH)
            raise InvalidCityError(MESSAGE_INVALID_CITY_LENGTH)

        return cleaned

    # ---------------------------------------------------------
    # Request handling
    # ---------------------------------------------------------

    def _request_data(self, url: str, params: dict,
        validate: Callable[[dict], None]) -> dict:
        """
        Perform one API call and return the validated JSON payload.

        Checks the API key up front, maps transport and HTTP failures
        onto the errors hierarchy, and runs the caller's payload
        validation before anything is returned.

        Raises:
            WeatherAppError: A subclass matching the failure.
        """

        if not self.api_key:
            logger.error("API request attempted without a key.")
            raise ApiKeyMissingError(MESSAGE_KEY_MISSING)

        try:
            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

        except ConnectionError as error:
            logger.error("Connection failed: %s", redact_url(str(error)))
            raise NetworkError(MESSAGE_NETWORK) from None

        except Timeout as error:
            logger.error("Request timed out: %s", redact_url(str(error)))
            raise NetworkError(MESSAGE_TIMEOUT) from None

        except HTTPError as error:
            self._map_http_error(error)

        except RequestException as error:
            logger.error("Request failed: %s", redact_url(str(error)))
            raise ApiServiceError(MESSAGE_SERVICE) from None

        try:
            data = response.json()
        except ValueError:
            logger.error("Response was not valid JSON (HTTP %s).",
                response.status_code)
            raise ApiDataError(MESSAGE_BAD_PAYLOAD) from None

        validate(data)

        return data

    def _map_http_error(self, error: HTTPError) -> NoReturn:
        """
        Turn a failed HTTP response into the matching errors.py type.

        Raises:
            ApiKeyInvalidError: On 401.
            CityNotFoundError: On 404.
            RateLimitError: On 429.
            ApiServiceError: On 5xx and every other status.
        """

        status = error.response.status_code if error.response is not None else None

        # str(error) embeds the full request URL, so it only goes to the
        # log through redact_url.
        logger.error("API returned HTTP %s: %s", status, redact_url(str(error)))

        if status in STATUS_ERRORS:
            error_class, user_message = STATUS_ERRORS[status]
            raise error_class(user_message, debug_detail=f"HTTP {status}") from None

        raise ApiServiceError(MESSAGE_SERVICE, debug_detail=f"HTTP {status}") from None

    # ---------------------------------------------------------
    # Payload validation
    # ---------------------------------------------------------

    def _validate_current_payload(self, data: dict) -> None:
        """
        Check that a current weather payload has every field the app reads.

        Raises:
            ApiDataError: If a field is missing.
        """

        missing = [
            path for path in CURRENT_REQUIRED_FIELDS
            if not _path_exists(data, path)
        ]

        if missing:
            self._raise_payload_error(data, missing)

    def _validate_forecast_payload(self, data: dict) -> None:
        """
        Check that a forecast payload has every field the app reads.

        Every entry in "list" must carry the fields used to build a day.

        Raises:
            ApiDataError: If the list is missing, empty, or incomplete.
        """

        missing = []

        if not _path_exists(data, FORECAST_LIST_FIELD):
            missing.append(FORECAST_LIST_FIELD)
        elif not isinstance(data["list"], list) or not data["list"]:
            missing.append(FORECAST_LIST_FIELD)
        else:
            for index, item in enumerate(data["list"]):
                missing.extend(
                    ("list", index) + path
                    for path in FORECAST_ITEM_FIELDS
                    if not _path_exists(item, path)
                )

        if missing:
            self._raise_payload_error(data, missing)

    def _raise_payload_error(self, data: dict, missing: list[tuple]) -> NoReturn:
        """
        Log the payload shape and raise ApiDataError.

        Only top-level keys and field paths are logged, never values.
        """

        logger.error("Unexpected payload shape. Top level keys: %s. Missing: %s.",
            sorted(data.keys()) if isinstance(data, dict) else type(data).__name__,
            [".".join(str(step) for step in path) for path in missing])

        raise ApiDataError(MESSAGE_BAD_PAYLOAD) from None

    # ---------------------------------------------------------
    # Current weather
    # ---------------------------------------------------------

    def get_current_weather(self, city: str) -> WeatherData:
        """
        Retrieve the current weather for the specified city.

        Args:
            city: Name of the city to search for.

        Returns:
            A WeatherData object containing the current weather.

        Raises:
            WeatherAppError: A subclass matching the failure.
        """

        # ---------------------------------------------------------
        # Validate city name and API key
        # ---------------------------------------------------------

        city = self._validate_city(city)

        # ---------------------------------------------------------
        # Build request URL
        # ---------------------------------------------------------

        url = (
            f"{BASE_URL}"
            f"{CURRENT_WEATHER_ENDPOINT}"
        )

        params = {
            "q": city, "appid": self.api_key, "units": DEFAULT_UNITS
        }

        data = self._request_data(
            url,
            params,
            self._validate_current_payload
        )

        # ---------------------------------------
        # Convert to WeatherData
        # ---------------------------------------

        try:
            return WeatherData(
                city=data["name"],
                country=data["sys"]["country"],

                temperature_f=data["main"]["temp"],
                temperature_c=fahrenheit_to_celsius(data["main"]["temp"]),

                feels_like_f=data["main"]["feels_like"],
                feels_like_c=fahrenheit_to_celsius(data["main"]["feels_like"]),

                temp_min_f=data["main"]["temp_min"],
                temp_min_c=fahrenheit_to_celsius(data["main"]["temp_min"]),

                temp_max_f=data["main"]["temp_max"],
                temp_max_c=fahrenheit_to_celsius(data["main"]["temp_max"]),

                description=data["weather"][0]["description"].title(),
                weather_id=data["weather"][0]["id"],

                humidity=data["main"]["humidity"],
                wind_speed=data["wind"]["speed"],
                pressure=data["main"]["pressure"],
                visibility=data.get("visibility", 0),

                sunrise=data["sys"]["sunrise"],
                sunset=data["sys"]["sunset"],

                timezone=data["timezone"],
            )
        except (KeyError, TypeError, ValueError) as error:
            # The shape check above passed, so this is a type the
            # conversion cannot handle. Log the type name only, the
            # message could embed payload values.
            logger.error("Current weather conversion failed: %s",
                type(error).__name__)
            raise ApiDataError(MESSAGE_BAD_PAYLOAD) from None

    # ---------------------------------------------------------
    # 5-day forecast
    # ---------------------------------------------------------

    def get_forecast(self, city: str) -> list[ForecastData]:
        """
        Retrieve the 5-day forecast for the specified city.

        For each day, the forecast entry closest to midday is used.

        Args:
            city: Name of the city to search for.

        Returns:
            A list of ForecastData objects, one per day, sorted by date.

        Raises:
            WeatherAppError: A subclass matching the failure.
        """

        # ---------------------------------------------------------
        # Validate city name and API key
        # ---------------------------------------------------------

        city = self._validate_city(city)

        # ---------------------------------------------------------
        # Build request URL
        # ---------------------------------------------------------

        url = (
            f"{BASE_URL}"
            f"{FORECAST_ENDPOINT}"
        )

        params = {
            "q": city,
            "appid": self.api_key,
            "units": DEFAULT_UNITS,
        }

        data = self._request_data(
            url,
            params,
            self._validate_forecast_payload
        )

        daily_forecasts = {}

        # ---------------------------------------------------------
        # Find the forecast closest to midday for each day
        # ---------------------------------------------------------

        try:
            for item in data["list"]:

                forecast_time = datetime.fromtimestamp(item["dt"])

                date = forecast_time.date()

                distance = abs(forecast_time.hour - 12)

                if date not in daily_forecasts:
                    daily_forecasts[date] = (distance, item)
                    continue

                best_distance, _ = daily_forecasts[date]

                if distance < best_distance:
                    daily_forecasts[date] = (distance, item)
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            logger.error("Forecast conversion failed: %s", type(error).__name__)
            raise ApiDataError(MESSAGE_BAD_PAYLOAD) from None

        # ---------------------------------------------------------
        # Convert to ForecastData objects
        # ---------------------------------------------------------

        forecast = []

        try:
            for _, item in daily_forecasts.values():
                forecast_time = datetime.fromtimestamp(item["dt"])

                temperature_f = item["main"]["temp"]

                forecast.append(
                    ForecastData(
                        day=forecast_time.strftime("%a"),
                        date=forecast_time.strftime("%Y-%m-%d"),

                        temperature_f=temperature_f,
                        temperature_c=fahrenheit_to_celsius(temperature_f),

                        description=item["weather"][0]["description"].title(),
                        weather_id=item["weather"][0]["id"],
                    )
                )
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            logger.error("Forecast conversion failed: %s", type(error).__name__)
            raise ApiDataError(MESSAGE_BAD_PAYLOAD) from None

        # ---------------------------------------------------------
        # Sort by date
        # ---------------------------------------------------------

        forecast.sort(key=lambda day: day.date)

        return forecast
