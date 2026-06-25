"""
engine.py — Core Orchestrator & State Machine
Fixes: double-posting lock, reliable hotkey state, processing guard,
       audio level feeding to HUD, proper cleanup on cancel.
"""

import logging
import queue
import threading
import time

try:
    from sounds import play_start, play_stop
except Exception:

    def play_start():
        pass

    def play_stop():
        pass


logger = logging.getLogger("mike.engine")


class EngineState:
    IDLE = "idle"
    RECORDING_PTT = "recording_ptt"
    RECORDING_CONT = "recording_cont"
    PAUSED_CONT = "paused_cont"
    PROCESSING = "processing"


class MikeEngine:
    def __init__(
        self, config, audio, transcription, ai, filters, injection, db, settings
    ):
        self.config = config
        self.audio = audio
        self.transcribe = transcription
        self.ai = ai
        self.filters = filters
        self.inject = injection
        self.db = db
        self.settings = settings

        self.state = EngineState.IDLE
        self.mode = settings.get("active_mode", "raw")
        self.hud = None  # set after HUD is created
        self.dashboard = None  # set when dashboard is opened

        self._state_lock = threading.Lock()
        self._process_lock = threading.Lock()  # ← key fix: prevents double-post
        self._ptt_active = False
        self._session_start = None
        self._task_queue = queue.Queue()

        # Continuous mode
        self._cont_thread = None
        self._cont_stop = threading.Event()
        self._cont_pause = threading.Event()
        self._toggle_seq = 0  # increments on every toggle call
        self._last_toggle_t = 0.0  # time of last successful toggle (seconds)

        # Worker thread for transcription/LLM (non-blocking)
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    # ─── State Helpers ────────────────────────────────────────────────────────

    def _set_state(self, new_state: str):
        with self._state_lock:
            old = self.state
            self.state = new_state
            logger.debug(f"State: {old} → {new_state}")
        if self.hud:
            hud_state_map = {
                EngineState.IDLE: "silent",
                EngineState.RECORDING_PTT: "recording",
                EngineState.RECORDING_CONT: "continuous",
                EngineState.PAUSED_CONT: "continuous",  # keep LIVE shown when paused
                EngineState.PROCESSING: "processing",
            }
            self.hud.set_state(hud_state_map.get(new_state, "silent"))

    def _is_idle(self):
        return self.state == EngineState.IDLE

    # ─── PTT (Push-to-Talk) ───────────────────────────────────────────────────

    def start_recording(self):
        """Called by hotkey listener on Ctrl+Shift press."""
        with self._state_lock:
            # Only start if truly idle — block if processing or already recording
            if self.state not in (EngineState.IDLE,):
                logger.debug(f"start_recording ignored — state is {self.state}")
                return
            if self._ptt_active:
                logger.debug("start_recording ignored — _ptt_active already True")
                return
            self._ptt_active = True

        logger.info("PTT start")
        self._set_state(EngineState.RECORDING_PTT)
        self._session_start = time.time()
        play_start()
        self.audio.start_capture(level_callback=self._on_audio_level)

    def stop_and_transcribe(self):
        """Called by hotkey listener on Ctrl+Shift release, or confirm button."""
        with self._state_lock:
            if self.state == EngineState.IDLE:
                self._ptt_active = False
                return
            if self.state not in (
                EngineState.RECORDING_PTT,
                EngineState.RECORDING_CONT,
            ):
                self._ptt_active = False
                return
            if not self._ptt_active and self.state == EngineState.RECORDING_PTT:
                return
            self._ptt_active = False
            current_state = self.state  # noqa: F841

        logger.info("PTT stop → queuing transcription")
        play_stop()
        audio_buf = self.audio.stop_capture()
        duration = time.time() - (self._session_start or time.time())

        if audio_buf is None or duration < 0.3:
            # Too short — ignore (avoids phantom transcriptions from noise)
            self._set_state(EngineState.IDLE)
            return

        self._set_state(EngineState.PROCESSING)
        self._task_queue.put(("transcribe", audio_buf, duration))

    def cancel_recording(self):
        """Discard current recording with no transcription."""
        logger.info("Recording cancelled")
        self.audio.stop_capture()
        self._ptt_active = False
        self._cont_stop.set()
        self._set_state(EngineState.IDLE)

    # ─── Continuous Mode ──────────────────────────────────────────────────────

    def toggle_continuous(self):
        """Toggle continuous mode. Double-fire protected via sequence counter."""
        import time as _time

        now = _time.monotonic()

        with self._state_lock:
            # Enforce minimum 2 seconds between toggles regardless of source
            if now - self._last_toggle_t < 2.0:
                logger.debug("Toggle ignored — too soon after last toggle")
                return
            self._last_toggle_t = now
            current = self.state

        if current == EngineState.IDLE:
            logger.info("Continuous mode toggle → ON")
            self._start_continuous()
        elif current in (EngineState.RECORDING_CONT, EngineState.PAUSED_CONT):
            logger.info("Continuous mode toggle → OFF")
            self._stop_continuous()

    def _start_continuous(self):
        logger.info("Continuous mode ON")
        self._cont_stop.clear()
        self._cont_pause.clear()
        self._set_state(EngineState.RECORDING_CONT)
        self._cont_thread = threading.Thread(target=self._continuous_loop, daemon=True)
        self._cont_thread.start()

    def _stop_continuous(self):
        logger.info("Continuous mode OFF")
        self._cont_stop.set()
        self._set_state(EngineState.IDLE)

    def pause_continuous(self):
        self._cont_pause.set()
        self._set_state(EngineState.PAUSED_CONT)

    def resume_continuous(self):
        self._cont_pause.clear()
        self._set_state(EngineState.RECORDING_CONT)

    def _continuous_loop(self):
        chunk_sec = float(self.config.get("continuous_chunk_seconds", 5))
        while not self._cont_stop.is_set():
            if self._cont_pause.is_set():
                time.sleep(0.1)
                continue

            start = time.time()
            self.audio.start_capture(level_callback=self._on_audio_level)
            while not self._cont_stop.is_set() and not self._cont_pause.is_set():
                if time.time() - start >= chunk_sec:
                    break
                time.sleep(0.05)

            buf = self.audio.stop_capture()
            duration = time.time() - start
            if buf and duration >= 0.5:
                self._task_queue.put(("transcribe", buf, duration))

        self._set_state(EngineState.IDLE)

    # ─── Worker Thread ────────────────────────────────────────────────────────

    def _worker_loop(self):
        """Single worker thread — guarantees no concurrent transcriptions."""
        while True:
            try:
                task = self._task_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if task is None:  # Shutdown signal
                break

            if task[0] == "transcribe":
                _, audio_buf, duration = task
                self._process_audio(audio_buf, duration)

    def _process_audio(self, audio_buf, duration: float):
        """Full pipeline: transcribe → filter → AI → inject → save."""
        # Acquire lock — prevents double-post even if queue had duplicate entries
        if not self._process_lock.acquire(blocking=False):
            logger.warning("Already processing — dropping duplicate task")
            return

        try:
            # 1. Transcribe
            logger.info("Transcribing…")
            raw_text = self.transcribe.transcribe(audio_buf)
            if not raw_text or not raw_text.strip():
                logger.info("Empty transcript — skipping")
                return

            # 2. Filler filter
            cleaned = self.filters.apply_all(raw_text)
            if not cleaned or len(cleaned.strip()) < 2:
                logger.info("Post-filter text too short — skipping")
                return

            # 3. Detect special triggers
            is_prompt, prompt_content = self.filters.detect_prompt_mode(cleaned)
            is_pointwise, pointwise_content = self.filters.detect_pointwise_mode(
                cleaned
            )

            # 4. Route to AI or direct
            if is_prompt:
                logger.info("Prompt mode triggered")
                final_text = self.ai.format_prompt(prompt_content)
                session_type = "prompt"
            elif is_pointwise:
                logger.info("Pointwise mode triggered")
                final_text = self.ai.format_pointwise(pointwise_content)
                session_type = "dictation"
            elif self.mode == "semi_formal":
                final_text = self.ai.semi_formal(cleaned)
                session_type = "dictation"
            elif self.mode == "polished":
                final_text = self.ai.polished(cleaned)
                session_type = "dictation"
            else:
                final_text = cleaned
                session_type = "dictation"

            if not final_text or not final_text.strip():
                return

            # 5. Inject text at cursor
            logger.info(f"Injecting {len(final_text.split())} words")
            self.inject.insert(final_text)

            # 6. Save session
            word_count = len(final_text.split())
            self.db.save_session(
                duration_seconds=duration,
                word_count=word_count,
                char_count=len(final_text),
                mode=self.mode,
                session_type=session_type,
                raw_transcript=raw_text,
                final_text=final_text,
            )

            # 7. Show brief HUD confirmation
            if self.hud:
                self.hud.show_notification(f"✓ {word_count} words", 1200)

        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)
            if self.hud:
                self.hud.show_notification("⚠ Error — check console", 2000)
        finally:
            self._process_lock.release()
            # Restore correct state after processing
            if self.state == EngineState.PROCESSING:
                # If continuous loop is still running, go back to RECORDING_CONT
                if (
                    not self._cont_stop.is_set()
                    and self._cont_thread
                    and self._cont_thread.is_alive()
                ):
                    self._set_state(EngineState.RECORDING_CONT)
                else:
                    self._set_state(EngineState.IDLE)

    # ─── Audio Level Callback ─────────────────────────────────────────────────

    def _on_audio_level(self, level: float):
        """Called by audio module with live RMS level."""
        if self.hud:
            self.hud.set_audio_level(level)

    # ─── Settings ─────────────────────────────────────────────────────────────

    def set_mode(self, mode: str):
        self.mode = mode
        self.settings.set("active_mode", mode)
        if self.hud:
            self.hud.set_mode(mode)
        logger.info(f"Mode: {mode}")

    # ─── Dashboard ────────────────────────────────────────────────────────────

    def open_dashboard(self):
        """Open dashboard window.
        - Frozen (exe): spawn same Mike.exe --dashboard (no external Python needed)
        - Dev (script): spawn pythonw main.py --dashboard (no console)
        """
        import os
        import pathlib
        import subprocess
        import sys

        NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW
        DETACHED = 0x00000008  # DETACHED_PROCESS

        try:
            env = os.environ.copy()
            for k in list(env.keys()):
                if (
                    k.startswith("_PYI")
                    or k.startswith("_MEI")
                    or k in ("TCL_LIBRARY", "TK_LIBRARY")
                ):
                    env.pop(k, None)

            if getattr(sys, "frozen", False):
                # ── Frozen: reuse the same exe with --dashboard flag ──────────
                cmd = [sys.executable, "--dashboard"]
                logger.info(f"Opening dashboard (frozen): {cmd}")
                subprocess.Popen(
                    cmd,
                    env=env,
                    creationflags=NO_WINDOW | DETACHED,
                )
            else:
                # ── Dev: use pythonw (no console window) ──────────────────────
                exe = pathlib.Path(sys.executable)
                pythonw = exe.parent / "pythonw.exe"
                if not pythonw.exists():
                    pythonw = exe  # fallback
                main_py = pathlib.Path(__file__).resolve().parent / "main.py"
                cmd = [str(pythonw), str(main_py), "--dashboard"]
                logger.info(f"Opening dashboard (dev): {cmd}")
                subprocess.Popen(
                    cmd,
                    env=env,
                    creationflags=NO_WINDOW,
                )
            logger.info("Dashboard subprocess launched")
        except Exception as e:
            logger.error(f"Dashboard launch failed: {e}", exc_info=True)

    def open_settings(self):
        """Open dashboard on settings tab."""
        self.open_dashboard()

    # ─── Kill Switch ──────────────────────────────────────────────────────────

    def force_stop_mic(self):
        """Nuclear kill: stop ALL mic activity immediately, return to IDLE.
        Bypasses all debounce guards. Safe to call from any thread or state.
        """
        logger.info("force_stop_mic called")
        self._cont_stop.set()
        self._ptt_active = False
        try:
            self.audio.stop_capture()
        except Exception:
            pass
        self._set_state(EngineState.IDLE)
        logger.info("Mic force-stopped → IDLE")

    def wake_mic(self):
        """Reset mic to a clean idle state so it's ready for use again.
        Call this when Mike is stuck/glitched — clears all locks and events.
        """
        logger.info("wake_mic called — resetting engine state")
        self.force_stop_mic()
        # Replace stop/pause events with fresh ones so continuous mode
        # can be started again cleanly after a force_stop.
        import time as _t

        _t.sleep(0.15)  # brief window for continuous thread to notice and exit
        self._cont_stop = threading.Event()
        self._cont_pause = threading.Event()
        self._ptt_active = False
        self._last_toggle_t = 0.0  # reset debounce so toggles work immediately
        logger.info("Mike wake complete — ready")
        if self.hud:
            self.hud.show_notification("✓ Mike ready", 1500)

    # ─── Cleanup ──────────────────────────────────────────────────────────────

    def shutdown(self):
        logger.info("Engine shutting down")
        self.cancel_recording()
        self._cont_stop.set()
        self._task_queue.put(None)
