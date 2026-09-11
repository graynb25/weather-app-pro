"""
utils.py
=========

Helper functions used throughout the application.

Keeping conversions here prevents duplicate code
and makes future updates much easier.
"""

import re
from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------
# Secrets
# ---------------------------------------------------------

def redact_url(url: str) -> str:
    """
    Replace the appid query parameter value with ***.

    Anything derived from a request URL goes through this before it can
    reach a log file or an error message, so the API key never leaks.
    """

    return re.sub(r"([?&]appid=)[^&]*", r"\1***", url)


# ---------------------------------------------------------
# Temperature
# ---------------------------------------------------------

def fahrenheit_to_celsius(temp_f: float) -> float:
    """
    Convert Fahrenheit to Celsius.
    """

    return (temp_f - 32) * 5 / 9

def meters_per_second_to_mph(speed: float) -> float:
    """
    Convert meters/second to miles/hour.
    """

    return speed * 2.237

def meters_per_second_to_kmh(speed: float) -> float:
    """
    Convert meters/second to kilometers/hour.
    """

    return speed * 3.6

def miles_per_hour_to_kmh(speed: float) -> float:
    """
    Convert miles/hour to kilometers/hour.

    The API is queried in imperial, so wind arrives as mph and the
    metric display converts from there.
    """

    return speed * 1.609344

# ---------------------------------------------------------
# Visibility
# ---------------------------------------------------------

def meters_to_miles(distance: float) -> float:
    """
    Convert meters to miles.
    """

    return distance / 1609.34


def meters_to_km(distance: float) -> float:
    """
    Convert meters to kilometers.
    """

    return distance / 1000

# ---------------------------------------------------------
# Time
# ---------------------------------------------------------

def unix_to_local_time(timestamp: int, offset_seconds: int) -> str:
    """
    Convert a Unix timestamp into the city's local time.

    Parameters
    ----------
    timestamp
        Unix timestamp from OpenWeatherMap.

    offset_seconds
        Timezone offset supplied by the API.

    Returns
    -------
    str
        Example:
            06:42 AM
    """

    tz = timezone(timedelta(seconds=offset_seconds))

    return datetime.fromtimestamp(
        timestamp,
        tz
    ).strftime("%I:%M %p")