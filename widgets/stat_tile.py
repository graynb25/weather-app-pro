"""
stat_tile.py
============

One measurement tile from the glass console design: a micro label over
a monospace value, on a glass panel.

Replaces the icon based DetailCard in the main window; DetailCard stays
in the codebase untouched for anything that still wants it.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout

LETTER_SPACING = 1.1


class StatTile(QFrame):
    """
    A label and value pair on a glass tile.
    """

    def __init__(self, title: str):
        super().__init__()

        self.setObjectName("statTile")

        self.title_label = QLabel(title.upper())
        self.value_label = QLabel()

        self.title_label.setObjectName("statTitle")
        self.value_label.setObjectName("statValue")

        self.title_label.setAlignment(Qt.AlignLeft)
        self.value_label.setAlignment(Qt.AlignLeft)

        title_font = self.title_label.font()
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, LETTER_SPACING)
        self.title_label.setFont(title_font)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

        self.setLayout(layout)

    def set_value(self, value: str) -> None:
        """
        Set the tile's value text, for example "72%".
        """

        self.value_label.setText(value)
