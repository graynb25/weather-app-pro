"""
crash_hooks.py
==============

Last-resort handlers so a crash leaves a trace in the log.

Responsibilities:
    - Log uncaught exceptions with a full stack trace
    - Log Qt warnings and errors that would otherwise vanish
    - Show one friendly dialog before the process exits

main.py installs these once, right after logging. The dialog needs a
running QApplication, so the hooks stay quiet in headless contexts.
"""

import logging
import sys
import traceback

from PyQt5.QtCore import qInstallMessageHandler, QtMsgType
from PyQt5.QtWidgets import QApplication, QMessageBox

logger = logging.getLogger(f"weather.{__name__}")

CRASH_MESSAGE = (
    "Weather App Pro hit an unexpected error and has to close. "
    "Details were written to logs/app.log."
)

_QT_LEVELS = {
    QtMsgType.QtDebugMsg: logging.DEBUG,
    QtMsgType.QtInfoMsg: logging.INFO,
    QtMsgType.QtWarningMsg: logging.WARNING,
    QtMsgType.QtCriticalMsg: logging.ERROR,
    QtMsgType.QtFatalMsg: logging.ERROR,
}


def _show_crash_dialog() -> None:
    """
    Show the crash dialog when a QApplication exists to host it.
    """

    if QApplication.instance() is None:
        return

    QMessageBox.critical(None, "Weather App Pro", CRASH_MESSAGE)


def _handle_exception(exc_type, exc_value, exc_tb) -> None:
    """
    Log the exception, tell the user, then let Python die normally.
    """

    logger.error("Unhandled exception:\n%s",
        "".join(traceback.format_exception(exc_type, exc_value, exc_tb)))

    _show_crash_dialog()

    sys.__excepthook__(exc_type, exc_value, exc_tb)


def _handle_qt_message(msg_type, context, message) -> None:
    """
    Route Qt's own messages into our log.
    """

    logger.log(_QT_LEVELS.get(msg_type, logging.INFO), "Qt: %s", message)


def install_crash_hooks() -> None:
    """
    Install the exception and Qt message handlers.
    """

    sys.excepthook = _handle_exception
    qInstallMessageHandler(_handle_qt_message)
