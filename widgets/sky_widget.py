"""
sky_widget.py
=============

The animated condition background for the glass console design.

Responsibilities:
    - Paint a full-window vertical gradient for the active condition
    - Paint the ambient scene: sun, moon, stars, clouds, rain, snow,
      or mist, driven by a timer
    - Hold the app's main layout as its content

The widget is a plain painted surface. It never touches the network,
the API key, or anything below the UI layer; ui.py tells it which
condition to show. Particle counts stay low so the timer keeps a
steady frame pace even on modest hardware.

Design source: instance/preview/05-glass-console.html (local preview).
"""

import math
import random

from PyQt5.QtCore import QPoint, QPointF, QRectF, QTimer, Qt
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QPen, QRadialGradient
from PyQt5.QtWidgets import QWidget

from managers.condition_theme import ConditionTheme

FRAME_MS = 33  # roughly 30 frames per second

RAIN_DROPS = 60
SNOW_FLAKES = 40
STAR_COUNT = 70
CLOUD_BLOBS = 26


class SkyWidget(QWidget):
    """
    Painted condition background that hosts the main window layout.
    """

    def __init__(self):
        super().__init__()

        self.condition = ConditionTheme.DEFAULT_CONDITION

        # Scene state, seeded per condition
        self._drops = []
        self._flakes = []
        self._stars = []
        self._clouds = []
        self._phase = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self.set_condition(self.condition)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def set_condition(self, condition: str) -> None:
        """
        Switch the scene to a condition key from ConditionTheme.

        Unknown keys fall back to the default palette, so this never
        raises.
        """

        self.condition = condition if ConditionTheme.is_known(condition) \
            else ConditionTheme.DEFAULT_CONDITION

        self._seed_scene()

        if not self._timer.isActive():
            self._timer.start(FRAME_MS)

        self.update()

    def palette(self) -> dict:
        """
        The active condition's palette.
        """

        return ConditionTheme.palette(self.condition)

    def set_paused(self, paused: bool) -> None:
        """
        Stop the scene timer while the window is minimized so a hidden
        animation does not burn CPU.
        """

        if paused:
            self._timer.stop()
        elif not self._timer.isActive() and self.isVisible():
            self._timer.start(FRAME_MS)

    # ---------------------------------------------------------
    # Scene state
    # ---------------------------------------------------------

    def _seed_scene(self) -> None:
        """
        Rebuild the particle state for the active condition.
        """

        self._drops = []
        self._flakes = []
        self._stars = []
        self._clouds = []

        width = max(self.width(), 1)
        height = max(self.height(), 1)

        if self.condition == "rain":
            self._drops = [
                {
                    "x": random.uniform(0, width),
                    "y": random.uniform(-height, 0),
                    "speed": random.uniform(14, 26),
                    "length": random.uniform(14, 26),
                    "alpha": random.randint(60, 130),
                }
                for _ in range(RAIN_DROPS)
            ]

        if self.condition == "snow":
            self._flakes = [
                {
                    "x": random.uniform(0, width),
                    "y": random.uniform(-height, 0),
                    "speed": random.uniform(1.2, 2.8),
                    "radius": random.uniform(1.6, 3.6),
                    "sway": random.uniform(0.4, 1.4),
                    "phase": random.uniform(0, math.tau),
                }
                for _ in range(SNOW_FLAKES)
            ]

        if self.condition == "night":
            self._stars = [
                {
                    "x": random.uniform(0, width),
                    "y": random.uniform(0, height * 0.6),
                    "radius": random.uniform(0.7, 1.6),
                    "speed": random.uniform(0.4, 1.4),
                    "phase": random.uniform(0, math.tau),
                }
                for _ in range(STAR_COUNT)
            ]

        if self.condition in ("cloudy", "mist"):
            self._clouds = [
                {
                    "x": random.uniform(-0.1 * width, width),
                    "y": random.uniform(0.04, 0.85) * height,
                    "rx": random.uniform(90, 220),
                    "ry": random.uniform(22, 48),
                    "speed": random.uniform(0.25, 0.8),
                    "alpha": random.randint(18, 42),
                }
                for _ in range(CLOUD_BLOBS)
            ]

    # ---------------------------------------------------------
    # Animation
    # ---------------------------------------------------------

    def _tick(self) -> None:
        """
        Advance the scene one frame.
        """

        self._phase += 1.0

        width = max(self.width(), 1)
        height = max(self.height(), 1)

        for drop in self._drops:
            drop["y"] += drop["speed"]

            if drop["y"] > height:
                drop["y"] = random.uniform(-80, -20)
                drop["x"] = random.uniform(0, width)

        for flake in self._flakes:
            flake["y"] += flake["speed"]

            if flake["y"] > height:
                flake["y"] = random.uniform(-30, -10)
                flake["x"] = random.uniform(0, width)

        for cloud in self._clouds:
            cloud["x"] += cloud["speed"]

            if cloud["x"] - cloud["rx"] > width:
                cloud["x"] = -cloud["rx"]

        self.update()

    # ---------------------------------------------------------
    # Painting
    # ---------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self._paint_gradient(painter)

        if self.condition == "clear":
            self._paint_sun_or_moon(painter, sun=True)
        elif self.condition == "night":
            self._paint_stars(painter)
            self._paint_sun_or_moon(painter, sun=False)
        elif self.condition == "rain":
            self._paint_rain(painter)
        elif self.condition == "snow":
            self._paint_snow(painter)
        elif self.condition in ("cloudy", "mist"):
            self._paint_clouds(painter)

        painter.end()

    def _paint_gradient(self, painter: QPainter) -> None:
        palette = self.palette()

        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(palette["top"]))
        gradient.setColorAt(0.55, QColor(palette["mid"]))
        gradient.setColorAt(1.0, QColor(palette["bottom"]))

        painter.fillRect(self.rect(), gradient)

    def _paint_sun_or_moon(self, painter: QPainter, sun: bool) -> None:
        """
        Draw the drifting sun or moon in the upper right, with a soft
        radial glow like the preview.
        """

        drift = math.sin(self._phase / 55.0) * 10.0

        center = QPointF(
            self.width() * 0.84,
            self.height() * 0.16 + drift,
        )

        radius = 46 if sun else 38

        if sun:
            glow = QColor(255, 214, 110, 120)
            core_in = QColor("#fff7d6")
            core_out = QColor("#ffb340")
        else:
            glow = QColor(190, 200, 240, 90)
            core_in = QColor("#fdfbf2")
            core_out = QColor("#aab3d4")

        halo = QRadialGradient(center, radius * 3.2)
        halo.setColorAt(0.0, glow)
        halo.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(halo)
        painter.drawEllipse(center, radius * 3.2, radius * 3.2)

        body = QRadialGradient(center, radius)
        body.setColorAt(0.0, core_in)
        body.setColorAt(1.0, core_out)

        painter.setBrush(body)
        painter.drawEllipse(center, radius, radius)

    def _paint_rain(self, painter: QPainter) -> None:
        pen = QPen()
        pen.setWidthF(1.4)
        pen.setCapStyle(Qt.RoundCap)

        painter.setPen(pen)

        for drop in self._drops:
            pen.setColor(QColor(255, 255, 255, drop["alpha"]))
            painter.setPen(pen)

            painter.drawLine(
                QPointF(drop["x"], drop["y"]),
                QPointF(drop["x"] - 2.5, drop["y"] - drop["length"]),
            )

    def _paint_snow(self, painter: QPainter) -> None:
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 215))

        for flake in self._flakes:
            sway_x = math.sin(self._phase / 22.0 + flake["phase"]) * 14.0 * flake["sway"]

            painter.drawEllipse(
                QPointF(flake["x"] + sway_x, flake["y"]),
                flake["radius"],
                flake["radius"],
            )

    def _paint_stars(self, painter: QPainter) -> None:
        painter.setPen(Qt.NoPen)

        for star in self._stars:
            twinkle = 0.5 + 0.5 * math.sin(self._phase / 18.0 * star["speed"] + star["phase"])
            alpha = int(70 + 170 * twinkle)

            painter.setBrush(QColor(255, 255, 255, alpha))

            painter.drawEllipse(
                QPointF(star["x"], star["y"]),
                star["radius"],
                star["radius"],
            )

    def _paint_clouds(self, painter: QPainter) -> None:
        painter.setPen(Qt.NoPen)

        for cloud in self._clouds:
            painter.setBrush(QColor(235, 242, 250, cloud["alpha"]))

            painter.drawEllipse(QRectF(
                cloud["x"] - cloud["rx"],
                cloud["y"] - cloud["ry"],
                cloud["rx"] * 2,
                cloud["ry"] * 2,
            ))

    # ---------------------------------------------------------
    # Timer hygiene
    # ---------------------------------------------------------

    def hideEvent(self, event) -> None:
        self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event) -> None:
        if not self._timer.isActive():
            self._timer.start(FRAME_MS)

        super().showEvent(event)
