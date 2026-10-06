"""
config.py - Config file loader
Reads config.json from %LOCALAPPDATA%/Mike/config.json
"""

import json
import logging
import os
import pathlib
import tempfile

logger = logging.getLogger("mike.config")

CONFIG_PATH = pathlib.Path.home() / "AppData" / "Local" / "Mike" / "config.json"

DEFAULTS = {
    "groq_api_key": "",
    "default_mode": "semi_formal",
    "hud_opacity": 0.95,
    "hud_x": None,
    "hud_y": None,
    "continuous_chunk_seconds": 5,
    "transcription_language": "en",
    "inject_method": "clipboard",
}


class Config:
    def __init__(self, path: pathlib.Path = None):
        self.path = path or CONFIG_PATH
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._data.update(loaded)
            except Exception as e:
                logger.warning(f"Config load error: {e} — using defaults")

    def get(self, key: str, default=None):
        return self._data.get(
            key, default if default is not None else DEFAULTS.get(key)
        )

    def reload(self):
        """Reload config from disk while preserving defaults for missing keys."""
        self._data = dict(DEFAULTS)
        self._load()

    def set(self, key: str, value):
        self._data[key] = value
        self._save()

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as f:
                temporary_path = pathlib.Path(f.name)
                json.dump(self._data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary_path, self.path)
        except Exception as e:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError as cleanup_error:
                    logger.warning(
                        "Could not remove temporary config file %s: %s",
                        temporary_path,
                        cleanup_error,
                    )
            logger.error(f"Config save error: {e}")

    def is_api_key_set(self) -> bool:
        key = self._data.get("groq_api_key", "")
        return bool(key) and key.startswith("gsk_")
