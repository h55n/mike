"""
db.py — SQLite Access Layer
WAL mode for reliability. Thread-safe via connection-per-thread pattern.
"""

import datetime
import logging
import pathlib
import sqlite3
import threading

logger = logging.getLogger("mike.db")

DB_PATH = pathlib.Path.home() / "AppData" / "Local" / "Mike" / "mike.db"


CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    duration_seconds REAL    NOT NULL,
    word_count       INTEGER NOT NULL,
    char_count       INTEGER NOT NULL,
    mode             TEXT    NOT NULL CHECK(mode IN ('raw','semi_formal','polished')),
    session_type     TEXT    NOT NULL CHECK(session_type IN ('dictation','prompt')),
    raw_transcript   TEXT    NOT NULL,
    final_text       TEXT    NOT NULL,
    app_name         TEXT
);
"""

CREATE_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: pathlib.Path = None):
        self.path = path or DB_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(str(self.path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn = conn
        return self._local.conn

    def _init_db(self):
        c = self._conn()
        c.execute(CREATE_SESSIONS)
        c.execute(CREATE_SETTINGS)
        c.commit()

    def save_session(
        self,
        duration_seconds,
        word_count,
        char_count,
        mode,
        session_type,
        raw_transcript,
        final_text,
        app_name=None,
    ):
        try:
            self._conn().execute(
                """INSERT INTO sessions
                   (duration_seconds, word_count, char_count, mode,
                    session_type, raw_transcript, final_text, app_name)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    duration_seconds,
                    word_count,
                    char_count,
                    mode,
                    session_type,
                    raw_transcript,
                    final_text,
                    app_name,
                ),
            )
            self._conn().commit()
        except Exception as e:
            logger.error(f"save_session error: {e}")

    def get_sessions(self, limit: int = 200) -> list[dict]:
        try:
            rows = (
                self._conn()
                .execute(
                    "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
                )
                .fetchall()
            )
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"get_sessions error: {e}")
            return []

    def get_setting(self, key: str, default=None):
        try:
            row = (
                self._conn()
                .execute("SELECT value FROM settings WHERE key=?", (key,))
                .fetchone()
            )
            return row[0] if row else default
        except Exception:
            return default

    def save_setting(self, key: str, value: str):
        try:
            self._conn().execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)",
                (key, str(value)),
            )
            self._conn().commit()
        except Exception as e:
            logger.error(f"save_setting error: {e}")
