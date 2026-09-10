"""
weather_api.py
==============

Handles all communication with the OpenWeatherMap API.

Responsibilities:
    - Get current weather
    - Get 5-day forecast
    - Hide API implementation details from the UI

Author: Gray Nelson
Project: Weather App Pro
"""

import os
import requests

from dotenv import load_dotenv

from config import (BASE_URL, CURRENT_WEATHER_ENDPOINT, FORECAST_ENDPOINT,
    REQUEST_TIMEOUT, DEFAULT_UNITS)

from weather_model import WeatherData, ForecastData
from datetime import datetime

from requests.exceptions import (
    ConnectionError,
    Timeout,
    HTTPError,
    RequestException,
)

# ---------------------------------------------------------
# Load environment variables (.env)
# ---------------------------------------------------------

load_dotenv()

class WeatherAPI:
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")


    def api_key_exists(self) -> bool:
        return bool(self.api_key)

    def _make_request(self, url: str, params: dict, city: str) -> dict:
        """
        Send a request to the OpenWeatherMap API and return
        the JSON response.

        Raises:
            ValueError: If the request cannot be completed.
        """

        try:

            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            self._validate_response(response, city)

            return response.json()

        except ConnectionError:
            raise ValueError(
                "No internet connection."
            )

        except Timeout:
            raise ValueError(
                "The request timed out. Please try again."
            )

        except HTTPError:
            raise

        except RequestException:
            raise ValueError(
                "Unable to contact the weather service."
            )

    def _validate_response(self, response: requests.Response, city: str) -> None:
        """
        Validate an OpenWeatherMap API response.

        Raises:
            ValueError: If the request failed with a known error.
        """

        if response.status_code == 404:
            raise ValueError(
                f'City "{city}" was not found.'
            )

        if response.status_code == 401:
            raise ValueError(
                "Invalid OpenWeatherMap API key."
            )

        if response.status_code == 429:
            raise ValueError(
                "OpenWeatherMap rate limit exceeded."
            )

        response.raise_for_status()

    def get_current_weather(self, city: str) -> WeatherData:
        """
            Retrieve the current weather for the specified city.

            Args:
                city: Name of the city to search for.

            Returns:
                A WeatherData object containing the current weather.
            """
        # ---------------------------------------------------------
        # Validate city name
        # ---------------------------------------------------------

        city = city.strip()

        if not city:
            raise ValueError(
                "City name cannot be empty."
            )

        # ---------------------------------------------------------
        # Verify API key
        # ---------------------------------------------------------

        if not self.api_key:
            raise ValueError(
                "OpenWeather API key not found."
            )

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

        data = self._make_request(
            url,
            params,
            city
        )

        # ---------------------------------------
        # Temperature
        # ---------------------------------------

        temperature_f = data["main"]["temp"]
        temperature_c = (temperature_f - 32) * 5 / 9

        feels_like_f = data["main"]["feels_like"]
        feels_like_c = (feels_like_f - 32) * 5 / 9

        temp_min_f = data["main"]["temp_min"]
        temp_max_f = data["main"]["temp_max"]

        temp_min_c = (temp_min_f - 32) * 5 / 9
        temp_max_c = (temp_max_f - 32) * 5 / 9

        # ---------------------------------------
        # Return WeatherData object
        # ---------------------------------------

        return WeatherData(
            city=data["name"],
            country=data["sys"]["country"],

            temperature_f=temperature_f,
            temperature_c=temperature_c,

            feels_like_f=feels_like_f,
            feels_like_c=feels_like_c,

            temp_min_f=temp_min_f,
            temp_min_c=temp_min_c,

            temp_max_f=temp_max_f,
            temp_max_c=temp_max_c,

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

    def get_forecast(self, city: str) -> list[ForecastData]:
        url = (
            f"{BASE_URL}"
            f"{FORECAST_ENDPOINT}"
        )

        params = {
            "q": city,
            "appid": self.api_key,
            "units": DEFAULT_UNITS,
        }

        data = self._make_request(
            url,
            params,
            city
        )

        daily_forecasts = {}

        # ---------------------------------------------------------
        # Find the forecast closest to midday for each day
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Convert to ForecastData objects
        # ---------------------------------------------------------

        forecast = []

        for _, item in daily_forecasts.values():
            forecast_time = datetime.fromtimestamp(item["dt"])

            temperature_f = item["main"]["temp"]
            temperature_c = (temperature_f - 32) * 5 / 9

            forecast.append(
                ForecastData(
                    day=forecast_time.strftime("%a"),
                    date=forecast_time.strftime("%Y-%m-%d"),

                    temperature_f=temperature_f,
                    temperature_c=temperature_c,

                    description=item["weather"][0]["description"].title(),
                    weather_id=item["weather"][0]["id"],
                )
            )

        # ---------------------------------------------------------
        # Sort by date
        # ---------------------------------------------------------

        forecast.sort(key=lambda day: day.date)

        return forecast


