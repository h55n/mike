"""
setup_wizard.py — First-Run API Key Setup  v2.4.0
Shown when no Groq API key is configured.
Design: Mode Dark Editorial — consistent with dashboard palette.
"""

import logging
logger = logging.getLogger("mike.setup_wizard")


def show_setup_wizard() -> str:
    """
    Show a modal dialog asking for the Groq API key.
    Returns the key string if provided, or '' if cancelled/skipped.
    """
    try:
        import sys
        from PyQt6.QtWidgets import (
            QApplication, QDialog, QVBoxLayout, QHBoxLayout,
            QLabel, QLineEdit, QPushButton,
        )
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        app = QApplication.instance() or QApplication(sys.argv)

        dlg = QDialog()
        dlg.setWindowTitle("Mike — Setup")
        dlg.setFixedSize(500, 300)
        dlg.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        dlg.setStyleSheet("""
            QDialog {
                background: #121212;
            }
            QLabel {
                color: #eef2e3;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                background: #0c0c0c;
                color: #eef2e3;
                border: 1px solid #374151;
                border-radius: 4px;
                padding: 12px 16px;
                font-family: 'Times New Roman', serif;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #9ca3af;
            }
        """)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(14)

        title = QLabel("Welcome to Mike")
        title.setStyleSheet(
            "font-size: 28px; font-weight: 400; color: #eef2e3; "
            "font-family: 'Georgia', 'Times New Roman', serif; letter-spacing: -0.5px;"
        )
        layout.addWidget(title)

        sub = QLabel(
            "Enter your Groq API key to enable voice dictation.\n"
            "Get a free key at console.groq.com — no credit card needed."
        )
        sub.setStyleSheet(
            "color: #9ca3af; font-size: 13px; "
            "font-family: 'Segoe UI', sans-serif; line-height: 1.5;"
        )
        sub.setWordWrap(True)
        layout.addWidget(sub)

        key_input = QLineEdit()
        key_input.setPlaceholderText("gsk_…")
        key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_input.setFixedHeight(46)
        layout.addWidget(key_input)

        err_lbl = QLabel("")
        err_lbl.setStyleSheet("color: #d96b6b; font-size: 12px; font-family: 'Segoe UI', sans-serif;")
        layout.addWidget(err_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        skip_btn = QPushButton("Skip for now")
        skip_btn.setFixedHeight(46)
        skip_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #9ca3af;
                border: 1px solid #374151;
                border-radius: 4px;
                padding: 10px 24px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                color: #eef2e3;
                border-color: #9ca3af;
            }
        """)

        save_btn = QPushButton("Save and continue")
        save_btn.setFixedHeight(46)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #eef2e3;
                color: #043f2e;
                border: none;
                border-radius: 4px;
                padding: 10px 24px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #f5f4ef;
            }
            QPushButton:pressed {
                background: #d8dcc8;
            }
        """)

        btn_row.addWidget(skip_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        # Fixed neutral style (no accumulation)
        _neutral_style = (
            "background: #0c0c0c; color: #eef2e3; "
            "border: 1px solid #374151; border-radius: 4px; "
            "padding: 12px 16px; font-family: 'Times New Roman', serif; font-size: 14px;"
        )

        result = {"key": ""}

        def _save():
            k = key_input.text().strip()
            if not k.startswith("gsk_") or len(k) < 20:
                err_lbl.setText("Key must start with 'gsk_' and be at least 20 characters.")
                key_input.setStyleSheet(_neutral_style + " border: 1px solid #d96b6b;")
                return
            result["key"] = k
            dlg.accept()

        def _skip():
            dlg.reject()

        save_btn.clicked.connect(_save)
        skip_btn.clicked.connect(_skip)
        key_input.returnPressed.connect(_save)

        dlg.exec()
        return result["key"]

    except Exception as e:
        logger.warning(f"Setup wizard failed: {e}")
        return ""
