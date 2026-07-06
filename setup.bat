@echo off
rem One-time setup: create a venv and install Promptoire's dependencies
setlocal
cd /d "%~dp0"

echo Creating virtual environment (.venv)...
python -m venv .venv || (echo Could not create venv. Install Python 3.9+ first. & pause & exit /b 1)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt || (echo Install failed. & pause & exit /b 1)

echo Creating desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Create-PromptoireShortcut.ps1" || echo Could not create desktop shortcut automatically.

echo.
echo Done. Double-click Promptoire.bat to start.
echo A PROMPTOIRE desktop shortcut is ready when Windows allows it.
echo (Tip: use Settings to enable launch at startup.)
pause
