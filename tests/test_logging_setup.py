"""
test_logging_setup.py
=====================

Tests for the logging bootstrap in logging_setup.py.
"""

import logging

from conftest import DUMMY_API_KEY

from logging_setup import setup_logging
from utils import redact_url


def test_setup_logging_writes_rotating_file(tmp_path):
    logger = logging.getLogger("weather")

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    log_file = tmp_path / "app.log"
    setup_logging(console=False, log_file=log_file)

    try:
        logging.getLogger("weather.weather_api").debug("bootstrap smoke message")
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    content = log_file.read_text(encoding="utf-8")

    assert "bootstrap smoke message" in content
    assert "weather.weather_api" in content


def test_setup_logging_is_idempotent(tmp_path):
    logger = logging.getLogger("weather")

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    try:
        setup_logging(console=False, log_file=tmp_path / "app.log")
        setup_logging(console=False, log_file=tmp_path / "app.log")

        assert len(logger.handlers) == 1
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
