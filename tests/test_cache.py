"""
test_cache.py
=============

Tests for WeatherCache in cache.py.
"""

from datetime import datetime

from cache import WeatherCache
from weather_model import WeatherData, ForecastData


def sample_weather() -> WeatherData:
    return WeatherData(
        city="London", country="GB",

        temperature_f=59.0, temperature_c=15.0,
        feels_like_f=57.2, feels_like_c=14.0,
        temp_min_f=50.0, temp_min_c=10.0,
        temp_max_f=64.4, temp_max_c=18.0,

        description="Light Rain", weather_id=500,

        humidity=72, wind_speed=8.0, pressure=1015, visibility=10000,

        sunrise=1767763200, sunset=1767792000, timezone=3600,
    )


def sample_forecast() -> list[ForecastData]:
    return [
        ForecastData(
            day="Mon", date="2026-01-05",
            temperature_f=50.0, temperature_c=10.0,
            description="Scattered Clouds", weather_id=802,
        )
    ]


def test_roundtrip(tmp_path):
    cache = WeatherCache(tmp_path / "cache.json")

    before = datetime.now().replace(microsecond=0)

    cache.save(sample_weather(), sample_forecast())

    loaded = cache.load()

    assert loaded is not None

    weather, forecast, fetched_at = loaded

    assert weather.city == "London"
    assert weather.weather_id == 500
    assert weather.temperature_c == 15.0
    assert forecast[0].day == "Mon"
    assert forecast[0].description == "Scattered Clouds"
    assert datetime.fromtimestamp(fetched_at) >= before


def test_missing_file_returns_none(tmp_path):
    cache = WeatherCache(tmp_path / "cache.json")

    assert cache.load() is None


def test_corrupt_file_returns_none(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("{ not json", encoding="utf-8")

    assert WeatherCache(path).load() is None


def test_wrong_shape_returns_none(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text('{"weather": 42}', encoding="utf-8")

    assert WeatherCache(path).load() is None


def test_no_temp_file_left_behind(tmp_path):
    cache = WeatherCache(tmp_path / "cache.json")

    cache.save(sample_weather(), sample_forecast())

    leftovers = [p.name for p in tmp_path.iterdir()]

    assert leftovers == ["cache.json"]
