@echo off
setlocal
cd /d "%~dp0"

REM ============================================================
REM start_promptoire.bat - Smart launcher for Promptoire
REM Prefers source (venv) so code changes take effect immediately
REM ============================================================

REM PRIORITY 1: Use local .venv pythonw if available (best for development)
if exist ".venv\Scripts\pythonw.exe" (
  start "Promptoire" ".venv\Scripts\pythonw.exe" promptoire.py
  exit /b 0
)

REM PRIORITY 2: Use system pythonw without console
where pythonw >nul 2>&1
if %errorlevel%==0 (
  start "Promptoire" /min pythonw promptoire.py
  exit /b 0
)

REM PRIORITY 3: Use system python (will show console briefly)
where python >nul 2>&1
if %errorlevel%==0 (
  start "Promptoire" /min python promptoire.py
  exit /b 0
)

REM PRIORITY 4: Fallback to packaged EXE (onefile) if no Python available
if exist "dist\Promptoire.exe" (
  start "Promptoire" "dist\Promptoire.exe"
  exit /b 0
)

REM PRIORITY 5: Support onedir build (dist\Promptoire\Promptoire.exe)
if exist "dist\Promptoire\Promptoire.exe" (
  start "Promptoire" "dist\Promptoire\Promptoire.exe"
  exit /b 0
)

REM No launcher found
echo ERROR: Could not find Python or Promptoire.exe
echo Please install Python or run: python -m venv .venv
pause
exit /b 1
