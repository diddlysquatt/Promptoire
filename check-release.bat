@echo off
rem Run the local GitHub-readiness checks before pushing Promptoire.
setlocal EnableExtensions
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

where node >nul 2>nul || (
  echo Node.js is required for frontend syntax checks.
  exit /b 1
)

call :run "%PY%" tests\test_smoke.py || exit /b 1
call :run "%PY%" -m compileall -q promptoire_app tests || exit /b 1
for %%F in (bridge.js state.js components.js launcher.js editor.js bulk.js settings.js app.js) do (
  call :run node --check promptoire_app\web\js\%%F || exit /b 1
)
if exist "_selftest.json" del /q "_selftest.json"
call :run "%PY%" -m promptoire_app --selftest || exit /b 1
call :run powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Check-PromptoireShortcut.ps1" || exit /b 1

if not exist "_selftest.json" (
  echo Self-test report was not written.
  exit /b 1
)
call :run "%PY%" -c "import json, sys; d=json.load(open('_selftest.json', encoding='utf-8')); sys.exit(0 if d.get('mock') is False and d.get('native_hwnd') is True and d.get('window_icon') is True and d.get('minimum_window') == [360, 420] and not d.get('error') else 1)" || exit /b 1

for %%F in (prompts.json promptoire.config.json _selftest.json) do (
  git ls-files --error-unmatch "%%F" >nul 2>nul && (
    echo Private runtime file is tracked: %%F
    exit /b 1
  )
)

echo.
echo Git status:
git status --short
echo.
echo Release preflight passed.
exit /b 0

:run
echo.
echo ^> %*
%*
exit /b %errorlevel%
