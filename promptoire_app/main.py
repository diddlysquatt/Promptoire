"""Promptoire app controller — window, tray, global hotkey, lifecycle.

Run:  python -m promptoire_app
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import webview  # pywebview

from . import __app_name__, __version__
from .api import Api
from .core import paths
from .core.library import PromptLibrary
from .core.settings import Settings
from .platform import window_fx
from .platform.hotkey import GlobalHotkey
from .platform.tray import Tray


class App:
    def __init__(self, *, debug: bool = False, selftest: bool = False):
        self.debug = debug
        self.selftest = selftest
        self.version = __version__
        self.settings = Settings(paths.settings_file()).load()
        self.library = PromptLibrary(paths.prompts_file()).load()

        self.window = None
        self.tray = Tray(__app_name__)
        self.hotkey = GlobalHotkey()
        self.api = Api(self)

        self._visible = True
        self._quitting = False
        self._save_timer: threading.Timer | None = None
        self._hwnd = 0

    # ---- platform helpers ---------------------------------------------------

    def platform_name(self) -> str:
        if sys.platform.startswith("win"):
            return "windows"
        if sys.platform == "darwin":
            return "macos"
        return "linux"

    # ---- run ----------------------------------------------------------------

    def run(self):
        if self.settings.get("behavior", "single_instance", default=True):
            if not _acquire_single_instance_lock():
                # Another instance owns it. Nothing to do here.
                print("Promptoire is already running.")
                return

        w = int(self.settings.get("window", "width", default=460))
        h = int(self.settings.get("window", "height", default=560))
        on_top = True

        index = paths.web_dir() / "index.html"
        self.window = webview.create_window(
            __app_name__,
            url=str(index),
            js_api=self.api,
            width=w,
            height=h,
            min_size=(360, 420),
            frameless=True,
            easy_drag=False,
            on_top=on_top,
            background_color="#0b0b13",
            text_select=True,
            zoomable=False,
        )
        self.window.events.closing += self._on_closing

        # Load via file:// (we use classic scripts, not ES modules, so no HTTP
        # server is needed). This is the most reliable pywebview path and keeps
        # the JS<->Python bridge working on the WinForms/EdgeChromium backend.
        webview.start(
            self._on_started,
            gui="edgechromium" if self.platform_name() == "windows" else None,
            debug=self.debug,
        )

    def _on_started(self):
        # Native polish once the OS window exists.
        try:
            self._hwnd = window_fx.find_hwnd_for_title(__app_name__)
            window_fx.apply_polish(self._hwnd, dark=True, rounded=True, acrylic=False)
        except Exception:
            pass

        # Restore last position if remembered.
        try:
            if self.settings.get("window", "remember_position", default=True):
                x = self.settings.get("window", "x")
                y = self.settings.get("window", "y")
                if isinstance(x, int) and isinstance(y, int):
                    self.window.move(x, y)
        except Exception:
            pass

        # Global hotkey.
        self.set_hotkey(self.settings.get("hotkey", default="ctrl+alt+space"))

        # Tray.
        if self.settings.get("behavior", "show_tray", default=True) and not self.selftest:
            self.tray.start(
                on_show=self.show_window,
                on_settings=self._tray_settings,
                on_quit=self.quit,
                icon_image=_load_tray_icon(),
            )

        if self.selftest:
            # Watchdog: the JS reports via api.selftest_report (real bridge
            # round-trip). If it never does, force-quit so we don't hang.
            threading.Thread(target=self._selftest_watchdog, daemon=True).start()

    def _selftest_watchdog(self):
        time.sleep(14)
        self.quit()

    # ---- window control -----------------------------------------------------

    def toggle_window(self):
        if self._visible:
            self.hide_window()
        else:
            self.show_window()

    def show_window(self, at_cursor: bool | None = None):
        if self.window is None:
            return
        try:
            if at_cursor is None:
                at_cursor = bool(self.settings.get("behavior", "open_at_cursor", default=True))
            if at_cursor:
                self._move_near_cursor()
            self.window.show()
            self._visible = True
            # Pull to front + focus the search box.
            try:
                self.window.evaluate_js("window.PROMPTOIRE && PROMPTOIRE.onShown && PROMPTOIRE.onShown()")
            except Exception:
                pass
            self._raise_to_front()
        except Exception:
            pass

    def hide_window(self):
        if self.window is None or self._quitting:
            return
        try:
            self._remember_position()
            self.window.hide()
            self._visible = False
        except Exception:
            pass

    def on_window_blur(self):
        # Primary hide-on-blur logic lives in JS (it knows the UI mode). This is
        # a backend no-op kept for API symmetry.
        pass

    def resize(self, width: int, height: int):
        if self.window is not None:
            self.window.resize(width, height)
            self.settings.update({"window": {"width": width, "height": height}})
            self.settings.save()

    def _move_near_cursor(self):
        try:
            cx, cy = _cursor_pos()
            sw, sh = _screen_size()
            w = int(self.settings.get("window", "width", default=460))
            h = int(self.settings.get("window", "height", default=560))
            x = min(max(cx - 40, 8), max(8, sw - w - 8))
            y = min(max(cy - 30, 8), max(8, sh - h - 8))
            self.window.move(int(x), int(y))
        except Exception:
            pass

    def _raise_to_front(self):
        """Reliably steal focus even from a background (hotkey) thread by
        briefly attaching to the current foreground thread's input queue —
        the standard workaround for Windows' SetForegroundWindow lock."""
        if not sys.platform.startswith("win") or not self._hwnd:
            return
        try:
            import ctypes
            u = ctypes.windll.user32
            k = ctypes.windll.kernel32
            HWND_TOPMOST = -1
            SWP = 0x0001 | 0x0002 | 0x0040  # NOSIZE | NOMOVE | SHOWWINDOW
            hwnd = self._hwnd

            fg = u.GetForegroundWindow()
            cur_tid = k.GetCurrentThreadId()
            fg_tid = u.GetWindowThreadProcessId(fg, None) if fg else 0

            u.AllowSetForegroundWindow(-1)  # ASFW_ANY
            attached = False
            if fg_tid and fg_tid != cur_tid:
                attached = bool(u.AttachThreadInput(fg_tid, cur_tid, True))
            u.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP)
            u.BringWindowToTop(hwnd)
            u.SetForegroundWindow(hwnd)
            u.SetActiveWindow(hwnd)
            if attached:
                u.AttachThreadInput(fg_tid, cur_tid, False)
        except Exception:
            pass

    def _remember_position(self):
        try:
            if not self.settings.get("window", "remember_position", default=True):
                return
            x, y = self.window.x, self.window.y
            if isinstance(x, int) and isinstance(y, int):
                self.settings.update({"window": {"x": x, "y": y}})
        except Exception:
            pass

    # ---- hotkey -------------------------------------------------------------

    def set_hotkey(self, combo: str) -> bool:
        combo = self.hotkey.normalize(combo)
        applied = self.hotkey.register(combo, self._hotkey_fired)
        self.settings.update({"hotkey": combo})
        self.settings.save()
        return applied

    def _hotkey_fired(self):
        # Runs on the keyboard listener thread; pywebview window ops are safe.
        self.toggle_window()

    # ---- settings application ----------------------------------------------

    def apply_settings(self, patch: dict):
        prev_hotkey = self.settings.get("hotkey")
        prev_tray = self.settings.get("behavior", "show_tray", default=True)
        self.settings.update(patch)
        self.settings.save()

        new_hotkey = self.settings.get("hotkey")
        if new_hotkey != prev_hotkey:
            self.set_hotkey(new_hotkey)

        new_tray = self.settings.get("behavior", "show_tray", default=True)
        if new_tray != prev_tray:
            if new_tray:
                self.tray.start(on_show=self.show_window, on_settings=self._tray_settings,
                                on_quit=self.quit, icon_image=_load_tray_icon())
            else:
                self.tray.stop()

        # Push theme/opacity changes to the live UI.
        try:
            self.window.evaluate_js(
                "window.PROMPTOIRE && PROMPTOIRE.onSettingsChanged && PROMPTOIRE.onSettingsChanged()"
            )
        except Exception:
            pass

    def _tray_settings(self):
        self.show_window(at_cursor=False)
        try:
            self.window.evaluate_js("window.PROMPTOIRE && PROMPTOIRE.openSettings && PROMPTOIRE.openSettings()")
        except Exception:
            pass

    def after_copy_paste(self):
        from .platform import clipboard
        threading.Thread(target=clipboard.paste_into_active_window, daemon=True).start()

    # ---- persistence (debounced) -------------------------------------------

    def save_library(self):
        self.library.save(backup=False)

    def save_library_soon(self, delay: float = 1.5):
        if self._save_timer is not None:
            self._save_timer.cancel()
        self._save_timer = threading.Timer(delay, self.save_library)
        self._save_timer.daemon = True
        self._save_timer.start()

    # ---- file dialogs -------------------------------------------------------

    def save_file_dialog(self, default_name: str) -> str | None:
        try:
            res = self.window.create_file_dialog(
                webview.SAVE_DIALOG, save_filename=default_name,
                file_types=("JSON Files (*.json)", "All files (*.*)"),
            )
            if isinstance(res, (list, tuple)):
                return res[0] if res else None
            return res
        except Exception:
            return None

    def open_file_dialog(self) -> str | None:
        try:
            res = self.window.create_file_dialog(
                webview.OPEN_DIALOG, allow_multiple=False,
                file_types=("JSON Files (*.json)", "All files (*.*)"),
            )
            if isinstance(res, (list, tuple)):
                return res[0] if res else None
            return res
        except Exception:
            return None

    # ---- lifecycle ----------------------------------------------------------

    def _on_closing(self):
        # Frameless close button calls window.destroy(); treat as quit.
        if not self._quitting:
            self.quit()
        return True

    def quit(self):
        if self._quitting:
            return
        self._quitting = True
        try:
            self._remember_position()
            self.settings.save()
            self.library.save(backup=True)
        except Exception:
            pass
        try:
            self.hotkey.unregister()
        except Exception:
            pass
        try:
            self.tray.stop()
        except Exception:
            pass
        try:
            if self.window is not None:
                self.window.destroy()
        except Exception:
            pass


# ---- module-level helpers ---------------------------------------------------

def _cursor_pos():
    import ctypes
    pt = ctypes.wintypes.POINT() if sys.platform.startswith("win") else None
    if pt is not None:
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
    return 200, 200


def _screen_size():
    if sys.platform.startswith("win"):
        import ctypes
        u = ctypes.windll.user32
        return u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    return 1920, 1080


def _load_tray_icon():
    try:
        from PIL import Image
        ico = paths.assets_dir() / "tray.png"
        if ico.exists():
            return Image.open(str(ico))
    except Exception:
        pass
    return None


_LOCK_HANDLE = None


def _acquire_single_instance_lock() -> bool:
    """Windows named mutex; cross-platform lockfile fallback."""
    global _LOCK_HANDLE
    if sys.platform.startswith("win"):
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            _LOCK_HANDLE = kernel32.CreateMutexW(None, False, "Promptoire_SingleInstance_Mutex")
            ERROR_ALREADY_EXISTS = 183
            if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
                return False
            return True
        except Exception:
            return True
    # POSIX: lockfile
    try:
        lock = paths.data_dir() / ".promptoire.lock"
        _LOCK_HANDLE = open(lock, "w")
        import fcntl  # type: ignore
        fcntl.flock(_LOCK_HANDLE, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except Exception:
        return False


def main():
    import ctypes  # noqa: F401  (ensures wintypes available on win)
    if sys.platform.startswith("win"):
        import ctypes.wintypes  # noqa: F401
    debug = "--debug" in sys.argv
    selftest = "--selftest" in sys.argv
    App(debug=debug, selftest=selftest).run()


if __name__ == "__main__":
    main()
