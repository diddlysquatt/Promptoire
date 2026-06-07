"""System tray icon via pystray (best-effort, runs on its own thread)."""

from __future__ import annotations

import threading
from typing import Callable

try:
    import pystray  # type: ignore
    from PIL import Image, ImageDraw  # type: ignore
    _HAVE = True
except Exception:
    _HAVE = False


def _default_icon():
    """A small rounded neon-purple square with a 'P' — used if no .ico asset."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, size - 4, size - 4], radius=16, fill=(124, 58, 237, 255))
    d.rounded_rectangle([4, 4, size - 4, size - 4], radius=16, outline=(196, 132, 252, 255), width=2)
    # crude P
    d.rectangle([24, 18, 30, 46], fill=(255, 255, 255, 255))
    d.ellipse([24, 18, 44, 34], outline=(255, 255, 255, 255), width=6)
    return img


class Tray:
    def __init__(self, app_name: str = "Promptoire"):
        self.app_name = app_name
        self._icon = None
        self._thread = None

    @property
    def available(self) -> bool:
        return _HAVE

    def start(self, *, on_show: Callable, on_settings: Callable, on_quit: Callable,
              icon_image=None) -> bool:
        if not _HAVE:
            return False
        try:
            image = icon_image or _default_icon()
            menu = pystray.Menu(
                pystray.MenuItem("Open Promptoire", lambda *_: on_show(), default=True),
                pystray.MenuItem("Settings", lambda *_: on_settings()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", lambda *_: self._quit(on_quit)),
            )
            self._icon = pystray.Icon(self.app_name, image, self.app_name, menu)
            self._thread = threading.Thread(target=self._icon.run, daemon=True)
            self._thread.start()
            return True
        except Exception:
            return False

    def _quit(self, on_quit):
        try:
            self.stop()
        finally:
            on_quit()

    def notify(self, message: str, title: str | None = None):
        if self._icon is not None:
            try:
                self._icon.notify(message, title or self.app_name)
            except Exception:
                pass

    def stop(self):
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
