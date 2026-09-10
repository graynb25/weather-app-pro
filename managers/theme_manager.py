"""
theme_manager.py
================

Loads Qt stylesheets (.qss) from the resources/styles folder.
"""

from pathlib import Path


class ThemeManager:
    """
    Loads application themes.
    """

    STYLE_FOLDER = (
        Path(__file__).resolve().parent.parent
        / "resources"
        / "styles"
    )

    DEFAULT_THEME = "light"

    @classmethod
    def theme_exists(cls, theme_name: str) -> bool:
        """
        Return True if the requested theme exists.
        """

        return (
                cls.STYLE_FOLDER / f"{theme_name}.qss"
        ).exists()

    @classmethod
    def available_themes(cls) -> list[str]:
        """
        Return all available themes.
        """

        return sorted(
            file.stem
            for file in cls.STYLE_FOLDER.glob("*.qss")
        )

    @classmethod
    def load_theme(cls, theme_name: str) -> str:
        """"
        Return the contents of a theme stylesheet.
        """

        if not cls.theme_exists(theme_name):
            theme_name = cls.DEFAULT_THEME

        path = cls.STYLE_FOLDER / f"{theme_name}.qss"

        return path.read_text(encoding="utf-8")