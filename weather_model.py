"""
weather_model.py
================

Contains the WeatherData dataclass.

This class stores weather information in a clean,
organized format so the UI doesn't need to know
how the API response is structured.
"""

from dataclasses import dataclass

@dataclass
class WeatherData:
    """
    Represents the current weather for one city.
    """

    # -------------------------------------------------
    # City Information
    # -------------------------------------------------

    city: str
    country: str

    # -------------------------------------------------
    # Temperature
    # -------------------------------------------------

    temperature_f: float
    temperature_c: float

    feels_like_f: float
    feels_like_c: float

    temp_min_f: float
    temp_min_c: float

    temp_max_f: float
    temp_max_c: float

    # -------------------------------------------------
    # Weather
    # -------------------------------------------------

    description: str
    weather_id: int

    # -------------------------------------------------
    # Details
    # -------------------------------------------------

    humidity: int
    wind_speed: float
    pressure: int
    visibility: float

    # -------------------------------------------------
    # Sun
    # -------------------------------------------------

    sunrise: int
    sunset: int

    # -------------------------------------------------
    # Time
    # -------------------------------------------------

    timezone: int

    # -------------------------------------------------
    # Forecast
    # -------------------------------------------------

    # -------------------------------------------------
    # Forecast
    # -------------------------------------------------

@dataclass
class ForecastData:
    """
    Represents one day in the 5-day forecast.
    """

    # -------------------------------------------------
    # Date
    # -------------------------------------------------

    day: str    # "Mon"
    date: str   # "2026-07-27"

    # -------------------------------------------------
    # Temperature
    # -------------------------------------------------

    temperature_f: float
    temperature_c: float

    # -------------------------------------------------
    # Weather
    # -------------------------------------------------

    description: str
    weather_id: int


