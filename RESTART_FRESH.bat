@echo off
setlocal
echo ========================================
echo  PROMPTOIRE - FRESH RESTART
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Killing all existing processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
taskkill /F /IM Promptoire.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul
echo     Done!

echo [2/4] Clearing Python cache...
if exist "__pycache__" (
    rmdir /s /q "__pycache__"
    echo     __pycache__ cleared!
) else (
    echo     No cache to clear
)
del /f /q *.pyc >nul 2>&1

echo [3/4] Removing lock files...
del /f /q Promptoire.lock >nul 2>&1
echo     Done!

echo [4/4] Starting Promptoire fresh...
echo.
echo ========================================

REM Use the same smart launcher logic as run.bat
REM PRIORITY 1: Use local .venv pythonw if available
if exist ".venv\Scripts\pythonw.exe" (
    echo     Using .venv Python...
    start "" ".venv\Scripts\pythonw.exe" promptoire.py
    goto :done
)

REM PRIORITY 2: Use system pythonw without console
where pythonw >nul 2>&1
if %errorlevel%==0 (
    echo     Using system pythonw...
    start "" pythonw.exe promptoire.py
    goto :done
)

REM PRIORITY 3: Use system python
where python >nul 2>&1
if %errorlevel%==0 (
    echo     Using system python...
    start "" python.exe promptoire.py
    goto :done
)

REM PRIORITY 4: Fallback to EXE
if exist "dist\Promptoire.exe" (
    echo     Using Promptoire.exe...
    start "" "dist\Promptoire.exe"
    goto :done
)

echo ERROR: Could not find Python or Promptoire.exe
pause
exit /b 1

:done
echo.
echo App started! Check your system tray.
echo.
echo If you don't see the window:
echo   - Look for the star icon in your system tray
echo   - Try the hotkey: Alt+Z (or your configured hotkey)
echo.
pause
