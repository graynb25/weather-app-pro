"""
lottie_widget.py
================

Reusable widget for displaying Lottie animations.

Responsibilities
----------------
- Load Lottie animations.
- Play animations.
- Stop animations.
- Hide all WebEngine logic from the rest of the application.

Author: Gray Nelson
Project: Weather App Pro
"""

from pathlib import Path

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QWidget, QVBoxLayout

class LottieWidget(QWidget):
    """
    Reusable widget for displaying Lottie animations.
    """

    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    HTML_FILE = (
            PROJECT_ROOT
            / "resources"
            / "html"
            / "lottie_player.html"
    )

    def __init__(self):
        super().__init__()

        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("""
        QWebEngineView{
            background: transparent;
            border: none;
        }
        """)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.web_view.setAttribute(Qt.WA_TranslucentBackground)
        self.player_ready = False
        self.web_view.loadFinished.connect(
            self.on_player_loaded
        )

        self.create_layout()
        self.load_player()

    def create_layout(self):
        layout = QVBoxLayout()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            self.web_view,
            alignment=Qt.AlignCenter
        )

        self.setLayout(layout)

    def load_player(self):
        self.web_view.load(
            QUrl.fromLocalFile(
                str(self.HTML_FILE)
            )
        )

        print(self.HTML_FILE)
        print(self.HTML_FILE.exists())

    def on_player_loaded(self, success: bool) -> None:
        """
        Called when the HTML player finishes loading.
        """

        self.player_ready = success

    def set_animation(self, animation_path: str) -> None:
        """
        Load a Lottie animation into the player.
        """

        if not self.player_ready:
            return

        script = f'setAnimation("{animation_path}")'

        self.web_view.page().runJavaScript(script)

    def play(self) -> None:
        """
        Play the current animation.
        """

        if self.player_ready:
            self.web_view.page().runJavaScript(
                "play();"
            )

    def pause(self) -> None:
        """
        Pause the current animation.
        """

        if self.player_ready:
            self.web_view.page().runJavaScript(
                "pause();"
            )

    def stop(self) -> None:
        """
        Stop the current animation.
        """

        if self.player_ready:
            self.web_view.page().runJavaScript(
                "stop();"
            )

