"""
sounds.py — Calm, soft audio feedback for PTT start/stop.

Generates smooth sine-wave tones via numpy → sounddevice so we can
control volume, attack/release envelope, and frequency precisely.
Falls back to winsound.Beep if sounddevice/numpy are unavailable.

Plays in a background thread so it never blocks the hotkey or engine.
"""

import threading
import logging
import math

logger = logging.getLogger("mike.sounds")


def _make_tone(freq: float, duration_s: float,
               volume: float = 0.18, sample_rate: int = 44100) -> "np.ndarray":
    """
    Build a sine-wave buffer with a short cosine fade-in/out envelope.
    volume=0.18 is deliberately quiet — calming, not startling.
    """
    import numpy as np
    n = int(sample_rate * duration_s)
    t = np.linspace(0, duration_s, n, endpoint=False)
    wave = np.sin(2 * math.pi * freq * t).astype(np.float32)

    # Envelope: 15 ms attack, 25 ms release
    attack_n  = min(int(0.015 * sample_rate), n)
    release_n = min(int(0.025 * sample_rate), n)

    for i in range(attack_n):
        wave[i] *= (1 - math.cos(math.pi * i / attack_n)) / 2
    for i in range(release_n):
        wave[n - release_n + i] *= (1 + math.cos(math.pi * i / release_n)) / 2

    return wave * volume


def _play_sequence(tones: list[tuple[float, float]]):
    """
    Play a sequence of (freq_hz, duration_s) tones sequentially,
    with a tiny gap between each note.
    Falls back to winsound.Beep on any error.
    """
    try:
        import numpy as np
        import sounddevice as sd

        buffers = [_make_tone(f, d) for f, d in tones]
        # 15 ms silence gap between notes
        gap = np.zeros(int(0.015 * 44100), dtype=np.float32)
        combined = np.concatenate(
            [b for pair in zip(buffers, [gap] * len(buffers)) for b in pair]
        )
        sd.play(combined, samplerate=44100, blocking=True)

    except Exception as e:
        logger.debug(f"Soft tone fallback to beep: {e}")
        try:
            import winsound
            for freq, dur in tones:
                winsound.Beep(max(37, min(32767, int(freq))), max(1, int(dur * 1000)))
        except Exception as e2:
            logger.debug(f"Beep also failed: {e2}")


def _run_async(tones: list[tuple[float, float]]):
    """Fire-and-forget: play tones in a daemon thread."""
    threading.Thread(target=_play_sequence, args=(tones,), daemon=True).start()


def play_start():
    """
    Gentle two-note ascending chime — mic is now listening.
    Uses a soft pentatonic interval (D5 → F#5): calming, musical.
    """
    _run_async([
        (587.3, 0.10),   # D5 — soft 'ready' note
        (739.9, 0.13),   # F#5 — gentle rise
    ])


def play_stop():
    """
    Gentle two-note descending chime — mic session ended.
    Uses F#5 → D5 (reverse of start): symmetrical, satisfying.
    """
    _run_async([
        (739.9, 0.10),   # F#5
        (587.3, 0.13),   # D5 — soft 'done' note
    ])
