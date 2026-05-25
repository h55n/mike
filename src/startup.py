"""
startup.py — Windows Startup Registry
Adds Mike to HKCU Run on every launch so the entry stays current.
Handles two cases:
  - Running as PyInstaller .exe: register the exe directly
  - Running as Python script: register pythonw + main.py with cd /d guard
"""

import sys
import logging
import pathlib
from paths import app_root, src_root

logger = logging.getLogger("mike.startup")

REG_KEY  = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Mike"

_PROJECT_DIR = app_root()
_SRC_DIR = src_root()


def _build_command() -> str:
    """Build the correct startup command for current runtime."""
    exe = pathlib.Path(sys.executable)

    # PyInstaller frozen exe — register it directly
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --startup'

    # Running as Python script — use pythonw (no console) + cd guard
    pythonw = exe.parent / "pythonw.exe"
    if not pythonw.exists():
        pythonw = exe  # fallback to python.exe

    main_py = _SRC_DIR / "main.py"
    return f'"{pythonw}" "{main_py}" --startup'


def add_to_startup():
    """Register Mike in HKCU Run. Safe to call on every launch."""
    try:
        import winreg
        cmd = _build_command()
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        logger.info(f"Startup registered: {cmd}")
    except Exception as e:
        logger.warning(f"Could not register startup: {e}")


def remove_from_startup():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        logger.info("Removed from startup")
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"Could not remove startup: {e}")


def is_in_startup() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False
