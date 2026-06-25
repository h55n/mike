import re

# --- setup_wizard.py ---
path_setup = 'f:/ANTIGRAVITY/mike/src/setup_wizard.py'
with open(path_setup, 'r', encoding='utf-8') as f:
    setup_code = f.read()

setup_code = setup_code.replace("background: #121212;", "background: #000000;")
setup_code = setup_code.replace("color: #eef2e3;", "color: #FFFFFF;")
setup_code = setup_code.replace("font-family: 'Segoe UI', sans-serif;", "font-family: 'Inter Tight', 'Segoe UI', sans-serif;")
setup_code = setup_code.replace("font-family: 'Georgia', 'Times New Roman', serif;", "font-family: 'PT Serif', serif;")
setup_code = setup_code.replace("font-family: 'Times New Roman', serif;", "font-family: 'Inter Tight', 'Segoe UI', sans-serif;")
setup_code = setup_code.replace("font-size: 28px;", "font-size: 41px; letter-spacing: -1.134px;")
setup_code = setup_code.replace("background: #0c0c0c;", "background: #FFFFFF;")
setup_code = setup_code.replace("color: #eef2e3;\\n                border: 1px solid #374151;", "color: #000000;\\n                border: 1px solid #E5E7EB;")
setup_code = setup_code.replace("border-radius: 4px;", "border-radius: 0px;")
setup_code = setup_code.replace("border: 1px solid #9ca3af;", "border: 1px solid #000000;")
setup_code = setup_code.replace("color: #9ca3af;", "color: #E5E7EB;")

# Primary button (save_btn)
save_btn_style = """            QPushButton {
                background: #C5FF4A;
                color: #000000;
                border: none;
                border-radius: 0px;
                padding: 10px 24px;
                font-family: 'Inter Tight', 'Segoe UI', sans-serif;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.16em;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background: #B0E645;
            }
            QPushButton:pressed {
                background: #96C93C;
            }"""
setup_code = re.sub(r'            QPushButton {\n                background: #eef2e3;.*?background: #d8dcc8;\n            }', save_btn_style, setup_code, flags=re.DOTALL)

# Secondary button (skip_btn)
skip_btn_style = """            QPushButton {
                background: transparent;
                color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 0px;
                padding: 10px 24px;
                font-family: 'Inter Tight', 'Segoe UI', sans-serif;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.16em;
                text-transform: uppercase;
            }
            QPushButton:hover {
                color: #FFFFFF;
                border-color: #FFFFFF;
                background: rgba(255,255,255,0.05);
            }"""
setup_code = re.sub(r'            QPushButton {\n                background: transparent;\n                color: #9ca3af;.*?border-color: #9ca3af;\n            }', skip_btn_style, setup_code, flags=re.DOTALL)

# Update neutral style variable
setup_code = setup_code.replace(
    "background: #0c0c0c; color: #eef2e3; border: 1px solid #374151; border-radius: 4px; padding: 12px 16px; font-family: 'Times New Roman', serif; font-size: 14px;",
    "background: #FFFFFF; color: #000000; border: 1px solid #E5E7EB; border-radius: 0px; padding: 12px 16px; font-family: 'Inter Tight', 'Segoe UI', sans-serif; font-size: 14px;"
)
setup_code = setup_code.replace("border: 1px solid #d96b6b;", "border: 1px solid #FF4D4F;")

with open(path_setup, 'w', encoding='utf-8') as f:
    f.write(setup_code)

# --- hud.py ---
path_hud = 'f:/ANTIGRAVITY/mike/src/hud.py'
with open(path_hud, 'r', encoding='utf-8') as f:
    hud_code = f.read()

hud_tokens = """BG_PILL        = "#000000"      # Deep black
BG_HOVER       = "#000000"      # Deep black hover
BORDER_IDLE    = "#333333"      # Subtle border
BORDER_ACTIVE  = "#E5E7EB"      # Neutral light border
TEXT_PRIMARY   = "#FFFFFF"      # White body text
TEXT_MUTED     = "#9CA3AF"      # Muted gray
ACCENT_PINK    = "#C5FF4A"      # Lime accent
ACCENT_GREEN   = "#C5FF4A"      # Lime confirm
ACCENT_RED     = "#FF4D4F"      # Error red
ACCENT_AMBER   = "#C5FF4A"      # Lime recording"""

hud_code = re.sub(r'BG_PILL.*?ACCENT_AMBER.*?#fbbf24.*?\n', hud_tokens + '\n', hud_code, flags=re.DOTALL)
hud_code = hud_code.replace('FONT_BODY   = ("Segoe UI", 7, "normal")', 'FONT_BODY   = ("Inter Tight", 8, "normal")')
hud_code = hud_code.replace('FONT_SMALL  = ("Segoe UI", 7, "normal")', 'FONT_SMALL  = ("Inter Tight", 8, "normal")')
hud_code = hud_code.replace('FONT_BADGE  = ("Segoe UI", 6, "bold")', 'FONT_BADGE  = ("Inter Tight", 6, "bold")')

# Change _draw_pill to draw a sharp rectangle instead of a polygon capsule
draw_pill_old = """    def _draw_pill(self, c, w, h, r, fill, outline):
        \"\"\"
        Draw a silky-smooth pill shape.
        Steps=32 + smooth=True gives perfect anti-aliased capsule curves.
        Canvas bg is the chromakey so corners are transparent to the desktop.
        \"\"\"
        x0, y0, x1, y1 = 1, 1, w - 1, h - 1
        points = []
        steps = 32
        # Left semicircle
        cx, cy = x0 + r, y0 + r
        for i in range(steps + 1):
            angle = math.pi / 2 + math.pi * i / steps
            points.extend([cx + r * math.cos(angle), cy + r * math.sin(angle)])
        # Right semicircle
        cx, cy = x1 - r, y0 + r
        for i in range(steps + 1):
            angle = -math.pi / 2 + math.pi * i / steps
            points.extend([cx + r * math.cos(angle), cy + r * math.sin(angle)])
        c.create_polygon(points, fill=fill, outline=outline, width=1, smooth=True)"""

draw_pill_new = """    def _draw_pill(self, c, w, h, r, fill, outline):
        \"\"\"
        Draw a sharp rectangle (zkPass Neon Serif).
        \"\"\"
        c.create_rectangle(1, 1, w - 1, h - 1, fill=fill, outline=outline, width=1)"""

hud_code = hud_code.replace(draw_pill_old, draw_pill_new)

# Simplify waveform colors to just use Lime
waveform_color_old = """                # Lerp between ACCENT_PINK (#f472b6) and muted grey (#555555)
                r_c = int(244 - center_dist * (244 - 85))
                g_c = int(114 - center_dist * (114 - 85))
                b_c = int(182 - center_dist * (182 - 85))
                # Modulate by amplitude
                r_c = max(0, min(255, int(r_c * (0.5 + 0.5 * amp))))
                g_c = max(0, min(255, int(g_c * (0.5 + 0.5 * amp))))
                b_c = max(0, min(255, int(b_c * (0.5 + 0.5 * amp))))
                col = f"#{r_c:02x}{g_c:02x}{b_c:02x}\""""

waveform_color_new = """                r_c = 197 # C5
                g_c = 255 # FF
                b_c = 74  # 4A
                r_c = max(0, min(255, int(r_c * (0.3 + 0.7 * amp))))
                g_c = max(0, min(255, int(g_c * (0.3 + 0.7 * amp))))
                b_c = max(0, min(255, int(b_c * (0.3 + 0.7 * amp))))
                col = f"#{r_c:02x}{g_c:02x}{b_c:02x}\""""

hud_code = hud_code.replace(waveform_color_old, waveform_color_new)

# Spinner pink accent -> Lime accent
spinner_color_old = """                # Pink gradient: brightest dot is pink, others fade to grey
                r_val = int(alpha * 244)
                g_val = int(alpha * 114 * 0.5)
                b_val = int(alpha * 182 * 0.5)"""
spinner_color_new = """                # Lime gradient
                r_val = int(alpha * 197)
                g_val = int(alpha * 255)
                b_val = int(alpha * 74)"""
hud_code = hud_code.replace(spinner_color_old, spinner_color_new)

# LIVE dot glowing ring
pulse_ring_old = """                      fill="", outline="#22c55e44" if self._cont_pulse > 0.6 else "#22c55e22","""
pulse_ring_new = """                      fill="", outline="#C5FF4A44" if self._cont_pulse > 0.6 else "#C5FF4A22","""
hud_code = hud_code.replace(pulse_ring_old, pulse_ring_new)

pulse_dot_old = """        c.create_oval(dot_x - dot_r, mid_y - dot_r,
                      dot_x + dot_r, mid_y + dot_r,
                      fill=dot_col, outline="#22c55e", width=1)"""
pulse_dot_new = """        c.create_oval(dot_x - dot_r, mid_y - dot_r,
                      dot_x + dot_r, mid_y + dot_r,
                      fill=dot_col, outline="#C5FF4A", width=1)"""
hud_code = hud_code.replace(pulse_dot_old, pulse_dot_new)
hud_code = hud_code.replace('fill="#4ade80", anchor="w")', 'fill="#C5FF4A", anchor="w")')

with open(path_hud, 'w', encoding='utf-8') as f:
    f.write(hud_code)

print("Setup Wizard and HUD refactor scripts executed successfully.")
