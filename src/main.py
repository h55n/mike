"""
main.py — Mike Entry Point
Startup order:
  1. DPI awareness (must be before any UI)
  2. Logging setup
  3. Config + DB
  4. First-run wizard if no API key
  5. Build engine + modules
  6. Hotkey listener (background thread)
  7. Tray icon (background thread)
  8. Startup registry refresh
  9. HUD (main thread — tkinter requires main thread)
"""

import sys
import os
import io
import threading
import logging
import pathlib
import ctypes
import socket

# ─── Force CWD to script dir (fixes relative imports on registry/startup launch)
_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
os.chdir(_SCRIPT_DIR)
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# ─── DPI awareness (must be before any window creation) ───────────────────────
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)   # Per-monitor v2
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# ─── Fix stdout encoding for Windows console ──────────────────────────────────
if sys.stdout and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# ─── Logging setup ────────────────────────────────────────────────────────────
LOG_DIR = pathlib.Path.home() / "AppData" / "Local" / "Mike"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "mike.log", encoding="utf-8", mode="a"),
    ],
)
logger = logging.getLogger("mike.main")


def _show_error(title: str, msg: str):
    """Show a user-visible error dialog (tkinter fallback)."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, msg)
        root.destroy()
    except Exception:
        logger.error(f"[{title}] {msg}")



def _launch_dashboard_standalone():
    """Show dashboard as standalone window (no engine). For --dashboard flag."""
    logger.info("Dashboard standalone mode")
    try:
        from PyQt6.QtWidgets import QApplication
        import sys
        import pathlib
        import sqlite3

        # Locate DB
        db_path_str = ""
        if len(sys.argv) > 2:
            db_path_str = sys.argv[2]
        if not db_path_str:
            db_path_str = str(pathlib.Path.home() / "AppData" / "Local" / "Mike" / "mike.db")

        # Import db module for dashboard
        from db import Database
        db = Database()

        from dashboard import DashboardWindow
        app = QApplication.instance() or QApplication(sys.argv)
        win = DashboardWindow(db_ref=db)
        win.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Dashboard standalone failed: {e}", exc_info=True)
        _show_error("Mike — Dashboard Error", f"Failed to open dashboard:\n\n{e}")
        sys.exit(1)


def main():
    logger.info("-" * 60)
    logger.info("Mike starting...")
    logger.info(f"CWD: {os.getcwd()}")
    logger.info(f"Args: {sys.argv[1:]}")

    # ── 0. Single Instance Lock ────────────────────────────────────────────
    PORT = 44556
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        lock_socket.bind(("127.0.0.1", PORT))
    except OSError:
        # Already running! Signal the primary instance and exit
        logger.info("Mike is already running. Sending dashboard signal and exiting.")
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.sendto(b"OPEN_DASHBOARD", ("127.0.0.1", PORT))
        client.close()
        sys.exit(0)

    # ── 1. Config + DB ─────────────────────────────────────────────────────
    try:
        from config   import Config
        from db       import Database
        from settings import Settings

        config   = Config()
        db       = Database()
        settings = Settings(db)
    except Exception as e:
        _show_error("Mike — Startup Error", f"Failed to load config/database:\n\n{e}")
        sys.exit(1)

    # ── 1b. Startup registry ────────────────────────────────────────────────
    # Run early so registry is always current even if later steps crash.
    try:
        from startup import add_to_startup
        add_to_startup()
        logger.info("Startup registry refreshed (early)")
    except Exception as e:
        logger.warning(f"Startup registry (early): {e}")

    # ── 2. First-run wizard if no API key ──────────────────────────────────
    if not config.is_api_key_set():
        logger.info("No API key — showing setup wizard")
        try:
            from setup_wizard import show_setup_wizard
            key = show_setup_wizard()
            if key:
                config.set("groq_api_key", key)
                logger.info("API key saved")
            else:
                logger.warning("API key not set — transcription will fail.")
        except Exception as e:
            logger.warning(f"Setup wizard error: {e}")

    # ── 3. Build engine modules ────────────────────────────────────────────
    try:
        from audio        import AudioCapture
        from transcription import TranscriptionService
        from filters      import TextFilter
        from ai           import AIProcessor
        from injection    import TextInjector
        from engine       import MikeEngine

        audio         = AudioCapture(config)
        text_filter   = TextFilter()
        transcription = TranscriptionService(config)
        ai            = AIProcessor(config, filters=text_filter)
        injector      = TextInjector(config)

        engine = MikeEngine(
            config=config,
            audio=audio,
            transcription=transcription,
            ai=ai,
            filters=text_filter,
            injection=injector,
            db=db,
            settings=settings,
        )
    except Exception as e:
        _show_error("Mike — Startup Error", f"Failed to initialize engine:\n\n{e}")
        sys.exit(1)

    # Start the single instance listener thread
    def listen_for_signals():
        while True:
            try:
                data, _ = lock_socket.recvfrom(1024)
                if data == b"OPEN_DASHBOARD":
                    logger.info("Received OPEN_DASHBOARD signal")
                    engine.open_dashboard()
                elif data == b"KILL_MIC":
                    logger.info("Received KILL_MIC signal — force stopping mic")
                    engine.force_stop_mic()
                elif data == b"WAKE_MIC":
                    logger.info("Received WAKE_MIC signal — waking engine")
                    threading.Thread(target=engine.wake_mic, daemon=True).start()
            except Exception as e:
                logger.error(f"Signal listener error: {e}")

    threading.Thread(target=listen_for_signals, daemon=True).start()

    # If launched manually by user, open dashboard immediately
    if "--startup" not in sys.argv:
        engine.open_dashboard()

    # Restore saved mode
    saved_mode = settings.get("active_mode", config.get("default_mode", "raw"))
    engine.mode = saved_mode
    logger.info(f"Mode: {saved_mode}")

    # ── 4. Hotkey listener ─────────────────────────────────────────────────
    try:
        from hotkeys import HotkeyListener
        hotkeys = HotkeyListener(engine)
        hotkeys.start()
        logger.info("Hotkeys: Ctrl+Shift (PTT hold) | Ctrl+Shift+Space (Continuous toggle)")
    except Exception as e:
        logger.error(f"Hotkey listener failed: {e} — app will still work via tray")
        hotkeys = None

    # ── 5. System tray ────────────────────────────────────────────────────
    try:
        from tray import TrayIcon
        tray = TrayIcon(engine)
        tray_thread = threading.Thread(target=tray.start, daemon=True)
        tray_thread.start()
        logger.info("Tray icon started")
    except Exception as e:
        logger.error(f"Tray icon failed: {e}")

    # ── 6. Startup registry refresh (secondary — belt-and-suspenders) ─────────
    # Already ran early above; this second call ensures any late path changes land.
    try:
        from startup import add_to_startup
        add_to_startup()
    except Exception:
        pass

    # ── 7. HUD (must be on main thread) ───────────────────────────────────
    try:
        from hud import MikeHUD
        hud = MikeHUD(engine_ref=engine)
        engine.hud = hud
        hud.set_mode(saved_mode)
    except Exception as e:
        _show_error("Mike — HUD Error", f"Failed to create HUD:\n\n{e}")
        sys.exit(1)

    logger.info("Mike is ready")
    logger.info(f"Config: {config.path}")
    logger.info(f"Database: {db.path}")
    logger.info("-" * 60)

    try:
        hud.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt — shutting down")
    except Exception as e:
        logger.error(f"HUD crashed: {e}", exc_info=True)
    finally:
        engine.shutdown()
        if hotkeys:
            hotkeys.stop()
        logger.info("Mike stopped")


if __name__ == "__main__":
    if "--dashboard" in sys.argv:
        _launch_dashboard_standalone()
    else:
        main()
