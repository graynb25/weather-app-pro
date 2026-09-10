"""
main.py
========

Entry point for the Weather App.

Responsibilities
----------------
1. Create the QApplication.
2. Create the main application window.
3. Display the window.
4. Start Qt's event loop.

This file should remain very small.
All UI code belongs in ui.py.
"""

import sys

from PyQt5.QtWidgets import QApplication

from ui import WeatherApp


def main() -> None:
    """
    Create and run the application.
    """

    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()