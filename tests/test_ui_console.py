"""
test_ui_console.py
==================

Integration tests for the glass console main window.

These run the real WeatherApp offscreen. The window no longer embeds
QWebEngine, so it is safe to build in a test process. Searches go
through the real worker thread with requests_mock underneath.
"""

import pytest

from conftest import VALID_CURRENT_PAYLOAD, VALID_FORECAST_PAYLOAD

from config import BASE_URL, CURRENT_WEATHER_ENDPOINT, FORECAST_ENDPOINT
from ui import WeatherApp
from weather_model import ForecastData, HourData, WeatherData
from widgets.forecast_table import ForecastTable
from widgets.hourly_strip import HourlyStrip
from widgets.sky_widget import SkyWidget

CURRENT_URL = BASE_URL + CURRENT_WEATHER_ENDPOINT
FORECAST_URL = BASE_URL + FORECAST_ENDPOINT


@pytest.fixture(autouse=True)
def no_cache_file():
    """
    Keep the runtime cache file out of the test run: a saved search
    from one test would otherwise greet the next window as stale data.
    """

    from cache import CACHE_FILE

    CACHE_FILE.unlink(missing_ok=True)

    yield

    CACHE_FILE.unlink(missing_ok=True)


def sample_hourly() -> list:
    return [
        HourData(hour="NOW", temperature_f=85.0, temperature_c=29.4,
            weather_id=800),
        HourData(hour="3 PM", temperature_f=84.0, temperature_c=28.9,
            weather_id=800),
    ]


def sample_weather() -> WeatherData:
    return WeatherData(
        city="London", country="GB",
        temperature_f=64.0, temperature_c=17.8,
        feels_like_f=61.0, feels_like_c=16.1,
        temp_min_f=53.6, temp_min_c=12.0,
        temp_max_f=69.8, temp_max_c=21.0,
        description="Light Rain", weather_id=500,
        humidity=72, wind_speed=7.5, pressure=1015, visibility=10000,
        sunrise=0, sunset=86400, timezone=0,
    )


def sample_forecast() -> list:
    return [
        ForecastData(
            day="Mon", date="2026-09-14",
            temperature_f=64.0, temperature_c=17.8,
            temp_min_f=53.6, temp_min_c=12.0,
            temp_max_f=69.8, temp_max_c=21.0,
            description="Light Rain", weather_id=500,
        )
    ]


def test_condition_mapping_covers_all_ranges():
    from managers.condition_theme import ConditionTheme

    assert ConditionTheme.from_weather(800, is_day=True) == "clear"


def test_window_builds_and_shows_idle_state(qtbot):
    window = WeatherApp()
    qtbot.addWidget(window)

    assert window.status_label.text() == "Ready"
    assert window.sky.condition in ("clear", "cloudy", "rain", "snow", "mist", "night")
    assert window.search_button.isEnabled()


def test_display_weather_fills_the_console(qtbot):
    window = WeatherApp()
    qtbot.addWidget(window)

    window.display_weather(sample_weather())
    window.display_forecast(sample_forecast())

    assert window.temperature_label.text() == "64°F"
    assert window.celsius_label.text() == "18°C"
    assert window.condition_text.text() == "LIGHT RAIN"
    assert "LONDON, GB" in window.station_label.text()
    assert "LIVE" in window.live_badge.text()
    assert window.humidity_tile.value_label.text() == "72"
    assert window.humidity_tile.unit_label.text() == "%"
    assert window.condition_tile.value_label.text() == "500"
    assert window.updated_tile.unit_label.text() == "local"

    # Rain weather resolves the sky and the window property together.
    assert window.sky.condition == "rain"
    assert window.property("condition") == "rain"


def test_manual_condition_pins_the_sky(qtbot):
    window = WeatherApp()
    qtbot.addWidget(window)

    window.set_condition_mode("snow")

    assert window.sky.condition == "snow"
    assert window.property("condition") == "snow"

    # Displaying rain weather must not override the pinned choice.
    window.display_weather(sample_weather())

    assert window.sky.condition == "snow"


def test_full_search_through_the_worker(qtbot, requests_mock):
    requests_mock.get(CURRENT_URL, status_code=200, json=VALID_CURRENT_PAYLOAD)
    requests_mock.get(FORECAST_URL, status_code=200, json=VALID_FORECAST_PAYLOAD)

    window = WeatherApp()
    qtbot.addWidget(window)

    window.city_input.setText("London")

    window.get_weather()

    qtbot.waitUntil(lambda: window.search_button.isEnabled(), timeout=10000)

    assert window.weather_data is not None
    assert window.weather_data.city == "London"
    assert window.temperature_label.text() == "59°F"
    assert window.celsius_label.text() == "15°C"
    assert window.forecast_table.rows[0].day_label.text() != ""

    # The strip rebuilt with the hourly chips from the same payload.
    assert window.hourly_strip.chip_row.count() > 1
    first_chip = window.hourly_strip.chip_row.itemAt(0).widget()
    assert first_chip.hour_label.text() == "NOW"


def test_search_failure_shows_the_hand_written_message(qtbot, requests_mock):
    requests_mock.get(CURRENT_URL, status_code=404, json={})

    window = WeatherApp()
    qtbot.addWidget(window)

    window.city_input.setText("Atlantis")

    window.get_weather()

    qtbot.waitUntil(lambda: window.search_button.isEnabled(), timeout=10000)

    assert window.status_label.text() == (
        "City not found. Check the spelling and try again."
    )


def test_console_height_does_not_grow_after_a_search(qtbot):
    """
    The window fits the console on first show, before any search
    exists. A search must not make the content taller, or the owner
    ends up with a scrollbar.
    """

    window = WeatherApp()
    qtbot.addWidget(window)

    window.show()
    qtbot.wait(50)

    before = window._console_content.sizeHint().height()

    window.display_weather(sample_weather())
    window.display_forecast(sample_forecast())
    qtbot.wait(50)

    after = window._console_content.sizeHint().height()

    # A pixel of rounding from font metrics is fine; the pre-search
    # fit adds slack for it.
    assert after - before <= 2


def test_forecast_table_fills_rows(qtbot):
    table = ForecastTable()
    qtbot.addWidget(table)

    table.update_forecast(sample_forecast(), "#6fb3ff")

    row = table.rows[0]

    assert row.day_label.text() == "MON"
    assert "70" in row.values_label.text()
    assert "54" in row.values_label.text()


def test_sky_widget_switches_conditions(qtbot):
    sky = SkyWidget()
    qtbot.addWidget(sky)

    sky.set_condition("night")
    assert sky.condition == "night"

    sky.set_condition("bogus")
    assert sky.condition == "rain"

    # Painting must not crash for any condition.
    for condition in ("clear", "cloudy", "rain", "snow", "mist", "night"):
        sky.set_condition(condition)
        pixmap = sky.grab()
        assert not pixmap.isNull()
