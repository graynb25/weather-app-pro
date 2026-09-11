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

import paths


class FlagManager:
    """
    Returns the path to a country's flag icon.
    """

    RESOURCE_FOLDER = paths.resources_root()
    FLAG_FOLDER = RESOURCE_FOLDER / "icons" / "flags"

    @classmethod
    def get_flag_path(cls, country_code: str) -> str:
        filename = f"{country_code.lower()}.svg"

        flag = cls.FLAG_FOLDER / filename

        if flag.exists():
            return str(flag)

        return str(cls.FLAG_FOLDER / "not-available.svg")
