"""
flag_manager.py
===============

Handles flag icons used throughout the application.

Responsibilities
----------------
- Map OpenWeather flag IDs to icon files.
- Return the correct icon path.
- Keep flag icon-related logic out of the UI.

Author: Gray Nelson
Project: Weather App Pro
"""

from pathlib import Path


class FlagManager:
    """
    Returns the path to a country's flag icon.
    """

    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    RESOURCE_FOLDER = PROJECT_ROOT / "resources"
    FLAG_FOLDER = RESOURCE_FOLDER / "icons" / "flags"

    @classmethod
    def get_flag_path(cls, country_code: str) -> str:
        filename = f"{country_code.lower()}.svg"

        flag = cls.FLAG_FOLDER / filename

        if flag.exists():
            return str(flag)

        return str(cls.FLAG_FOLDER / "not-available.svg")
