"""
injection.py — Text Injection at Cursor
Uses clipboard for speed. Falls back to character typing for incompatible apps.
Fix: adds small delay after clipboard write to prevent double-paste race condition.
"""

import time
import threading
import logging
import pyperclip
import pyautogui

logger = logging.getLogger("mike.injection")

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0

# Words threshold: below this → clipboard paste; above → still clipboard
# (keyboard.type is too slow for long text and causes double-char issues)
CLIPBOARD_THRESHOLD = 5   # Always use clipboard for 5+ words

# Lock prevents two injections running simultaneously
_inject_lock = threading.Lock()


class TextInjector:
    def __init__(self, config):
        self.config = config

    def insert(self, text: str):
        """Paste text at current cursor position."""
        if not text or not text.strip():
            return

        method = self.config.get("inject_method", "clipboard")

        with _inject_lock:
            if method == "type" and len(text.split()) < 10:
                self._type_text(text)
            else:
                self._clipboard_paste(text)

    def _clipboard_paste(self, text: str):
        """Save clipboard, paste text, restore clipboard."""
        try:
            # Save current clipboard
            try:
                original = pyperclip.paste()
            except Exception:
                original = ""

            # Write our text
            pyperclip.copy(text)
            time.sleep(0.05)   # Allow clipboard to settle

            # Paste
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.08)   # Wait for paste to complete

            # Restore original clipboard after a brief delay
            def restore():
                time.sleep(0.5)
                try:
                    pyperclip.copy(original)
                except Exception:
                    pass

            threading.Thread(target=restore, daemon=True).start()
            logger.debug(f"Clipboard paste: {len(text)} chars")

        except Exception as e:
            logger.error(f"Clipboard paste failed: {e}")
            self._type_text(text)

    def _type_text(self, text: str):
        """Type text character by character (slower, more compatible)."""
        try:
            pyautogui.write(text, interval=0.012)
            logger.debug(f"Typed: {len(text)} chars")
        except Exception as e:
            logger.error(f"Type failed: {e}")
