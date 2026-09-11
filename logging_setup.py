"""
logging_setup.py
================

Logging bootstrap for Weather App Pro.

Responsibilities:
    - Configure the "weather" logger namespace once at startup
    - Write DEBUG level records to logs/app.log with rotation
    - Optionally mirror INFO level records to the console

main.py calls setup_logging() before the window is built. Modules log
through logging.getLogger("weather." + __name__), which nests under the
"weather" namespace and inherits this configuration.

Secrets: nothing may reach a log line without redaction. URLs go through
utils.redact_url, and exception text from the requests library is never
logged as-is (it can embed the request URL, which contains the key).
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

LOG_FOLDER = PROJECT_ROOT / "logs"
LOG_FILE = LOG_FOLDER / "app.log"

MAX_BYTES = 1_000_000     # 1 MB per file
BACKUP_COUNT = 5          # app.log.1 ... app.log.5

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(console: bool = False, log_file: Path = LOG_FILE) -> None:
    """
    Configure the app's logging namespace. Safe to call only once.

    Args:
        console: Also emit INFO and above to the console.
        log_file: Target file for the rotating handler. Tests use this
            to write somewhere disposable.
    """

    logger = logging.getLogger("weather")

    if logger.handlers:
        return

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT)

    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
