<div align="center">

<img src="Mike.svg" width="120" alt="Mike Logo" />

# Mike

**AI-powered voice dictation for Windows — speak anywhere, instantly.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Powered%20by-Groq-F55036?style=flat-square)](https://groq.com)
[![Whisper](https://img.shields.io/badge/ASR-Whisper-00A67E?style=flat-square)](https://openai.com/research/whisper)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D4?style=flat-square&logo=windows)](https://microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## What is Mike?

Mike is a **global voice dictation engine** that runs silently in your Windows system tray and transcribes your speech into any application — email, browser, code editor, Slack, anywhere. No clicks, no switching focus. Just press a hotkey and talk.

It uses **Groq's Whisper API** for near-instant transcription (typically under 500ms) and optionally polishes your speech through an AI language model to produce clean, professional text.

**Mike runs at startup, lives in the tray, and stays out of your way.**

---

## Features

| Feature | Details |
|---------|---------|
| 🎙️ **Push-to-Talk** | Hold `Ctrl+Shift`, speak, release — text appears at cursor |
| 🔁 **Continuous Mode** | Toggle `Ctrl+Shift+Space` — mic stays live, transcribes every 5s |
| 🧠 **AI Polishing** | Three modes: Raw, Semi-formal, Polished — cleans up your speech |
| 💬 **Symbol Expansion** | Say "degree symbol" → `°`, "plus minus" → `±`, "copyright symbol" → `©` |
| 🖥️ **Floating HUD** | Minimal pill above taskbar shows recording state and waveform |
| 📊 **Dashboard** | Full history, session stats, settings — one click from tray |
| 🚀 **Startup** | Registers itself to launch with Windows — always ready |
| 🪟 **Silent** | No terminal, no console — runs invisibly in the background |

---

## Hotkeys

| Action | Hotkey |
|--------|--------|
| Push-to-Talk (hold to record) | **Ctrl + Shift** |
| Toggle Continuous Mode | **Ctrl + Shift + Space** |
| Open Dashboard | Click tray icon → Dashboard |
| Cycle dictation mode | Click mode badge on HUD |

---

## HUD States

The floating pill above your taskbar tells you what Mike is doing:

| State | Appearance |
|-------|-----------|
| **Silent** | Tiny dark pill with mic dot — app is alive and listening |
| **Hover** | Expands to show hotkey hint and controls |
| **Recording** | Waveform animation — actively capturing audio |
| **Continuous** | Green border, **LIVE** badge, pulsing dot |
| **Processing** | Spinner — transcribing and injecting text |

---

## Dictation Modes

| Mode | What it does |
|------|-------------|
| **RAW** | Transcribes exactly what you say, minimal processing |
| **SF** *(Semi-formal)* | Cleans grammar, removes filler words, professional tone |
| **POL** *(Polished)* | Full AI rewrite — structured, publication-ready prose |

Switch modes by clicking the **RAW / SF / POL** badge on the HUD, or via the Dashboard Settings tab.

---

## Symbol Expansion

Say any of these phrases and Mike will type the actual symbol:

| Say | Get | | Say | Get |
|-----|-----|-|-----|-----|
| "plus minus symbol" | ± | | "copyright symbol" | © |
| "degree symbol" | ° | | "trademark symbol" | ™ |
| "right arrow" | → | | "check mark" | ✓ |
| "infinity symbol" | ∞ | | "not equal" | ≠ |
| "square root" | √ | | "approximately" | ≈ |
| "euro symbol" | € | | "bullet point" | • |
| "em dash" | — | | "dot dot dot" | … |

---

## Requirements

- **OS**: Windows 10 or 11
- **Python**: 3.11+ (for building from source)
- **Microphone**: Any input device supported by Windows
- **API Key**: [Groq API key](https://console.groq.com) (free tier available)

### How to get a Groq API Key
1. Go to the [Groq Console](https://console.groq.com) and create a free account.
2. Click on **API Keys** in the left sidebar.
3. Click the **Create API Key** button.
4. Name your key (e.g., "Mike Dictation") and copy the generated key (it starts with `gsk_...`).
5. Open Mike's Dashboard → **Settings**, paste your key, and click **Save**.

---

## Installation

### Option A — Build from source (recommended)

**1. Clone the repo**
```bash
git clone https://github.com/yourusername/mike.git
cd mike
```

**2. Set up your API key**
```bash
cp config.example.json config.json
# Edit config.json and paste your Groq API key
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

**3. Run the build & install script**
```powershell
powershell -ExecutionPolicy Bypass -File build_and_install.ps1
```

This script will:
- Install Python dependencies in a virtualenv
- Generate crisp icons from SVG sources
- Build `Mike.exe` via PyInstaller (~91MB, fully self-contained)
- Install to `%LOCALAPPDATA%\Programs\Mike\`
- Create Desktop and Start Menu shortcuts
- Register Mike to launch at Windows startup
- Start Mike immediately

**Total time: ~3 minutes**

### Option B — Pre-built binary

Download `Mike.exe` from [Releases](https://github.com/yourusername/mike/releases) and run it. On first launch it will ask for your Groq API key via the Dashboard settings.

---

## First Run

After installation:

1. Mike starts automatically and appears as a small dark pill near the center of your taskbar
2. Click the tray icon (bottom-right) to open the Dashboard
3. Go to **Settings** → paste your Groq API key → Save
4. Press **Ctrl+Shift** and start talking

---

## How It Works

```
You speak
    ↓
Microphone (sounddevice, 16kHz mono)
    ↓
Voice Activity Detection (RMS threshold filter)
    ↓
Groq Whisper API (transcription, <500ms)
    ↓
Text Filter (filler removal, symbol expansion, dedup)
    ↓
AI Polish (optional — Groq LLaMA via chat completions)
    ↓
pyautogui.typewrite() → text appears at cursor
```

### Architecture

| File | Role |
|------|------|
| `main.py` | Entry point, startup flags, single-instance lock, orchestration |
| `engine.py` | State machine — IDLE / PTT / CONTINUOUS / PROCESSING |
| `hotkeys.py` | Global hotkey listener (pynput), timer-deferred PTT |
| `audio.py` | Mic capture, VAD, 16kHz WAV encoding |
| `transcription.py` | Groq Whisper API client |
| `ai.py` | Groq LLaMA polishing (semi-formal / polished modes) |
| `filters.py` | Text cleaning, symbol expansion, filler removal |
| `injection.py` | Keyboard text injection via pyautogui |
| `hud.py` | Floating Tkinter HUD pill — 4 animated states |
| `dashboard.py` | PyQt6 dashboard — history, stats, settings |
| `tray.py` | pystray system tray icon and menu |
| `db.py` | SQLite history database |
| `startup.py` | Windows registry auto-start |

---

## Configuration

`config.json` (created at `%LOCALAPPDATA%\Mike\config.json`):

```json
{
  "groq_api_key": "gsk_...",
  "mode": "semi_formal",
  "continuous_chunk_seconds": 5,
  "language": "en"
}
```

| Key | Values | Default |
|-----|--------|---------|
| `groq_api_key` | Your Groq API key | — |
| `mode` | `raw` / `semi_formal` / `polished` | `semi_formal` |
| `continuous_chunk_seconds` | `3`–`10` | `5` |
| `language` | `en` / `hi` / `ur` / any Whisper lang code | `en` |

---

## Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File uninstall.ps1
```

This removes the exe, shortcuts, and registry startup entry. Your config and history are preserved.

---

## Troubleshooting

**Mike doesn't start**
- Check `%LOCALAPPDATA%\Mike\mike.log` for errors
- Ensure your Groq API key is valid at [console.groq.com](https://console.groq.com)

**Hotkeys not triggering**
- Make sure Mike is running (check system tray)
- Ctrl+Shift may be grabbed by Windows language switcher if you have multiple input languages — try removing extra languages from Windows settings

**Audio rejected / nothing transcribed**
- Speak for at least 0.3 seconds
- Check your default microphone in Windows Sound settings

**Text appears in wrong place**
- Click your target text field first, then press the hotkey

---

## Building

Dependencies are listed in `requirements.txt`. Key ones:

```
groq
pynput
PyQt6
pystray
sounddevice
scipy
numpy
pyautogui
cairosvg
pillow
pyinstaller
```

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

Built with ❤️ using [Groq](https://groq.com) · [Whisper](https://openai.com/research/whisper) · [Python](https://python.org)

**Made by h55n**

</div>
