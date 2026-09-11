"""
test_favorites.py
=================

Tests for Favorites in favorites.py: dedupe, cap, persistence, and
defensive IO.
"""

import json

from favorites import MAX_FAVORITES, Favorites


def test_missing_file_starts_empty(tmp_path):
    favorites = Favorites(tmp_path / "favorites.json")

    assert favorites.get() == []


def test_add_and_roundtrip(tmp_path):
    path = tmp_path / "favorites.json"
    favorites = Favorites(path)

    assert favorites.add("London") is True
    assert favorites.add("Los Angeles") is True

    reloaded = Favorites(path)

    assert reloaded.get() == ["London", "Los Angeles"]


def test_duplicates_are_ignored_case_insensitively(tmp_path):
    favorites = Favorites(tmp_path / "favorites.json")

    assert favorites.add("London") is True
    assert favorites.add("london ") is False
    assert favorites.add("LONDON") is False

    assert favorites.get() == ["London"]
    assert favorites.contains("LoNdOn") is True


def test_empty_names_are_rejected(tmp_path):
    favorites = Favorites(tmp_path / "favorites.json")

    assert favorites.add("   ") is False
    assert favorites.get() == []


def test_remove_is_case_insensitive(tmp_path):
    favorites = Favorites(tmp_path / "favorites.json")
    favorites.add("London")

    assert favorites.remove("london") is True
    assert favorites.get() == []
    assert favorites.remove("London") is False


def test_list_is_capped(tmp_path):
    favorites = Favorites(tmp_path / "favorites.json")

    for index in range(MAX_FAVORITES + 5):
        favorites.add(f"City {index}")

    assert len(favorites.get()) == MAX_FAVORITES
    assert favorites.add("One more") is False
    assert favorites.get()[-1] == f"City {MAX_FAVORITES - 1}"


def test_corrupt_file_starts_empty(tmp_path):
    path = tmp_path / "favorites.json"
    path.write_text("{ not json", encoding="utf-8")

    favorites = Favorites(path)

    assert favorites.get() == []


def test_non_string_entries_are_dropped(tmp_path):
    path = tmp_path / "favorites.json"
    path.write_text(json.dumps(["London", 42, None, "  ", "Kyiv"]),
        encoding="utf-8")

    favorites = Favorites(path)

    assert favorites.get() == ["London", "Kyiv"]


def test_list_is_capped_on_load(tmp_path):
    path = tmp_path / "favorites.json"
    path.write_text(json.dumps([f"City {i}" for i in range(20)]),
        encoding="utf-8")

    favorites = Favorites(path)

    assert len(favorites.get()) == MAX_FAVORITES
