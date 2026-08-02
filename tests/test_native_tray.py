"""Windows-only native probe for Promptoire's notification-area lifecycle.

This opens a real pywebview window and real pystray icon, then checks
minimize, native close, restore, and explicit quit behavior. It uses an
isolated temporary data folder and never reads or changes the user's library.
"""

from __future__ import annotations

import ctypes
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from promptoire_app.core import paths
from promptoire_app.core.settings import Settings
from promptoire_app.main import App
from promptoire_app.platform import window_fx


def _wait_for(predicate, timeout: float = 6.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return False


class NativeTrayProbe(App):
    def __init__(self):
        super().__init__(debug=False, selftest=False)
        self.report: dict = {"ok": False, "error": "probe did not complete"}

    def _on_started(self):
        super()._on_started()
        threading.Thread(target=self._probe, daemon=True).start()

    def _probe(self):
        try:
            hwnd = self._resolve_hwnd()
            if not hwnd:
                raise RuntimeError("native window handle was unavailable")

            user32 = ctypes.windll.user32
            tray_ready = _wait_for(
                lambda: self.tray._icon is not None
                and self.tray._thread is not None
                and self.tray._thread.is_alive()
                and bool(getattr(self.tray._icon, "visible", False))
            )
            initial = {
                "visible": bool(user32.IsWindowVisible(hwnd)),
                "icon": window_fx.has_window_icon(hwnd),
                "icon_applied": self._window_icon_applied,
                "tray_ready": tray_ready,
            }

            self.window.minimize()
            minimized_to_tray = _wait_for(
                lambda: not self._visible and not bool(user32.IsWindowVisible(hwnd))
            )

            self.show_window(at_cursor=False)
            restored_after_minimize = _wait_for(
                lambda: self._visible
                and bool(user32.IsWindowVisible(hwnd))
                and not bool(user32.IsIconic(hwnd))
            )
            state_after_minimize_restore = {
                "controller_visible": self._visible,
                "native_visible": bool(user32.IsWindowVisible(hwnd)),
                "native_minimized": bool(user32.IsIconic(hwnd)),
            }

            user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
            close_to_tray = _wait_for(
                lambda: not self._visible
                and not self._quitting
                and not bool(user32.IsWindowVisible(hwnd))
            )

            self.show_window(at_cursor=False)
            restored_after_close = _wait_for(
                lambda: self._visible
                and bool(user32.IsWindowVisible(hwnd))
                and not bool(user32.IsIconic(hwnd))
            )
            state_after_close_restore = {
                "controller_visible": self._visible,
                "native_visible": bool(user32.IsWindowVisible(hwnd)),
                "native_minimized": bool(user32.IsIconic(hwnd)),
            }

            self.report = {
                "ok": all((
                    initial["visible"],
                    initial["icon"],
                    initial["icon_applied"],
                    initial["tray_ready"],
                    minimized_to_tray,
                    restored_after_minimize,
                    close_to_tray,
                    restored_after_close,
                )),
                "initial": initial,
                "minimized_to_tray": minimized_to_tray,
                "restored_after_minimize": restored_after_minimize,
                "state_after_minimize_restore": state_after_minimize_restore,
                "close_to_tray": close_to_tray,
                "restored_after_close": restored_after_close,
                "state_after_close_restore": state_after_close_restore,
            }
        except Exception as exc:
            self.report = {"ok": False, "error": repr(exc)}
        finally:
            self.quit()


def main() -> int:
    if not sys.platform.startswith("win"):
        print(json.dumps({"ok": True, "skipped": "Windows only"}))
        return 0

    with tempfile.TemporaryDirectory(prefix="promptoire-native-tray-") as temp_dir:
        os.environ["PROMPTOIRE_DATA_DIR"] = temp_dir
        settings = Settings(paths.settings_file()).load()
        settings.update({
            "behavior": {
                "single_instance": False,
                "show_tray": True,
                "hide_on_blur": False,
                "open_at_cursor": False,
                "launch_at_startup": False,
            }
        })
        settings.save()

        window_fx.set_process_app_id()
        app = NativeTrayProbe()
        # Do not claim the user's global shortcut during an isolated probe.
        app.set_hotkey = lambda _combo: True
        app.run()
        print(json.dumps(app.report, indent=2), flush=True)
        return 0 if app.report.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
