"""
hud.py — Floating HUD for Mike
Three states: SILENT (tiny pill) → HOVER (expanded with hints) → RECORDING (waveform)
Design: Dark surface, off-white text, pink accent for hotkeys, ElevenLabs-inspired

Fixes applied in this version:
  - HWND WS_EX_NOACTIVATE now correctly ADDED (not removed) — window no longer steals focus
  - _apply_geometry() preserves dragged position instead of forcing center
  - Unused 'start_w' variable removed from _animate_step
  - Waveform bars now use a warm amber/pink gradient accent
  - Green dot color formula guarded against values <80 (valid hex always)
  - show_notification expands to hover size so text never overflows
  - Hover expand delay reduced to 60 ms for snappier feel
  - ANIM_STEPS increased to 10, ANIM_DELAY lowered to 14 ms for smoother motion
  - Continuous LIVE dot now has glow ring for premium look
  - Recording waveform bars use accent-colored gradient
  - Processing spinner uses pink accent dots
  - HUD position saved on every geometry update during drag
"""

import tkinter as tk
import math
import threading
import ctypes
import time


# ─── Design Tokens ───────────────────────────────────────────────────────────
BG_PILL        = "#000000"      # Deep black
BG_HOVER       = "#000000"      # Deep black hover
BORDER_IDLE    = "#333333"      # Subtle border
BORDER_ACTIVE  = "#E5E7EB"      # Neutral light border
TEXT_PRIMARY   = "#FFFFFF"      # White body text
TEXT_MUTED     = "#9CA3AF"      # Muted gray
ACCENT_PINK    = "#C5FF4A"      # Lime accent
ACCENT_GREEN   = "#C5FF4A"      # Lime confirm
ACCENT_RED     = "#FF4D4F"      # Error red
ACCENT_AMBER   = "#C5FF4A"      # Lime recording

FONT_BODY   = ("Inter Tight", 8, "normal")
FONT_SMALL  = ("Inter Tight", 8, "normal")
FONT_BADGE  = ("Inter Tight", 6, "bold")

# Window geometry
PILL_W, PILL_H         = 68, 16       # Silent collapsed pill
HOVER_W, HOVER_H       = 152, 52      # Hover expanded
RECORD_W, RECORD_H     = 156, 30      # PTT recording with waveform
CONT_W,   CONT_H       = 124, 22      # Continuous mode LIVE indicator
NOTIF_W,  NOTIF_H      = 160, 26      # Notification toast size

TASKBAR_H     = 52
MARGIN_BOTTOM = 22    # Just above taskbar — lower, comfortable gap
ANIM_STEPS    = 10    # More steps = smoother
ANIM_DELAY    = 14    # ms per frame — ~70 fps feel

WAVEFORM_BARS   = 9
WAVEFORM_MAX_H  = 13
WAVEFORM_MIN_H  = 3

# Alpha per state
ALPHA_SILENT    = 0.58
ALPHA_ACTIVE    = 0.97
ALPHA_CONT      = 0.92   # Continuous mode — visible but not intrusive

# Continuous pulse animation
CONT_PULSE_MAX  = 0.88
CONT_PULSE_MIN  = 0.30


class MikeHUD:
    def __init__(self, engine_ref=None):
        self.engine = engine_ref
        self.root   = tk.Tk()

        self._state            = "silent"
        self._prev_state       = "silent"
        self._mode             = "raw"
        self._wave_phase       = 0.0
        self._wave_amplitudes  = [0.3] * WAVEFORM_BARS
        self._audio_level      = 0.0
        self._cont_pulse       = CONT_PULSE_MIN   # for continuous dot pulse
        self._cont_pulse_dir   = 1
        self._drag_x           = 0
        self._drag_y           = 0
        self._drag_win_x       = 0
        self._drag_win_y       = 0
        self._is_dragging      = False
        self._hover_timer      = None
        self._anim_frame       = None
        self._current_w        = PILL_W
        self._current_h        = PILL_H
        self._target_w         = PILL_W
        self._target_h         = PILL_H
        # Track window position separately from geometry calls
        self._win_x            = None
        self._win_y            = None
        self._elapsed_seconds  = 0
        self._elapsed_timer    = None
        self._canvas           = None

        self._setup_window()
        self._build_ui()
        self._position_window()
        self._bind_events()
        self._start_waveform_loop()

        # Defer HWND styling until after the window is actually mapped
        self.root.after(200, self._apply_hwnd_styles)

    # ─── Window Setup ─────────────────────────────────────────────────────────

    def _setup_window(self):
        r = self.root
        r.title("Mike HUD")
        r.overrideredirect(True)
        r.wm_attributes("-topmost", True)
        r.wm_attributes("-alpha", ALPHA_SILENT)
        # Chromakey colour — must not appear in any pill fill
        # Corners painted this colour will be fully transparent
        CHROMA = "#010101"
        r.configure(bg=CHROMA)
        r.wm_attributes("-transparentcolor", CHROMA)

    def _apply_hwnd_styles(self):
        """
        Remove from Alt+Tab and taskbar.
        Add WS_EX_NOACTIVATE so window never steals keyboard focus.
        Must run after window is mapped so FindWindowW succeeds.
        """
        GWL_EXSTYLE      = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_NOACTIVATE = 0x08000000
        WS_EX_LAYERED    = 0x00080000
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "Mike HUD")
            if hwnd:
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                # ADD WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE, WS_EX_LAYERED
                new_style = style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_LAYERED
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        except Exception:
            pass

    def _position_window(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        default_x = (sw - self._current_w) // 2
        default_y = sh - TASKBAR_H - self._current_h - MARGIN_BOTTOM

        # Restore saved position if engine/settings available
        x, y = default_x, default_y
        if self.engine and hasattr(self.engine, "settings"):
            try:
                sx = self.engine.settings.get("hud_x")
                sy = self.engine.settings.get("hud_y")
                if sx is not None and sy is not None:
                    x = int(sx)
                    y = int(sy)
                    # Clamp to screen bounds
                    x = max(0, min(x, sw - self._current_w))
                    y = max(0, min(y, sh - self._current_h))
            except Exception:
                x, y = default_x, default_y

        self._win_x = x
        self._win_y = y
        self.root.geometry(f"{self._current_w}x{self._current_h}+{x}+{y}")

    # ─── Canvas UI Builder ────────────────────────────────────────────────────

    def _build_ui(self):
        CHROMA = "#010101"
        self._canvas = tk.Canvas(
            self.root,
            width=self._current_w,
            height=self._current_h,
            bg=CHROMA,        # Corners stay chroma → transparent to desktop
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True)
        self._render_state()

    def _render_state(self):
        c = self._canvas
        c.delete("all")
        w, h = self._current_w, self._current_h
        r = h // 2

        if self._state == "silent":
            self.root.wm_attributes("-alpha", ALPHA_SILENT)
            self._draw_pill(c, w, h, r, BG_PILL, BORDER_IDLE)
            cx, cy = w // 2, h // 2
            # Pulsing mic dot in silent state
            c.create_oval(cx - 3, cy - 4, cx + 3, cy + 4,
                          fill=TEXT_MUTED, outline="")

        elif self._state == "hover":
            self.root.wm_attributes("-alpha", ALPHA_ACTIVE)
            self._draw_pill(c, w, h, r, BG_HOVER, BORDER_ACTIVE)
            self._draw_hover_content(c, w, h)

        elif self._state == "continuous":
            self.root.wm_attributes("-alpha", ALPHA_CONT)
            self._draw_pill(c, w, h, r, BG_PILL, "#22c55e")
            self._draw_continuous_content(c, w, h)

        elif self._state in ("recording", "processing"):
            self.root.wm_attributes("-alpha", ALPHA_ACTIVE)
            self._draw_pill(c, w, h, r, BG_PILL, BORDER_ACTIVE)
            self._draw_record_content(c, w, h)

    def _draw_pill(self, c, w, h, r, fill, outline):
        """
        Draw a sharp rectangle (zkPass Neon Serif).
        """
        c.create_rectangle(1, 1, w - 1, h - 1, fill=fill, outline=outline, width=1)

    def _draw_continuous_content(self, c, w, h):
        """Continuous mode: pulsing green dot + LIVE label + red X stop button."""
        mid_y = h // 2

        # Red X stop button (right side)
        x_r   = 9
        x_x   = w - x_r - 4
        c.create_oval(x_x - x_r, mid_y - x_r,
                      x_x + x_r, mid_y + x_r,
                      fill="#2a1a1a", outline="#f87171", width=1,
                      tags="cont_stop_btn")
        c.create_text(x_x, mid_y, text="×",
                      font=("Segoe UI", 10, "bold"),
                      fill="#f87171", anchor="center",
                      tags="cont_stop_btn")

        # Pulsing green dot (left) — clamp brightness to valid 0–255 range
        dot_r = int(3 + 2 * self._cont_pulse)
        dot_x = 14
        brightness = max(0, min(255, int(80 + 175 * self._cont_pulse)))
        dot_col = f"#00{brightness:02x}00"

        # Outer glow ring
        glow_r = dot_r + 2
        c.create_oval(dot_x - glow_r, mid_y - glow_r,
                      dot_x + glow_r, mid_y + glow_r,
                      fill="", outline="#C5FF4A44" if self._cont_pulse > 0.6 else "#C5FF4A22",
                      width=1)
        c.create_oval(dot_x - dot_r, mid_y - dot_r,
                      dot_x + dot_r, mid_y + dot_r,
                      fill=dot_col, outline="#C5FF4A", width=1)

        # LIVE label (centre-left)
        c.create_text(dot_x + 14, mid_y, text="LIVE",
                      font=("Segoe UI", 7, "bold"),
                      fill="#C5FF4A", anchor="w")

    def _draw_hover_content(self, c, w, h):
        """Hover: Dictate label + hotkey + mode/settings/dashboard buttons."""
        # Top row
        mid_y = 15
        c.create_text(w // 2 - 14, mid_y, text="Dictate",
                      font=("Segoe UI", 7, "normal"), fill=TEXT_PRIMARY, anchor="e")
        c.create_text(w // 2 - 9, mid_y, text="Ctrl+Shift",
                      font=("Segoe UI", 7, "bold"), fill=ACCENT_PINK, anchor="w")

        # Bottom row: 3 icon buttons
        badge_y = 37
        r_btn = 9

        # Mode badge (left) — cycles RAW / SF / POL on click
        mode_label = {"raw": "RAW", "semi_formal": "SF", "polished": "POL"}.get(self._mode, "RAW")
        mode_color  = {"raw": TEXT_MUTED, "semi_formal": ACCENT_GREEN, "polished": "#93c5fd"}.get(self._mode, TEXT_MUTED)
        bx = 22
        c.create_oval(bx - r_btn, badge_y - r_btn, bx + r_btn, badge_y + r_btn,
                      fill="#2a2723", outline=BORDER_ACTIVE, width=1)
        c.create_text(bx, badge_y, text=mode_label, font=FONT_BADGE,
                      fill=mode_color, anchor="center", tags="mode_badge")

        # Settings/Edit button (centre) — gear symbol
        ex = w // 2
        c.create_oval(ex - r_btn, badge_y - r_btn, ex + r_btn, badge_y + r_btn,
                      fill="#2a2723", outline=BORDER_ACTIVE, width=1)
        c.create_text(ex, badge_y, text="\u2699",   # ⚙ gear
                      font=("Segoe UI", 8),
                      fill=TEXT_MUTED, anchor="center", tags="edit_btn")

        # Dashboard button (right) — triple bar
        dx = w - 22
        c.create_oval(dx - r_btn, badge_y - r_btn, dx + r_btn, badge_y + r_btn,
                      fill="#2a2723", outline=BORDER_ACTIVE, width=1)
        c.create_text(dx, badge_y, text="\u2261",   # ≡ triple bar / dashboard
                      font=("Segoe UI", 10, "bold"),
                      fill=TEXT_MUTED, anchor="center", tags="dash_btn")

    def _draw_record_content(self, c, w, h):
        """Recording/processing state: X | waveform/spinner | checkmark."""
        mid_y = h // 2

        # X button
        c.create_oval(4, mid_y - 9, 20, mid_y + 9,
                      fill="#2a1a1a", outline=ACCENT_RED, width=1)
        c.create_text(12, mid_y, text="✕", font=("Segoe UI", 7, "bold"),
                      fill=ACCENT_RED, anchor="center", tags="cancel_btn")

        # Checkmark button
        c.create_oval(w - 20, mid_y - 9, w - 4, mid_y + 9,
                      fill="#1a2a1a", outline=ACCENT_GREEN, width=1)
        c.create_text(w - 12, mid_y, text="✓", font=("Segoe UI", 7, "bold"),
                      fill=ACCENT_GREEN, anchor="center", tags="confirm_btn")

        if self._state == "processing":
            # Spinner dots with pink accent
            cx_s = w // 2
            dot_r = 2
            for i in range(8):
                angle = math.pi * 2 * i / 8 + self._wave_phase
                dx_s = cx_s + 12 * math.cos(angle)
                dy_s = mid_y + 6 * math.sin(angle)
                idx = (i + int(self._wave_phase * 4 / math.pi)) % 8
                alpha = 0.15 + 0.85 * (idx / 8)
                # Lime gradient
                r_val = int(alpha * 197)
                g_val = int(alpha * 255)
                b_val = int(alpha * 74)
                r_val = max(0, min(255, r_val))
                g_val = max(0, min(255, g_val))
                b_val = max(0, min(255, b_val))
                col = f"#{r_val:02x}{g_val:02x}{b_val:02x}"
                c.create_oval(dx_s - dot_r, dy_s - dot_r, dx_s + dot_r, dy_s + dot_r,
                              fill=col, outline="")
        else:
            # Waveform bars with warm accent gradient
            bar_w = 2
            spacing = 3
            total_bar_w = WAVEFORM_BARS * (bar_w + spacing) - spacing
            start_x = (w - total_bar_w) // 2
            center_i = WAVEFORM_BARS // 2
            for i, amp in enumerate(self._wave_amplitudes):
                bar_h = max(2, int(WAVEFORM_MIN_H + (WAVEFORM_MAX_H - WAVEFORM_MIN_H) * amp))
                bx = start_x + i * (bar_w + spacing)
                by = mid_y - bar_h // 2
                # Color: center bars pink/amber, outer bars muted
                center_dist = abs(i - center_i) / max(center_i, 1)
                r_c = 197 # C5
                g_c = 255 # FF
                b_c = 74  # 4A
                r_c = max(0, min(255, int(r_c * (0.3 + 0.7 * amp))))
                g_c = max(0, min(255, int(g_c * (0.3 + 0.7 * amp))))
                b_c = max(0, min(255, int(b_c * (0.3 + 0.7 * amp))))
                col = f"#{r_c:02x}{g_c:02x}{b_c:02x}"
                # Rounded rectangle via two rects + oval top/bottom
                c.create_rectangle(bx, by, bx + bar_w, by + bar_h,
                                   fill=col, outline="")

    # ─── State Machine ────────────────────────────────────────────────────────

    def set_state(self, state: str):
        """Thread-safe state change."""
        self.root.after(0, self._set_state_main, state)

    def _set_state_main(self, state: str):
        if state == self._state:
            return
        self._prev_state = self._state
        self._state = state

        if state == "silent":
            self._stop_elapsed_timer()
            self._animate_to(PILL_W, PILL_H)
        elif state == "hover":
            self._animate_to(HOVER_W, HOVER_H)
        elif state == "continuous":
            self._stop_elapsed_timer()
            self._animate_to(CONT_W, CONT_H)
        elif state == "recording":
            self._elapsed_seconds = 0
            self._start_elapsed_timer()
            self._animate_to(RECORD_W, RECORD_H)
        elif state == "processing":
            self._stop_elapsed_timer()
            self._animate_to(RECORD_W, RECORD_H)

    def set_mode(self, mode: str):
        self._mode = mode
        self.root.after(0, self._render_state)

    def set_audio_level(self, level: float):
        self._audio_level = max(0.0, min(1.0, level))

    # ─── Animation ────────────────────────────────────────────────────────────

    def _animate_to(self, target_w, target_h):
        self._target_w = target_w
        self._target_h = target_h
        if self._anim_frame:
            self.root.after_cancel(self._anim_frame)
            self._anim_frame = None
        self._anim_start_w = self._current_w
        self._anim_start_h = self._current_h
        self._animate_step(0)

    def _animate_step(self, step):
        if step >= ANIM_STEPS:
            self._current_w = self._target_w
            self._current_h = self._target_h
            self._apply_geometry()
            self._render_state()
            return

        # Ease out cubic for smooth deceleration
        t = (step + 1) / ANIM_STEPS
        t_eased = 1 - (1 - t) ** 3

        self._current_w = int(self._anim_start_w + (self._target_w - self._anim_start_w) * t_eased)
        self._current_h = int(self._anim_start_h + (self._target_h - self._anim_start_h) * t_eased)
        self._apply_geometry()
        self._render_state()

        self._anim_frame = self.root.after(ANIM_DELAY, self._animate_step, step + 1)

    def _apply_geometry(self):
        """
        Resize the window while keeping it centred horizontally —
        UNLESS the user has dragged it, in which case preserve their X.
        We track whether the window was ever dragged in self._win_x / _win_y.
        During an animation the width changes, so re-centre horizontally
        around the *saved* centre point, not the raw saved x.
        """
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        if self._win_x is None:
            # Initial position — centre bottom
            x = (sw - self._current_w) // 2
            y = sh - TASKBAR_H - self._current_h - MARGIN_BOTTOM
        else:
            # Keep the window centred on the saved centre-x (survives width changes)
            saved_center_x = self._win_x + (self._target_w // 2 if not self._is_dragging else self._current_w // 2)
            x = saved_center_x - self._current_w // 2
            x = max(0, min(x, sw - self._current_w))
            y = self._win_y
            # Clamp y to screen
            y = max(0, min(y, sh - self._current_h))

        self._canvas.config(width=self._current_w, height=self._current_h)
        self.root.geometry(f"{self._current_w}x{self._current_h}+{x}+{y}")

    # ─── Waveform Loop ────────────────────────────────────────────────────────

    def _start_waveform_loop(self):
        self._waveform_tick()

    def _waveform_tick(self):
        self._wave_phase += 0.15
        if self._wave_phase > math.pi * 2:
            self._wave_phase -= math.pi * 2

        if self._state == "recording":
            for i in range(WAVEFORM_BARS):
                phase_offset = i * 0.45
                base = 0.15 + 0.4 * self._audio_level
                variation = 0.3 * math.sin(self._wave_phase * 2.5 + phase_offset)
                target_amp = max(0.05, min(1.0, base + variation))
                self._wave_amplitudes[i] += (target_amp - self._wave_amplitudes[i]) * 0.3
            self._render_state()
        elif self._state == "processing":
            self._render_state()
        elif self._state == "continuous":
            # Pulse the green dot
            step = 0.055
            self._cont_pulse += step * self._cont_pulse_dir
            if self._cont_pulse >= CONT_PULSE_MAX:
                self._cont_pulse = CONT_PULSE_MAX
                self._cont_pulse_dir = -1
            elif self._cont_pulse <= CONT_PULSE_MIN:
                self._cont_pulse = CONT_PULSE_MIN
                self._cont_pulse_dir = 1
            self._render_state()

        self.root.after(45, self._waveform_tick)

    # ─── Elapsed Timer ────────────────────────────────────────────────────────

    def _start_elapsed_timer(self):
        self._elapsed_timer = self.root.after(1000, self._tick_elapsed)

    def _tick_elapsed(self):
        self._elapsed_seconds += 1
        if self._state == "recording":
            self._elapsed_timer = self.root.after(1000, self._tick_elapsed)

    def _stop_elapsed_timer(self):
        if self._elapsed_timer:
            self.root.after_cancel(self._elapsed_timer)
            self._elapsed_timer = None

    # ─── Event Bindings ───────────────────────────────────────────────────────

    def _bind_events(self):
        c = self._canvas
        c.bind("<Enter>",         self._on_mouse_enter)
        c.bind("<Leave>",         self._on_mouse_leave)
        c.bind("<ButtonPress-1>", self._on_drag_start)
        c.bind("<B1-Motion>",     self._on_drag_motion)
        c.bind("<ButtonRelease-1>", self._on_drag_end)
        c.tag_bind("cancel_btn",    "<Button-1>", self._on_cancel)
        c.tag_bind("confirm_btn",   "<Button-1>", self._on_confirm)
        c.tag_bind("mode_badge",    "<Button-1>", self._on_mode_click)
        c.tag_bind("dash_btn",      "<Button-1>", self._on_dashboard)
        c.tag_bind("edit_btn",      "<Button-1>", self._on_edit)
        c.tag_bind("cont_stop_btn", "<Button-1>", self._on_stop_continuous)

    def _on_mouse_enter(self, event):
        if self._hover_timer:
            self.root.after_cancel(self._hover_timer)
            self._hover_timer = None
        if self._state == "silent":
            self._hover_timer = self.root.after(60, self._do_hover_expand)

    def _do_hover_expand(self):
        self._hover_timer = None
        self._set_state_main("hover")

    def _on_mouse_leave(self, event):
        if self._hover_timer:
            self.root.after_cancel(self._hover_timer)
            self._hover_timer = None
        if self._state == "hover":
            self._hover_timer = self.root.after(220, self._do_hover_collapse)

    def _do_hover_collapse(self):
        self._hover_timer = None
        self._set_state_main("silent")

    def _on_drag_start(self, event):
        self._drag_x = event.x_root
        self._drag_y = event.y_root
        self._drag_win_x = self.root.winfo_x()
        self._drag_win_y = self.root.winfo_y()
        self._is_dragging = True
        if self._hover_timer:
            self.root.after_cancel(self._hover_timer)
            self._hover_timer = None

    def _on_drag_motion(self, event):
        dx = event.x_root - self._drag_x
        dy = event.y_root - self._drag_y
        x = self._drag_win_x + dx
        y = self._drag_win_y + dy
        self._win_x = x
        self._win_y = y
        self.root.geometry(f"+{x}+{y}")

    def _on_drag_end(self, event):
        self._is_dragging = False
        # Save position after drag
        self._win_x = self.root.winfo_x()
        self._win_y = self.root.winfo_y()
        if self.engine:
            try:
                self.engine.settings.set("hud_x", str(self._win_x))
                self.engine.settings.set("hud_y", str(self._win_y))
            except Exception:
                pass

    def _on_cancel(self, event):
        """X button in recording/processing state — nuclear kill."""
        if self.engine:
            threading.Thread(target=self.engine.force_stop_mic, daemon=True).start()
        self._set_state_main("silent")

    def _on_confirm(self, event):
        if self.engine:
            self.engine.stop_and_transcribe()

    def _on_mode_click(self, event):
        modes = ["raw", "semi_formal", "polished"]
        idx = (modes.index(self._mode) + 1) % len(modes)
        new_mode = modes[idx]
        self._mode = new_mode
        if self.engine:
            self.engine.set_mode(new_mode)
        self._render_state()

    def _on_dashboard(self, event):
        if self.engine:
            self.engine.open_dashboard()

    def _on_stop_continuous(self, event):
        """× button on continuous HUD — bypasses toggle debounce, stops immediately."""
        if self.engine:
            threading.Thread(target=self.engine._stop_continuous, daemon=True).start()

    def _on_edit(self, event):
        if self.engine:
            self.engine.open_settings()

    # ─── Public API ───────────────────────────────────────────────────────────

    def show_notification(self, text: str, duration_ms: int = 2000):
        self.root.after(0, self._flash_notification, text, duration_ms)

    def _flash_notification(self, text: str, duration_ms: int):
        """Show toast notification — expands to NOTIF size so text fits."""
        # Temporarily expand to notification size
        self._canvas.config(width=NOTIF_W, height=NOTIF_H)
        self.root.wm_attributes("-alpha", ALPHA_ACTIVE)

        # Centre the notification at current position
        if self._win_x is not None:
            sw = self.root.winfo_screenwidth()
            cx = self._win_x + self._current_w // 2
            nx = max(0, min(cx - NOTIF_W // 2, sw - NOTIF_W))
            ny = self._win_y
        else:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            nx = (sw - NOTIF_W) // 2
            ny = sh - TASKBAR_H - NOTIF_H - MARGIN_BOTTOM

        self.root.geometry(f"{NOTIF_W}x{NOTIF_H}+{nx}+{ny}")

        c = self._canvas
        c.delete("all")
        r = NOTIF_H // 2
        self._draw_pill(c, NOTIF_W, NOTIF_H, r, BG_HOVER, BORDER_ACTIVE)
        c.create_text(NOTIF_W // 2, NOTIF_H // 2, text=text, font=FONT_SMALL,
                      fill=TEXT_PRIMARY, anchor="center")

        def _restore():
            self._canvas.config(width=self._current_w, height=self._current_h)
            self._render_state()
            self._apply_geometry()

        self.root.after(duration_ms, _restore)

    def run(self):
        self.root.mainloop()

    def quit(self):
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass
