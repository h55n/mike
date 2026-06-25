"""
ai.py — Groq LLaMA Wrappers
Modes: semi_formal, polished, prompt formatter, pointwise list formatter.
All functions strip preamble, return clean output only.
"""

import logging
import time

from groq import Groq

logger = logging.getLogger("mike.ai")

MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 1000
TEMPERATURE = 0.25  # Low — consistent, not robotic

MAX_RETRIES = 2
RETRY_DELAYS = [1.5, 3.0]

# ─── System Prompts ───────────────────────────────────────────────────────────

SEMI_FORMAL_PROMPT = """\
You are a concise writing assistant. The user dictated this text using voice recognition.
Clean it up with these exact rules:
- Fix grammar and punctuation only
- Remove redundant or repeated phrases
- Make the tone professional but conversational
- Preserve the speaker's EXACT meaning, voice, and grammatical person
- Do NOT change imperative commands — "do this" must stay "do this", never "I will do this"
- Do NOT change first-person to third-person or add new subjects
- Do NOT restructure sentences — only clean them in place
- Do NOT add new information
- Do NOT include any explanation, preamble, quotes, or commentary
- Return ONLY the cleaned text
"""

POLISHED_PROMPT = """\
You are a professional editor. The user dictated this text using voice recognition.
Rewrite it into polished, clear prose:
- Fix all grammar, punctuation, and sentence structure
- Improve clarity and concision
- Maintain a professional tone
- Preserve the original meaning and grammatical person COMPLETELY
- Do NOT change imperative commands — "do this" stays "do this", never "I will do this"
- Do NOT add subjects, change voice, or restructure imperatives into statements
- Do NOT add new information
- Do NOT include any explanation, preamble, quotes, or commentary
- Return ONLY the final rewritten text
"""

PROMPT_FORMATTER_PROMPT = """\
You are a prompt engineering expert. The user has spoken a rough idea for an AI prompt.
Convert it into a clear, specific, well-structured prompt for use with an AI assistant like ChatGPT or Claude.

Rules for a good prompt:
- Be specific and include context
- State the desired output format if relevant
- Remove ambiguity
- Use second person ("You are...", "Write...", "Explain...")

Do NOT include any explanation, preamble, quotation marks around the prompt, or commentary.
Return ONLY the formatted prompt text.
"""

POINTWISE_PROMPT = """\
You are a list formatter. The user has spoken content that should be organized into a numbered list.
Convert the content into a clean numbered list format:
- Use format: 1. First item\n2. Second item\n3. Third item
- Each item should be concise and clear
- Preserve all the user's points — do not drop any
- Fix grammar within each point
- Do NOT add items the user didn't mention
- Do NOT include any explanation, preamble, or commentary
- Return ONLY the numbered list
"""


class AIProcessor:
    def __init__(self, config, filters=None):
        self.config = config
        self.filters = filters  # TextFilter instance for output cleaning
        self._client = None
        self._client_api_key = None

    def _get_client(self) -> Groq:
        if hasattr(self.config, "reload"):
            self.config.reload()
        api_key = self.config.get("groq_api_key", "")
        if not api_key or not api_key.startswith("gsk_"):
            raise ValueError("Groq API key not configured.")
        if self._client is None or self._client_api_key != api_key:
            self._client = Groq(api_key=api_key)
            self._client_api_key = api_key
        return self._client

    def _call_llm(self, text: str, system_prompt: str) -> str:
        """Core LLM call with retry logic."""
        for attempt in range(MAX_RETRIES + 1):
            try:
                client = self._get_client()
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text},
                    ],
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                )
                result = resp.choices[0].message.content.strip()

                # Strip LLM preamble artifacts
                if self.filters:
                    result = self.filters.clean_llm_output(result)

                return result

            except ValueError:
                raise
            except Exception as e:
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning(
                        f"LLM attempt {attempt+1} failed: {e} — retrying in {delay}s"
                    )
                    time.sleep(delay)
                    self._client = None
                else:
                    logger.error(f"LLM failed: {e}")
                    return text  # Fallback: return input unchanged

    # ─── Public Methods ───────────────────────────────────────────────────────

    def semi_formal(self, text: str) -> str:
        """Clean up, fix grammar, professional but conversational."""
        logger.info("AI: semi_formal processing")
        return self._call_llm(text, SEMI_FORMAL_PROMPT)

    def polished(self, text: str) -> str:
        """Full rewrite into polished prose."""
        logger.info("AI: polished processing")
        return self._call_llm(text, POLISHED_PROMPT)

    def format_prompt(self, text: str) -> str:
        """
        Convert rough spoken idea → well-structured AI prompt.
        Triggered by 'prompt-' prefix.
        """
        logger.info("AI: prompt formatting")
        return self._call_llm(text, PROMPT_FORMATTER_PROMPT)

    def format_pointwise(self, text: str) -> str:
        """
        Convert spoken content → numbered list.
        Triggered by 'pointwise', 'numbered list', 'list this', etc.
        """
        logger.info("AI: pointwise formatting")
        return self._call_llm(text, POINTWISE_PROMPT)

    def invalidate_client(self):
        """Force re-connect after API key change."""
        self._client = None
        self._client_api_key = None
