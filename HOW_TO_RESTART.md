# 🔄 How to Restart Promptoire Fresh

## Quick Method (RECOMMENDED)

**Just double-click:** `RESTART_FRESH.bat`

This will:
1. ✅ Kill all running instances
2. ✅ Clear Python cache
3. ✅ Remove lock files
4. ✅ Start the app fresh

---

## Manual Method

If you prefer to do it manually:

### Step 1: Kill All Running Instances

**Option A - Task Manager:**
1. Press `Ctrl + Shift + Esc`
2. Look for these processes:
   - `python.exe`
   - `pythonw.exe`
   - `Promptoire.exe`
3. Right-click each one → "End Task"

**Option B - Quick Batch File:**
- Double-click: `KILL_APP.bat`

**Option C - Command Line:**
```cmd
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe
taskkill /F /IM Promptoire.exe
```

### Step 2: Clear Cache (Optional but Recommended)

Delete these if they exist:
- `__pycache__` folder
- Any `*.pyc` files
- `Promptoire.lock` file

### Step 3: Start Fresh

**Running from Source:**
```cmd
pythonw.exe promptoire.py
```

**Running from EXE:**
```cmd
dist\Promptoire.exe
```

---

## Troubleshooting

### ❌ Problem: Window has Windows title bar

**Solution:** 
- Make sure you're using the LATEST version of `promptoire.py`
- The fix is already applied - the window should be borderless
- Try `RESTART_FRESH.bat` to ensure you're not running an old cached version

### ❌ Problem: Window appears as just a colored square

**Solution:** 
- This was a timing issue that's now fixed
- The window is now hidden during initialization and only shows when ready
- Use `RESTART_FRESH.bat` to start with the new code

### ❌ Problem: Can't find the window after starting

**Check these places:**
1. **System Tray** - Look for the ⭐ star icon (or your custom icon)
2. **Hotkey** - Try `Alt+Z` to teleport the window to your cursor
3. **Off-screen** - The window might be positioned off-screen:
   - Right-click tray icon → "Reset Position"

### ❌ Problem: App won't start / No process running

**Check the logs:**
```
logs\promptoire.log
```

Look for error messages at the bottom of the file.

**Common fixes:**
1. Make sure Python is installed: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Check if port/mutex is locked by another instance

### ❌ Problem: Multiple instances running

The app should be single-instance, but if you have multiple:
1. Use `KILL_APP.bat` to kill ALL instances
2. Wait 2-3 seconds
3. Use `RESTART_FRESH.bat` to start ONE new instance

---

## Files You Created

- **RESTART_FRESH.bat** - Complete restart procedure
- **KILL_APP.bat** - Just kill running instances
- **start_promptoire.bat** - Normal startup (already existed)
- **Launch_Promptoire.bat** - Alternative startup (already existed)

---

## What Was Fixed

The recent update fixed:
1. ✅ **Windows title bar** - Now properly borderless from the start
2. ✅ **Colored square on startup** - Window is hidden until fully initialized
3. ✅ **Flickering** - Smooth, clean appearance when starting

The key changes:
- Window is now hidden (`withdraw()`) immediately on creation
- `overrideredirect(True)` is set BEFORE any window operations
- Window only appears (`deiconify()`) after everything is fully set up

---

## Need More Help?

Check the logs for detailed information:
```
logs\promptoire.log
```

The last few lines will show what happened during startup.
