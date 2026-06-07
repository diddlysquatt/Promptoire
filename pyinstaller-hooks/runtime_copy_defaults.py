"""
Runtime hook for PyInstaller one-file build.

On first run, if `prompts.json` or `settings.json` do not exist in the current
working directory, copy them out of the bundled resources into the CWD so the
app can read/write them normally thereafter.
"""

from __future__ import annotations

import sys
from pathlib import Path


def copy_resource_if_missing(filename: str) -> None:
    try:
        target_path = Path(filename)
        if target_path.exists():
            return
        base_dir = getattr(sys, "_MEIPASS", None)
        if not base_dir:
            return
        source_path = Path(base_dir) / filename
        if source_path.exists():
            try:
                target_path.write_bytes(source_path.read_bytes())
            except Exception:
                # Best-effort; ignore copy errors
                pass
    except Exception:
        # Never let the hook break app startup
        pass


for resource in ("prompts.json", "settings.json"):
    copy_resource_if_missing(resource)




