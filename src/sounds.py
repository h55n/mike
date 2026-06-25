"""
sounds.py — Mike audio feedback using the signature initiation chime.

Play order:
  play_start() → mike_chime.mp3 at ~25% volume  (mic ON)
  play_stop()  → mike_chime.mp3 at ~15% volume  (mic OFF, quieter to distinguish)

Falls back to a soft synthetic sine-wave tone if pygame is unavailable,
or to winsound.Beep as a last resort.

All playback is fire-and-forget via a daemon thread — never blocks the engine.
"""

import threading
import logging
import math
from paths import asset_path

logger = logging.getLogger("mike.sounds")

# ── Volume levels (0.0 – 1.0) ────────────────────────────────────────────────
_VOL_ON  = 0.25   # mic ON  — audible but unobtrusive
_VOL_OFF = 0.15   # mic OFF — quieter than ON so direction is clear

# Cached pygame init state
_pygame_ready = None   # None = untested, True/False = tested


def _ensure_pygame() -> bool:
    """Initialise pygame.mixer once; return True if usable."""
    global _pygame_ready
    if _pygame_ready is not None:
        return _pygame_ready
    try:
        import pygame
        if not pygame.get_init():
            pygame.init()
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        _pygame_ready = True
    except Exception as e:
        logger.debug(f"pygame unavailable: {e}")
        _pygame_ready = False
    return _pygame_ready


def _play_mp3(volume: float):
    """Load and play mike_chime.mp3 at the given volume (0.0–1.0)."""
    chime = asset_path("mike_chime.mp3")
    if not chime.exists():
        logger.debug(f"Chime not found at {chime} — falling back to tone")
        return False

    if not _ensure_pygame():
        return False

    try:
        import pygame
        sound = pygame.mixer.Sound(str(chime))
        # pygame Sound volume: 0.0–1.0
        sound.set_volume(max(0.0, min(1.0, volume)))
        sound.play()
        return True
    except Exception as e:
        logger.debug(f"pygame playback error: {e}")
        return False


# ── Soft sine-wave fallback (no external deps beyond numpy/sounddevice) ───────

def _make_tone(freq: float, duration_s: float,
               volume: float = 0.12, sample_rate: int = 44100):
    """
    Sine-wave buffer with cosine attack/release envelope.
    volume deliberately kept very soft as a last-resort fallback.
    """
    import numpy as np
    n = int(sample_rate * duration_s)
    t = np.linspace(0, duration_s, n, endpoint=False)
    wave = np.sin(2 * math.pi * freq * t).astype(np.float32)

    attack_n  = min(int(0.015 * sample_rate), n)
    release_n = min(int(0.025 * sample_rate), n)
    for i in range(attack_n):
        wave[i] *= (1 - math.cos(math.pi * i / attack_n)) / 2
    for i in range(release_n):
        wave[n - release_n + i] *= (1 + math.cos(math.pi * i / release_n)) / 2
    return wave * volume


def _play_tone_fallback(tones: list):
    """Play synthetic tones via sounddevice, or winsound.Beep as last resort."""
    try:
        import numpy as np
        import sounddevice as sd
        buffers = [_make_tone(f, d) for f, d in tones]
        gap = np.zeros(int(0.015 * 44100), dtype=np.float32)
        combined = np.concatenate(
            [b for pair in zip(buffers, [gap] * len(buffers)) for b in pair]
        )
        sd.play(combined, samplerate=44100, blocking=True)
    except Exception as e:
        logger.debug(f"Tone fallback → winsound: {e}")
        try:
            import winsound
            for freq, dur in tones:
                winsound.Beep(max(37, min(32767, int(freq))), max(1, int(dur * 1000)))
        except Exception as e2:
            logger.debug(f"winsound also failed: {e2}")


# ── Public API ────────────────────────────────────────────────────────────────

def _run(fn, *args):
    """Fire-and-forget in a daemon thread."""
    threading.Thread(target=fn, args=args, daemon=True).start()


def play_start():
    """
    Mike ON chime — plays mike_chime.mp3 at 25% volume.
    Falls back to a soft two-note ascending tone.
    """
    def _do():
        if not _play_mp3(_VOL_ON):
            _play_tone_fallback([(587.3, 0.10), (739.9, 0.13)])
    _run(_do)


def play_stop():
    """
    Mike OFF chime — plays mike_chime.mp3 at 15% volume (quieter than ON).
    Falls back to a soft two-note descending tone.
    """
    def _do():
        if not _play_mp3(_VOL_OFF):
            _play_tone_fallback([(739.9, 0.10), (587.3, 0.13)])
    _run(_do)
