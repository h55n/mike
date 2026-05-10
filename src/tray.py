"""
tray.py — System Tray Icon (pystray)
"""
import threading
import logging
import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger("mike.tray")


def _make_icon_image() -> Image.Image:
    """Generate a simple tray icon programmatically if assets not found."""
    try:
        return Image.open("assets/tray_icon.png").resize((64, 64))
    except Exception:
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Dark rounded pill
        d.ellipse([4, 16, 60, 48], fill="#1c1917", outline="#4a4540", width=2)
        # Mic dot
        d.ellipse([28, 26, 36, 38], fill="#f5f4f2")
        return img


class TrayIcon:
    def __init__(self, engine):
        self.engine = engine
        self._icon  = None

    def start(self):
        """Run tray icon (blocks — call in background thread)."""
        img = _make_icon_image()

        def mode_checked(mode):
            return lambda item: self.engine.mode == mode

        menu = pystray.Menu(
            pystray.MenuItem("Mike", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Raw",
                lambda i, it: self.engine.set_mode("raw"),
                checked=mode_checked("raw"),
                radio=True,
            ),
            pystray.MenuItem(
                "Semi-Formal",
                lambda i, it: self.engine.set_mode("semi_formal"),
                checked=mode_checked("semi_formal"),
                radio=True,
            ),
            pystray.MenuItem(
                "Polished",
                lambda i, it: self.engine.set_mode("polished"),
                checked=mode_checked("polished"),
                radio=True,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Dashboard", lambda i, it: self.engine.open_dashboard(), default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit Mike", self._quit),
        )

        self._icon = pystray.Icon("mike", img, "Mike — Voice Dictation", menu)
        self._icon.run()

    def _quit(self, icon, item):
        icon.stop()
        self.engine.shutdown()
        import os, sys
        os._exit(0)

    def update_icon(self, state: str):
        """Swap icon based on state (optional visual feedback in tray)."""
        pass
