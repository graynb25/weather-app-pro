"""
main.py
========

Entry point for the Weather App.

Responsibilities
----------------
1. Set up logging and crash hooks.
2. Enforce a single running instance.
3. Create the QApplication with High DPI scaling.
4. Create the main application window.
5. Run the first-run API key setup when no key exists.
6. Display the window and start Qt's event loop.

This file should remain very small.
All UI code belongs in ui.py.
"""

import os
import sys

from PyQt5.QtCore import QLockFile, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

import paths
from crash_hooks import install_crash_hooks
from logging_setup import setup_logging
from ui import WeatherApp


def main() -> None:
    """
    Create and run the application.
    """

    # Mirror INFO level log records in the console when asked for.
    # The flag lives in .env (see .env.example), which python-dotenv
    # loads while ui.py imports weather_api.
    setup_logging(console=os.getenv("WEATHER_CONSOLE_LOG") == "1")

    install_crash_hooks()

    # Crisp rendering on scaled displays. Must happen before the
    # QApplication exists.
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # One instance at a time. The lock lives in the data directory and
    # releases automatically when the process dies.
    paths.ensure_data_dir()

    lock = QLockFile(str(paths.data_dir() / "app.lock"))
    lock.setStaleLockTime(0)

    if not lock.tryLock(100):
        QMessageBox.warning(
            None,
            "Weather App Pro",
            "Weather App Pro is already running.",
        )
        sys.exit(0)

    window = WeatherApp()

    # First run: ask for a free OpenWeatherMap key and store it in the
    # data directory. Skipping is fine; the app warns again on search.
    if not window.weather_api.api_key_exists():
        window.offer_key_setup()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
