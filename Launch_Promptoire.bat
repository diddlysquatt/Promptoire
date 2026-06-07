@echo off
REM ============================================================
REM Launch_Promptoire.bat - Simple launcher wrapper
REM Delegates to run.bat for smart Python/EXE detection
REM ============================================================
cd /d "%~dp0"
call run.bat
