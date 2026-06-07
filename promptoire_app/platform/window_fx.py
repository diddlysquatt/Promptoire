"""Best-effort native window polish on Windows 11 (DWM): rounded corners,
immersive dark mode, and an optional acrylic/mica backdrop. All calls are
wrapped so failure on older Windows or non-Windows is silent — the CSS UI
looks good regardless; this is progressive enhancement.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

# DWM window attributes (dwmapi.h).
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMWA_BORDER_COLOR = 34

# Corner preferences.
DWMWCP_DEFAULT = 0
DWMWCP_DONOTROUND = 1
DWMWCP_ROUND = 2
DWMWCP_ROUNDSMALL = 3

# Backdrop types.
DWMSBT_NONE = 1
DWMSBT_MAINWINDOW = 2      # Mica
DWMSBT_TRANSIENTWINDOW = 3  # Acrylic
DWMSBT_TABBEDWINDOW = 4     # Tabbed Mica


def _is_windows() -> bool:
    return sys.platform.startswith("win")


def _set_attr(hwnd: int, attr: int, value: int) -> bool:
    if not _is_windows() or not hwnd:
        return False
    try:
        val = ctypes.c_int(value)
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd), ctypes.c_uint(attr), ctypes.byref(val), ctypes.sizeof(val)
        )
        return res == 0
    except Exception:
        return False


def apply_polish(hwnd: int, *, dark: bool = True, rounded: bool = True,
                 acrylic: bool = False) -> None:
    """Apply the full set of niceties to a window handle."""
    if not _is_windows() or not hwnd:
        return
    if dark:
        _set_attr(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 1)
    if rounded:
        _set_attr(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND)
    if acrylic:
        # Only meaningful on Win11 22H2+ and when the surface has transparency.
        _set_attr(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, DWMSBT_TRANSIENTWINDOW)


def find_hwnd_for_title(title: str) -> int:
    """Locate a top-level window by its exact title (used to grab pywebview's)."""
    if not _is_windows():
        return 0
    try:
        FindWindow = ctypes.windll.user32.FindWindowW
        FindWindow.restype = wintypes.HWND
        hwnd = FindWindow(None, title)
        return int(hwnd) if hwnd else 0
    except Exception:
        return 0
