# -*- mode: python ; coding: utf-8 -*-
# Build:  pyinstaller Promptoire.spec
# Output: dist/Promptoire/Promptoire.exe  (one-dir; starts fast, AV-friendly)

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
# pywebview's Windows backend (EdgeChromium via WinForms) + tray + hotkey.
hiddenimports += collect_submodules("webview")
hiddenimports += ["clr", "pystray._win32", "PIL._tkinter_finder"]

a = Analysis(
    ['promptoire_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('promptoire_app/web', 'web'),   # HTML/CSS/JS frontend -> _MEIPASS/web
        ('icons/replicate-prediction-2j5y20xssnrmc0crx40tp1mzjc.ico', 'icons'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'PySide6', 'PyQt5',
        # The tray icon is generated from simple Pillow drawing primitives;
        # Promptoire never decodes AVIF/WebP files. Leaving these plugins out
        # trims several megabytes from the portable build.
        'PIL.AvifImagePlugin', 'PIL.WebPImagePlugin',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Promptoire',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,            # UPX off: faster cold start, fewer AV false positives
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icons\\replicate-prediction-2j5y20xssnrmc0crx40tp1mzjc.ico'],
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Promptoire',
)
