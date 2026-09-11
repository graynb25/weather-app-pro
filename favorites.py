"""
favorites.py
============

Persisted saved cities for Weather App Pro (favorites.json).

Responsibilities:
    - Keep an ordered list of saved city names
    - Cap the list (10 is plenty) and dedupe case-insensitively
    - Persist on every change, never on close
    - Defensive IO: corrupt or missing files fall back to an empty
      list; writes go through a temp file plus rename

The API key and anything derived from it never goes into this file.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(f"weather.{__name__}")

PROJECT_ROOT = Path(__file__).resolve().parent

FAVORITES_FILE = PROJECT_ROOT / "favorites.json"

MAX_FAVORITES = 10


class Favorites:
    """
    Loads, validates, and persists the saved cities.
    """

    def __init__(self, path=None):
        self.path = Path(path) if path else FAVORITES_FILE
        self.cities = []
        self.load()

    # ---------------------------------------------------------
    # Access
    # ---------------------------------------------------------

    def get(self) -> list[str]:
        """
        Return the saved cities in display order.
        """

        return list(self.cities)

    def contains(self, city: str) -> bool:
        """
        True when the city is already saved, case-insensitively.
        """

        wanted = city.strip().casefold()

        return any(existing.casefold() == wanted for existing in self.cities)

    # ---------------------------------------------------------
    # Changes (each one persists immediately)
    # ---------------------------------------------------------

    def add(self, city: str) -> bool:
        """
        Save a city. Returns False when it is already saved or the
        list is full.
        """

        cleaned = city.strip()

        if not cleaned or self.contains(cleaned):
            return False

        if len(self.cities) >= MAX_FAVORITES:
            return False

        self.cities.append(cleaned)
        self.save()

        return True

    def remove(self, city: str) -> bool:
        """
        Remove a saved city, case-insensitively. Returns False when
        it was not saved.
        """

        wanted = city.strip().casefold()

        for index, existing in enumerate(self.cities):
            if existing.casefold() == wanted:
                del self.cities[index]
                self.save()

                return True

        return False

    # ---------------------------------------------------------
    # IO
    # ---------------------------------------------------------

    def load(self) -> None:
        """
        Read favorites.json over an empty list.

        A missing, corrupt, or invalid file leaves the list empty with
        a warning; it can never stop the app from starting.
        """

        if not self.path.exists():
            return

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))

        except (OSError, ValueError) as error:
            logger.warning("Ignoring unreadable favorites: %s",
                type(error).__name__)

            return

        if not isinstance(payload, list):
            logger.warning("Ignoring favorites with an unexpected shape.")
            return

        cities = []

        for entry in payload:
            if not isinstance(entry, str):
                continue

            cleaned = entry.strip()

            if cleaned and not self._contains_in(cities, cleaned):
                cities.append(cleaned)

        self.cities = cities[:MAX_FAVORITES]

    def save(self) -> None:
        """
        Write favorites.json atomically.

        A write failure is logged and swallowed: favorites are a
        convenience, never a dependency.
        """

        tmp_path = self.path.with_suffix(".json.tmp")

        try:
            tmp_path.write_text(
                json.dumps(self.cities, indent=2), encoding="utf-8"
            )
            os.replace(tmp_path, self.path)
        except OSError as error:
            logger.warning("Could not write favorites: %s", error)

    @staticmethod
    def _contains_in(cities: list[str], city: str) -> bool:
        wanted = city.casefold()

        return any(existing.casefold() == wanted for existing in cities)
