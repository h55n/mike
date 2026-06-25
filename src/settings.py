"""
settings.py — Settings wrapper over SQLite
"""

import logging

logger = logging.getLogger("mike.settings")


class Settings:
    def __init__(self, db):
        self.db = db

    def get(self, key: str, default=None):
        return self.db.get_setting(key, default)

    def set(self, key: str, value):
        self.db.save_setting(key, str(value))
