@echo off
rem Launch Promptoire (no console window)
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" -m promptoire_app %*
) else (
  where pythonw >nul 2>nul && (
    start "" pythonw -m promptoire_app %*
  ) || (
    echo Python not found. Run setup.bat first, or install Python 3.9+.
    pause
  )
)
