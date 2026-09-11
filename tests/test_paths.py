"""
test_paths.py
============

Tests for the frozen-aware path resolution in paths.py.
"""

import sys
from pathlib import Path

import paths


def test_dev_mode_puts_everything_in_the_project(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "is_frozen", lambda: False)

    assert paths.app_root() == Path(__file__).resolve().parent.parent
    assert paths.data_dir() == paths.app_root()
    assert paths.cache_file() == paths.data_dir() / "cache.json"
    assert paths.log_file() == paths.data_dir() / "logs" / "app.log"


def test_frozen_mode_uses_meipass_and_local_app_data(monkeypatch, tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths.sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))

    assert paths.app_root() == bundle
    assert paths.resources_root() == bundle / "resources"
    assert paths.version_file() == bundle / "VERSION"

    data_dir = paths.data_dir()

    assert data_dir == tmp_path / "LocalAppData" / paths.DATA_DIR_NAME

    paths.ensure_data_dir()

    assert data_dir.exists()

    assert paths.key_file() == data_dir / ".env"
    assert paths.settings_file() == data_dir / "settings.json"
    assert paths.favorites_file() == data_dir / "favorites.json"
    assert paths.cache_file() == data_dir / "cache.json"
    assert paths.log_file() == data_dir / "logs" / "app.log"


def test_frozen_without_meipass_falls_back_to_the_exe_folder(monkeypatch, tmp_path):
    exe_folder = tmp_path / "exe"
    exe_folder.mkdir()

    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.delattr(paths.sys, "_MEIPASS", raising=False)
    monkeypatch.setattr(paths.sys, "executable", str(exe_folder / "WeatherAppPro.exe"))

    assert paths.app_root() == exe_folder
