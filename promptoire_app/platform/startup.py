"""Launch-at-login via the Windows per-user Run key (best-effort, safe)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Promptoire"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _launch_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    # Running from source: defer to the launcher script (handles venv + cwd).
    from ..core.paths import app_root
    bat = app_root() / "Promptoire.bat"
    if bat.exists():
        comspec = os.environ.get("ComSpec") or str(Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "cmd.exe")
        return f'"{comspec}" /d /c ""{bat}""'
    return f'"{sys.executable}" -m promptoire_app'


def _cleanup_legacy_startup_file() -> None:
    """Remove the obsolete pre-rebuild startup script, if it is still present."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return
    legacy = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "Promptoire.bat"
    try:
        if not legacy.exists():
            return
        text = legacy.read_text(encoding="utf-8", errors="ignore").lower()
        if "promptoire.py" in text or "akashic prompts" in text:
            legacy.unlink()
    except OSError:
        pass


def is_enabled() -> bool:
    if not sys.platform.startswith("win"):
        return False
    _cleanup_legacy_startup_file()
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_QUERY_VALUE) as k:
            value, _ = winreg.QueryValueEx(k, APP_NAME)
            return str(value or "").strip().casefold() == _launch_command().strip().casefold()
    except FileNotFoundError:
        return False
    except Exception:
        return False


def set_enabled(enabled: bool) -> bool:
    if not sys.platform.startswith("win"):
        return False
    _cleanup_legacy_startup_file()
    try:
        import winreg
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0,
                                winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE) as k:
            if enabled:
                winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _launch_command())
            else:
                try:
                    winreg.DeleteValue(k, APP_NAME)
                except FileNotFoundError:
                    pass
        return is_enabled() is bool(enabled)
    except Exception:
        return False
