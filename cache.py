"""
cache.py
========

Stores the last successful search so the app can show something
without a live request.

Responsibilities:
    - Save WeatherData, the forecast, and a timestamp as plain JSON
    - Load them back, defensively
    - Never store or log the API key

The file is small and rewritten whole on every save, through a temp
file plus rename, so a crash mid-write cannot corrupt the previous
copy. Only dataclass fields are stored, never anything derived from
the request or the key.
"""

import json
import logging
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from weather_model import WeatherData, ForecastData, HourData

logger = logging.getLogger(f"weather.{__name__}")

PROJECT_ROOT = Path(__file__).resolve().parent

CACHE_FILE = PROJECT_ROOT / "cache.json"


class WeatherCache:
    """
    Reads and writes the last successful weather result.
    """

    def __init__(self, path: Path = CACHE_FILE):
        self.path = path

    def save(self, weather: WeatherData,
        forecast: list[ForecastData], hourly: list = ()) -> None:
        """
        Write the given result to disk, replacing any previous one.

        A write failure is logged and swallowed: the cache is a
        convenience, never a dependency.
        """

        payload = {
            "fetched_at": int(datetime.now().timestamp()),
            "weather": asdict(weather),
            "forecast": [asdict(day) for day in forecast],
            "hourly": [asdict(chip) for chip in hourly],
        }

        tmp_path = self.path.with_suffix(".json.tmp")

        try:
            tmp_path.write_text(json.dumps(payload), encoding="utf-8")
            os.replace(tmp_path, self.path)
        except OSError as error:
            logger.warning("Could not write the weather cache: %s", error)

    def load(self):
        """
        Return (weather, forecast, hourly, fetched_at) from the last
        save, or None when there is no readable cache.

        Corrupt or unexpected files are ignored with a warning rather
        than raised, so a bad cache can never stop the app from
        starting. Caches written before the hourly strip existed load
        with an empty hourly list.
        """

        if not self.path.exists():
            return None

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))

            weather = WeatherData(**payload["weather"])
            forecast = [ForecastData(**day) for day in payload["forecast"]]
            hourly = [HourData(**chip) for chip in payload.get("hourly", [])]
            fetched_at = int(payload["fetched_at"])

        except (OSError, ValueError, KeyError, TypeError) as error:
            # The type name only: stringified payloads could hold
            # arbitrary values.
            logger.warning("Ignoring an unreadable weather cache: %s",
                type(error).__name__)

            return None

        return weather, forecast, hourly, fetched_at
