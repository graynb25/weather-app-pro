"""
test_favorites_bar.py
=====================

Tests for FavoritesBar in widgets/favorites_bar.py.
"""

from widgets.favorites_bar import FavoritesBar


def sample_cities() -> list:
    return ["London", "Kyiv"]


def test_bar_builds_chips_plus_add(qtbot):
    bar = FavoritesBar()
    qtbot.addWidget(bar)

    bar.set_cities(sample_cities())

    # Two city chips, the add chip, and the trailing stretch.
    assert bar.row.count() == len(sample_cities()) + 2

    first = bar.row.itemAt(0).widget()

    assert first.text() == "London"


def test_clicking_a_chip_emits_the_city(qtbot):
    bar = FavoritesBar()
    qtbot.addWidget(bar)

    bar.set_cities(sample_cities())

    clicked = []
    bar.city_clicked.connect(clicked.append)

    chip = bar.row.itemAt(1).widget()
    chip.click()

    assert clicked == ["Kyiv"]


def test_add_chip_emits_add_requested(qtbot):
    bar = FavoritesBar()
    qtbot.addWidget(bar)

    requested = []
    bar.add_requested.connect(lambda: requested.append(True))

    bar.add_chip.click()

    assert requested == [True]


def test_rebuild_replaces_old_chips(qtbot):
    bar = FavoritesBar()
    qtbot.addWidget(bar)

    bar.set_cities(sample_cities())
    bar.set_cities(["Paris"])

    # One city chip, the add chip, and the trailing stretch.
    assert bar.row.count() == 3

    assert bar.row.itemAt(0).widget().text() == "Paris"
    assert bar.row.itemAt(1).widget() is bar.add_chip
