"""Frozen-build entry point for Promptoire (used by PyInstaller).

For running from source, prefer:  python -m promptoire_app
"""

from promptoire_app.main import main

if __name__ == "__main__":
    main()
