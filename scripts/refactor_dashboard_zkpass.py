import re

path = 'f:/ANTIGRAVITY/mike/src/dashboard.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update Design Tokens
tokens_old = """# ─── Design Tokens (Mode Dark Editorial) ─────────────────────────────────────
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
_PRIMARY_HOVER   = "#065a40"   # button hover"""

tokens_new = """# ─── Design Tokens (zkPass Neon Serif) ───────────────────────────────────────
# Core palette
_PRIMARY      = "#C5FF4A"   # vivid lime accent
_SECONDARY    = "#FFFFFF"   # pure white text on dark
_TERTIARY     = "#000000"   # deep black background
_SURFACE      = "#000000"   # black surface
_BORDER       = "#E5E7EB"   # neutral light border
_MUTED        = "#9ca3af"   # muted grey for low emphasis
_ERROR        = "#FF4D4F"   # red
_NEUTRAL      = "#E5E7EB"   # neutral grey

# Derived interaction shades
_SURFACE_HOVER   = "#111111"   # dark hover
_CARD_BG         = "#FFFFFF"   # cards are white in this system
_CARD_HOVER      = "#FAFAFA"   # light hover for cards
_SIDEBAR_BG      = "#000000"   # black sidebar
_INPUT_BG        = "#FFFFFF"   # white inputs
_PRIMARY_HOVER   = "#B0E645"   # lime darker hover"""

if tokens_old in code:
    code = code.replace(tokens_old, tokens_new)

# 2. Update QSS_MAIN
# Re-write QSS_MAIN entirely
qss_pattern = r'QSS_MAIN = f"""\n.*?# ─── Mode Indicator ───'
qss_new = """QSS_MAIN = f\"\"\"
/* ── Root ── */
QMainWindow, QWidget#root {
    background: {_TERTIARY};
}
QWidget {
    font-family: 'Inter Tight', 'Segoe UI', sans-serif;
}

/* ── Scroll bars ── */
QScrollArea {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: {_TERTIARY};
    width: 4px;
    border-radius: 0px;
    margin: 2px 0;
}
QScrollBar::handle:vertical {
    background: {_MUTED};
    border-radius: 0px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: {_SECONDARY};
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

/* ── Inputs ── */
QLineEdit {
    background: {_INPUT_BG};
    color: #000000;
    border: 1px solid {_BORDER};
    border-radius: 0px;
    padding: 14px 16px;
    font-family: 'Inter Tight', 'Segoe UI', sans-serif;
    font-size: 15px;
    selection-background-color: {_PRIMARY};
    selection-color: #000000;
}
QLineEdit:focus {
    border: 1px solid #000000;
    background: #FFFFFF;
}
QLineEdit::placeholder {
    color: {_MUTED};
}

/* ── ComboBox ── */
QComboBox {
    background: {_INPUT_BG};
    color: #000000;
    border: 1px solid {_BORDER};
    border-radius: 0px;
    padding: 8px 12px;
    font-family: 'Inter Tight', 'Segoe UI', sans-serif;
    font-size: 12px;
    font-weight: 600;
    min-height: 36px;
    text-transform: uppercase;
    letter-spacing: 0.16em;
}
QComboBox:hover {
    border: 1px solid #000000;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF;
    color: #000000;
    border: 1px solid {_BORDER};
    selection-background-color: {_PRIMARY};
    selection-color: #000000;
    padding: 4px;
    outline: none;
}

/* ── Buttons ── */

/* Primary: lime fill, black text, no radius */
QPushButton#primary_btn {
    background: {_PRIMARY};
    color: #000000;
    border: none;
    border-radius: 0px;
    padding: 19px 16px;
    height: 48px;
    font-family: 'Inter Tight', 'Segoe UI', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}
QPushButton#primary_btn:hover {
    background: {_PRIMARY_HOVER};
}
QPushButton#primary_btn:pressed {
    background: #96C93C;
}

/* Secondary: transparent, black/white text depending on context, no radius */
QPushButton#secondary_btn {
    background: transparent;
    color: {_SECONDARY};
    border: 1px solid {_BORDER};
    border-radius: 0px;
    padding: 19px 16px;
    height: 48px;
    font-family: 'Inter Tight', 'Segoe UI', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}
QPushButton#secondary_btn:hover {
    border-color: {_SECONDARY};
    background: rgba(255,255,255,0.05);
}

/* Ghost: nav-style smaller button */
QPushButton#ghost_btn {
    background: transparent;
    color: {_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 0px;
    padding: 10px 20px;
    font-family: 'Inter Tight', 'Segoe UI', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}
QPushButton#ghost_btn:hover {
    color: {_SECONDARY};
    border-color: {_SECONDARY};
}

/* Copy button */
QPushButton#copy_btn {
    background: transparent;
    color: {_MUTED};
    border: none;
    font-size: 16px;
}
QPushButton#copy_btn:hover {
    color: {_SECONDARY};
}

# ─── Mode Indicator ───"""
code = re.sub(qss_pattern, qss_new, code, flags=re.DOTALL)

# 3. Update Title text (StatCard and Header)
code = code.replace("font-family: 'Georgia', 'Times New Roman', serif;", "font-family: 'PT Serif', serif;")
code = code.replace("font-family: 'Times New Roman', serif;", "font-family: 'PT Serif', serif;")

# 4. Search box inline styles
sb_old = """            QLineEdit {
                background: {_INPUT_BG};
                color: {_SECONDARY};
                border: 1px solid {_BORDER};
                border-radius: 8px;
                padding: 8px 14px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }"""
sb_new = """            QLineEdit {
                background: {_INPUT_BG};
                color: #000000;
                border: 1px solid {_BORDER};
                border-radius: 0px;
                padding: 8px 14px;
                font-family: 'Inter Tight', 'Segoe UI', sans-serif;
                font-size: 13px;
            }"""
code = code.replace(sb_old, sb_new)

# 5. Fix card text colors (since cards are white now, text must be black)
# In StatCard:
# self.value_lbl uses _SECONDARY (white). It should be black inside a white card.
code = code.replace("color: {_SECONDARY}; font-size: 32px;", "color: #000000; font-size: 32px;")
code = code.replace("color: {_MUTED}; font-size: 11px;", "color: #666666; font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em;")
code = code.replace("border-radius: 12px;", "border-radius: 8px;")
# In SessionRow:
code = code.replace('self.text_lbl.setStyleSheet(f"color: {_SECONDARY}; font-size: 13px;")', 'self.text_lbl.setStyleSheet("color: #000000; font-size: 15px;")')
code = code.replace('time_lbl.setStyleSheet(f"color: {_MUTED}; font-size: 11px;")', 'time_lbl.setStyleSheet("color: #666666; font-size: 11px;")')
code = code.replace('self.setStyleSheet(f"background: {_CARD_BG}; border-radius: 12px;")', 'self.setStyleSheet(f"background: {_CARD_BG}; border-radius: 8px;")')
code = code.replace('self.setStyleSheet(f"background: {_CARD_HOVER}; border-radius: 12px;")', 'self.setStyleSheet(f"background: {_CARD_HOVER}; border-radius: 8px;")')
code = code.replace('self.text_edit.setStyleSheet(f"color: {_SECONDARY};', 'self.text_edit.setStyleSheet(f"color: #000000;')

# Top layout labels
code = code.replace('color: {_SECONDARY}; font-size: 28px;', 'color: {_SECONDARY}; font-size: 41px;')

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Dashboard UI refactor script executed successfully.")
