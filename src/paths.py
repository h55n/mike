"""
paths.py - Runtime path helpers for dev and PyInstaller builds.
"""
import pathlib
import sys


def app_root() -> pathlib.Path:
    """Return the project root in dev, or PyInstaller extraction root when frozen."""
    if getattr(sys, "frozen", False):
        return pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(sys.executable).parent))
    return pathlib.Path(__file__).resolve().parent.parent


def src_root() -> pathlib.Path:
    """Return the source directory containing app modules."""
    return app_root() / "src"


def asset_path(*parts: str) -> pathlib.Path:
    """Return a path under the bundled assets directory."""
    return app_root() / "assets" / pathlib.Path(*parts)
