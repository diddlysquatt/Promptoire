"""Filesystem locations for Promptoire.

Portable by default: data lives next to the app (the repo root in dev, the
folder containing the .exe when frozen by PyInstaller). This keeps the user's
existing `prompts.json` in place and makes "copy the folder to back up" true.
An env override (PROMPTOIRE_DATA_DIR) is honored for tests / custom setups.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, "frozen", False):  # PyInstaller bundle
        return Path(sys.executable).resolve().parent
    # promptoire_app/core/paths.py -> repo root is two parents up.
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    override = os.environ.get("PROMPTOIRE_DATA_DIR")
    base = Path(override).expanduser() if override else app_root()
    base.mkdir(parents=True, exist_ok=True)
    return base


def prompts_file() -> Path:
    return data_dir() / "prompts.json"


def settings_file() -> Path:
    return data_dir() / "promptoire.config.json"


def backups_dir() -> Path:
    d = data_dir() / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def web_dir() -> Path:
    """Folder holding the HTML/CSS/JS frontend."""
    if getattr(sys, "frozen", False):
        # Bundled as data via PyInstaller (see Promptoire.spec).
        return Path(sys._MEIPASS) / "web"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[1] / "web"


def assets_dir() -> Path:
    return web_dir() / "assets"


def app_icon() -> Path:
    name = "promptoire.ico"
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "icons" / name  # type: ignore[attr-defined]
    return app_root() / "icons" / name
