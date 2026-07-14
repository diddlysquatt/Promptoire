"""Best-effort native window polish on Windows 11 (DWM): rounded corners,
immersive dark mode, and an optional acrylic/mica backdrop. All calls are
wrapped so failure on older Windows or non-Windows is silent — the CSS UI
looks good regardless; this is progressive enhancement.
"""

from __future__ import annotations

import ctypes
import sys
import time
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

RESIZE_HIT_TESTS = {
    "left": 10,          # HTLEFT
    "right": 11,         # HTRIGHT
    "top": 12,           # HTTOP
    "top-left": 13,      # HTTOPLEFT
    "top-right": 14,     # HTTOPRIGHT
    "bottom": 15,        # HTBOTTOM
    "bottom-left": 16,   # HTBOTTOMLEFT
    "bottom-right": 17,  # HTBOTTOMRIGHT
}


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


def resize_hit_test(direction: str) -> int:
    """Return the Win32 hit-test code for a resize edge/corner."""
    return RESIZE_HIT_TESTS.get(str(direction or "").strip().lower(), 0)


def resize_bounds(bounds: tuple[int, int, int, int], direction: str, dx: int, dy: int,
                  min_width: int, min_height: int) -> tuple[int, int, int, int]:
    """Calculate a resized (left, top, right, bottom) rectangle."""
    left, top, right, bottom = bounds
    direction = str(direction or "").strip().lower()
    if "left" in direction:
        left = min(left + dx, right - min_width)
    if "right" in direction:
        right = max(right + dx, left + min_width)
    if "top" in direction:
        top = min(top + dy, bottom - min_height)
    if "bottom" in direction:
        bottom = max(bottom + dy, top + min_height)
    return left, top, right, bottom


def begin_resize(hwnd: int, direction: str, *, min_width: int = 360,
                 min_height: int = 420) -> bool:
    """Run an interactive resize loop for a frameless Windows window.

    WinForms removes the native sizing frame when pywebview is frameless, so
    forwarding WM_NCLBUTTONDOWN alone is not dependable. Tracking the physical
    mouse while its primary button is held keeps every edge/corner reliable and
    costs CPU only for the few moments the user is actively resizing.
    """
    direction = str(direction or "").strip().lower()
    if not _is_windows() or not hwnd or not resize_hit_test(direction):
        return False
    try:
        user32 = ctypes.windll.user32
        if not user32.IsWindow(wintypes.HWND(hwnd)):
            return False

        rect = wintypes.RECT()
        start = wintypes.POINT()
        if not user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
            return False
        if not user32.GetCursorPos(ctypes.byref(start)):
            return False

        # GetWindowRect is in physical pixels for this backend. Match the
        # pywebview logical minimum size at the window's current DPI.
        try:
            scale = max(1.0, float(user32.GetDpiForWindow(wintypes.HWND(hwnd))) / 96.0)
        except Exception:
            scale = 1.0
        min_w = max(1, round(min_width * scale))
        min_h = max(1, round(min_height * scale))

        user32.ReleaseCapture()
        VK_LBUTTON = 0x01
        SWP_NOZORDER = 0x0004
        SWP_NOACTIVATE = 0x0010
        while user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000:
            point = wintypes.POINT()
            if not user32.GetCursorPos(ctypes.byref(point)):
                break
            dx, dy = point.x - start.x, point.y - start.y
            left, top, right, bottom = resize_bounds(
                (rect.left, rect.top, rect.right, rect.bottom), direction, dx, dy, min_w, min_h
            )
            if (left, top, right, bottom) != (rect.left, rect.top, rect.right, rect.bottom):
                user32.SetWindowPos(
                    wintypes.HWND(hwnd), None, left, top, right - left, bottom - top,
                    SWP_NOZORDER | SWP_NOACTIVATE,
                )
            time.sleep(0.008)
        # A valid handle/direction means the resize gesture started even if the
        # user released without moving.
        return True
    except Exception:
        return False
