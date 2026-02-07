# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Desktop Lens
To build: pyinstaller desktop-lens.spec
"""

import os
import sys

block_cipher = None

# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['desktop-lens.py'],
    pathex=[script_dir],
    binaries=[],
    datas=[
        ('assets/icon.svg', 'assets'),
        ('assets/icon.ico', 'assets'),
    ],
    hiddenimports=[
        'gi',
        'gi.repository.Gtk',
        'gi.repository.Gdk',
        'gi.repository.Gst',
        'gi.repository.GLib',
        'gi.repository.GstVideo',
        'gi.repository.GdkPixbuf',
        'pynput',
        'pynput.keyboard',
        'cairo',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DesktopLens',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for windowed app (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DesktopLens',
)
