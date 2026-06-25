"""
hotkeys.py — Global Hotkey Listener  (v2.2)
Uses pynput Listener + Win32 GetAsyncKeyState for double-verified triggers.

Hotkeys:
  Ctrl + Shift (hold)         → PTT record (hold to talk, release to transcribe)
  Ctrl + Shift + Space        → Toggle continuous mode ON/OFF

DESIGN DECISIONS & BUG FIXES:
1. Win32 physical-key verification before PTT fires.
   pynput's _pressed set can hold stale entries when focus changes steal
   key-up events.  Before actually starting PTT we query GetAsyncKeyState
   to confirm Ctrl and Shift are *physically* down on the hardware.

2. Ghost-key cleanup loop.
   A background thread runs every 500 ms and cross-checks every modifier
   in _pressed against GetAsyncKeyState.  Stale keys are removed, which
   prevents PTT from ghost-firing on the next innocent keypress.

3. PTT watchdog timer.
   If the key-up event for Ctrl or Shift is never received (because the
   window loses focus mid-hold), the watchdog fires after 30 s and calls
   stop_and_transcribe(), preventing an infinite silent recording.

4. Higher PTT debounce (400 ms vs. old 200 ms).
   Prevents rapid double-fires that were showing up in the log.

5. Comprehensive Shift normalization.
   Covers keyboard.Key.shift, keyboard.Key.shift_l AND keyboard.Key.shift_r
   so the detection is consistent across all keyboard brands / layouts.

6. Ctrl+Shift+Space window extended to 200 ms (was 120 ms).
   Gives slower typists more time to add Space for continuous toggle.
"""

import ctypes
import logging
import threading
import time

from pynput import keyboard

logger = logging.getLogger("mike.hotkeys")


# ─── Win32 GetAsyncKeyState helpers ──────────────────────────────────────────

VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_SPACE = 0x20


def _key_down(vk_code: int) -> bool:
    """Return True if the given virtual-key is *physically* held right now."""
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)
    except Exception:
        return False


def _ctrl_held() -> bool:
    return _key_down(VK_LCONTROL) or _key_down(VK_RCONTROL)


def _shift_held() -> bool:
    return _key_down(VK_LSHIFT) or _key_down(VK_RSHIFT)


def _space_held() -> bool:
    return _key_down(VK_SPACE)


# ─── HotkeyListener ──────────────────────────────────────────────────────────


class HotkeyListener:
    def __init__(self, engine):
        self.engine = engine
        self._pressed = set()
        self._ptt_active = False
        self._listener = None
        self._lock = threading.Lock()
        self._ptt_timer = None  # deferred PTT start timer
        self._watchdog = None  # auto-release watchdog

        # Debounce timings (ms)
        self._last_ptt_start = 0.0
        self._last_toggle = 0.0
        self._ptt_debounce_ms = 400  # raised from 200 → prevents rapid re-fires
        self._cont_debounce_ms = 1000  # 1 s — prevents key-repeat spam on Space

        # Window to wait for Space before committing PTT
        self._ptt_delay_s = 0.20  # 200 ms (was 120 ms)

        # PTT safety: if held >30 s with no key-up, auto-release
        self._PTT_MAX_S = 30.0

        # Ghost-key cleanup thread
        self._cleanup_running = False
        self._cleanup_thread = None

    # ── Key sets ──────────────────────────────────────────────────────────────

    CTRL_KEYS = {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl}
    SHIFT_KEYS = {keyboard.Key.shift, keyboard.Key.shift_r, keyboard.Key.shift_l}
    SPACE_KEYS = {keyboard.Key.space}

    def _has_ctrl(self):
        return bool(self._pressed & self.CTRL_KEYS)

    def _has_shift(self):
        return bool(self._pressed & self.SHIFT_KEYS)

    def _has_space(self):
        return bool(self._pressed & self.SPACE_KEYS)

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,
        )
        self._listener.daemon = True
        self._listener.start()

        # Ghost-key cleanup loop
        self._cleanup_running = True
        self._cleanup_thread = threading.Thread(
            target=self._ghost_key_loop, daemon=True, name="mike-hotkey-cleanup"
        )
        self._cleanup_thread.start()

        logger.info(
            "Hotkey listener started — "
            "PTT: Ctrl+Shift (hold) | Continuous: Ctrl+Shift+Space"
        )

    def stop(self):
        self._cleanup_running = False
        self._cancel_ptt_timer()
        self._cancel_watchdog()
        if self._listener:
            self._listener.stop()
        logger.info("Hotkey listener stopped")

    # ── pynput event handlers ─────────────────────────────────────────────────

    def _on_press(self, key):
        with self._lock:
            self._pressed.add(key)
            self._handle_press()

    def _on_release(self, key):
        with self._lock:
            was_ptt = self._ptt_active
            self._pressed.discard(key)

            is_modifier = key in self.CTRL_KEYS or key in self.SHIFT_KEYS

            # Cancel deferred PTT if a modifier lifts before timer fires
            if is_modifier and self._ptt_timer:
                self._cancel_ptt_timer()

            # Stop active PTT on Ctrl or Shift release
            # Double-verify with Win32 so we don't stop on an unrelated key
            if was_ptt and is_modifier:
                if not _ctrl_held() or not _shift_held():
                    self._do_ptt_stop()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _cancel_ptt_timer(self):
        if self._ptt_timer:
            self._ptt_timer.cancel()
            self._ptt_timer = None

    def _cancel_watchdog(self):
        if self._watchdog:
            self._watchdog.cancel()
            self._watchdog = None

    def _start_watchdog(self):
        self._cancel_watchdog()
        self._watchdog = threading.Timer(self._PTT_MAX_S, self._watchdog_fire)
        self._watchdog.daemon = True
        self._watchdog.start()

    def _watchdog_fire(self):
        """Auto-release PTT after 30 s if key-up was missed."""
        with self._lock:
            self._watchdog = None
            if self._ptt_active:
                logger.warning("PTT watchdog fired — auto-releasing after 30 s")
                self._do_ptt_stop()

    def _do_ptt_stop(self):
        """Stop active PTT (must be called inside self._lock)."""
        self._ptt_active = False
        self._cancel_watchdog()
        logger.debug("PTT released → stop_and_transcribe")
        threading.Thread(target=self.engine.stop_and_transcribe, daemon=True).start()

    def _sync_pressed(self):
        """Remove ghost modifier keys whose Win32 state says they are up."""
        if not _ctrl_held():
            self._pressed -= self.CTRL_KEYS
        if not _shift_held():
            self._pressed -= self.SHIFT_KEYS
        if not _space_held():
            self._pressed -= self.SPACE_KEYS

    def _ghost_key_loop(self):
        """
        Background thread: every 500 ms cross-check _pressed against
        GetAsyncKeyState and evict any stale ghost entries.
        This prevents PTT from ghost-firing after focus changes.
        """
        while self._cleanup_running:
            time.sleep(0.5)
            with self._lock:
                self._sync_pressed()
                # Also auto-release a stuck PTT if keys are physically up
                if self._ptt_active and not _ctrl_held() and not _shift_held():
                    logger.warning(
                        "Ghost-key cleanup: PTT active but keys physically up — auto-releasing"
                    )
                    self._do_ptt_stop()

    def _handle_press(self):
        """Called inside lock on every key press."""
        now = time.time() * 1000  # ms

        ctrl = self._has_ctrl()
        shift = self._has_shift()
        space = self._has_space()

        # ── Ctrl + Shift + Space → toggle continuous ───────────────────────────
        if ctrl and shift and space:
            self._cancel_ptt_timer()
            if now - self._last_toggle > self._cont_debounce_ms:
                self._last_toggle = now
                logger.info("Continuous mode toggle (Ctrl+Shift+Space)")
                threading.Thread(
                    target=self.engine.toggle_continuous, daemon=True
                ).start()
            return

        # ── Ctrl + Shift (no Space) → schedule PTT after 200 ms window ─────────
        if (
            ctrl
            and shift
            and not space
            and not self._ptt_active
            and not self._ptt_timer
        ):
            if now - self._last_ptt_start > self._ptt_debounce_ms:
                self._last_ptt_start = now
                self._ptt_timer = threading.Timer(self._ptt_delay_s, self._fire_ptt)
                self._ptt_timer.daemon = True
                self._ptt_timer.start()

    def _fire_ptt(self):
        """
        Called 200 ms after Ctrl+Shift was detected.
        Uses Win32 GetAsyncKeyState to verify keys are PHYSICALLY held,
        preventing ghost triggers from stale pynput _pressed entries.
        """
        with self._lock:
            self._ptt_timer = None

            # Physical verification — the most important guard
            ctrl_ok = _ctrl_held()
            shift_ok = _shift_held()
            space_ok = _space_held()

            if not ctrl_ok or not shift_ok:
                # Keys lifted during the 200 ms window — clean up ghosts
                self._sync_pressed()
                return

            if space_ok:
                # Space arrived — this is a continuous toggle, not PTT
                return

            if self._ptt_active:
                # Already recording (shouldn't happen, but be safe)
                return

            self._ptt_active = True
            self._start_watchdog()
            logger.info("PTT start (Ctrl+Shift)")
            threading.Thread(target=self.engine.start_recording, daemon=True).start()
