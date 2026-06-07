Promptoire — Windows Release Guide

Overview
- Desktop app: Python + Tkinter, packaged with PyInstaller into an EXE (one‑file or one‑dir)
- Optional Chrome Extension: load via `chrome://extensions` (unpacked)

Prerequisites (for building EXE)
- Windows 10/11
- Python 3.9–3.12 installed and on PATH
- PowerShell or Command Prompt

1) Clean checkout
```powershell
git clone <your-repo-url>
cd "Promptoire"
```

2) Create venv and install deps
```powershell
python -m venv .venv
. .venv\Scripts\activate
pip install -r requirements.txt
```

3) Local run (dev)
```powershell
python promptoire.py
```

4) Build EXE
Option A (spec file; recommended)
```powershell
pyinstaller Promptoire.spec
```

Option B (CLI one‑liner)
```powershell
pyinstaller --noconfirm --windowed --name Promptoire --icon icons/app.ico promptoire.py
```

Outputs
- One‑file: `dist/Promptoire.exe` — single file (may have slower first‑run on some AV setups)
- One‑dir: `dist/Promptoire/Promptoire.exe` — folder with support files (often faster start)
- On first run, default `prompts.json` and `settings.json` are copied next to the EXE if missing (handled by runtime hook)

5) Smoke test the EXE
```powershell
./dist/Promptoire.exe
```

6) Package for distribution
Include these files in a ZIP (choose one‑file or one‑dir layout):

One‑file ZIP contents:
- `dist/Promptoire.exe`
- `prompts.json` (your curated prompts)
- `settings.json` (portable defaults)
- `README.md`
- `LICENSE`
- `start_promptoire.bat` (launcher; prefers EXE, falls back to pythonw)

One‑dir ZIP contents:
- Entire folder `dist/Promptoire/` (contains `Promptoire.exe` and support files)
- `prompts.json`
- `settings.json`
- `README.md`
- `LICENSE`
- `start_promptoire.bat`

Suggested ZIP name: `Promptoire-Windows-x64.zip`

7) Install on another Windows 11 PC (no Python needed)
- Download and unzip the ZIP anywhere (e.g., `C:\Apps\Promptoire`)
- Run `start_promptoire.bat` (auto-detects one‑file/one‑dir) or run the EXE directly
- To run on startup: Win+R → `shell:startup` → place a shortcut to `start_promptoire.bat` or the EXE

Desktop shortcut behavior
- In‑app Settings → "Desktop Shortcut" creates a `.lnk` pointing to the current run context (source/venv).
- For packaged releases, create a shortcut to the shipped EXE or `start_promptoire.bat`.

Chrome Extension (optional)
1) Open Chrome → `chrome://extensions/`
2) Enable Developer mode
3) Click "Load unpacked" → select the `chrome-extension` folder
4) Pin the extension

Notes
- Icons: the build uses the first available `.ico` from `icons/` list in `Promptoire.spec`
- Logs: app writes to `logs/promptoire.log` when run from source; EXE may create app‑local logs
- Single instance: enforced by the main app
- Performance: the spec disables UPX to improve cold‑start on some systems; consider one‑dir for fastest startup

Troubleshooting
- Missing module: run `pip install -r requirements.txt` in the venv
- No window but process running: launching from source uses `pythonw`; use `start_promptoire.bat` to suppress console
- Antivirus false positive: code‑sign the EXE if distributing broadly


