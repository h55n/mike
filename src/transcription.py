"""
transcription.py — Groq Whisper Wrapper
Fixes:
  - Removed INITIAL_PROMPT that leaked "Transcribe everything literally" into output
  - Retry with exponential backoff
  - Hallucination detection
  - Language forced to English
"""

import time
import logging
from groq import Groq

logger = logging.getLogger("mike.transcription")

# Whisper hallucinates these phrases on silence/noise
WHISPER_HALLUCINATIONS = {
    "thank you",
    "thank you.",
    "thanks for watching",
    "thanks for watching.",
    "you",
    "bye",
    "bye.",
    "subscribe",
    "like and subscribe",
    "see you next time",
    "goodbye",
    "transcribe everything literally",
    "transcribe everything literally.",
    "do not add punctuation unless spoken",
    "",
}

MAX_RETRIES   = 3
RETRY_DELAYS  = [1.0, 2.0, 4.0]


class TranscriptionService:
    def __init__(self, config):
        self.config  = config
        self._client = None
        self._client_api_key = None

    def _get_client(self) -> Groq:
        """Lazy-init Groq client."""
        if hasattr(self.config, "reload"):
            self.config.reload()
        api_key = self.config.get("groq_api_key", "")
        if not api_key or not api_key.startswith("gsk_"):
            raise ValueError(
                "Groq API key not configured. "
                "Open the dashboard → Settings and enter your key from console.groq.com"
            )
        if self._client is None or self._client_api_key != api_key:
            self._client = Groq(api_key=api_key)
            self._client_api_key = api_key
        return self._client

    def transcribe(self, audio_buffer) -> str:
        """
        Transcribe audio buffer (BytesIO WAV) → cleaned string.
        Returns empty string on failure or hallucination.
        """
        for attempt in range(MAX_RETRIES):
            try:
                client = self._get_client()
                audio_buffer.seek(0)

                response = client.audio.transcriptions.create(
                    file=("audio.wav", audio_buffer.read()),
                    model="whisper-large-v3-turbo",   # Fast + accurate
                    language=self.config.get("transcription_language", "en"),
                    response_format="text",
                    # NO prompt= parameter — it was leaking into transcripts
                    temperature=0.0,
                )

                text = str(response).strip() if response else ""

                if self._is_hallucination(text):
                    logger.info(f"Hallucination detected: '{text[:60]}' — discarding")
                    return ""

                logger.info(f"Transcript ({len(text.split())} words): {text[:100]}{'…' if len(text) > 100 else ''}")
                return text

            except ValueError as e:
                logger.error(str(e))
                raise

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[attempt]
                    logger.warning(f"Transcription attempt {attempt+1} failed: {e} — retrying in {delay}s")
                    time.sleep(delay)
                    self._client = None
                else:
                    logger.error(f"Transcription failed after {MAX_RETRIES} attempts: {e}")
                    return ""

        return ""

    def _is_hallucination(self, text: str) -> bool:
        """Detect Whisper hallucinations."""
        if not text:
            return True
        normalized = text.strip().lower().rstrip(".,!?")
        if normalized in WHISPER_HALLUCINATIONS:
            return True
        # Any text that starts with known prompt artifacts
        if normalized.startswith("transcribe") and len(normalized.split()) < 6:
            return True
        # Single char
        words = normalized.split()
        if len(words) == 1 and len(words[0]) <= 1:
            return True
        return False

    def invalidate_client(self):
        self._client = None
        self._client_api_key = None
