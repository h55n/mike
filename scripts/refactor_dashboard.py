import re

path = 'f:/ANTIGRAVITY/mike/src/dashboard.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Ensure we don't double replace
if 'border-radius: 8px;' not in code or 'border-radius: 4px;' in code:
    code = re.sub(r'border-radius:\s*4px;', 'border-radius: 8px;', code)

if 'border-left: 2px solid transparent;' in code:
    nav_old = """                border-left: 2px solid transparent;
                border-radius: 0px;
                padding: 11px 16px;
                text-align: left;"""
    nav_new = """                border-radius: 8px;
                margin: 2px 12px;
                padding: 11px 16px;
                text-align: left;"""
    code = code.replace(nav_old, nav_new)

    nav_h_old = """            QPushButton:checked {
                background: rgba(4,63,46,0.35);
                color: {_SECONDARY};
                border-left: 2px solid #6ee7b7;
            }"""
    nav_h_new = """            QPushButton:checked {
                background: {_PRIMARY};
                color: {_SECONDARY};
            }"""
    code = code.replace(nav_h_old, nav_h_new)

    nav_hover_old = """            QPushButton:hover {
                background: rgba(238,242,227,0.04);
                color: {_SECONDARY};
            }"""
    nav_hover_new = """            QPushButton:hover {
                background: rgba(238,242,227,0.08);
                color: {_SECONDARY};
            }"""
    code = code.replace(nav_hover_old, nav_hover_new)

def add_log(func_name, log_stmt):
    global code
    pattern = rf"(def {func_name}\(self.*?:\n)(\s+)"
    match = re.search(pattern, code)
    if match:
        if log_stmt not in code[match.start():match.end() + 200]:
            indent = match.group(2)
            replacement = match.group(1) + indent + log_stmt + "\n" + indent
            code = code[:match.start()] + replacement + code[match.end():]

add_log('_nav_to', 'logger.info(f"Navigating to page: {key}")')
add_log('_on_search', 'logger.debug(f"Search query changed: {_text}")')
add_log('_apply_filters', 'logger.info("Applying session filters")')
add_log('_export_sessions', 'logger.info("Exporting sessions requested")')
add_log('_save_api_key', 'logger.info("Saving API key")')
add_log('_save_inject_method', 'logger.info("Saving inject method")')
add_log('_kill_mic', 'logger.warning("Kill Mike requested")')
add_log('_wake_mike', 'logger.info("Wake Mike requested")')
add_log('_load_data', 'logger.debug("Loading dashboard data from database")')
add_log('refresh', 'logger.info("Dashboard refresh triggered")')
add_log('_copy_text', 'logger.info("Session text copied to clipboard")')
add_log('_toggle_expand', 'logger.debug(f"Toggled session row expansion: {not self.expanded}")')

code = code.replace("layout.addWidget(self._build_topbar())", "        # Topbar removed for cleaner UI")

sf_old = """        filter_bar.addWidget(_lbl("Mode:"))"""
sf_new = """        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search sessions…")
        self.search_box.setFixedWidth(200)
        self.search_box.setFixedHeight(36)
        self.search_box.setStyleSheet(f\"\"\"
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
        \"\"\")
        self.search_box.textChanged.connect(self._on_search)
        
        export_btn = QPushButton("Export")
        export_btn.setObjectName("ghost_btn")
        export_btn.setFixedHeight(36)
        export_btn.clicked.connect(self._export_sessions)

        filter_bar.addWidget(self.search_box)
        filter_bar.addSpacing(16)
        filter_bar.addWidget(_lbl("Mode:"))"""
if "self.search_box = QLineEdit()" not in code:
    code = code.replace(sf_old, sf_new)

sfe_old = """        filter_bar.addStretch()
        layout.addLayout(filter_bar)"""
sfe_new = """        filter_bar.addStretch()
        filter_bar.addWidget(export_btn)
        layout.addLayout(filter_bar)"""
if "filter_bar.addWidget(export_btn)" not in code:
    code = code.replace(sfe_old, sfe_new)

code = code.replace("font-size: 10px;", "font-size: 12px;")

ss_old = """            StatCard {
                background: {_CARD_BG};
                border: 1px solid {_BORDER};
                border-radius: 8px;
                border-left: 3px solid {self.accent};
            }"""
ss_new = """            StatCard {
                background: {_CARD_BG};
                border: 1px solid {_BORDER};
                border-radius: 12px;
                border-left: 4px solid {self.accent};
            }"""
code = code.replace(ss_old, ss_new)

ssh_old = """            StatCard:hover {
                background: {_CARD_HOVER};
                border: 1px solid {_MUTED};
                border-left: 3px solid {self.accent};
            }"""
ssh_new = """            StatCard:hover {
                background: {_CARD_HOVER};
                border: 1px solid {_MUTED};
                border-left: 4px solid {self.accent};
            }"""
code = code.replace(ssh_old, ssh_new)

sr_old = """            SessionRow {
                background: {_CARD_BG};
                border: 1px solid {_BORDER};
                border-radius: 8px;
            }"""
sr_new = """            SessionRow {
                background: {_CARD_BG};
                border: 1px solid {_BORDER};
                border-radius: 12px;
            }"""
code = code.replace(sr_old, sr_new)

sc_old = """                border-radius: 8px;
            }
        \"\"\")
        return card"""
sc_new = """                border-radius: 12px;
            }
        \"\"\")
        return card"""
code = code.replace(sc_old, sc_new)

logo_old = """            font-size: 28px;"""
logo_new = """            font-size: 36px;"""
if "font-size: 28px;" in code:
    code = code.replace(logo_old, logo_new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Dashboard rewritten successfully.")
