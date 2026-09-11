"""
main.py
========

Entry point for the Weather App.

Responsibilities
----------------
1. Set up logging.
2. Create the QApplication.
3. Create the main application window.
4. Display the window.
5. Start Qt's event loop.

This file should remain very small.
All UI code belongs in ui.py.
"""

import os
import sys

from PyQt5.QtWidgets import QApplication

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

    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()