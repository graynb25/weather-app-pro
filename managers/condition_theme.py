"""
condition_theme.py
==================

Maps OpenWeatherMap conditions to the visual identity used by the
glass console design.

Responsibilities:
    - Translate a weather id plus day or night into a condition key
    - Provide the palette for each condition: three gradient stops
      and one accent color

The accent reaches QSS through a dynamic property on the main window
and reaches painted widgets (the sky, the range bars) as plain values,
so this table is the single source for both.

Design source: instance/preview/05-glass-console.html (local preview).
"""

# Palette values are read by SkyWidget (gradient painting), by the
# range bars, and by the QSS attribute selectors in console.qss.
# Keep every entry complete: all four keys, valid hex colors.
PALETTES = {
    "clear": {
        "top": "#2f80d9", "mid": "#63a9ef", "bottom": "#ffd98a",
        "accent": "#ffb454",
    },
    "cloudy": {
        "top": "#46586f", "mid": "#6d80a0", "bottom": "#a8b8cd",
        "accent": "#9db8d9",
    },
    "rain": {
        "top": "#37455c", "mid": "#55708e", "bottom": "#8aa5bd",
        "accent": "#6fb3ff",
    },
    "snow": {
        "top": "#55688a", "mid": "#8ca2c2", "bottom": "#dfe8f2",
        "accent": "#9fd8ff",
    },
    "mist": {
        "top": "#4b5563", "mid": "#6b7684", "bottom": "#9aa5b1",
        "accent": "#b8c4cc",
    },
    "night": {
        "top": "#070b1e", "mid": "#141c3f", "bottom": "#2c3a6e",
        "accent": "#b48cff",
    },
}

DEFAULT_CONDITION = "rain"


class ConditionTheme:
    """
    Condition keys and palettes for the glass console design.
    """

    DEFAULT_CONDITION = "rain"

    @classmethod
    def from_weather(cls, weather_id: int, is_day: bool) -> str:
        """
        Translate an OpenWeatherMap condition id into a condition key.

        OpenWeatherMap id ranges: 2xx thunderstorm, 3xx drizzle,
        5xx rain, 6xx snow, 7xx atmosphere (fog, haze, ash), 800 clear,
        801 to 804 clouds.

        Args:
            weather_id: The condition id from the API response.
            is_day: False between sunset and sunrise at the city.

        Returns:
            One of the keys in PALETTES. Clear skies fall back to the
            night palette after dark; unknown ids fall back to rain.
        """

        if 200 <= weather_id < 300:
            return "rain"

        if 300 <= weather_id < 400:
            return "rain"

        if 500 <= weather_id < 600:
            return "rain"

        if 600 <= weather_id < 700:
            return "snow"

        if 700 <= weather_id < 800:
            return "mist"

        if weather_id == 800:
            return "clear" if is_day else "night"

        if 801 <= weather_id <= 802:
            return "cloudy" if is_day else "night"

        if 803 <= weather_id <= 804:
            return "cloudy"

        return DEFAULT_CONDITION

    @classmethod
    def palette(cls, condition: str) -> dict:
        """
        Return the palette for a condition key.

        Unknown keys fall back to the default condition so a typo can
        never crash the paint path.
        """

        return PALETTES.get(condition, PALETTES[DEFAULT_CONDITION])

    @classmethod
    def accent(cls, condition: str) -> str:
        """
        Return the accent color for a condition key.
        """

        return cls.palette(condition)["accent"]

    @classmethod
    def is_known(cls, condition: str) -> bool:
        """
        Return True when the key exists in the palette table.
        """

        return condition in PALETTES
