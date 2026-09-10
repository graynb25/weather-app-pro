"""
animation_manager.py
====================

Handles all Lottie animations used throughout the application.

Responsibilities
----------------
- Locate weather animations.
- Locate detail animations.
- Return animation paths.
- Hide animation file structure from the UI.

Author: Gray Nelson
Project: Weather App Pro
"""

# ==========================================================
# Imports
# ==========================================================

from pathlib import Path
from PyQt5.QtCore import QUrl



# ==========================================================
# Animation Manager
# ==========================================================

class AnimationManager:
    """
    Provides paths to all Lottie animations used by the application.
    """

    # ------------------------------------------------------
    # Project folders
    # ------------------------------------------------------

    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    RESOURCE_FOLDER = PROJECT_ROOT / "resources"
    WEATHER_FOLDER = RESOURCE_FOLDER / "animations" / "weather"
    DETAIL_FOLDER = RESOURCE_FOLDER / "animations" / "details"

    # ------------------------------------------------------
    # Detail animation lookup
    # ------------------------------------------------------

    DETAIL_ANIMATIONS = {
        "feels_like": "thermometer.json",
        "humidity": "humidity.json",
        "wind": "wind.json",
        "pressure": "pressure-low.json",
        "sunrise": "sunrise.json",
        "sunset": "sunset.json",

        # Placeholder until a visibility animation is added
        "visibility": "not-available.json",
    }

    # ------------------------------------------------------
    # Public Methods
    # ------------------------------------------------------

    @classmethod
    def get_weather_animation(cls, weather_id: int) -> str:
        """
        Return the appropriate weather animation.
        """

        if 200 <= weather_id <= 232:
            filename = "thunderstorms.json"

        elif 300 <= weather_id <= 321:
            filename = "drizzle.json"

        elif 500 <= weather_id <= 531:
            filename = "rain.json"

        elif 600 <= weather_id <= 622:
            filename = "snow.json"

        elif 701 <= weather_id <= 781:

            if weather_id == 762:
                filename = "volcano.json"

            elif weather_id == 771:
                filename = "wind.json"

            else:
                filename = "fog.json"

        elif weather_id == 800:
            filename = "clear-day.json"

        elif 801 <= weather_id <= 804:
            filename = "cloudy.json"

        else:
            filename = "not-available.json"

        return QUrl.fromLocalFile(
            str(cls.WEATHER_FOLDER / filename)
        ).toString()

    @classmethod
    def get_detail_animation(cls, detail_name: str) -> str:
        """
        Return the requested detail animation.
        """

        filename = cls.DETAIL_ANIMATIONS.get(
            detail_name,
            "not-available.json"
        )

        return QUrl.fromLocalFile(
            str(cls.DETAIL_FOLDER / filename)
        ).toString()

    @classmethod
    def animation_exists(cls, animation_path: str) -> bool:
        """
        Return True if the animation exists.
        """

        return Path(animation_path).exists()

    @classmethod
    def available_weather_animations(cls) -> list[str]:
        """
        Return all available weather animations.
        """

        return sorted(
            file.stem
            for file in cls.WEATHER_FOLDER.glob("*.json")
        )

    @classmethod
    def available_detail_animations(cls) -> list[str]:
        """
        Return all available detail animations.
        """

        return sorted(
            file.stem
            for file in cls.DETAIL_FOLDER.glob("*.json")
        )