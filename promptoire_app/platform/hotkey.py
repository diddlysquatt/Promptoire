"""Global hotkey registration via the `keyboard` library (best-effort).

Runs the callback on the keyboard listener thread; we marshal back onto the UI
thread in the caller. If `keyboard` is unavailable (or blocked, e.g. needs
elevation), registration fails gracefully and the app still works via the tray
and the window itself.
"""

from __future__ import annotations

from typing import Callable

try:
    import keyboard  # type: ignore
    _HAVE = True
except Exception:
    _HAVE = False


class GlobalHotkey:
    def __init__(self):
        self._handle = None
        self._combo: str | None = None
        self._callback: Callable[[], None] | None = None

    @property
    def available(self) -> bool:
        return _HAVE

    @property
    def combo(self) -> str | None:
        return self._combo

    def register(self, combo: str, callback: Callable[[], None]) -> bool:
        self.unregister()
        self._callback = callback
        if not _HAVE or not combo:
            self._combo = combo or None
            return False
        try:
            # suppress=False so the keystroke still reaches other apps if unused.
            self._handle = keyboard.add_hotkey(combo, self._fire, suppress=False)
            self._combo = combo
            return True
        except Exception:
            self._handle = None
            self._combo = combo
            return False

    def _fire(self):
        cb = self._callback
        if cb:
            try:
                cb()
            except Exception:
                pass

    def unregister(self) -> None:
        if self._handle is not None and _HAVE:
            try:
                keyboard.remove_hotkey(self._handle)
            except Exception:
                pass
        self._handle = None

    def normalize(self, combo: str) -> str:
        raw = (combo or "").strip().lower()
        if "+" in raw:
            parts = raw.replace(" ", "").split("+")
        else:
            parts = raw.split()
        aliases = {
            "control": "ctrl",
            "meta": "win",
            "windows": "win",
            "backquote": "`",
            "grave": "`",
            "~": "`",
        }
        return "+".join(aliases.get(part, part) for part in parts if part)
