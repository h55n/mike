"""
dashboard.py — Mike Dashboard  v2.4.0
Design: Mode Dark Editorial — deep forest-green surface, ivory text,
        serif headlines, Graphik-style utility labels.
"""

import sys
import os
import socket
import subprocess
import pathlib
import datetime
import logging
from paths import app_root, asset_path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QComboBox,
    QDateEdit, QFileDialog, QTextEdit, QStackedWidget,
)
from PyQt6.QtCore import (
    Qt, QDate, QTimer, QSize,
)
from PyQt6.QtGui import (
    QFont, QColor, QIcon,
)

logger = logging.getLogger("mike.dashboard")


# ─── Design Tokens (Mode Dark Editorial) ─────────────────────────────────────
# Core palette
_PRIMARY      = "#043f2e"   # deep forest-green — brand/accent
_SECONDARY    = "#eef2e3"   # soft ivory — primary text on dark
_TERTIARY     = "#121212"   # near-black page canvas
_SURFACE      = "#0f2f25"   # deep green surface for sidebar / panels
_BORDER       = "#374151"   # cool low-contrast divider
_MUTED        = "#9ca3af"   # secondary/metadata text
_ERROR        = "#d96b6b"   # muted red for errors/destructive
_NEUTRAL      = "#f5f4ef"   # quieter off-white

# Derived interaction shades
_SURFACE_HOVER   = "#163d2e"   # slightly lighter green for hover
_CARD_BG         = "#121212"   # card interior
_CARD_HOVER      = "#191919"   # card hover
_SIDEBAR_BG      = "#0a2920"   # deeper than surface
_INPUT_BG        = "#0c0c0c"   # input fields
_PRIMARY_HOVER   = "#065a40"   # button hover

# Mode badge colors (kept distinct but tonal)
_MODE_COLORS = {
    "raw":        (_MUTED,    "#1a1a1a"),
    "semi_formal": ("#6ee7b7", "#0d2a1e"),
    "polished":   ("#93c5fd", "#0d1a2e"),
}

# ─── Global Stylesheet ────────────────────────────────────────────────────────
QSS_MAIN = f"""
/* ── Root ── */
QMainWindow, QWidget#root {{
    background: {_TERTIARY};
}}
QWidget {{
    font-family: 'Segoe UI', sans-serif;
}}

/* ── Scroll bars ── */
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: {_TERTIARY};
    width: 4px;
    border-radius: 2px;
    margin: 2px 0;
}}
QScrollBar::handle:vertical {{
    background: {_BORDER};
    border-radius: 2px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{
    background: {_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

/* ── Inputs ── */
QLineEdit {{
    background: {_INPUT_BG};
    color: {_SECONDARY};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 14px 16px;
    font-family: 'Times New Roman', serif;
    font-size: 14px;
    selection-background-color: {_PRIMARY};
}}
QLineEdit:focus {{
    border: 1px solid {_MUTED};
    background: #111111;
}}
QLineEdit::placeholder {{
    color: {_MUTED};
}}

/* ── ComboBox ── */
QComboBox {{
    background: {_INPUT_BG};
    color: {_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
    font-weight: 500;
    min-height: 36px;
}}
QComboBox:hover {{
    border: 1px solid {_MUTED};
    color: {_SECONDARY};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}
QComboBox QAbstractItemView {{
    background: #1a1a1a;
    color: {_SECONDARY};
    border: 1px solid {_BORDER};
    selection-background-color: {_PRIMARY};
    selection-color: {_SECONDARY};
    padding: 4px;
    outline: none;
}}

/* ── Buttons ── */

/* Primary: ivory fill, dark green text */
QPushButton#primary_btn {{
    background: {_SECONDARY};
    color: {_PRIMARY};
    border: none;
    border-radius: 8px;
    padding: 17px 30px 16px;
    height: 50px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0px;
}}
QPushButton#primary_btn:hover {{
    background: {_NEUTRAL};
}}
QPushButton#primary_btn:pressed {{
    background: #d8dcc8;
}}

/* Secondary: transparent, ivory text, border */
QPushButton#secondary_btn {{
    background: transparent;
    color: {_SECONDARY};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 17px 30px 16px;
    height: 50px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    font-weight: 500;
}}
QPushButton#secondary_btn:hover {{
    border-color: {_MUTED};
    background: rgba(238,242,227,0.05);
}}

/* Ghost: nav-style smaller button */
QPushButton#ghost_btn {{
    background: transparent;
    color: {_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 10px 20px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#ghost_btn:hover {{
    color: {_SECONDARY};
    border-color: {_MUTED};
    background: rgba(238,242,227,0.04);
}}

/* Copy button */
QPushButton#copy_btn {{
    background: transparent;
    color: {_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 6px 14px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 11px;
    font-weight: 500;
}}
QPushButton#copy_btn:hover {{
    background: rgba(4,63,46,0.3);
    border-color: #6ee7b7;
    color: #6ee7b7;
}}

/* Danger: muted red */
QPushButton#danger_btn {{
    background: rgba(217,107,107,0.12);
    color: {_ERROR};
    border: 1px solid rgba(217,107,107,0.35);
    border-radius: 8px;
    padding: 10px 18px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    font-weight: 500;
    min-height: 38px;
}}
QPushButton#danger_btn:hover {{
    background: rgba(217,107,107,0.22);
    border-color: {_ERROR};
}}

/* Wake: muted green */
QPushButton#wake_btn {{
    background: rgba(4,63,46,0.25);
    color: #6ee7b7;
    border: 1px solid rgba(110,231,183,0.3);
    border-radius: 8px;
    padding: 10px 18px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    font-weight: 500;
    min-height: 38px;
}}
QPushButton#wake_btn:hover {{
    background: rgba(4,63,46,0.40);
    border-color: #6ee7b7;
}}

/* ── Date pickers ── */
QDateEdit {{
    background: {_INPUT_BG};
    color: {_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 6px 10px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
}}
QDateEdit:hover {{ border-color: {_MUTED}; }}
QCalendarWidget {{
    background: #1a1a1a;
    color: {_SECONDARY};
}}
QCalendarWidget QAbstractItemView {{
    background: #1a1a1a;
    color: {_SECONDARY};
    selection-background-color: {_PRIMARY};
}}
"""


# ─── Stat Card ────────────────────────────────────────────────────────────────

class StatCard(QWidget):
    """
    A single stat tile: large serif number + Graphik overline label.
    Styled per Mode Dark Editorial card spec.
    """
    def __init__(self, label: str, value: str, accent: str = _MUTED):
        super().__init__()
        self.accent = accent
        self.setFixedHeight(104)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(6)

        self.val_label = QLabel(str(value))
        self.val_label.setStyleSheet(f"""
            font-family: 'Times New Roman', serif;
            font-size: 36px;
            font-weight: 400;
            color: {_SECONDARY};
            letter-spacing: -1px;
            line-height: 43px;
        """)

        self.lbl_label = QLabel(label.upper())
        self.lbl_label.setStyleSheet(f"""
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            font-weight: 600;
            color: {_MUTED};
            letter-spacing: 0.06em;
        """)

        layout.addWidget(self.val_label)
        layout.addWidget(self.lbl_label)

        self.setStyleSheet(f"""
            StatCard {{
                background: {_CARD_BG};
                border: 1px solid {_BORDER};
                border-radius: 8px;
                border-left: 3px solid {self.accent};
            }}
            StatCard:hover {{
                background: {_CARD_HOVER};
                border: 1px solid {_MUTED};
                border-left: 3px solid {self.accent};
            }}
        """)

    def update_value(self, value: str):
        self.val_label.setText(str(value))


# ─── Mode Badge ───────────────────────────────────────────────────────────────

class ModeBadge(QLabel):
    """High-contrast capsule badge for RAW / SF / POL."""
    _LABELS = {"raw": "RAW", "semi_formal": "SF", "polished": "POL"}

    def __init__(self, mode: str):
        super().__init__()
        fg, bg = _MODE_COLORS.get(mode, (_MUTED, "#1a1a1a"))
        self.setText(self._LABELS.get(mode, mode.upper()))
        self.setFixedSize(42, 22)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {fg};
                border: 1px solid {fg}55;
                border-radius: 9999px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 9px;
                font-weight: 600;
                letter-spacing: 0.06em;
            }}
        """)


# ─── Session Row ──────────────────────────────────────────────────────────────

class SessionRow(QWidget):
    """Expandable session entry — dark surface, ivory text, editorial spacing."""

    def __init__(self, session: dict):
        super().__init__()
        self.session = session
        self.expanded = False
        self._build(session)

    def _build(self, s: dict):
        self.setStyleSheet(f"""
            SessionRow {{
                background: {_CARD_BG};
                border: 1px solid {_BORDER};
                border-radius: 8px;
            }}
            SessionRow:hover {{
                border: 1px solid {_MUTED};
                background: {_CARD_HOVER};
            }}
        """)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 14, 16, 14)
        self.main_layout.setSpacing(10)

        # ── Header row ──────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(10)

        ts_raw = str(s.get("created_at", ""))
        try:
            ts = datetime.datetime.fromisoformat(ts_raw.replace(" ", "T"))
        except Exception:
            ts = None
        time_str = ts.strftime("%b %d  %H:%M") if ts else "—"

        ts_lbl = QLabel(time_str)
        ts_lbl.setStyleSheet(
            f"color: {_MUTED}; font-size: 12px; font-family: 'Segoe UI', sans-serif;"
        )

        badge = ModeBadge(s.get("mode", "raw"))

        stype = s.get("session_type", "dictation")
        type_lbl = QLabel("⚡ PROMPT" if stype == "prompt" else "🎙 DICTATE")
        type_lbl.setStyleSheet(f"""
            color: {'#f472b6' if stype == 'prompt' else _MUTED};
            font-size: 12px;
            font-weight: 600;
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: 0.06em;
        """)

        wc_lbl = QLabel(f"{s.get('word_count', 0)} words")
        wc_lbl.setStyleSheet(
            f"color: {_BORDER}; font-size: 11px; font-family: 'Segoe UI', sans-serif;"
        )

        self.arrow = QLabel("›")
        self.arrow.setStyleSheet(f"color: {_BORDER}; font-size: 18px;")

        header.addWidget(ts_lbl)
        header.addWidget(badge)
        header.addWidget(type_lbl)
        header.addStretch()
        header.addWidget(wc_lbl)
        header.addWidget(self.arrow)
        self.main_layout.addLayout(header)

        # ── Preview ─────────────────────────────────────────────────────────
        preview_text = str(s.get("final_text", ""))[:140]
        if len(str(s.get("final_text", ""))) > 140:
            preview_text += "…"
        self.preview_lbl = QLabel(preview_text)
        self.preview_lbl.setStyleSheet(
            f"color: {_MUTED}; font-size: 13px; "
            f"font-family: 'Times New Roman', serif; line-height: 1.5;"
        )
        self.preview_lbl.setWordWrap(True)
        self.main_layout.addWidget(self.preview_lbl)

        # ── Expanded full text ───────────────────────────────────────────────
        self.full_text = QTextEdit()
        self.full_text.setPlainText(str(s.get("final_text", "")))
        self.full_text.setReadOnly(True)
        self.full_text.setMaximumHeight(180)
        self.full_text.setStyleSheet(f"""
            QTextEdit {{
                background: #0a0a0a;
                color: {_SECONDARY};
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                font-family: 'Times New Roman', serif;
                font-size: 14px;
                line-height: 1.6;
            }}
        """)
        self.full_text.hide()
        self.main_layout.addWidget(self.full_text)

        # ── Copy row (expanded only) ─────────────────────────────────────────
        copy_row = QHBoxLayout()
        copy_row.setContentsMargins(0, 0, 0, 0)
        self.copy_btn = QPushButton("Copy text")
        self.copy_btn.setObjectName("copy_btn")
        self.copy_btn.setFixedHeight(30)
        self.copy_btn.clicked.connect(self._copy_text)
        self.copy_status = QLabel("")
        self.copy_status.setStyleSheet(
            f"color: #6ee7b7; font-size: 11px; font-family: 'Segoe UI', sans-serif;"
        )
        copy_row.addWidget(self.copy_btn)
        copy_row.addWidget(self.copy_status)
        copy_row.addStretch()
        self.copy_row_widget = QWidget()
        self.copy_row_widget.setLayout(copy_row)
        self.copy_row_widget.setStyleSheet("background: transparent;")
        self.copy_row_widget.hide()
        self.main_layout.addWidget(self.copy_row_widget)

        self.mousePressEvent = self._toggle_expand

    def _copy_text(self):
        logger.info("Session text copied to clipboard")
        text = str(self.session.get("final_text", ""))
        QApplication.clipboard().setText(text)
        self.copy_status.setText("Copied!")
        QTimer.singleShot(2000, lambda: self.copy_status.setText(""))

    def _toggle_expand(self, event):
        logger.debug(f"Toggled session row expansion: {not self.expanded}")
        self.expanded = not self.expanded
        self.full_text.setVisible(self.expanded)
        self.copy_row_widget.setVisible(self.expanded)
        self.preview_lbl.setVisible(not self.expanded)
        self.arrow.setText("⌄" if self.expanded else "›")


# ─── Dashboard Window ─────────────────────────────────────────────────────────

class DashboardWindow(QMainWindow):
    def __init__(self, db_ref=None):
        super().__init__()
        from config import Config
        self.config = Config()
        self.db = db_ref
        self._sessions = []
        self._refresh_timer = None
        self.setWindowTitle("Mike — Dashboard")
        self.setMinimumSize(900, 640)
        self.resize(1060, 720)
        self.setStyleSheet(QSS_MAIN)

        _ico = asset_path("mike.ico")
        if _ico.exists():
            self.setWindowIcon(QIcon(str(_ico)))

        self._build_ui()
        self._load_data()
        self._start_refresh_timer()

    def closeEvent(self, event):
        """Cancel refresh timer on close to prevent ghost callbacks."""
        if self._refresh_timer is not None:
            self._refresh_timer.stop()
            self._refresh_timer = None
        super().closeEvent(event)

    # ─── UI Build ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("root")
        central.setStyleSheet(f"background: {_TERTIARY};")
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_main(), stretch=1)

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(
            f"background: {_SIDEBAR_BG}; border-right: 1px solid {_BORDER};"
        )
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(24, 32, 24, 28)
        layout.setSpacing(2)

        # Brand
        logo = QLabel("Mike")
        logo.setStyleSheet(f"""
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 36px;
            font-weight: 400;
            color: {_SECONDARY};
            letter-spacing: -0.5px;
        """)
        sub = QLabel("Voice Dictation")
        sub.setStyleSheet(
            f"color: {_MUTED}; font-size: 11px; font-family: 'Segoe UI', sans-serif;"
            f" font-weight: 500; letter-spacing: 0.04em; margin-bottom: 24px;"
        )
        layout.addWidget(logo)
        layout.addWidget(sub)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {_BORDER}; margin: 8px 0 16px 0;")
        layout.addWidget(divider)

        # Nav items
        self._nav_btns = {}
        nav_items = [
            ("Overview",  "overview"),
            ("Sessions",  "sessions"),
            ("Settings",  "settings"),
        ]
        for label, key in nav_items:
            btn = self._nav_button(label, key)
            layout.addWidget(btn)

        layout.addStretch()

        # ── Mic Controls ──────────────────────────────────────────────────────
        mic_label = QLabel("MIC CONTROLS")
        mic_label.setStyleSheet(
            f"color: {_BORDER}; font-size: 9px; font-weight: 600; "
            f"letter-spacing: 0.1em; font-family: 'Segoe UI', sans-serif; "
            f"margin-bottom: 8px; margin-top: 4px;"
        )
        layout.addWidget(mic_label)

        kill_btn = QPushButton("⏹  Kill Mike")
        kill_btn.setObjectName("danger_btn")
        kill_btn.setToolTip("Force-stop Mike completely")
        kill_btn.clicked.connect(self._kill_mic)
        layout.addWidget(kill_btn)

        layout.addSpacing(6)

        wake_btn = QPushButton("▶  Wake Mike")
        wake_btn.setObjectName("wake_btn")
        wake_btn.setToolTip("Reset Mike if glitched, or relaunch if not running")
        wake_btn.clicked.connect(self._wake_mike)
        layout.addWidget(wake_btn)

        layout.addSpacing(12)

        self.status_lbl = QLabel("● Active")
        self.status_lbl.setStyleSheet(
            f"color: #6ee7b7; font-size: 11px; font-family: 'Segoe UI', sans-serif;"
        )
        layout.addWidget(self.status_lbl)

        return sidebar

    def _nav_button(self, label: str, key: str):
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setChecked(key == "overview")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {_MUTED};
                border: none;
                border-radius: 8px;
                margin: 2px 12px;
                padding: 11px 16px;
                text-align: left;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(238,242,227,0.04);
                color: {_SECONDARY};
            }}
            QPushButton:checked {{
                background: rgba(4,63,46,0.35);
                color: {_SECONDARY};
                border-left: 2px solid #6ee7b7;
            }}
        """)
        btn.clicked.connect(lambda _checked, k=key: self._nav_to(k))
        self._nav_btns[key] = btn
        return btn

    def _nav_to(self, key: str):
        logger.info(f"Navigating to page: {key}")
        for k, b in self._nav_btns.items():
            b.setChecked(k == key)
        self.stack.setCurrentIndex({"overview": 0, "sessions": 1, "settings": 2}.get(key, 0))

    # ── Main Content ──────────────────────────────────────────────────────────

    def _build_main(self):
        container = QWidget()
        container.setStyleSheet(f"background: {_TERTIARY};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

                # Topbar removed for cleaner UI

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_overview_page())   # 0
        self.stack.addWidget(self._build_sessions_page())   # 1
        self.stack.addWidget(self._build_settings_page())   # 2
        layout.addWidget(self.stack, stretch=1)

        return container

    def _build_topbar(self):
        bar = QWidget()
        bar.setFixedHeight(56)
        bar.setStyleSheet(
            f"background: {_TERTIARY}; border-bottom: 1px solid {_BORDER};"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(30, 0, 30, 0)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search sessions…")
        self.search_box.setFixedWidth(300)
        self.search_box.setFixedHeight(36)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background: {_INPUT_BG};
                color: {_SECONDARY};
                border: 1px solid {_BORDER};
                border-radius: 8px;
                padding: 8px 14px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {_MUTED};
            }}
        """)
        self.search_box.textChanged.connect(self._on_search)
        layout.addWidget(self.search_box)
        layout.addStretch()

        export_btn = QPushButton("Export")
        export_btn.setObjectName("ghost_btn")
        export_btn.setFixedHeight(36)
        export_btn.clicked.connect(self._export_sessions)
        layout.addWidget(export_btn)

        return bar

    # ── Overview Page ─────────────────────────────────────────────────────────

    def _build_overview_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        heading = QLabel("Overview")
        heading.setStyleSheet(f"""
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 36px;
            font-weight: 400;
            color: {_SECONDARY};
            letter-spacing: -0.5px;
            line-height: 43px;
        """)
        layout.addWidget(heading)

        # Stat cards — 4 in a row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.stat_total = StatCard("All Time Words",  "—", "#6ee7b7")
        self.stat_today = StatCard("Today",           "—", "#93c5fd")
        self.stat_week  = StatCard("This Week",       "—", "#f9a8d4")
        self.stat_saved = StatCard("Time Saved (min)","—", "#fcd34d")
        stats_row.addWidget(self.stat_total)
        stats_row.addWidget(self.stat_today)
        stats_row.addWidget(self.stat_week)
        stats_row.addWidget(self.stat_saved)
        layout.addLayout(stats_row)

        # Section label
        recent_label = QLabel("RECENT SESSIONS")
        recent_label.setStyleSheet(f"""
            color: {_MUTED};
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.08em;
            font-family: 'Segoe UI', sans-serif;
            margin-top: 10px;
        """)
        layout.addWidget(recent_label)

        self.recent_scroll = QScrollArea()
        self.recent_scroll.setWidgetResizable(True)
        self.recent_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.recent_container = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_container)
        self.recent_layout.setSpacing(8)
        self.recent_layout.setContentsMargins(0, 0, 4, 0)
        self.recent_layout.addStretch()
        self.recent_scroll.setWidget(self.recent_container)
        self.recent_scroll.setStyleSheet("background: transparent;")
        layout.addWidget(self.recent_scroll, stretch=1)

        return page

    # ── Sessions Page ─────────────────────────────────────────────────────────

    def _build_sessions_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        heading = QLabel("Session History")
        heading.setStyleSheet(f"""
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 36px;
            font-weight: 400;
            color: {_SECONDARY};
            letter-spacing: -0.5px;
        """)
        layout.addWidget(heading)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        def _lbl(text: str) -> QLabel:
            l = QLabel(text)
            l.setStyleSheet(
                f"color: {_MUTED}; font-size: 12px; font-weight: 500;"
                f" font-family: 'Segoe UI', sans-serif;"
            )
            return l

        self.mode_filter = QComboBox()
        self.mode_filter.addItems(["All Modes", "Raw", "Semi-Formal", "Polished"])
        self.mode_filter.currentIndexChanged.connect(self._apply_filters)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Dictation", "Prompt"])
        self.type_filter.currentIndexChanged.connect(self._apply_filters)

        _date_style = (
            f"background: {_INPUT_BG}; color: {_MUTED}; "
            f"border: 1px solid {_BORDER}; border-radius: 8px; padding: 6px 10px;"
        )
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setStyleSheet(_date_style)
        self.date_from.dateChanged.connect(self._apply_filters)

        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setStyleSheet(_date_style)
        self.date_to.dateChanged.connect(self._apply_filters)

        filter_bar.addWidget(_lbl("Mode:"))
        filter_bar.addWidget(self.mode_filter)
        filter_bar.addSpacing(8)
        filter_bar.addWidget(_lbl("Type:"))
        filter_bar.addWidget(self.type_filter)
        filter_bar.addSpacing(8)
        filter_bar.addWidget(_lbl("From:"))
        filter_bar.addWidget(self.date_from)
        filter_bar.addWidget(_lbl("To:"))
        filter_bar.addWidget(self.date_to)
        filter_bar.addStretch()
        filter_bar.addWidget(export_btn)
        layout.addLayout(filter_bar)

        self.session_scroll = QScrollArea()
        self.session_scroll.setWidgetResizable(True)
        self.session_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sessions_container = QWidget()
        self.sessions_layout = QVBoxLayout(self.sessions_container)
        self.sessions_layout.setSpacing(8)
        self.sessions_layout.setContentsMargins(0, 0, 4, 0)
        self.sessions_layout.addStretch()
        self.session_scroll.setWidget(self.sessions_container)
        layout.addWidget(self.session_scroll, stretch=1)

        return page

    # ── Settings Page ─────────────────────────────────────────────────────────

    def _build_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        heading = QLabel("Settings")
        heading.setStyleSheet(f"""
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 36px;
            font-weight: 400;
            color: {_SECONDARY};
            letter-spacing: -0.5px;
        """)
        layout.addWidget(heading)

        # ── API Key card ──────────────────────────────────────────────────────
        api_card = self._settings_card()
        api_layout = QVBoxLayout(api_card)
        api_layout.setContentsMargins(24, 24, 24, 24)
        api_layout.setSpacing(12)

        api_title = QLabel("Groq API Key")
        api_title.setStyleSheet(f"""
            color: {_SECONDARY};
            font-size: 16px;
            font-weight: 400;
            font-family: 'Times New Roman', serif;
        """)
        api_sub = QLabel(
            "Get your free key at console.groq.com — Whisper + LLaMA, no credit card needed."
        )
        api_sub.setStyleSheet(
            f"color: {_MUTED}; font-size: 13px; font-family: 'Segoe UI', sans-serif;"
        )
        api_sub.setWordWrap(True)

        key_row = QHBoxLayout()
        key_row.setSpacing(10)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("gsk_…")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setFixedHeight(44)
        self.api_key_input.setText(self.config.get("groq_api_key", ""))

        show_btn = QPushButton("Show")
        show_btn.setObjectName("ghost_btn")
        show_btn.setFixedWidth(70)
        show_btn.setFixedHeight(44)
        show_btn.clicked.connect(self._toggle_key_visibility)

        save_btn = QPushButton("Save Key")
        save_btn.setObjectName("primary_btn")
        save_btn.setFixedHeight(44)
        save_btn.clicked.connect(self._save_api_key)

        key_row.addWidget(self.api_key_input, stretch=1)
        key_row.addWidget(show_btn)
        key_row.addWidget(save_btn)

        api_layout.addWidget(api_title)
        api_layout.addWidget(api_sub)
        api_layout.addLayout(key_row)
        layout.addWidget(api_card)

        # ── Inject method card ────────────────────────────────────────────────
        inject_card = self._settings_card()
        inj_layout = QVBoxLayout(inject_card)
        inj_layout.setContentsMargins(24, 24, 24, 24)
        inj_layout.setSpacing(12)

        inj_title = QLabel("Text Injection Method")
        inj_title.setStyleSheet(f"""
            color: {_SECONDARY};
            font-size: 16px;
            font-weight: 400;
            font-family: 'Times New Roman', serif;
        """)
        inj_sub = QLabel(
            "Clipboard (fast, recommended) or Type (slower, more compatible with all apps)."
        )
        inj_sub.setStyleSheet(
            f"color: {_MUTED}; font-size: 13px; font-family: 'Segoe UI', sans-serif;"
        )
        inj_sub.setWordWrap(True)

        self.inject_combo = QComboBox()
        self.inject_combo.addItems(["Clipboard (Ctrl+V)", "Character-by-character"])
        method = self.config.get("inject_method", "clipboard")
        self.inject_combo.setCurrentIndex(0 if method == "clipboard" else 1)
        self.inject_combo.setFixedHeight(44)

        inj_save = QPushButton("Save")
        inj_save.setObjectName("primary_btn")
        inj_save.setFixedHeight(44)
        inj_save.clicked.connect(self._save_inject_method)

        inj_row = QHBoxLayout()
        inj_row.setSpacing(10)
        inj_row.addWidget(self.inject_combo, stretch=1)
        inj_row.addWidget(inj_save)

        inj_layout.addWidget(inj_title)
        inj_layout.addWidget(inj_sub)
        inj_layout.addLayout(inj_row)
        layout.addWidget(inject_card)

        layout.addStretch()
        return page

    def _settings_card(self) -> QWidget:
        """Return a styled settings card container."""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background: {_CARD_BG};
                border: 1px solid {_BORDER};
                border-radius: 8px;
            }}
        """)
        return card

    # ─── Data Loading ─────────────────────────────────────────────────────────

    def _load_data(self):
        logger.debug("Loading dashboard data from database")
        if not self.db:
            self._load_mock_data()
            return
        try:
            sessions = self.db.get_sessions(limit=200)
            self._sessions = sessions
            self._update_stats()
            self._refresh_session_list(sessions)
            self._refresh_recent(sessions[:5])
        except Exception as e:
            logger.error(f"[Dashboard] DB error: {e}")

    def _load_mock_data(self):
        for card in (self.stat_total, self.stat_today, self.stat_week, self.stat_saved):
            card.update_value("0")

    def _update_stats(self):
        if not self._sessions:
            return
        today    = datetime.date.today()
        week_ago = today - datetime.timedelta(days=7)

        total_words = sum(s.get("word_count", 0) for s in self._sessions)
        today_words = sum(
            s.get("word_count", 0) for s in self._sessions
            if _session_date(s) == today
        )
        week_words = sum(
            s.get("word_count", 0) for s in self._sessions
            if _session_date(s) >= week_ago
        )
        time_saved = round(total_words / 45)

        self.stat_total.update_value(f"{total_words:,}")
        self.stat_today.update_value(f"{today_words:,}")
        self.stat_week.update_value(f"{week_words:,}")
        self.stat_saved.update_value(f"{time_saved}")

    def _refresh_session_list(self, sessions):
        while self.sessions_layout.count() > 1:
            item = self.sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for s in sessions:
            row = SessionRow(s)
            self.sessions_layout.insertWidget(self.sessions_layout.count() - 1, row)

    def _refresh_recent(self, sessions):
        while self.recent_layout.count() > 1:
            item = self.recent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for s in sessions:
            row = SessionRow(s)
            self.recent_layout.insertWidget(self.recent_layout.count() - 1, row)

    def _start_refresh_timer(self):
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(10_000)
        self._refresh_timer.timeout.connect(self._load_data)
        self._refresh_timer.start()

    # ─── Filtering & Search ───────────────────────────────────────────────────

    def _on_search(self, _text: str):
        logger.debug(f"Search query changed: {_text}")
        self._apply_filters()

    def _apply_filters(self):
        logger.info("Applying session filters")
        search    = self.search_box.text().lower()
        mode_idx  = self.mode_filter.currentIndex()
        type_idx  = self.type_filter.currentIndex()
        date_from = self.date_from.date().toPyDate()
        date_to   = self.date_to.date().toPyDate()

        mode_map  = {0: None, 1: "raw", 2: "semi_formal", 3: "polished"}
        type_map  = {0: None, 1: "dictation", 2: "prompt"}
        mode_filter = mode_map.get(mode_idx)
        type_filter = type_map.get(type_idx)

        filtered = []
        for s in self._sessions:
            if mode_filter and s.get("mode") != mode_filter:
                continue
            if type_filter and s.get("session_type") != type_filter:
                continue
            sd = _session_date(s)
            if sd < date_from or sd > date_to:
                continue
            if search and search not in str(s.get("final_text", "")).lower():
                continue
            filtered.append(s)

        self._refresh_session_list(filtered)

    # ─── Export ───────────────────────────────────────────────────────────────

    def _export_sessions(self):
        logger.info("Exporting sessions requested")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Sessions", "", "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            for s in self._sessions:
                f.write(
                    f"--- {s.get('created_at')} | {s.get('mode')} | "
                    f"{s.get('word_count', 0)} words ---\n"
                )
                f.write(str(s.get("final_text", "")) + "\n\n")

    # ─── Settings Actions ─────────────────────────────────────────────────────

    _KEY_INPUT_NEUTRAL = (
        f"background: {_INPUT_BG}; color: {_SECONDARY}; "
        f"border: 1px solid {_BORDER}; border-radius: 8px; "
        f"padding: 14px 16px; font-family: 'Times New Roman', serif; font-size: 14px;"
    )

    def _toggle_key_visibility(self):
        is_pw = self.api_key_input.echoMode() == QLineEdit.EchoMode.Password
        self.api_key_input.setEchoMode(
            QLineEdit.EchoMode.Normal if is_pw else QLineEdit.EchoMode.Password
        )

    def _save_api_key(self):
        logger.info("Saving API key")
        key = self.api_key_input.text().strip()
        if not key.startswith("gsk_") or len(key) < 20:
            self.api_key_input.setStyleSheet(
                self._KEY_INPUT_NEUTRAL + f" border: 1px solid {_ERROR};"
            )
            return
        self.config.set("groq_api_key", key)
        self.api_key_input.setStyleSheet(
            self._KEY_INPUT_NEUTRAL + " border: 1px solid #6ee7b7;"
        )
        QTimer.singleShot(2000, self._reset_key_input_style)

    def _reset_key_input_style(self):
        self.api_key_input.setStyleSheet(self._KEY_INPUT_NEUTRAL)

    def _save_inject_method(self):
        logger.info("Saving inject method")
        method = "clipboard" if self.inject_combo.currentIndex() == 0 else "type"
        self.config.set("inject_method", method)

    # ─── Mic Controls ─────────────────────────────────────────────────────────

    _MIKE_PORT = 44556

    def _send_mic_signal(self, signal: bytes) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.sendto(signal, ("127.0.0.1", self._MIKE_PORT))
            s.close()
            return True
        except Exception:
            return False

    def _set_status(self, text: str, color: str = "#6ee7b7", reset_ms: int = 3000):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; font-family: 'Segoe UI', sans-serif;"
        )
        if reset_ms > 0:
            QTimer.singleShot(reset_ms, self._reset_status)

    def _reset_status(self):
        self.status_lbl.setText("● Active")
        self.status_lbl.setStyleSheet(
            "color: #6ee7b7; font-size: 11px; font-family: 'Segoe UI', sans-serif;"
        )

    def _kill_mic(self):
        logger.warning("Kill Mike requested")
        sent = self._send_mic_signal(b"KILL_MIC")
        if sent:
            self._set_status("⏹ Mike killed", _ERROR)
        else:
            self._set_status("⚠ Mike not running", "#fcd34d")

    def _wake_mike(self):
        logger.info("Wake Mike requested")
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        mike_alive = False
        try:
            probe.bind(("127.0.0.1", self._MIKE_PORT))
        except OSError:
            mike_alive = True
        finally:
            try:
                probe.close()
            except Exception:
                pass

        if mike_alive:
            self._send_mic_signal(b"WAKE_MIC")
            self._set_status("▶ Wake signal sent", "#6ee7b7")
        else:
            mike_exe = (
                pathlib.Path(os.environ.get("LOCALAPPDATA", ""))
                / "Programs" / "Mike" / "Mike.exe"
            )
            if mike_exe.exists():
                try:
                    env = os.environ.copy()
                    for k in list(env.keys()):
                        if k.startswith("_PYI") or k.startswith("_MEI") or k in (
                            "TCL_LIBRARY", "TK_LIBRARY"
                        ):
                            env.pop(k, None)
                    subprocess.Popen(
                        [str(mike_exe), "--startup"],
                        env=env,
                        creationflags=0x08000000,
                    )
                    self._set_status("▶ Launching Mike…", "#6ee7b7")
                except Exception as e:
                    self._set_status(f"⚠ Launch failed: {e}", _ERROR)
            else:
                self._set_status("⚠ Mike.exe not found", _ERROR)

    def refresh(self):
        logger.info("Dashboard refresh triggered")
        """Reload data from DB."""
        self._load_data()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _session_date(s: dict) -> datetime.date:
    try:
        ts = s.get("created_at", "")
        return datetime.datetime.fromisoformat(str(ts).replace(" ", "T")).date()
    except Exception:
        return datetime.date.today()


# ─── Launch Helpers ───────────────────────────────────────────────────────────

def launch_dashboard(db_ref=None):
    """Launch or show the dashboard window. Must be called from the Qt main thread."""
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        app.setFont(QFont("Segoe UI", 10))
        created_app = True

    win = DashboardWindow(db_ref=db_ref)
    win.show()
    win.raise_()
    win.activateWindow()

    if created_app:
        app.exec()
    return win


if __name__ == "__main__":
    """
    Standalone entry point for subprocess launch from engine.py.
    Usage: python dashboard.py [db_path]
    """
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

    _here = pathlib.Path(__file__).resolve().parent
    _root = app_root()
    for _path in (str(_here), str(_root)):
        if _path not in sys.path:
            sys.path.insert(0, _path)
    os.chdir(_root)

    db_ref = None
    if len(sys.argv) > 1 and sys.argv[1]:
        try:
            from db import Database
            db_ref = Database(path=pathlib.Path(sys.argv[1]))
        except Exception as e:
            logger.error(f"[Dashboard] DB load error: {e}")

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyle("Fusion")

    win = DashboardWindow(db_ref=db_ref)
    win.show()
    sys.exit(app.exec())
