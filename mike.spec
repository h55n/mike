# mike.spec — PyInstaller build spec
# Build via: build_and_install.ps1  (do NOT run pyinstaller directly)

import sys

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets',    'assets'),
        ('config.json', '.'),
    ],
    hiddenimports=[
        # Windows backend
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        # Qt
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        # Audio / AI
        'sounddevice',
        'scipy.io.wavfile',
        'groq',
        # Image / tray
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'pystray',
        'pystray._win32',
        # DB
        'sqlite3',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Strip heavy unused Qt modules to keep exe lean
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngine',
        'matplotlib',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Mike',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='assets/mike.ico',
    version_info=None,
)
