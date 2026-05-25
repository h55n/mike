"""
dashboard.py — Mike Dashboard
Full PyQt6 window: stats panel, session history, search, filter, export.
Design: ElevenLabs-inspired — warm near-black, off-white, pastel accents.
"""

import sys
import os
import socket
import subprocess
import pathlib
import datetime
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QComboBox,
    QDateEdit, QFileDialog, QTextEdit, QSizeGrip, QStackedWidget,
    QGraphicsDropShadowEffect, QSplitter, QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import (
    Qt, QDate, QThread, pyqtSignal, QTimer, QPropertyAnimation,
    QEasingCurve, QSize, QPoint,
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QPainter, QBrush, QPen,
    QLinearGradient, QFontDatabase,
)

logger = logging.getLogger("mike.dashboard")


# ─── Design Tokens ───────────────────────────────────────────────────────────
CANVAS      = "#f5f4f2"
CANVAS_SOFT = "#fafaf9"
INK         = "#0c0a09"
SURFACE     = "#ffffff"
SURFACE_STR = "#f0efed"
DARK_BG     = "#111110"
DARK_CARD   = "#1c1917"
DARK_HOVER  = "#28251f"
HAIRLINE    = "#e7e5e4"
BODY_TEXT   = "#4e4e4e"
MUTED       = "#78716c"
MUTED_SOFT  = "#a8a29e"

GRAD_MINT    = "#a7e5d3"
GRAD_PEACH   = "#f4c5a8"
GRAD_LAVEND  = "#c8b8e0"
GRAD_SKY     = "#a8c8e8"
GRAD_ROSE    = "#e8b8c4"

ACCENT_PINK  = "#f472b6"
ACCENT_GREEN = "#4ade80"
ACCENT_AMBER = "#fbbf24"

BADGE_RAW    = "#1c1917"
BADGE_SF     = "#1c2d1a"
BADGE_POL    = "#1a1c2d"

# Mode badge text colors
MODE_COLORS = {
    "raw":        ("#f5f4f2", "#2a2723"),
    "semi_formal": ("#4ade80", "#1c2d1a"),
    "polished":   ("#93c5fd", "#1a1c2d"),
}

QSS_MAIN = """
QMainWindow, QWidget#root {
    background: #111110;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: #1c1917;
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #3d3935;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QLineEdit {
    background: #1c1917;
    color: #f5f4f2;
    border: 1px solid #2e2b28;
    border-radius: 10px;
    padding: 8px 14px;
    font-family: 'Segoe UI';
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #4a4540;
}
QComboBox {
    background: #1c1917;
    color: #a8a29e;
    border: 1px solid #2e2b28;
    border-radius: 8px;
    padding: 5px 10px;
    font-family: 'Segoe UI';
    font-size: 12px;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background: #1c1917;
    color: #f5f4f2;
    border: 1px solid #3d3935;
    selection-background-color: #2e2b28;
}
QPushButton#pill_btn {
    background: #2a2723;
    color: #f5f4f2;
    border: 1px solid #4a4540;
    border-radius: 9999px;
    padding: 8px 20px;
    min-width: 80px;
    font-family: 'Segoe UI';
    font-size: 13px;
    font-weight: 500;
}
QPushButton#pill_btn:hover { background: #3d3935; color: #ffffff; border-color: #6a6460; }
QPushButton#pill_btn:pressed { background: #1c1917; }
QPushButton#ghost_btn {
    background: transparent;
    color: #a8a29e;
    border: 1px solid #2e2b28;
    border-radius: 9999px;
    padding: 7px 18px;
    min-width: 60px;
    font-family: 'Segoe UI';
    font-size: 12px;
}
QPushButton#ghost_btn:hover {
    color: #f5f4f2;
    border-color: #4a4540;
    background: #1c1917;
}
QPushButton#copy_btn {
    background: #1c1917;
    color: #78716c;
    border: 1px solid #2e2b28;
    border-radius: 6px;
    padding: 4px 12px;
    font-family: 'Segoe UI';
    font-size: 11px;
}
QPushButton#copy_btn:hover {
    color: #f5f4f2;
    border-color: #4ade80;
    color: #4ade80;
}
QPushButton#danger_btn {
    background: #2a1010;
    color: #f87171;
    border: 1px solid #4a2020;
    border-radius: 9999px;
    padding: 8px 16px;
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: 600;
}
QPushButton#danger_btn:hover { background: #3a1515; border-color: #f87171; color: #ffffff; }
QPushButton#danger_btn:pressed { background: #1a0a0a; }
QPushButton#wake_btn {
    background: #102a10;
    color: #4ade80;
    border: 1px solid #204a20;
    border-radius: 9999px;
    padding: 8px 16px;
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: 600;
}
QPushButton#wake_btn:hover { background: #153a15; border-color: #4ade80; color: #ffffff; }
QPushButton#wake_btn:pressed { background: #0a1a0a; }
"""


class StatCard(QWidget):
    def __init__(self, label, value, accent=None):
        super().__init__()
        self.accent = accent or MUTED
        self.setFixedHeight(88)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        self.val_label = QLabel(str(value))
        self.val_label.setStyleSheet(f"""
            font-family: 'Segoe UI';
            font-size: 28px;
            font-weight: 300;
            color: #f5f4f2;
            letter-spacing: -0.5px;
        """)
        self.lbl_label = QLabel(label)
        self.lbl_label.setStyleSheet(f"""
            font-family: 'Segoe UI';
            font-size: 11px;
            font-weight: 500;
            color: {MUTED};
            letter-spacing: 1px;
            text-transform: uppercase;
        """)
        layout.addWidget(self.val_label)
        layout.addWidget(self.lbl_label)

        self.setStyleSheet(f"""
            StatCard {{
                background: #1c1917;
                border: 1px solid #2e2b28;
                border-radius: 14px;
                border-left: 3px solid {self.accent};
            }}
        """)

    def update_value(self, value):
        self.val_label.setText(str(value))


class ModeBadge(QLabel):
    def __init__(self, mode: str):
        super().__init__()
        labels = {"raw": "RAW", "semi_formal": "SF", "polished": "POL"}
        fg, bg = MODE_COLORS.get(mode, ("#a8a29e", "#2a2723"))
        self.setText(labels.get(mode, mode.upper()))
        self.setFixedSize(38, 20)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {fg};
                border: 1px solid {fg}44;
                border-radius: 4px;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
        """)


class SessionRow(QWidget):
    def __init__(self, session: dict):
        super().__init__()
        self.session = session
        self.expanded = False
        self._build(session)

    def _build(self, s: dict):
        self.setStyleSheet("""
            SessionRow {
                background: #1c1917;
                border: 1px solid #2a2723;
                border-radius: 12px;
            }
            SessionRow:hover {
                border: 1px solid #3d3935;
                background: #221f1c;
            }
        """)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 12)
        self.main_layout.setSpacing(8)

        # Header row
        header = QHBoxLayout()
        header.setSpacing(10)

        # Timestamp
        ts_raw = str(s.get("created_at", ""))
        try:
            # SQLite stores "YYYY-MM-DD HH:MM:SS"; fromisoformat needs "T" sep on Py<3.11
            ts = datetime.datetime.fromisoformat(ts_raw.replace(" ", "T"))
        except Exception:
            ts = None
        time_str = ts.strftime("%b %d  %H:%M") if ts else "—"
        ts_lbl = QLabel(time_str)
        ts_lbl.setStyleSheet("color: #78716c; font-size: 12px; font-family: 'Segoe UI';")

        # Mode badge
        badge = ModeBadge(s.get("mode", "raw"))

        # Type tag
        stype = s.get("session_type", "dictation")
        type_lbl = QLabel("⚡ PROMPT" if stype == "prompt" else "🎙 DICTATE")
        type_lbl.setStyleSheet(f"""
            color: {'#f472b6' if stype == 'prompt' else MUTED_SOFT};
            font-size: 10px;
            font-weight: 600;
            font-family: 'Segoe UI';
            letter-spacing: 0.5px;
        """)

        # Word count
        wc_lbl = QLabel(f"{s.get('word_count', 0)} words")
        wc_lbl.setStyleSheet("color: #4a4540; font-size: 11px; font-family: 'Segoe UI';")

        # Expand arrow
        self.arrow = QLabel("›")
        self.arrow.setStyleSheet("color: #4a4540; font-size: 16px;")

        header.addWidget(ts_lbl)
        header.addWidget(badge)
        header.addWidget(type_lbl)
        header.addStretch()
        header.addWidget(wc_lbl)
        header.addWidget(self.arrow)
        self.main_layout.addLayout(header)

        # Preview text
        preview = str(s.get("final_text", ""))[:120]
        if len(str(s.get("final_text", ""))) > 120:
            preview += "…"
        self.preview_lbl = QLabel(preview)
        self.preview_lbl.setStyleSheet("color: #a8a29e; font-size: 12px; font-family: 'Segoe UI'; line-height: 1.5;")
        self.preview_lbl.setWordWrap(True)
        self.main_layout.addWidget(self.preview_lbl)

        # Expanded text (hidden by default)
        self.full_text = QTextEdit()
        self.full_text.setPlainText(str(s.get("final_text", "")))
        self.full_text.setReadOnly(True)
        self.full_text.setMaximumHeight(160)
        self.full_text.setStyleSheet("""
            QTextEdit {
                background: #111110;
                color: #d6d3d1;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
        """)
        self.full_text.hide()
        self.main_layout.addWidget(self.full_text)

        # Copy button row (shown when expanded)
        copy_row = QHBoxLayout()
        copy_row.setContentsMargins(0, 0, 0, 0)
        self.copy_btn = QPushButton("Copy text")
        self.copy_btn.setObjectName("copy_btn")
        self.copy_btn.setFixedHeight(26)
        self.copy_btn.clicked.connect(self._copy_text)
        self.copy_status = QLabel("")
        self.copy_status.setStyleSheet("color: #4ade80; font-size: 11px; font-family: 'Segoe UI';")
        copy_row.addWidget(self.copy_btn)
        copy_row.addWidget(self.copy_status)
        copy_row.addStretch()
        self.copy_row_widget = QWidget()
        self.copy_row_widget.setLayout(copy_row)
        self.copy_row_widget.setStyleSheet("background: transparent;")
        self.copy_row_widget.hide()
        self.main_layout.addWidget(self.copy_row_widget)

        # Click to expand
        self.mousePressEvent = self._toggle_expand

    def _copy_text(self):
        text = str(self.session.get("final_text", ""))
        QApplication.clipboard().setText(text)
        self.copy_status.setText("Copied!")
        QTimer.singleShot(2000, lambda: self.copy_status.setText(""))

    def _toggle_expand(self, event):
        self.expanded = not self.expanded
        self.full_text.setVisible(self.expanded)
        self.copy_row_widget.setVisible(self.expanded)
        self.preview_lbl.setVisible(not self.expanded)
        self.arrow.setText("v" if self.expanded else ">")
        self.setStyleSheet(self.styleSheet())


class DashboardWindow(QMainWindow):
    def __init__(self, db_ref=None):
        super().__init__()
        from config import Config
        self.config = Config()
        self.db = db_ref
        self._sessions = []
        self._session_widgets = []
        self.setWindowTitle("Mike - Dashboard")
        self.setMinimumSize(860, 620)
        self.resize(1000, 700)
        self.setStyleSheet(QSS_MAIN)
        # Set mic icon instead of Python default
        _ico = pathlib.Path(__file__).parent / "assets" / "mike.ico"
        if _ico.exists():
            self.setWindowIcon(QIcon(str(_ico)))
        self._build_ui()
        self._load_data()
        self._start_refresh_timer()

    # ─── UI Build ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("root")
        central.setStyleSheet("background: #111110;")
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        # Main content area
        main_area = self._build_main()
        root_layout.addWidget(main_area, stretch=1)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background: #0c0a09; border-right: 1px solid #1c1917;")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 28, 20, 28)
        layout.setSpacing(4)

        # Logo / brand
        logo = QLabel("Mike")
        logo.setStyleSheet("""
            font-family: 'Georgia', serif;
            font-size: 22px;
            font-weight: 300;
            color: #f5f4f2;
            letter-spacing: -0.3px;
            margin-bottom: 4px;
        """)
        sub = QLabel("Voice Dictation")
        sub.setStyleSheet("color: #4a4540; font-size: 11px; font-family: 'Segoe UI'; margin-bottom: 28px;")
        layout.addWidget(logo)
        layout.addWidget(sub)

        # Nav items — emoji icons for clarity
        self._nav_btns = {}
        nav_items = [
            ("🏠", "Overview",  "overview"),
            ("📋", "Sessions",  "sessions"),
            ("⚙️", "Settings",  "settings"),
        ]
        for icon, label, key in nav_items:
            btn = self._nav_button(icon, label, key)
            layout.addWidget(btn)

        layout.addStretch()

        # ─── Mic Controls (kill switch + wake) ───────────────────────────
        mic_label = QLabel("MIC CONTROLS")
        mic_label.setStyleSheet("color: #3d3935; font-size: 9px; font-weight: 600; "
                                "letter-spacing: 1.2px; font-family: 'Segoe UI'; "
                                "margin-bottom: 4px;")
        layout.addWidget(mic_label)

        kill_btn = QPushButton("⏹  Kill Mike")
        kill_btn.setObjectName("danger_btn")
        kill_btn.setFixedHeight(34)
        kill_btn.setToolTip("Kill the Mike background app completely (sends KILL_MIC signal)")
        kill_btn.clicked.connect(self._kill_mic)
        layout.addWidget(kill_btn)

        wake_btn = QPushButton("▶  Wake Mike")
        wake_btn.setObjectName("wake_btn")
        wake_btn.setFixedHeight(34)
        wake_btn.setToolTip("Reset Mike if glitched, or relaunch if not running")
        wake_btn.clicked.connect(self._wake_mike)
        layout.addWidget(wake_btn)

        # Status dot
        self.status_lbl = QLabel("● Active")
        self.status_lbl.setStyleSheet("color: #4ade80; font-size: 11px; "
                                      "font-family: 'Segoe UI'; margin-top: 8px;")
        layout.addWidget(self.status_lbl)

        return sidebar

    def _nav_button(self, icon, label, key):
        btn = QPushButton(f"  {icon}  {label}")
        btn.setCheckable(True)
        btn.setChecked(key == "overview")
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #78716c;
                border: none;
                border-radius: 8px;
                padding: 10px 12px;
                text-align: left;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QPushButton:hover { background: #1c1917; color: #d6d3d1; }
            QPushButton:checked { background: #1c1917; color: #f5f4f2; }
        """)
        btn.clicked.connect(lambda checked, k=key: self._nav_to(k))
        self._nav_btns[key] = btn
        return btn

    def _nav_to(self, key):
        for k, b in self._nav_btns.items():
            b.setChecked(k == key)
        self.stack.setCurrentIndex({"overview": 0, "sessions": 1, "settings": 2}.get(key, 0))

    def _build_main(self):
        container = QWidget()
        container.setStyleSheet("background: #111110;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        topbar = self._build_topbar()
        layout.addWidget(topbar)

        # Stacked pages
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_overview_page())   # 0
        self.stack.addWidget(self._build_sessions_page())   # 1
        self.stack.addWidget(self._build_settings_page())   # 2
        layout.addWidget(self.stack, stretch=1)

        return container

    def _build_topbar(self):
        bar = QWidget()
        bar.setFixedHeight(56)
        bar.setStyleSheet("background: #111110; border-bottom: 1px solid #1c1917;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(28, 0, 28, 0)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search sessions…")
        self.search_box.setFixedWidth(280)
        self.search_box.textChanged.connect(self._on_search)
        layout.addWidget(self.search_box)
        layout.addStretch()

        export_btn = QPushButton("Export")
        export_btn.setObjectName("ghost_btn")
        export_btn.clicked.connect(self._export_sessions)
        layout.addWidget(export_btn)

        return bar

    def _build_overview_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        # Heading
        heading = QLabel("Overview")
        heading.setStyleSheet("""
            font-family: 'Georgia', serif;
            font-size: 28px;
            font-weight: 300;
            color: #f5f4f2;
            letter-spacing: -0.4px;
        """)
        layout.addWidget(heading)

        # Stats grid (2×2)
        self.stat_total   = StatCard("ALL TIME WORDS", "—", GRAD_MINT)
        self.stat_today   = StatCard("TODAY", "—", GRAD_PEACH)
        self.stat_week    = StatCard("THIS WEEK", "—", GRAD_SKY)
        self.stat_saved   = StatCard("TIME SAVED (MIN)", "—", GRAD_LAVEND)

        row1 = QHBoxLayout()
        row1.setSpacing(12)
        row1.addWidget(self.stat_total)
        row1.addWidget(self.stat_today)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(12)
        row2.addWidget(self.stat_week)
        row2.addWidget(self.stat_saved)
        layout.addLayout(row2)

        # Recent sessions (last 5)
        recent_label = QLabel("Recent Sessions")
        recent_label.setStyleSheet("color: #78716c; font-size: 11px; font-weight: 600; letter-spacing: 1.2px; font-family: 'Segoe UI'; text-transform: uppercase;")
        layout.addWidget(recent_label)

        self.recent_scroll = QScrollArea()
        self.recent_scroll.setWidgetResizable(True)
        self.recent_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.recent_container = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_container)
        self.recent_layout.setSpacing(8)
        self.recent_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_layout.addStretch()
        self.recent_scroll.setWidget(self.recent_container)
        self.recent_scroll.setStyleSheet("background: transparent;")
        layout.addWidget(self.recent_scroll, stretch=1)

        return page

    def _build_sessions_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header + filters
        heading = QLabel("Session History")
        heading.setStyleSheet("font-family: 'Georgia', serif; font-size: 28px; font-weight: 300; color: #f5f4f2; letter-spacing: -0.4px;")
        layout.addWidget(heading)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.mode_filter = QComboBox()
        self.mode_filter.addItems(["All Modes", "Raw", "Semi-Formal", "Polished"])
        self.mode_filter.currentIndexChanged.connect(self._apply_filters)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Dictation", "Prompt"])
        self.type_filter.currentIndexChanged.connect(self._apply_filters)

        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setStyleSheet("background: #1c1917; color: #a8a29e; border: 1px solid #2e2b28; border-radius: 8px; padding: 5px;")
        self.date_from.dateChanged.connect(self._apply_filters)

        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setStyleSheet("background: #1c1917; color: #a8a29e; border: 1px solid #2e2b28; border-radius: 8px; padding: 5px;")
        self.date_to.dateChanged.connect(self._apply_filters)

        lbl_mode = QLabel("Mode:")
        lbl_mode.setStyleSheet("color: #d6d3d1; font-size: 12px; font-family: 'Segoe UI';")
        lbl_type = QLabel("Type:")
        lbl_type.setStyleSheet("color: #d6d3d1; font-size: 12px; font-family: 'Segoe UI';")
        lbl_from = QLabel("From:")
        lbl_from.setStyleSheet("color: #d6d3d1; font-size: 12px; font-family: 'Segoe UI';")
        lbl_to = QLabel("To:")
        lbl_to.setStyleSheet("color: #d6d3d1; font-size: 12px; font-family: 'Segoe UI';")

        filter_bar.addWidget(lbl_mode)
        filter_bar.addWidget(self.mode_filter)
        filter_bar.addWidget(lbl_type)
        filter_bar.addWidget(self.type_filter)
        filter_bar.addWidget(lbl_from)
        filter_bar.addWidget(self.date_from)
        filter_bar.addWidget(lbl_to)
        filter_bar.addWidget(self.date_to)
        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        # Session list
        self.session_scroll = QScrollArea()
        self.session_scroll.setWidgetResizable(True)
        self.session_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sessions_container = QWidget()
        self.sessions_layout = QVBoxLayout(self.sessions_container)
        self.sessions_layout.setSpacing(8)
        self.sessions_layout.setContentsMargins(0, 0, 8, 0)
        self.sessions_layout.addStretch()
        self.session_scroll.setWidget(self.sessions_container)
        layout.addWidget(self.session_scroll, stretch=1)

        return page

    def _build_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        heading = QLabel("Settings")
        heading.setStyleSheet("font-family: 'Georgia', serif; font-size: 28px; font-weight: 300; color: #f5f4f2; letter-spacing: -0.4px;")
        layout.addWidget(heading)

        # API Key card
        api_card = QWidget()
        api_card.setStyleSheet("background: #1c1917; border: 1px solid #2e2b28; border-radius: 14px;")
        api_layout = QVBoxLayout(api_card)
        api_layout.setContentsMargins(20, 20, 20, 20)
        api_layout.setSpacing(10)

        api_title = QLabel("Groq API Key")
        api_title.setStyleSheet("color: #f5f4f2; font-size: 14px; font-weight: 600; font-family: 'Segoe UI';")
        api_sub = QLabel("Get your free key at console.groq.com — Whisper + LLaMA, no credit card needed.")
        api_sub.setStyleSheet("color: #78716c; font-size: 12px; font-family: 'Segoe UI';")
        api_sub.setWordWrap(True)

        key_row = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("gsk_…")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(self.config.get("groq_api_key", ""))

        show_btn = QPushButton("Show")
        show_btn.setObjectName("ghost_btn")
        show_btn.setFixedWidth(60)
        show_btn.clicked.connect(lambda: self.api_key_input.setEchoMode(
            QLineEdit.EchoMode.Normal if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password
            else QLineEdit.EchoMode.Password
        ))

        save_btn = QPushButton("Save Key")
        save_btn.setObjectName("pill_btn")
        save_btn.clicked.connect(self._save_api_key)

        key_row.addWidget(self.api_key_input)
        key_row.addWidget(show_btn)
        key_row.addWidget(save_btn)

        api_layout.addWidget(api_title)
        api_layout.addWidget(api_sub)
        api_layout.addLayout(key_row)
        layout.addWidget(api_card)

        # Inject method card
        inject_card = QWidget()
        inject_card.setStyleSheet("background: #1c1917; border: 1px solid #2e2b28; border-radius: 14px;")
        inj_layout = QVBoxLayout(inject_card)
        inj_layout.setContentsMargins(20, 20, 20, 20)
        inj_layout.setSpacing(10)

        inj_title = QLabel("Text Injection Method")
        inj_title.setStyleSheet("color: #f5f4f2; font-size: 14px; font-weight: 600; font-family: 'Segoe UI';")
        inj_sub = QLabel("Clipboard (fast, recommended) or Type (slower, more compatible with all apps).")
        inj_sub.setStyleSheet("color: #78716c; font-size: 12px; font-family: 'Segoe UI';")
        inj_sub.setWordWrap(True)

        self.inject_combo = QComboBox()
        self.inject_combo.addItems(["Clipboard (Ctrl+V)", "Character-by-character"])
        method = self.config.get("inject_method", "clipboard")
        self.inject_combo.setCurrentIndex(0 if method == "clipboard" else 1)
        inj_save = QPushButton("Save")
        inj_save.setObjectName("pill_btn")
        inj_save.clicked.connect(self._save_inject_method)

        inj_row = QHBoxLayout()
        inj_row.addWidget(self.inject_combo)
        inj_row.addWidget(inj_save)

        inj_layout.addWidget(inj_title)
        inj_layout.addWidget(inj_sub)
        inj_layout.addLayout(inj_row)
        layout.addWidget(inject_card)

        layout.addStretch()
        return page

    # ─── Data Loading ─────────────────────────────────────────────────────────

    def _load_data(self):
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
        """Show placeholder data when no DB connected."""
        self.stat_total.update_value("0")
        self.stat_today.update_value("0")
        self.stat_week.update_value("0")
        self.stat_saved.update_value("0")

    def _update_stats(self):
        if not self._sessions:
            return
        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=7)

        total_words = sum(s.get("word_count", 0) for s in self._sessions)
        today_words = sum(s.get("word_count", 0) for s in self._sessions
                         if _session_date(s) == today)
        week_words  = sum(s.get("word_count", 0) for s in self._sessions
                         if _session_date(s) >= week_ago)
        time_saved  = round(total_words / 45)

        self.stat_total.update_value(f"{total_words:,}")
        self.stat_today.update_value(f"{today_words:,}")
        self.stat_week.update_value(f"{week_words:,}")
        self.stat_saved.update_value(f"{time_saved}")

    def _refresh_session_list(self, sessions):
        # Clear old widgets
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
        self._refresh_timer = QTimer()
        self._refresh_timer.setInterval(10_000)  # refresh every 10s
        self._refresh_timer.timeout.connect(self._load_data)
        self._refresh_timer.start()

    # ─── Filtering & Search ───────────────────────────────────────────────────

    def _on_search(self, text: str):
        self._apply_filters()

    def _apply_filters(self):
        search = self.search_box.text().lower()
        mode_idx = self.mode_filter.currentIndex()
        type_idx = self.type_filter.currentIndex()
        date_from = self.date_from.date().toPyDate()
        date_to   = self.date_to.date().toPyDate()

        mode_map = {0: None, 1: "raw", 2: "semi_formal", 3: "polished"}
        type_map = {0: None, 1: "dictation", 2: "prompt"}
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
        path, _ = QFileDialog.getSaveFileName(self, "Export Sessions", "", "Text Files (*.txt)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            for s in self._sessions:
                f.write(f"--- {s.get('created_at')} | {s.get('mode')} | {s.get('word_count',0)} words ---\n")
                f.write(str(s.get("final_text", "")) + "\n\n")

    # ─── Settings Actions ─────────────────────────────────────────────────────

    def _save_api_key(self):
        key = self.api_key_input.text().strip()
        if not key.startswith("gsk_"):
            self.api_key_input.setStyleSheet(self.api_key_input.styleSheet() + "border: 1px solid #f87171;")
            return
        self.config.set("groq_api_key", key)
        self.api_key_input.setStyleSheet(self.api_key_input.styleSheet() + "border: 1px solid #4ade80;")

    def _save_inject_method(self):
        method = "clipboard" if self.inject_combo.currentIndex() == 0 else "type"
        self.config.set("inject_method", method)

    # ─── Mic Controls ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

    _MIKE_PORT = 44556  # Must match main.py PORT

    def _send_mic_signal(self, signal: bytes) -> bool:
        """Send UDP signal to the running Mike main process."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.sendto(signal, ("127.0.0.1", self._MIKE_PORT))
            s.close()
            return True
        except Exception:
            return False

    def _set_status(self, text: str, color: str = "#4ade80", reset_ms: int = 3000):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; font-family: 'Segoe UI'; margin-top: 8px;"
        )
        if reset_ms:
            QTimer.singleShot(reset_ms, lambda: self._set_status("● Active", "#4ade80", 0))

    def _kill_mic(self):
        """Force-stop mic: sends KILL_MIC signal to main Mike process."""
        sent = self._send_mic_signal(b"KILL_MIC")
        if sent:
            self._set_status("⏹ Mike killed", "#f87171")
        else:
            self._set_status("⚠ Mike not running", "#fbbf24")

    def _wake_mike(self):
        """Reset/restart Mike: sends WAKE_MIC, or relaunches if process is dead."""
        # 1. Try to probe if Mike is running (attempt to bind its port)
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        mike_alive = False
        try:
            probe.bind(("127.0.0.1", self._MIKE_PORT))
            # Bind succeeded → Mike is NOT running
            mike_alive = False
        except OSError:
            # Port taken → Mike is running
            mike_alive = True
        finally:
            try:
                probe.close()
            except Exception:
                pass

        if mike_alive:
            # Mike is alive but possibly glitched — send wake signal
            self._send_mic_signal(b"WAKE_MIC")
            self._set_status("▶ Wake signal sent", "#4ade80")
        else:
            # Mike is dead — relaunch exe from install path
            mike_exe = (
                pathlib.Path(os.environ.get("LOCALAPPDATA", ""))
                / "Programs" / "Mike" / "Mike.exe"
            )
            if mike_exe.exists():
                try:
                    env = os.environ.copy()
                    for k in list(env.keys()):
                        if k.startswith("_PYI") or k.startswith("_MEI") or k in ("TCL_LIBRARY", "TK_LIBRARY"):
                            env.pop(k, None)
                    subprocess.Popen(
                        [str(mike_exe), "--startup"],
                        env=env,
                        creationflags=0x08000000,  # CREATE_NO_WINDOW
                    )
                    self._set_status("▶ Launching Mike…", "#4ade80")
                except Exception as e:
                    self._set_status(f"⚠ Launch failed: {e}", "#f87171")
            else:
                self._set_status("⚠ Mike.exe not found", "#f87171")

    def refresh(self):
        """Call to reload data from DB."""
        self._load_data()


def _session_date(s: dict) -> datetime.date:
    try:
        ts = s.get("created_at", "")
        return datetime.datetime.fromisoformat(str(ts).replace(" ", "T")).date()
    except Exception:
        return datetime.date.today()


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

    # Ensure project dir is in path (needed when launched as subprocess)
    import pathlib
    _here = pathlib.Path(__file__).resolve().parent
    if str(_here) not in sys.path:
        sys.path.insert(0, str(_here))
    import os
    os.chdir(_here)

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
