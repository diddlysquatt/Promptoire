"""Clipboard copy + optional auto-paste, with graceful fallbacks."""

from __future__ import annotations

import sys
import time

try:
    import pyperclip  # type: ignore
    _HAVE_PYPERCLIP = True
except Exception:
    _HAVE_PYPERCLIP = False


def copy(text: str) -> bool:
    if _HAVE_PYPERCLIP:
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            pass
    # Windows fallback via clip.exe.
    if sys.platform.startswith("win"):
        try:
            import subprocess
            p = subprocess.Popen(["clip.exe"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode("utf-16-le"))
            return p.returncode == 0
        except Exception:
            pass
    return False


def paste() -> str | None:
    if _HAVE_PYPERCLIP:
        try:
            return pyperclip.paste()
        except Exception:
            pass
    if sys.platform.startswith("win"):
        try:
            import subprocess
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0:
                return res.stdout
        except Exception:
            pass
    return None


def paste_into_active_window() -> bool:
    """Best-effort: send Ctrl+V to the previously focused window.

    Only used when the user enables 'paste after copy'. Requires the `keyboard`
    library; silently no-ops otherwise.
    """
    try:
        import keyboard  # type: ignore
        time.sleep(0.06)
        keyboard.send("ctrl+v")
        return True
    except Exception:
        return False
