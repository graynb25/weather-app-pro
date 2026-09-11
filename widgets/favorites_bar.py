"""
favorites_bar.py
================

The saved-cities row under the search bar: one chip per favorite, a
plus chip to save the current city, and a right-click menu on each
chip to remove it.

The bar is display only; ui.py owns the Favorites store and reacts to
the signals.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QMenu, QPushButton

ADD_CHIP_TEXT = "+"


class CityChip(QPushButton):
    """
    A saved city. Left click searches it, right click offers removal.
    """

    remove_requested = pyqtSignal(str)

    def __init__(self, city: str):
        super().__init__(city)

        self.city = city

        self.setObjectName("cityChip")
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"Search {city} (right click to remove)")

        font = self.font()
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        self.setFont(font)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        remove_action = menu.addAction(f"Remove {self.city}")

        if menu.exec(event.globalPos()) == remove_action:
            self.remove_requested.emit(self.city)


class FavoritesBar(QFrame):
    """
    One row: a chip per saved city, then the plus chip.
    """

    city_clicked = pyqtSignal(str)
    add_requested = pyqtSignal()
    remove_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setObjectName("favoritesBar")

        self.row = QHBoxLayout()
        self.row.setContentsMargins(2, 0, 2, 0)
        self.row.setSpacing(8)

        self.add_chip = QPushButton(ADD_CHIP_TEXT)
        self.add_chip.setObjectName("addChip")
        self.add_chip.setFixedSize(34, 30)
        self.add_chip.setCursor(Qt.PointingHandCursor)
        self.add_chip.setToolTip("Add the current city to favorites")

        self.add_chip.clicked.connect(self.add_requested)

        self.set_cities([])
        self.row.addWidget(self.add_chip)
        self.row.addStretch()

        self.setLayout(self.row)

    def set_cities(self, cities: list[str]) -> None:
        """
        Rebuild the row: city chips, then the plus chip, then the
        stretch.

        The plus chip is reused across rebuilds, so it is taken out of
        the layout but never scheduled for deletion.
        """

        while self.row.count():
            item = self.row.takeAt(0)
            widget = item.widget()

            if widget is not None and widget is not self.add_chip:
                widget.deleteLater()

        for city in cities:
            chip = CityChip(city)

            chip.clicked.connect(
                lambda checked=False, name=city: self.city_clicked.emit(name)
            )
            chip.remove_requested.connect(self.remove_requested)

            self.row.addWidget(chip)

        self.row.addWidget(self.add_chip)
        self.row.addStretch()

    def set_add_enabled(self, enabled: bool) -> None:
        """
        The plus chip only makes sense once a city is on screen.
        """

        self.add_chip.setEnabled(enabled)
