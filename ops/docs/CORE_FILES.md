# Core Files Documentation

## Application Entry Points

### Main Application Files
- `promptoire.py` - Main application entry point
- `start_promptoire.bat` - Windows batch launcher
- `Launch_Promptoire.bat` - Alternative launcher

### Configuration Files
- `settings.json` - Application configuration
- `prompts.json` - Prompt database storage
- `chrome-extension/` - Browser extension components

### Build and Distribution
- `Promptoire.spec` - PyInstaller specification
- `requirements.txt` - Python dependencies
- `package-lock.json` - Node.js dependencies

## Source Code Structure

### Core Source Files (`src/`)
- `src/constants.py` - Application constants and configuration
- `src/validators.py` - Input validation functions
- `src/utils/helpers.py` - General utility functions

### Infrastructure Files (`ops/`)
- `ops/docs/` - Project documentation
  - `PROJECT_JOURNAL.md` - Development activity log
  - `CORE_FILES.md` - Core files documentation (this file)
  - `FEATURES.md` - Feature documentation
- `ops/agent_logs/` - Agent activity logs
  - `INDEX.md` - Agent logs index
  - `A1_*.md` - Agent A1 activity logs

## Documentation Files
- `README.md` - Project overview
- `README-COMPLETE.md` - Complete setup guide
- `RELEASE.md` - Release notes
- `LICENSE` - Project license
- `ENHANCED_FEATURES.md` - Feature enhancements documentation
- `FIXES_APPLIED.md` - Bug fixes documentation
- `TOOLBAR_FIXES_SUMMARY.md` - UI fixes summary

## Development and Testing
- `test_enhanced_app.py` - Application testing
- `__diag.py` - Diagnostic utilities
- `__diag2.py` - Additional diagnostics
- `__tmp_debug.py` - Temporary debugging utilities

## Build Artifacts
- `build/` - Build output directory
- `dist/` - Distribution packages
- `__pycache__/` - Python bytecode cache

## Data and Storage
- `logs/` - Application logs directory
- `backups/` - Backup storage
- `Prompts/` - Prompt data storage
- `pyinstaller-hooks/` - Custom PyInstaller hooks

## UI and Assets
- `icons/` - Application icons and images
- `PromptCodex.txt` - Prompt reference text

## Maintenance Scripts
- `KILL_APP.bat` - Application termination script
- `RESTART_FRESH.bat` - Fresh restart script
- `HOW_TO_RESTART.md` - Restart instructions
- `ALKASHICPROMPTS` - Legacy configuration file

---

**Note:** This documentation reflects the current project structure and may be updated as development progresses.