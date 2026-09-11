"""
main.py
========

Entry point for the Weather App.

Responsibilities
----------------
1. Set up logging and crash hooks.
2. Create the QApplication.
3. Create the main application window.
4. Warn once when the API key is missing.
5. Display the window and start Qt's event loop.

This file should remain very small.
All UI code belongs in ui.py.
"""

import os
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

from crash_hooks import install_crash_hooks
from logging_setup import setup_logging
from ui import WeatherApp
from weather_api import MESSAGE_KEY_MISSING


def main() -> None:
    """
    Create and run the application.
    """

    # Mirror INFO level log records in the console when asked for.
    # The flag lives in .env (see .env.example), which python-dotenv
    # loads while ui.py imports weather_api.
    setup_logging(console=os.getenv("WEATHER_CONSOLE_LOG") == "1")

    install_crash_hooks()

    app = QApplication(sys.argv)
    window = WeatherApp()

    # Surface a missing key now, instead of failing on the first search.
    # The message names the variable, never its value.
    if not window.weather_api.api_key_exists():
        QMessageBox.warning(window, "Weather App Pro", MESSAGE_KEY_MISSING)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
