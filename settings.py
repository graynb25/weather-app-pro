"""
settings.py
===========

Persisted user settings for Weather App Pro (settings.json).

Responsibilities:
    - Load and save plain JSON settings
    - Fall back to defaults on missing, corrupt, or invalid files
    - Write through a temp file plus rename so a crash mid-write
      cannot corrupt the previous copy

Defensive IO per docs/error-handling-and-security.md item 3.6. Only
the known keys below are ever read, unknown keys are dropped, and
invalid values fall back to that key's default. The API key and
anything derived from it never goes into this file.
"""

import json
import logging
import os

import paths

from pathlib import Path

logger = logging.getLogger(f"weather.{__name__}")

SETTINGS_FILE = paths.settings_file()

UNITS = ("imperial", "metric")
CONDITION_MODES = ("auto", "clear", "cloudy", "rain", "snow", "mist", "night")
REFRESH_MINUTES = (5, 10, 15, 30, 60)

DEFAULTS = {
    "units": "imperial",
    "condition_mode": "auto",
    "refresh_minutes": 10,
    "window": None,          # [x, y, width, height] once saved
}


class Settings:
    """
    Loads, validates, and persists the user's settings.
    """

    def __init__(self, path=None):
        self.path = Path(path) if path else SETTINGS_FILE
        self.values = dict(DEFAULTS)
        self.load()

    # ---------------------------------------------------------
    # Access
    # ---------------------------------------------------------

    def get(self, key: str):
        """
        Return a setting value. Unknown keys raise like a dict.
        """

        return self.values[key]

    def set(self, key: str, value) -> None:
        """
        Validate, store, and immediately persist a setting.

        Invalid values are ignored with a warning, keeping the
        previous one.
        """

        validated = self._validate(key, value)

        if validated is None:
            logger.warning("Rejected invalid value for %s: %r", key, value)
            return

        self.values[key] = validated
        self.save()

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def _validate(self, key: str, value):
        """
        Return a validated copy of the value, or None when invalid.
        """

        if key == "units":
            return value if value in UNITS else None

        if key == "condition_mode":
            return value if value in CONDITION_MODES else None

        if key == "refresh_minutes":
            if isinstance(value, int) and not isinstance(value, bool) \
                    and value in REFRESH_MINUTES:
                return value
            return None

        if key == "window":
            if not isinstance(value, (list, tuple)) or len(value) != 4:
                return None

            if not all(isinstance(n, int) and not isinstance(n, bool)
                    for n in value):
                return None

            width = value[2]
            height = value[3]

            if width < 420 or height < 450:
                return None

            return [int(n) for n in value]

        return None

    # ---------------------------------------------------------
    # IO
    # ---------------------------------------------------------

    def load(self) -> None:
        """
        Read settings.json over the defaults.

        A missing, empty, corrupt, or invalid file leaves the defaults
        in place with a warning; it can never stop the app from
        starting.
        """

        if not self.path.exists():
            return

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))

            if not isinstance(payload, dict):
                raise ValueError("settings root is not an object")

        except (OSError, ValueError) as error:
            logger.warning("Ignoring unreadable settings: %s",
                type(error).__name__)

            return

        for key in DEFAULTS:
            if key not in payload:
                continue

            validated = self._validate(key, payload[key])

            if validated is not None:
                self.values[key] = validated
            else:
                logger.warning("Ignored invalid stored value for %s", key)

    def save(self) -> None:
        """
        Write settings.json atomically.

        A write failure is logged and swallowed: settings are a
        convenience, never a dependency.
        """

        tmp_path = self.path.with_suffix(".json.tmp")

        try:
            tmp_path.write_text(
                json.dumps(self.values, indent=2), encoding="utf-8"
            )
            os.replace(tmp_path, self.path)
        except OSError as error:
            logger.warning("Could not write settings: %s", error)
