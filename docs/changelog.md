# Mike — Changelog

## [v2.4.1] — 2026-06-25 — Hotfixes & Linting

### Fixed
- **`export_btn` NameError**: Fixed a critical crash where the dashboard would fail to launch due to `export_btn` being undefined. Properly initialized the search and export buttons within the Sessions layout.
- **Linting & Hygiene**: Addressed unused PyQt6 imports and missing f-string placeholders highlighted by flake8.

---

## [v2.4.0] — 2026-06-25 — Mode Dark Editorial UI Revamp

### Added
- **Mode Dark Editorial design system**: Full dashboard UI revamp using the project's official design spec. Deep forest-green surfaces (`#0f2f25`), ivory text (`#eef2e3`), editorial serif headlines (Georgia/Times New Roman), Graphik-style utility labels (Segoe UI), and a controlled palette of `#043f2e` / `#121212` / `#374151`.
- **Signature chime sound**: `mike_chime.mp3` now plays on mic ON (25% volume) and mic OFF (15% volume) via `pygame.mixer`. Falls back gracefully to synthetic sine tones → `winsound.Beep`.
- **Project organisation**: `mike initiation sound.mp3` moved to `assets/mike_chime.mp3`; `mike design.md` moved to `docs/design.md`. Root directory cleaned of `error.txt`.

### Changed
- **`dashboard.py`**: Complete rewrite. New design tokens, 4-wide stat card row (serif numbers + Graphik overline labels), session rows with dark surface and ivory text, primary buttons (ivory fill/dark green text/4px radius/50px height), sidebar with left-border active nav indicator, ComboBox and DateEdit matching input card style.
- **`setup_wizard.py`**: Redesigned to match the Mode Dark Editorial palette. Fixed stylesheet accumulation bug (border state now set via a clean base style string, never appended).
- **`sounds.py`**: Rewritten to use `mike_chime.mp3` at reduced volume. Three-tier fallback: `pygame` → `sounddevice` → `winsound.Beep`.
- **`requirements.txt`**: Added `pygame` for MP3 playback.

### Fixed
- **Refresh timer leak on close**: `DashboardWindow.closeEvent()` now cancels the 10-second refresh `QTimer` before the window is destroyed.
- **Status label lambda capture**: `_set_status()` reset callback moved to a named method `_reset_status()` — eliminates the mutable-closure edge case.
- **API key input border accumulation**: `_reset_key_input_style()` helper replaces the inline lambda, ensures clean stylesheet replacement.
- **Toggle key visibility**: Extracted to `_toggle_key_visibility()` method for clarity and testability.

---

## [v2.3.0] — 2026-05-25 — Full Audit Pass

### Fixed (Security)
- **API key exposed in committed config.json**: The live Groq API key was committed to the repository. The committed `config.json` is now blanked to a template. The `.gitignore` already excludes the file; the live key lives only in `%LOCALAPPDATA%\Mike\config.json`.

### Fixed (Critical)
- **`setup_wizard.py` missing**: Referenced in `main.py` but the file did not exist. First-run setup would silently fail (caught in a try/except), leaving users with no API key and a broken app. A full PyQt6 first-run wizard is now implemented.
- **`datetime.fromisoformat()` crash on session rows**: SQLite stores timestamps as `"YYYY-MM-DD HH:MM:SS"` (space separator). Python < 3.11 requires `"T"` as the ISO 8601 separator. Every `SessionRow` in the dashboard could crash on render, silently hiding all session history. Fixed with `.replace(" ", "T")` normalization.

### Fixed (Audio / UX)
- **PTT audio feedback missing**: `sounds.play_start()` / `play_stop()` were implemented but never called. PTT start/stop now plays the chimes as intended.
- **HUD position not restored**: HUD saves `hud_x`/`hud_y` on drag but never read them back at startup — the HUD always appeared centered. Position is now restored from settings on launch, clamped to screen bounds.

### Fixed (Hygiene)
- **`print()` used in production paths**: `sounds.py` and `dashboard.py` used `print()` for error reporting. All replaced with `logging` so errors appear in `mike.log`.

### Changed
- **PyInstaller spec updated**: Added `setup_wizard`, `sounds`, `winsound` as hidden imports; bundled `src/` into the exe so the dashboard subprocess can locate all modules.
- **`.gitignore` extended**: `Mike-Console.spec`, `_check_syntax.py`, `error.txt` added.

---

## [v2.2.1] — 2026-05-23 — Silent Crash Hotfix


### Fixed
- **PyInstaller Windowless Crash**: Fixed a critical bug where `Mike.exe` crashed silently and immediately on launch. PyInstaller's windowless mode (`--noconsole`) nullifies `sys.stdout`. The Python `logging.StreamHandler(sys.stdout)` constructor was throwing a fatal exception before any logs could be written to disk. The handler is now safely conditionally added only if `sys.stdout` is present.

---

## [v2.2.0] — 2026-05-23 — Hotkey Reliability & Production Polish

### Fixed (Critical)
- **Ghost key PTT triggers**: The single biggest bug — when another app stole focus mid-hold, pynput missed the key-up event and left Ctrl/Shift permanently in the `_pressed` set. Any subsequent keypress (ANY key) would then immediately fire PTT recording. Fixed by adding a **Win32 `GetAsyncKeyState` physical verification** layer that confirms keys are actually held on hardware before PTT commits.
- **PTT fires on just Ctrl (or just Shift)**: Was possible when ghost keys accumulated over multiple focus changes. The physical verification ensures both Ctrl AND Shift must be physically down simultaneously.
- **Stuck recording (infinite loop)**: If the key-up event for Ctrl or Shift was missed entirely, the app would record forever with no way to stop it except Kill Mike. Fixed with a **30-second PTT watchdog timer** that auto-releases and transcribes if no key-up arrives.
- **Audio `input overflow` spam**: The log was flooding with WARNING-level overflow messages every few seconds during processing. Overflow is a normal artifact of audio buffering — now logged at DEBUG level only.
- **Double PTT fires from rapid key presses**: Debounce raised from 200 ms → 400 ms to eliminate rapid double-starts visible in the logs.
- **`shift_l` not recognized on some keyboards**: Added `keyboard.Key.shift_l` to the SHIFT_KEYS set alongside `shift` and `shift_r`. Some keyboards and layouts emit the explicit `shift_l` variant.
- **Continuous mode × button unresponsive**: Direct `_stop_continuous()` call (no debounce) was already in place; confirmed working correctly.

### Added
- **Ghost-key cleanup background thread**: Every 500 ms, cross-checks the pynput `_pressed` set against Win32 physical state and evicts any stale entries. Also auto-releases any stuck PTT that Win32 confirms is no longer physically held.
- **PTT watchdog timer (30 s safety net)**: Prevents permanently-stuck silent recording sessions when key-up events are missed due to focus changes, screen locks, or OS-level interrupts.
- **Physical key re-verification on release**: The `_on_release` handler now double-checks via `GetAsyncKeyState` before stopping PTT — prevents stopping when an unrelated key is released.
- **Ctrl+Shift+Space window extended**: 120 ms → 200 ms gives more time for Space to arrive and correctly route to continuous toggle instead of PTT.

### Changed
- **Minimum PTT debounce raised**: 200 ms → 400 ms.
- **Minimum voice frames lowered**: 6 → 4 (~0.25 s of speech). Short words like "yes", "no", "go" were sometimes being dropped.
- **Minimum avg RMS threshold lowered**: 100 → 80 to capture quieter speakers more reliably.
- **Build**: Version bumped to `2.2.0`.

---

## [v2.1.0] — 2026-05-17 — Mic Kill Switch & Startup Fix

### Added
- **Mic Kill Switch (Dashboard)**: Two new buttons in the dashboard sidebar under "MIC CONTROLS":
  - **⏹ Kill Mike** (red) — sends `KILL_MIC` UDP signal to the main Mike process. This now completely shuts down the Mike background engine (`os._exit(0)`) to ensure all processes and hooks are cleared. The dashboard UI remains open.
  - **▶ Wake Mike** (green) — if Mike is running but glitched, sends `WAKE_MIC` signal to reset all engine state. If Mike's process is completely dead (crashed or intentionally killed), automatically relaunches `Mike.exe` from the install directory.
- **Mic Kill Switch (System Tray)**: Right-click the tray icon now shows:
  - Live mic state label (e.g. `● Mic: Idle`, `🔴 Mic: LIVE`, `⏸ Mic: Paused`)
  - **⏹ Stop Mic / Kill Live** menu item — calls `force_stop_mic()` instantly from any state.
- **`engine.force_stop_mic()`**: New nuclear kill method. Stops all recording/continuous threads, resets `_ptt_active`, calls `audio.stop_capture()`, forces state to IDLE. Bypasses all debounce guards.
- **`engine.wake_mic()`**: New reset method. Calls `force_stop_mic()`, then replaces `_cont_stop`/`_cont_pause` events with fresh ones and resets the toggle debounce timer — so continuous mode can be started cleanly again.
- **UDP Signals**: Main process signal listener now handles two new signals:
  - `KILL_MIC` — cleanly shuts down the engine and exits the background application completely (`os._exit(0)`).
  - `WAKE_MIC` — calls `engine.wake_mic()` in a daemon thread.

### Fixed
- **PyInstaller Subprocess Crashes ("Tcl data directory not found")**: Fixed a critical bug where launching or waking the app from the dashboard caused fatal PyInstaller extraction errors. Stripped `_MEIPASS` and `TCL_LIBRARY` environment variables before spawning child processes to prevent temporary folder collisions and file-locking issues.
- **HUD × button debounce (continuous mode)**: `_on_stop_continuous` previously called `toggle_continuous()` which has a hard 2-second guard. If the user tapped × too soon after the mode started, the click was silently dropped. Fixed to call `engine._stop_continuous()` directly — no debounce, always works.
- **HUD X button (recording/processing)**: `_on_cancel` now calls `engine.force_stop_mic()` instead of `cancel_recording()`. If the engine was in continuous mode (not PTT), the old cancel had no effect. Nuclear kill handles both.
- **Startup registry — early registration**: `add_to_startup()` now runs immediately after Config/DB load (before engine build). Previously it ran at step 6, meaning a crash anywhere in between left the registry stale. Double-called at step 6 as belt-and-suspenders.

### Changed
- **Dashboard sidebar**: Added "MIC CONTROLS" section with Kill Mike and Wake Mike buttons above the status dot.
- **Dashboard status feedback**: Status dot shows contextual messages (e.g. "⏹ Mike killed", "▶ Wake signal sent", "⚠ Mike not running") that auto-reset to "● Active" after 3 seconds.
- **Build**: Version bumped to `2.1.0`.

---

## [2026-05-10] — Structural Refactor & Dashboard Fixes

### Changed
- **Repository Structure**: Reorganized files into a standard `src/`, `scripts/`, `docs/`, and `assets/` structure for a cleaner GitHub presence. Removed old `.db` files from root.
- **API Key Handling**: Fixed `dashboard.py` to correctly load and save the Groq API key using the standard `config.json` file instead of the local SQLite database.

### Fixed
- **GitHub README Logo**: Corrected the logo path in `README.md` to point to `assets/Mike.svg` so it renders properly on the repository page.

## [2026-05-10] — GitHub Release & Continuous Mode Polish

### Added
- **GitHub Repository**: Initialized repo, added `.gitignore`, `LICENSE`, `config.example.json`, and comprehensive `README.md`.
- **Continuous Mode HUD Button**: Added a clickable red `×` button on the continuous mode HUD to instantly stop continuous recording.
- **Symbol Expansion**: Added `_expand_symbols()` in `filters.py`. Spoken phrases like "degree symbol" or "plus minus" are automatically converted to their Unicode characters (90+ supported).

### Fixed
- **Continuous Mode Double-Fire**: Fixed a bug where `Ctrl+Shift+Space` would trigger multiple times due to OS key-repeat. Added a monotonic sequence counter (`_toggle_seq`) and a 2-second cooldown to `toggle_continuous` in `engine.py`.
- **Ambient Noise Rejection**: Fixed continuous mode transcribing silence and background noise. Raised `MIN_VOICE_FRAMES` to `6` and added `MIN_AVG_RMS = 100` to `audio.py` to ensure only clear speech is processed.
- **Continuous Mode Stuck IDLE**: Fixed an issue in `engine.py` where continuous mode would drop to `IDLE` state between audio chunks. It now properly restores `RECORDING_CONT` after processing a chunk.
- **Global Hotkey Interception**: Reverted from Windows `WH_KEYBOARD_LL` hook back to `pynput` because the low-level hook failed inside PyInstaller frozen executables.

### Changed
- **Hotkeys**: Push-to-Talk is now `Ctrl+Shift` (hold). Continuous mode is `Ctrl+Shift+Space`. This bypasses Windows OS-level hotkey interference (like language switching).
- **PTT Timer Delay**: Added a 120ms delay to `Ctrl+Shift` PTT start to allow the user to press `Space` for continuous mode without triggering a conflict between the two modes.

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
