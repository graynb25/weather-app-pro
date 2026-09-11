"""
stat_tile.py
============

One measurement tile from the glass console design: a micro label over
a monospace value, on a glass panel.

The optional unit ("%", "mph", "local", ...) renders as a smaller
label beside the value.

Replaces the icon based DetailCard in the main window; DetailCard stays
in the codebase untouched for anything that still wants it.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

LETTER_SPACING = 1.1


class StatTile(QFrame):
    """
    A label and value pair on a glass tile, with an optional unit.
    """

    def __init__(self, title: str):
        super().__init__()

        self.setObjectName("statTile")

        self.title_label = QLabel(title.upper())
        self.value_label = QLabel()
        self.unit_label = QLabel()

        self.title_label.setObjectName("statTitle")
        self.value_label.setObjectName("statValue")
        self.unit_label.setObjectName("statUnit")

        self.title_label.setAlignment(Qt.AlignLeft)
        self.value_label.setAlignment(Qt.AlignLeft)
        self.unit_label.setAlignment(Qt.AlignLeft)
        self.unit_label.setVisible(False)

        title_font = self.title_label.font()
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, LETTER_SPACING)
        self.title_label.setFont(title_font)

        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(6)
        value_row.addWidget(self.value_label, 0, Qt.AlignBaseline)
        value_row.addWidget(self.unit_label, 0, Qt.AlignBaseline)
        value_row.addStretch()

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        layout.addWidget(self.title_label)
        layout.addLayout(value_row)
        layout.addStretch()

        self.setLayout(layout)

    def set_value(self, value: str, unit: str = "") -> None:
        """
        Set the tile's value, for example "72" with unit "%".
        """

        self.value_label.setText(value)

        self.unit_label.setText(unit)
        self.unit_label.setVisible(bool(unit))
