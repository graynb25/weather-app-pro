"""
icon_manager.py
===============

Handles weather icons used throughout the application.

Responsibilities
----------------
- Map OpenWeather weather IDs to icon files.
- Return the correct icon path.
- Keep all icon-related logic out of the UI.

Author: Gray Nelson
Project: Weather App Pro
"""

import paths


class IconManager:
    """
    Returns the correct icon path for a weather condition.
    """

    # Resource folders (resolved through paths.py so a frozen
    # build finds them in its extraction directory)
    RESOURCE_FOLDER = paths.resources_root()
    WEATHER_FOLDER = RESOURCE_FOLDER / "icons" / "weather"
    DETAIL_FOLDER = RESOURCE_FOLDER / "icons" / "details"

    # ---------------------------------------------------------
    # Detail Icons
    # ---------------------------------------------------------

    DETAIL_ICONS = {
        "feels_like": "thermometer.svg",
        "humidity": "humidity.svg",
        "wind": "wind.svg",
        "visibility": "visibility.svg",
        "pressure": "barometer.svg",
        "sunrise": "sunrise.svg",
        "sunset": "sunset.svg",
    }

    @classmethod
    def get_icon_path(cls, weather_id: int) -> str:
        """
        Return the path to the correct icon.

        Args:
            weather_id:
                OpenWeather weather condition ID.

        Returns:
            Path to an SVG icon.
        """

        # Thunderstorms
        if 200 <= weather_id <= 232:
            filename = "thunderstorms.svg"

        # Drizzle
        elif 300 <= weather_id <= 321:
            filename = "drizzle.svg"

        # Rain
        elif 500 <= weather_id <= 531:
            filename = "rain.svg"

        # Snow
        elif 600 <= weather_id <= 622:
            filename = "snow.svg"

        # Atmosphere (mist, fog, smoke, etc.)
        elif 701 <= weather_id <= 781:

            if weather_id == 762:
                filename = "volcano.svg"

            elif weather_id == 771:
                filename = "wind.svg"

            else:
                filename = "fog.svg"

        # Clear sky
        elif weather_id == 800:
            filename = "clear-day.svg"

        # Clouds
        elif 801 <= weather_id <= 804:
            filename = "cloudy.svg"

        # Anything unexpected
        else:
            filename = "not-available.svg"

        return str(cls.WEATHER_FOLDER / filename)

    @classmethod
    def get_detail_icon(cls, detail_name: str) -> str:
        """
        Return the path to a detail SVG icon.
        """

        filename = cls.DETAIL_ICONS.get(
            detail_name,
            "not-available.svg"
        )

        return str(cls.DETAIL_FOLDER / filename)
