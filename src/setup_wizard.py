"""
setup_wizard.py — First-Run API Key Setup
Shown when no Groq API key is configured.
Simple PyQt6 dialog: enter key → validate format → return.
"""

import logging
logger = logging.getLogger("mike.setup_wizard")


def show_setup_wizard() -> str:
    """
    Show a modal dialog asking for the Groq API key.
    Returns the key string if provided, or '' if cancelled.
    """
    try:
        import sys
        from PyQt6.QtWidgets import (
            QApplication, QDialog, QVBoxLayout, QHBoxLayout,
            QLabel, QLineEdit, QPushButton, QWidget,
        )
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        app = QApplication.instance() or QApplication(sys.argv)

        dlg = QDialog()
        dlg.setWindowTitle("Mike — Setup")
        dlg.setFixedSize(480, 280)
        dlg.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        dlg.setStyleSheet("""
            QDialog {
                background: #111110;
            }
            QLabel {
                color: #f5f4f2;
                font-family: 'Segoe UI';
            }
            QLineEdit {
                background: #1c1917;
                color: #f5f4f2;
                border: 1px solid #2e2b28;
                border-radius: 8px;
                padding: 10px 14px;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #4a4540; }
            QPushButton {
                background: #2a2723;
                color: #f5f4f2;
                border: 1px solid #4a4540;
                border-radius: 8px;
                padding: 8px 20px;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QPushButton:hover { background: #3d3935; }
            QPushButton#skip {
                background: transparent;
                color: #78716c;
                border: 1px solid #2e2b28;
            }
            QPushButton#skip:hover { color: #a8a29e; border-color: #3d3935; }
        """)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        title = QLabel("Welcome to Mike")
        title.setStyleSheet("font-size: 22px; font-weight: 300; color: #f5f4f2; font-family: 'Georgia', serif;")
        layout.addWidget(title)

        sub = QLabel(
            "Enter your Groq API key to enable voice dictation.\n"
            "Get a free key at console.groq.com — no credit card needed."
        )
        sub.setStyleSheet("color: #78716c; font-size: 12px;")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        key_input = QLineEdit()
        key_input.setPlaceholderText("gsk_…")
        key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(key_input)

        err_lbl = QLabel("")
        err_lbl.setStyleSheet("color: #f87171; font-size: 11px;")
        layout.addWidget(err_lbl)

        btn_row = QHBoxLayout()
        skip_btn = QPushButton("Skip for now")
        skip_btn.setObjectName("skip")
        save_btn = QPushButton("Save and continue")
        btn_row.addWidget(skip_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        result = {"key": ""}

        def _save():
            k = key_input.text().strip()
            if not k.startswith("gsk_") or len(k) < 20:
                err_lbl.setText("Key must start with 'gsk_' and be at least 20 characters.")
                key_input.setStyleSheet(key_input.styleSheet() + "border: 1px solid #f87171;")
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
