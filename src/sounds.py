"""
sounds.py — Minimal, calm audio feedback for PTT start/stop.

Uses winsound.Beep() — built-in Windows, no numpy/sounddevice dependency,
guaranteed to work even while a sounddevice InputStream is recording.
Plays in a background thread so it never blocks the hotkey or engine.
"""

import threading
import logging
import winsound

logger = logging.getLogger("mike.sounds")


def _beep(freq: int, duration_ms: int):
    """Fire-and-forget beep in a daemon thread."""
    def _run():
        try:
            winsound.Beep(freq, duration_ms)
        except Exception as e:
            logger.debug(f"Beep error: {e}")
    threading.Thread(target=_run, daemon=True).start()


def play_start():
    """Soft upward chime — mic is now listening."""
    def _run():
        try:
            winsound.Beep(660, 60)
            winsound.Beep(880, 60)
        except Exception as e:
            logger.debug(f"Start chime error: {e}")
    threading.Thread(target=_run, daemon=True).start()


def play_stop():
    """Soft downward chime — mic is closing."""
    def _run():
        try:
            winsound.Beep(660, 60)
            winsound.Beep(480, 70)
        except Exception as e:
            logger.debug(f"Stop chime error: {e}")
    threading.Thread(target=_run, daemon=True).start()
