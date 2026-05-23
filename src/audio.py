"""
audio.py — Microphone Capture
Fixes:
  - Proper voice activity detection to ignore background noise
  - RMS level callback for HUD waveform
  - Minimum speech threshold (rejects pure ambient noise recordings)
  - Correct 16kHz mono for Whisper
"""

import io
import threading
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
import logging

logger = logging.getLogger("mike.audio")

SAMPLE_RATE  = 16000   # Whisper expects 16kHz
CHANNELS     = 1       # Mono
CHUNK_FRAMES = 1024    # Buffer chunk size
DTYPE        = "int16"

# Voice activity threshold — frames below this RMS are "silence"
# Helps filter out typing sounds, fan noise, etc. (0–32767 scale)
SILENCE_THRESHOLD = 300   # Only count frames clearly above ambient noise
MIN_VOICE_FRAMES  = 4     # Need at least 4 above-threshold chunks (~0.25s of speech)
MIN_AVG_RMS       = 80    # Entire chunk must average at least this RMS (rejects silent rooms)


class AudioCapture:
    def __init__(self, config=None):
        self.config         = config or {}
        self._frames        = []
        self._recording     = False
        self._stream        = None
        self._lock          = threading.Lock()
        self._level_cb      = None   # callback(float 0.0–1.0)
        self._voice_frames  = 0      # count of above-threshold chunks

    # ─── Public API ───────────────────────────────────────────────────────────

    def start_capture(self, level_callback=None):
        """Start recording from default microphone."""
        with self._lock:
            if self._recording:
                return
            self._frames       = []
            self._voice_frames = 0
            self._recording    = True
            self._level_cb     = level_callback

        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_FRAMES,
                callback=self._audio_callback,
            )
            self._stream.start()
            logger.debug("Audio capture started")
        except Exception as e:
            logger.error(f"Failed to start audio: {e}")
            with self._lock:
                self._recording = False

    def stop_capture(self) -> io.BytesIO | None:
        """
        Stop recording and return WAV buffer, or None if no valid speech.
        Returns BytesIO ready for Whisper API.
        """
        with self._lock:
            if not self._recording:
                return None
            self._recording = False

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.warning(f"Stream close error: {e}")
            self._stream = None

        frames = self._frames
        self._frames = []

        if not frames:
            logger.debug("No audio frames captured")
            return None

        # Reject if average RMS across all frames is too low (ambient noise / silence)
        all_data = np.concatenate(frames, axis=0).flatten().astype(np.float32)
        avg_rms = float(np.sqrt(np.mean(all_data ** 2)))
        if avg_rms < MIN_AVG_RMS:
            logger.info(f"Rejecting capture — avg RMS {avg_rms:.0f} below threshold {MIN_AVG_RMS} (silence/ambient)")
            return None

        # Check we actually got real speech (not just background noise)
        if self._voice_frames < MIN_VOICE_FRAMES:
            logger.info(f"Rejecting capture — only {self._voice_frames} voice frames (likely noise)")
            return None

        audio_data = np.concatenate(frames, axis=0).flatten()
        if len(audio_data) < SAMPLE_RATE * 0.3:   # Less than 0.3 seconds
            logger.info("Audio too short — skipping")
            return None

        # Write to in-memory WAV
        buf = io.BytesIO()
        wav.write(buf, SAMPLE_RATE, audio_data.astype(np.int16))
        buf.seek(0)
        logger.debug(f"Audio captured: {len(audio_data)/SAMPLE_RATE:.2f}s, {self._voice_frames} voice frames")
        return buf

    def is_recording(self) -> bool:
        return self._recording

    def get_devices(self) -> list:
        """Return list of available input devices."""
        try:
            devices = sd.query_devices()
            return [d for d in devices if d["max_input_channels"] > 0]
        except Exception:
            return []

    # ─── Internal Callback ────────────────────────────────────────────────────

    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio chunk."""
        if status:
            # Input overflow is normal when processing is slow — log at DEBUG only,
            # don't warn the user; just keep capturing.
            if "input overflow" in str(status).lower():
                logger.debug(f"Audio status: {status}")
            else:
                logger.warning(f"Audio status: {status}")

        if not self._recording:
            return

        chunk = indata.copy()
        self._frames.append(chunk)

        # Compute RMS for this chunk
        rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
        if rms > SILENCE_THRESHOLD:
            self._voice_frames += 1

        # Normalize RMS to 0.0–1.0 for HUD (log scale feels more natural)
        level = min(1.0, rms / 3000.0)
        level = level ** 0.5   # Square root for more visual responsiveness

        if self._level_cb:
            try:
                self._level_cb(level)
            except Exception:
                pass
