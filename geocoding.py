"""
geocoding.py
============

City name suggestions from the OpenWeatherMap geocoding API.

Responsibilities:
    - Turn a partial city name into up to five GeoResult suggestions
    - Validate input and map failures onto the errors hierarchy
    - Keep the same secret rules as weather_api: URLs reach the log
    only through utils.redact_url, and hand-written user messages
    carry no exception or payload text

The geocoder never touches Qt; the suggest worker owns the threading.
Autocomplete is best effort: failures surface as empty suggestions,
never as dialogs.
"""

import logging
import os

import requests

from config import GEO_URL, GEO_LIMIT, REQUEST_TIMEOUT
from errors import (InvalidCityError, ApiKeyMissingError, ApiKeyInvalidError,
    CityNotFoundError, RateLimitError, ApiServiceError, NetworkError,
    ApiDataError)
from utils import redact_url
import paths

from requests.exceptions import ConnectionError, Timeout, RequestException

logger = logging.getLogger(f"weather.{__name__}")

MAX_QUERY_LENGTH = 85
COMMON_WHITESPACE = " \t\n\r\f\v"

# A one-line dotenv file stored in the data directory, written by the
# first-run dialog and loaded by weather_api at startup.
KEY_FILE_LINE = "OPENWEATHER_API_KEY={key}\n"


class GeoResult:
    """
    One suggestion: the city plus optional state and country.

    display is the popup text; query is what goes into the search box
    ("City, CC" disambiguates for the weather API).
    """

    def __init__(self, name: str, state: str = "", country: str = ""):
        self.name = name
        self.state = state
        self.country = country

        parts = [part for part in (name, state, country) if part]

        self.display = ", ".join(parts)

        query_parts = [part for part in (name, country) if part]

        self.query = ", ".join(query_parts)

    def __repr__(self) -> str:
        return f"GeoResult({self.display!r})"


def _validate_query(query: str) -> str:
    """
    Normalize and validate an autocomplete query.

    Returns:
        The query with collapsed inner whitespace.

    Raises:
        InvalidCityError: If the query is empty, has control
            characters, or is too long.
    """

    cleaned = " ".join(query.split())

    if not cleaned:
        raise InvalidCityError("Please enter a city name.")

    if any(
        (ord(ch) < 32 or ord(ch) == 127) and ch not in COMMON_WHITESPACE
        for ch in query
    ):
        raise InvalidCityError("That does not look like a valid city name.")

    if len(cleaned) > MAX_QUERY_LENGTH:
        raise InvalidCityError("City names are limited to 85 characters.")

    return cleaned


class Geocoder:
    """
    Queries the geocoding API for city suggestions.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")

    def search(self, query: str) -> list:
        """
        Fetch suggestions for a partial city name.

        Returns:
            Up to GEO_LIMIT GeoResult objects. An empty list means no
            matches.

        Raises:
            WeatherAppError: A subclass matching the failure. Callers
                treat failures as "no suggestions", never as dialogs.
        """

        cleaned = _validate_query(query)

        if not self.api_key:
            logger.debug("Suggest skipped: no API key.")
            raise ApiKeyMissingError("No API key found.")

        params = {
            "q": cleaned,
            "limit": GEO_LIMIT,
            "appid": self.api_key,
        }

        try:
            response = requests.get(
                GEO_URL,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

        except ConnectionError as error:
            logger.warning("Suggest connection failed: %s",
                redact_url(str(error)))
            raise NetworkError("Could not reach the weather service.") from None

        except Timeout as error:
            logger.warning("Suggest timed out: %s", redact_url(str(error)))
            raise NetworkError("The request timed out.") from None

        except RequestException as error:
            logger.warning("Suggest request failed: %s", redact_url(str(error)))
            raise ApiServiceError("The weather service is having problems.") from None

        status = response.status_code

        if status >= 400:
            # The URL embeds the key, so the raw error text is only
            # ever logged through redact_url.
            logger.warning("Suggest returned HTTP %s for %s",
                status, redact_url(response.url))

            if status == 401:
                raise ApiKeyInvalidError("The API key was rejected.")
            if status == 404:
                return []
            if status == 429:
                raise RateLimitError("Too many requests.")

            raise ApiServiceError("The weather service is having problems.")

        try:
            payload = response.json()
        except ValueError:
            logger.warning("Suggest response was not valid JSON.")
            raise ApiDataError("The weather service sent bad data.") from None

        if not isinstance(payload, list):
            logger.warning("Suggest payload was not a list.")
            raise ApiDataError("The weather service sent bad data.")

        results = []

        for entry in payload:
            result = self._parse_entry(entry)

            if result is not None:
                results.append(result)

        return results

    @staticmethod
    def _parse_entry(entry) -> "GeoResult | None":
        """
        Convert one payload entry, skipping malformed ones.

        Suggestions are best effort: one bad entry never discards the
        rest.
        """

        if not isinstance(entry, dict):
            return None

        name = str(entry.get("name", "")).strip()

        if not name:
            return None

        return GeoResult(
            name=name,
            state=str(entry.get("state", "")).strip(),
            country=str(entry.get("country", "")).strip(),
        )


def validate_key(api_key: str) -> bool:
    """
    Check an API key with one cheap geocoding call.

    Used by the first-run dialog before the key is stored. Any
    failure (rejected key, network trouble) counts as invalid: the
    dialog will say so and let the user retry.
    """

    try:
        response = requests.get(
            GEO_URL,
            params={"q": "London", "limit": 1, "appid": api_key},
            timeout=REQUEST_TIMEOUT,
        )
    except RequestException:
        return False

    return response.status_code == 200


def store_key(api_key: str) -> None:
    """
    Write the key to the dotenv-style file in the data directory.

    weather_api loads this file at startup. The key never goes
    anywhere else (see PRIVACY.md).
    """

    key_file = paths.key_file()

    key_file.write_text(KEY_FILE_LINE.format(key=api_key), encoding="utf-8")
