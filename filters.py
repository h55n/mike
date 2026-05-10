"""
filters.py — Text Cleaning & Trigger Detection
Fixes:
  - Repeated word/phrase deduplication
  - Surrounding sound / ambient noise transcription removal
  - Filler word stripping
  - Prompt mode detection
  - Pointwise mode (numbered list trigger)
  - Short phantom transcription rejection
  - Symbol expansion (spoken word → Unicode character)
"""

import re
import unicodedata


# ─── Filler patterns ─────────────────────────────────────────────────────────

FILLER_WORDS = [
    r"\bum+\b", r"\buh+\b", r"\bah+\b", r"\beh+\b",
    r"\ber+\b", r"\bhmm+\b", r"\bhm+\b", r"\bmm+\b",
    r"\byou know\b", r"\bbasically\b", r"\bliterally\b",
    r"\bkind of\b", r"\bsort of\b",
]

# Sentence-start fillers — only strip when at start of sentence
SENTENCE_START_FILLERS = [
    r"^so\b[,\s]?",
    r"^right\b[,\s]?",
    r"^okay so\b[,\s]?",
    r"^ok so\b[,\s]?",
    r"^and so\b[,\s]?",
]

# ─── Ambient noise / hallucination phrases ───────────────────────────────────
# Whisper sometimes transcribes silence or background noise as these phrases

AMBIENT_NOISE_PHRASES = [
    r"^\s*thank you\s*\.?\s*$",
    r"^\s*thanks for watching\s*\.?\s*$",
    r"^\s*you\s*\.?\s*$",
    r"^\s*bye\s*\.?\s*$",
    r"^\s*bye bye\s*\.?\s*$",
    r"^\s*subscribe\s*\.?\s*$",
    r"^\s*\.\s*$",
    r"^\s*\.\.\.\s*$",
    r"^\s*silence\s*\.?\s*$",
    r"^\s*music\s*\.?\s*$",
    r"^\s*\[music\]\s*$",
    r"^\s*\[silence\]\s*$",
    r"^\s*\[applause\]\s*$",
    r"^\s*\[laughter\]\s*$",
    r"^\s*\[noise\]\s*$",
    r"^\s*\[inaudible\]\s*$",
    r"^\s*the\s*$",
    r"^\s*a\s*$",
    r"^\s*i\s*$",
]

# ─── Prompt trigger patterns ─────────────────────────────────────────────────

PROMPT_TRIGGERS = [
    "prompt-",
    "prompt -",
    "prompt–",
    "prompt—",
    "prompt dash",
    "prompt hyphen",
]

# ─── Pointwise trigger patterns ───────────────────────────────────────────────

POINTWISE_TRIGGERS = [
    "pointwise",
    "point wise",
    "point-wise",
    "numbered list",
    "list this",
    "list it",
    "make a list",
    "bullet points",
]


# ─── Symbol expansion map ──────────────────────────────────────────────
# Keys are spoken phrases (lowercase). Longer phrases listed first so they
# match before their shorter substrings do.
SYMBOL_MAP: list[tuple[str, str]] = [
    # Math / science
    ("plus minus symbol",        "±"),
    ("plus or minus symbol",     "±"),
    ("plus or minus",            "±"),
    ("plus minus",               "±"),
    ("not equal to",             "≠"),
    ("not equal",                "≠"),
    ("not equals",               "≠"),
    ("approximately equal to",   "≈"),
    ("approximately equal",      "≈"),
    ("approximately",            "≈"),
    ("less than or equal to",    "≤"),
    ("less than or equal",       "≤"),
    ("greater than or equal to", "≥"),
    ("greater than or equal",    "≥"),
    ("infinity symbol",          "∞"),
    ("infinity sign",            "∞"),
    ("square root symbol",       "√"),
    ("square root",              "√"),
    ("micro symbol",             "μ"),
    ("micro sign",               "μ"),
    ("pi symbol",                "π"),
    ("delta symbol",             "Δ"),
    ("sigma symbol",             "Σ"),
    ("summation symbol",         "Σ"),
    ("superscript two",          "²"),
    ("superscript 2",            "²"),
    ("squared symbol",           "²"),
    ("superscript three",        "³"),
    ("superscript 3",            "³"),
    ("cubed symbol",             "³"),
    # Legal / commercial
    ("copyright symbol",         "©"),
    ("copyright sign",           "©"),
    ("trademark symbol",         "™"),
    ("trade mark symbol",        "™"),
    ("trademark sign",           "™"),
    ("registered trademark",     "®"),
    ("registered symbol",        "®"),
    ("registered sign",          "®"),
    # Temperature / measurement
    ("degree symbol",            "°"),
    ("degrees symbol",           "°"),
    ("degree sign",              "°"),
    # Arrows
    ("left right arrow",         "↔"),
    ("double arrow",             "↔"),
    ("right arrow",              "→"),
    ("arrow right",              "→"),
    ("left arrow",               "←"),
    ("arrow left",               "←"),
    ("up arrow",                 "↑"),
    ("arrow up",                 "↑"),
    ("down arrow",               "↓"),
    ("arrow down",               "↓"),
    # Typography
    ("ellipsis symbol",          "…"),
    ("dot dot dot",              "…"),
    ("em dash",                  "—"),
    ("long dash",                "—"),
    ("en dash",                  "–"),
    ("bullet point symbol",      "•"),
    ("bullet symbol",            "•"),
    ("bullet point",             "•"),
    ("section symbol",           "§"),
    ("section sign",             "§"),
    ("paragraph symbol",         "¶"),
    ("paragraph sign",           "¶"),
    # Check / cross
    ("check mark symbol",        "✓"),
    ("checkmark symbol",         "✓"),
    ("check mark",               "✓"),
    ("checkmark",                "✓"),
    ("cross mark symbol",        "✗"),
    ("x mark symbol",            "✗"),
    ("cross mark",               "✗"),
    # Currency extras
    ("euro symbol",              "€"),
    ("euro sign",                "€"),
    ("pound symbol",             "£"),
    ("pound sign",               "£"),
    ("yen symbol",               "¥"),
    ("yen sign",                 "¥"),
    ("cent symbol",              "¢"),
    ("cent sign",                "¢"),
    # Misc
    ("heart symbol",             "♥"),
    ("star symbol",              "★"),
]


# ─── Main Filter Class ────────────────────────────────────────────────────────

class TextFilter:

    def apply_all(self, text: str) -> str:
        """Run full cleaning pipeline."""
        if not text:
            return ""

        text = self._normalize(text)

        # Reject ambient noise phantoms
        if self._is_ambient_noise(text):
            return ""

        # Reject suspiciously short transcriptions (likely noise)
        words = text.split()
        if len(words) == 1 and len(words[0]) <= 2 and words[0].lower() not in {
            "hi", "no", "ok", "go", "do", "to", "up", "in", "on", "at",
            "by", "as", "or", "if", "so", "an",
        }:
            return ""

        text = self._remove_fillers(text)
        text = self._expand_symbols(text)       # ← symbol expansion
        text = self._remove_repeated_words(text)
        text = self._remove_repeated_phrases(text)
        text = self._fix_spacing(text)

        return text.strip()

    def _normalize(self, text: str) -> str:
        """Normalize unicode, fix smart quotes, etc."""
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        return text

    def _is_ambient_noise(self, text: str) -> bool:
        """Return True if text looks like Whisper hallucination from ambient noise."""
        t = text.strip().lower()
        for pattern in AMBIENT_NOISE_PHRASES:
            if re.match(pattern, t, re.IGNORECASE):
                return True
        # Reject if it's just punctuation / symbols
        stripped = re.sub(r"[^\w\s]", "", t).strip()
        if not stripped:
            return True
        return False

    def _remove_fillers(self, text: str) -> str:
        # Remove standalone filler words
        for pattern in FILLER_WORDS:
            text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

        # Remove sentence-start fillers
        for pattern in SENTENCE_START_FILLERS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Remove Whisper artifact tags like [Music], [Silence], etc.
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"\(.*?\)", "", text)

        return text

    def _remove_repeated_words(self, text: str) -> str:
        """Fix 'I I want' → 'I want', 'the the' → 'the'."""
        # Repeated consecutive words (case-insensitive)
        text = re.sub(r"\b(\w+)(\s+\1)+\b", r"\1", text, flags=re.IGNORECASE)
        return text

    def _remove_repeated_phrases(self, text: str) -> str:
        """
        Remove a phrase that appears back-to-back (stuttered).
        Example: 'I want to go I want to go to the store' -> 'I want to go to the store'
        Only removes exact consecutive duplicates, not partial overlaps.
        """
        words = text.split()
        n = len(words)
        if n < 4:
            return text

        result = []
        i = 0
        while i < n:
            removed = False
            # Try phrase lengths from longest to shortest
            for phrase_len in range(min(6, n // 2), 1, -1):
                if i + phrase_len * 2 > n:
                    continue
                phrase_a = [w.lower() for w in words[i:i + phrase_len]]
                phrase_b = [w.lower() for w in words[i + phrase_len:i + phrase_len * 2]]
                if phrase_a == phrase_b:
                    # Keep first occurrence only
                    result.extend(words[i:i + phrase_len])
                    i += phrase_len * 2
                    removed = True
                    break
            if not removed:
                result.append(words[i])
                i += 1

        return " ".join(result)

    def _fix_spacing(self, text: str) -> str:
        """Collapse multiple spaces, fix punctuation spacing."""
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r"\s([,\.!?;:])", r"\1", text)
        text = re.sub(r"([,\.!?;:])\s*([,\.!?;:])", r"\1\2", text)
        # Capitalize first letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        return text.strip()

    def _expand_symbols(self, text: str) -> str:
        """
        Replace spoken symbol phrases with their Unicode characters.
        Example: 'temperature is 37 degree symbol' -> 'temperature is 37°'
        Matches are case-insensitive; longer phrases checked first (map is
        ordered longest-first per group).
        """
        for phrase, symbol in SYMBOL_MAP:
            # Word-boundary-aware replacement, case-insensitive
            pattern = r'(?i)\b' + re.escape(phrase) + r'\b'
            text = re.sub(pattern, symbol, text)
        return text

    # ─── Trigger Detection ────────────────────────────────────────────────────

    def detect_prompt_mode(self, text: str) -> tuple[bool, str]:
        """Returns (is_prompt, remainder_text)."""
        lower = text.lower().strip()
        for trigger in PROMPT_TRIGGERS:
            if lower.startswith(trigger):
                remainder = text[len(trigger):].strip()
                return True, remainder
        return False, text

    def detect_pointwise_mode(self, text: str) -> tuple[bool, str]:
        """
        Detects 'pointwise <content>' or 'numbered list <content>' etc.
        Returns (is_pointwise, content_after_trigger).
        """
        lower = text.lower().strip()
        for trigger in POINTWISE_TRIGGERS:
            if lower.startswith(trigger):
                remainder = text[len(trigger):].strip().lstrip(",:- ")
                if remainder:
                    return True, remainder
        return False, text

    def clean_llm_output(self, text: str) -> str:
        """
        Strip common LLM response artifacts from AI output.
        Prevents Claude/LLaMA from prefixing its response with explanations.
        """
        # Remove common LLM preambles
        preamble_patterns = [
            r"^here('s| is) (the|your) (cleaned|rewritten|polished|revised|formatted) (text|version|response|prompt)[:\s]*",
            r"^sure[,!]?\s*",
            r"^of course[,!]?\s*",
            r"^certainly[,!]?\s*",
            r"^absolutely[,!]?\s*",
        ]
        for p in preamble_patterns:
            text = re.sub(p, "", text, flags=re.IGNORECASE)

        # Remove markdown fences if LLM wraps in code blocks
        text = re.sub(r"^```\w*\n?", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n?```$", "", text, flags=re.MULTILINE)

        return text.strip()
