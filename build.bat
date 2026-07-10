@echo off
rem Build a standalone Promptoire.exe (one-dir) with PyInstaller
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" ( echo Run setup.bat first. & pause & exit /b 1 )
".venv\Scripts\python.exe" -m pip install pyinstaller >nul 2>nul
".venv\Scripts\python.exe" -m PyInstaller --noconfirm Promptoire.spec || (echo Build failed. & pause & exit /b 1)

echo.
echo Built: dist\Promptoire\Promptoire.exe
pause
