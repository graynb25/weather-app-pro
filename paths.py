"""
paths.py
========

Single source for every filesystem location the app uses.

Responsibilities:
    - Resolve the read-only application root (source folder in dev,
      the PyInstaller extraction directory when frozen)
    - Resolve the writable data directory (next to the source in dev,
      %LOCALAPPDATA%\\WeatherAppPro when frozen)
    - Provide one named path per runtime file

Running from source behaves exactly like before: everything lives in
the project folder. A frozen build cannot rely on that (Program Files
is not writable and onefile bundles extract to a temp directory), so
runtime files move to the user's data directory while resources and
VERSION stay on the read-only side.
"""

import os
import sys
from pathlib import Path

DATA_DIR_NAME = "WeatherAppPro"


def is_frozen() -> bool:
    """
    True when running from a PyInstaller bundle.
    """

    return bool(getattr(sys, "frozen", False))


def app_root() -> Path:
    """
    The read-only side: source folder in dev, extraction directory
    when frozen. Holds the code, resources, and the VERSION file.
    """

    if is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)

        if meipass:
            return Path(meipass)

        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


def data_dir() -> Path:
    """
    The writable side: runtime files (key file, settings, favorites,
    cache, logs). Next to the source in dev; %LOCALAPPDATA% when
    frozen.
    """

    if is_frozen():
        local_app_data = os.getenv(
            "LOCALAPPDATA",
            str(Path.home() / "AppData" / "Local"),
        )

        return Path(local_app_data) / DATA_DIR_NAME

    return app_root()


def ensure_data_dir() -> Path:
    """
    The data directory, created if missing.
    """

    directory = data_dir()
    directory.mkdir(parents=True, exist_ok=True)

    return directory


def version_file() -> Path:
    return app_root() / "VERSION"


def resources_root() -> Path:
    return app_root() / "resources"


def key_file() -> Path:
    return ensure_data_dir() / ".env"


def settings_file() -> Path:
    return ensure_data_dir() / "settings.json"


def favorites_file() -> Path:
    return ensure_data_dir() / "favorites.json"


def cache_file() -> Path:
    return ensure_data_dir() / "cache.json"


def log_file() -> Path:
    return ensure_data_dir() / "logs" / "app.log"
