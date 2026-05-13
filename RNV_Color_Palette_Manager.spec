# -*- mode: python ; coding: utf-8 -*-
"""
============================================================
RNV Color Palette Manager - PyInstaller Build Specification
============================================================

Builds a standalone executable that bundles the Python runtime,
PyQt6, Pillow, and all application resources into a single file.

Usage:
    pip install pyinstaller
    pyinstaller RNV_Color_Palette_Manager.spec

Output:
    dist/RNV_Color_Palette_Manager.exe   (Windows)
    dist/RNV_Color_Palette_Manager       (macOS / Linux)

Notes:
    - One-file mode is enabled for easy distribution. Extraction to
      a temp directory adds a few seconds to first-launch time; swap
      to one-folder mode (see comments below) for faster startup.
    - Build artifacts (build/ and dist/) are git-ignored.
    - App icon: resources/icons/icon.png is bundled for runtime use.
      For the taskbar/shortcut icon, convert icon.png to .ico (Windows)
      or .icns (macOS) and point the `icon=` parameter at that file.
"""
from pathlib import Path

# ============================================================
#  Paths & configuration
# ============================================================
APP_NAME    = "RNV_Color_Palette_Manager"
ENTRY_POINT = "RNV_Color_Palette_Manager.py"
ICON_PATH   = "resources/icons/icon.png"

# Resource directories bundled into the executable.
# Tuples are (source_path, dest_path_inside_bundle).
DATA_FILES = [
    ("resources/button_images",     "resources/button_images"),
    ("resources/background_images", "resources/background_images"),
    ("resources/fonts",             "resources/fonts"),
    ("resources/icons",             "resources/icons"),
]


# ============================================================
#  Analysis - discover all imports and dependencies
# ============================================================
a = Analysis(
    [ENTRY_POINT],
    pathex=[],
    binaries=[],
    datas=DATA_FILES,
    hiddenimports=[
        # PyInstaller usually detects these automatically, but listing
        # them explicitly guards against hook-detection edge cases.
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.sip",
        "PIL.Image",
        "PIL.ImageQt",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Strip large unused modules to shrink the binary.
        "tkinter",
        "unittest",
        "test",
        "pydoc",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)


# ============================================================
#  EXE - one-file build (recommended for distribution)
# ============================================================
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                  # Compress binary (requires UPX installed)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,             # No terminal window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
)


# ============================================================
#  Alternative: one-folder build (faster startup, larger footprint)
# ============================================================
# To switch from one-file to one-folder mode:
#   1. Remove a.binaries and a.datas from the EXE() call above.
#   2. Add exclude_binaries=True inside EXE().
#   3. Uncomment the COLLECT block below.
#
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name=APP_NAME,
# )
