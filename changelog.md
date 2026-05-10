# Mike — Changelog

## [2026-05-08] — UI Polish & Startup Reliability

### Fixed — Dashboard Icon in HUD Hover (hud.py)
- `⊞` icon → `📊` bar-chart emoji. Look like app icon, not Windows logo.

### Fixed — Resting Pill Transparency (hud.py)
- Silent pill alpha=0.65. Hover/active alpha=0.97. Alpha set per-state in `_render_state()`, not global.

### Fixed — Dashboard Filter Labels Unreadable (dashboard.py)
- Filter labels invisible on dark bg. Style loop fail on inserted widgets.
- Use explicit styled `QLabel` (`color: #d6d3d1`) before insert. Labels readable.

### Changed — Nav Bar Emojis (dashboard.py)
- Sidebar items use emoji, not ASCII brackets.
  - `[~]` → `🏠` (Overview)
  - `[=]` → `📋` (Sessions)
  - `[*]` → `⚙️` (Settings)

### Fixed — PC Startup Reliability (startup.py, main.py)
- Windows autostart use `C:\Windows\System32` CWD. Break relative imports.
- `add_to_startup()` build `cmd /c "cd /d <project_dir> && pythonw.exe main.py"`.
- Use `pythonw.exe` hide console window.
- `main.py` force `add_to_startup()` on launch. Overwrite stale registry.

## [2026-05-06] — Speed & Reliability Pass

### Speed Optimization
- **`transcription.py`**: Upgrade `whisper-large-v3-turbo`. 6x faster.
- **`transcription.py`**: Set `temperature=0.0`. Deterministic fast output.
- **`ai.py`**: Switch grammar LLM to `llama-3.3-70b-versatile`. 8b model act like chatbot, ignore format prompt. 70B follow grammar-only pipeline.
- **`ai.py`**: Add `CRITICAL INSTRUCTION: YOU ARE NOT A CHATBOT` guard. Block conversational bleed.
- **`ai.py`**: Reduce `_MAX_TOKENS` 1000 → 500. Dictation bursts short.
- **`transcription.py` & `ai.py`**: Add `_eager_init()` daemon thread. Groq clients instantiate in background on launch. Eliminate ~1s HTTPS handshake delay.

### Reliability & Windows Startup Fixes
- **`startup.py`**: Fix registry autostart command. Force `cmd /c "cd /d F:\ANTIGRAVITY\mike && pythonw.exe main.py"`.
- **`main.py` & `dashboard.py`**: Add `os.chdir(_SCRIPT_DIR)` + `sys.path.insert(0, ...)` at top. Fix import resolution for all launch methods.

### Bug Fixes (Hallucination, Rejection & Repetition)
- **`transcription.py`**: Fix short phrase rejection. RMS filter average entire clip volume. Reduce `MIN_RMS` 0.010 → 0.001.
- **`transcription.py`**: Fix "Whisper Loop" (repeating word). Remove `temperature=0.0` constraint. Add strict anti-loop context prompt.
- **`ai.py`**: Fix LLM stutter. Add `frequency_penalty=0.2`, `presence_penalty=0.2`, `temperature=0.3`. Stop word repetition.
- **`engine.py`**: Fix typo. HUD show "Processing…" not "Hiking…".

## [2026-05-06] — Major Stability & Accuracy Pass (7 Fixes)

### FIX 1 — "Recording" → "Listening" Rename
- **`engine.py`**: `"Recording…"` → `"Listening…"`, `"Continuous recording…"` → `"Live…"`, `"Stopping continuous…"` → `"Stopping live…"`.
- **`audio.py`**: Transition logs → `(Listening/Live)`.
- **`hud.py`**: `STATE_LABELS` correct.

### FIX 2 — Latency: Instant Cold Start
- **`audio.py`**: Add `_warmup_audio()` daemon thread. Open/close dummy stream. Force PortAudio init. Zero cold-start delay.
- **`transcription.py` / `ai.py`**: Lazy-init Groq client at module level.

### FIX 3 — Hallucination Flood
- **`audio.py`**: Add 1.2s duration guard in `stop()`. Discard short clips before API call.
- **`transcription.py`**: Add numpy fast RMS gate (threshold 0.008). Run before API call.
- **`transcription.py`**: Expand `HALLUCINATION_BLOCKLIST`. Block `"thank you for watching"`, `"okay."`, `"ok."`, `"mm"`, `","`.
- **`transcription.py`**: Block 1-word result. Mark hallucination.
- **`db.py`**: Add `cleanup_hallucinations()`. Delete bad sessions.
- **`main.py`**: Call cleanup on startup.

### FIX 4 — Dashboard Stats Showing 0
- **`dashboard.py`**: `_refresh_stats()` use Python `datetime.datetime.now()`. SQLite `date('now')` return UTC, break IST queries.
- **`dashboard.py`**: Queries use `substr(created_at,1,10)` + local date string.
- **`dashboard.py`**: Stat cards add `setMinimumWidth(140)`. Reduce font 28px. Prevent text clip.

### FIX 5 — Silent Startup Crashes
- **`main.py`**: Add `_show_error()` tkinter dialog. Show error on fail.
- **`main.py`**: Wrap startup steps in `try/except`. DB/engine fail → dialog + exit. Hotkey/tray fail → non-fatal.

### FIX 6 — Pill Rendering
- **`hud.py`**: Confirm pill use Pillow Canvas + 3× supersample + LANCZOS downscale. Set DPI per-monitor v2. Anti-aliased edges.

### FIX 7 — Hotkeys
- **`hotkeys.py`**: Confirm `GetAsyncKeyState` loop. Drop pynput. Require Ctrl+Win release before stop PTT. Prevent OS bounce.

## [2026-05-06] — Stability & Hallucination Fixes

### Fixed — LLM Conversational Hallucinations
- **`ai.py`**: Add negative constraint to `_SEMI_FORMAL_PROMPT` and `_POLISHED_PROMPT`. Ban conversational filler. Prevent trailing sentence autocomplete.

### Fixed — Hotkey Bounce
- **`hotkeys.py`**: Windows key intercept cause rapid toggle trigger. Spawn multiple threads → double paste. Require BOTH Ctrl+Win release before stop.

### Fixed — Background Noise Hallucinations
- **`transcription.py`**: Increase silence gate `MIN_RMS` 0.005 → 0.010. Fan noise trigger continuous mode → hallucination.

## [2026-05-04] — Critical Pipeline Fix & Polish Pass

### Fixed — HUD Status Messages
- **`hud.py`**: `_process_queue()` miss `"msg"` handler. Engine emit "Processing…" but HUD drop. Add `elif kind == "msg": self._show_status_text(data)`. Pill show "Listening…", "Processing…" real time.

### Fixed — Sound Effects
- **`sounds.py`**: Rewrite. Replace numpy/sounddevice with `winsound.Beep()`. Fix PortAudio thread stall. Zero-dependency. Work while mic open.

### Fixed — DPI Awareness
- **`hud.py`**: `SetProcessDpiAwareness(1)` → `SetProcessDpiAwareness(2)`. Match `main.py`. Fix blurry pill.

### Changed — "Processing" → "Hiking"
- **`engine.py` & `hud.py`**: `"Processing…"` / `"Polishing…"` → `"Hiking…"`.

### Fixed — Dashboard Stat Label Redundancy
- **`dashboard.py`**: Label `"Minutes saved"` → `"Time saved"`. Fix "198m saved Minutes saved" redundancy.

---

## [2026-05-04] — Full Diagnostic & Bugfix Pass

### Fixed — BUG 1: Microphone Always On
- **`audio.py`**: Confirm stream open only in `start()`. Close in `stop()`. Add debug print `STREAM OPENED/CLOSED`.

### Added
- **Sound Effects**: Add `sounds.py`. Sine sweep tone. Up on PTT start, down on stop. Soft feedback.

### Fixed — BUG 2 & 6: "Thank You" Hallucinations
- **`transcription.py`**: Add pre-flight guards. 1) Duration < 0.8s discard. 2) RMS < 0.01 discard. 3) 24-entry blocklist (`"thank you"`, `"bye"`). Return `""` silently.
- **`filters.py`**: Update regex. Catch unspaced hallucination. Cleanup artifact.
- Automated tests verify guards.

### Fixed — BUG 3: Hotkeys Not Triggering
- **`hotkeys.py`**: Revert to `GetAsyncKeyState` OS polling. `pynput` drop release event → stuck listen. Polling fix stuck key.

### Fixed — BUG 4: Full Diagnostic
- **`audio.py`**: Confirm no idle stream.
- **`engine.py`**: Strengthen `stop_ptt()` guard. Return immediately if not `RECORDING_PTT`. Prevent API call on `IDLE`.
- **`transcription.py`**: RMS + duration + blocklist guards active.
- **`injection.py`**: Guard whitespace/empty output. Return `True` (no-op). Clipboard save-before-paste + restore active.
- **`filters.py`**: Verify `remove_single_letter_fillers`. Keep valid words.
- **`config.py`**: Confirm frozen build use `LOCALAPPDATA`.
- **`db.py`**: Wrap write in `try/except`. Log error to `mike.log`.

### Fixed — BUG 5: Pill Pixelated
- **`main.py`**: Call `SetProcessDpiAwareness(2)` before import.
- **`hud.py`**: Call `tk scaling` fix. Crisp pill at 125/150/200% scale.

### Fixed — BUG 7: Dashboard Look
- **`dashboard.py`**: Apply `QFont("Segoe UI", 10)`. Apply `QPalette` colors. Add `QMenuBar`. Set window min size. Load `.ico`. Add DPI awareness.

### Fixed — BUG 8: Usage Stats Wrong
- **`db.py`**: Update stats query. Use `COALESCE(SUM, 0)`. Use `date('now', 'localtime')`. Add `time_saved_str` field.
- **`dashboard.py`**: Use `time_saved_str`. Fall back `"0"`.

---

## [2026-05-04] — Hotkeys & Hallucination Patch

### Fixed
- **`filters.py`**: Add `_HALLUCINATIONS` regex. Strip phrase mid-text.
- **`hotkeys.py`**: Replace set-based tracking with `GetAsyncKeyState` polling.
- **`dashboard.py`**: Fix API usage ∞% bug. Format time with hours.

---

## [Unreleased] — Previous Session

### Added
- **List Detection**: Convert spoken list to numbered list.
- **DPI Awareness**: `SetProcessDpiAwareness(1)` crisp UI.
- **Custom App Identity**: `SetCurrentProcessExplicitAppUserModelID` for taskbar icon.

### Changed
- **Dashboard Redesign**: ElevenLabs design tokens, drop shadow, rounded input, gradient sidebar, Inter/Segoe UI font.
- **HUD Pill Shape**: 3× Pillow render + LANCZOS downscale. Reduce 196px width. Use `[Ctrl]` + `[⊞]` keycaps.
- **AI Prompt**: Rewrite `semi_formal` and `polished` prompt. Preserve intent/tense/voice.

### Fixed
- **HUD Position Drift**: `_position_guard` polling via `wm_geometry()`. Force window back on OS intercept.
- **Crash on Newline Injection**: Auto-detect `\n` in output. Switch to clipboard method.
- **PyQt / Tkinter Conflicts**: Run dashboard in isolated subprocess.

## [2026-05-08] - Dashboard Subprocess & HUD UI Polish

### Fixed - Dashboard Crash (Main Thread Conflict)
- **`engine.py` & `dashboard.py`**: Fix background thread crash. PyQt6 require `QApplication` on main thread. Launch dashboard as isolated subprocess via `subprocess.Popen`. Avoid UI thread conflict.
- **`dashboard.py`**: Add standalone `__main__` entry point. Accept DB path arg.
- **`engine.py`**: Resolve `python.exe` interpreter dynamically for frozen PyInstaller exe.

### Fixed - HUD Pill Aesthetics & Position
- **`hud.py`**: Restore high-quality anti-aliased pill. Corners show black rectangle fix. Re-enable `-transparentcolor` chromakey (`#010101`). Set `smooth=True` on canvas polygon. Increase arc steps 32.
- Reduce pill size (Silent: `68x16`, Hover: `148x50`, Recording: `152x30`).
- Lower HUD position. Reduce `MARGIN_BOTTOM` to `22px`. Rest above taskbar.

### Fixed - Dashboard Settings Visibility
- **`dashboard.py`**: Settings button (`Save Key`, `Show`, `Save`) unreadable dark text on dark bg. Update `QSS_MAIN` stylesheet. `pill_btn` and `ghost_btn` explicitly use near-white text (`#f5f4f2`).

### Changed - HUD Icons
- **`hud.py`**: Replace ASCII placeholder in hover state with Segoe UI symbol.
  - `*` (Settings) → `⚙` (U+2699 Gear)
  - `#` (Dashboard) → `≡` (U+2261 Triple Bar Menu)
