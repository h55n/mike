"""
hotkeys.py — Global Hotkey Listener
Uses pynput Listener (works reliably in PyInstaller frozen exes).

Hotkeys:
  Ctrl + Shift (hold)         → PTT record (hold to talk, release to transcribe)
  Ctrl + Shift + Space        → Toggle continuous mode ON/OFF

HOW PTT + CONTINUOUS COEXIST:
  The problem: pressing Ctrl then Shift triggers "Ctrl+Shift" → PTT would start
  BEFORE the user adds Space for continuous toggle. This causes PTT to start
  then immediately fight with the continuous toggle.

  Solution: PTT is deferred 120ms. If Space arrives within that window, we
  cancel the PTT timer and fire the continuous toggle instead. If Space does NOT
  arrive, PTT starts as normal. This makes the combos mutually exclusive with
  zero false triggers.
"""

import threading
import time
import logging
from pynput import keyboard

logger = logging.getLogger("mike.hotkeys")


class HotkeyListener:
    def __init__(self, engine):
        self.engine       = engine
        self._pressed     = set()
        self._ptt_active  = False
        self._listener    = None
        self._lock        = threading.Lock()
        self._ptt_timer   = None    # deferred PTT start timer

        # Debounce timings (ms)
        self._last_ptt_start   = 0.0
        self._last_toggle      = 0.0
        self._ptt_debounce_ms  = 200
        self._cont_debounce_ms = 1000   # 1s — prevents key-repeat spam on Space

        # Delay before PTT actually starts — gives Space time to arrive
        self._ptt_delay_s = 0.12   # 120ms window

    # ── Key sets ──────────────────────────────────────────────────────────────

    CTRL_KEYS  = {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
    SHIFT_KEYS = {keyboard.Key.shift,  keyboard.Key.shift_r}
    SPACE_KEYS = {keyboard.Key.space}

    def _has_ctrl(self):  return bool(self._pressed & self.CTRL_KEYS)
    def _has_shift(self): return bool(self._pressed & self.SHIFT_KEYS)
    def _has_space(self): return bool(self._pressed & self.SPACE_KEYS)

    # ── Listener ──────────────────────────────────────────────────────────────

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,
        )
        self._listener.daemon = True
        self._listener.start()
        logger.info("Hotkey listener started — PTT: Ctrl+Shift (hold) | Continuous: Ctrl+Shift+Space")

    def stop(self):
        self._cancel_ptt_timer()
        if self._listener:
            self._listener.stop()
        logger.info("Hotkey listener stopped")

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_press(self, key):
        with self._lock:
            self._pressed.add(key)
            self._handle_press()

    def _on_release(self, key):
        with self._lock:
            was_ptt = self._ptt_active
            self._pressed.discard(key)

            is_modifier = (key in self.CTRL_KEYS or key in self.SHIFT_KEYS)

            # Cancel pending PTT timer if a modifier is released before it fires
            if is_modifier and self._ptt_timer:
                self._cancel_ptt_timer()

            # Stop active PTT recording on Ctrl or Shift release
            if was_ptt and is_modifier:
                self._ptt_active = False
                logger.debug("PTT key released → stop_and_transcribe")
                threading.Thread(
                    target=self.engine.stop_and_transcribe, daemon=True
                ).start()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _cancel_ptt_timer(self):
        """Cancel any pending deferred PTT start."""
        if self._ptt_timer:
            self._ptt_timer.cancel()
            self._ptt_timer = None

    def _handle_press(self):
        """Called inside lock on every key press."""
        now = time.time() * 1000   # ms

        ctrl  = self._has_ctrl()
        shift = self._has_shift()
        space = self._has_space()

        # ── Ctrl + Shift + Space → toggle continuous ──────────────────────────
        # This MUST be checked before PTT so the timer can be cancelled.
        if ctrl and shift and space:
            # Cancel any pending PTT start — user is doing Ctrl+Shift+Space
            self._cancel_ptt_timer()

            if now - self._last_toggle > self._cont_debounce_ms:
                self._last_toggle = now
                logger.info("Continuous mode toggle (Ctrl+Shift+Space)")
                threading.Thread(
                    target=self.engine.toggle_continuous, daemon=True
                ).start()
            return

        # ── Ctrl + Shift (no Space) → schedule PTT after 120ms window ─────────
        # We wait 120ms to let a possible Space keypress arrive and cancel PTT.
        if ctrl and shift and not space and not self._ptt_active and not self._ptt_timer:
            if now - self._last_ptt_start > self._ptt_debounce_ms:
                self._last_ptt_start = now
                self._ptt_timer = threading.Timer(
                    self._ptt_delay_s, self._fire_ptt
                )
                self._ptt_timer.daemon = True
                self._ptt_timer.start()

    def _fire_ptt(self):
        """
        Called 120ms after Ctrl+Shift was pressed (if not cancelled by Space).
        Starts PTT only if Ctrl+Shift are still held and Space is NOT pressed.
        """
        with self._lock:
            self._ptt_timer = None
            if (self._has_ctrl() and self._has_shift()
                    and not self._has_space()
                    and not self._ptt_active):
                self._ptt_active = True
                logger.info("PTT start (Ctrl+Shift)")
                threading.Thread(
                    target=self.engine.start_recording, daemon=True
                ).start()
