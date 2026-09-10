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

from pathlib import Path


class IconManager:
    """
    Returns the correct icon path for a weather condition.
    """

    # Root folder of the application
    PROJECT_ROOT = Path(__file__).resolve().parent

    # Resource folders
    RESOURCE_FOLDER = PROJECT_ROOT / "resources"
    ICON_FOLDER = RESOURCE_FOLDER / "icons" / "weather"
    FLAG_FOLDER = RESOURCE_FOLDER / "icons" / "flags"

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

        return str(cls.ICON_FOLDER / filename)

    @classmethod
    def get_flag_path(cls, country_code: str) -> str:
        """
        Return the path to a country's flag icon.

        Args:
            country_code:
                ISO country code (US, JP, FR...)

        Returns:
            Path to the SVG flag.
        """

        filename = f"{country_code.lower()}.svg"

        flag = cls.FLAG_FOLDER / filename

        if flag.exists():
            return str(flag)

        return str(cls.FLAG_FOLDER / "not-available.svg")