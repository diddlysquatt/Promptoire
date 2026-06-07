@echo off
echo Killing Promptoire...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
taskkill /F /IM Promptoire.exe /T >nul 2>&1
echo Done!
timeout /t 2 /nobreak >nul
