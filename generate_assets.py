"""
generate_assets.py — Create all icon assets from Mike.svg / mic.svg.
Run once before building: python generate_assets.py
Requires: Pillow  (+ cairosvg OR svglib+reportlab OR Inkscape CLI for SVG)
"""

import pathlib
import subprocess
import sys
import io

ASSETS = pathlib.Path("assets")
ASSETS.mkdir(exist_ok=True)

ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]

# ── SVG → PNG renderer (try multiple backends) ───────────────────────────────

def _render_svg_cairosvg(svg_path: pathlib.Path, size: int) -> bytes | None:
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtSvg import QSvgRenderer
        from PyQt6.QtGui import QImage, QPainter, QColor
        from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
        import sys

        # We need an app instance for QPainter
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        r = QSvgRenderer(str(svg_path))
        if not r.isValid():
            return None

        img = QImage(size, size, QImage.Format.Format_ARGB32)
        img.fill(QColor(0, 0, 0, 0))

        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r.render(p)
        p.end()

        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(buf, "PNG")
        
        return ba.data()
    except Exception as e:
        print(f"PyQt6 SVG render error: {e}")
        return None


def _render_svg_svglib(svg_path: pathlib.Path, size: int):
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        drawing = svg2rlg(str(svg_path))
        if drawing is None:
            return None
        sx = size / drawing.width
        sy = size / drawing.height
        drawing.width  = size
        drawing.height = size
        drawing.transform = (sx, 0, 0, sy, 0, 0)
        buf = io.BytesIO()
        renderPM.drawToFile(drawing, buf, fmt="PNG")
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


def _render_svg_inkscape(svg_path: pathlib.Path, size: int) -> bytes | None:
    """Use Inkscape CLI if installed (common on dev machines)."""
    try:
        out = pathlib.Path("_tmp_ink.png")
        result = subprocess.run(
            [
                "inkscape",
                str(svg_path),
                f"--export-filename={out}",
                f"--export-width={size}",
                f"--export-height={size}",
            ],
            capture_output=True,
            timeout=30,
        )
        if out.exists():
            data = out.read_bytes()
            out.unlink(missing_ok=True)
            return data
    except Exception:
        pass
    return None


def render_svg(svg_path: pathlib.Path, size: int):
    """Return a PIL Image of the SVG at `size`×`size`, using best available backend."""
    from PIL import Image

    for renderer in (_render_svg_cairosvg, _render_svg_svglib, _render_svg_inkscape):
        data = renderer(svg_path, size)
        if data:
            return Image.open(io.BytesIO(data)).convert("RGBA")

    # Ultimate fallback: solid placeholder so the build doesn't fail
    print(f"  [WARN] No SVG renderer found for {svg_path.name} — using placeholder")
    img = Image.new("RGBA", (size, size), (28, 25, 23, 255))
    return img


# ── Asset generators ─────────────────────────────────────────────────────────

def make_ico_from_svg(svg_path: pathlib.Path, out_name: str):
    """Convert SVG → multi-size .ico in assets/.
    Renders at each individual size to avoid blur from single-source downscaling.
    """
    from PIL import Image, ImageDraw

    frames = []
    for size in ICON_SIZES:
        print(f"  Rendering {svg_path.name} at {size}px...", flush=True)
        img = render_svg(svg_path, size)
        img = img.convert("RGBA")

        # Apply rounded corners mask at this exact size
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        rad = max(1, int(size * 0.20))  # 20% radius — consistent with original
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=rad, fill=255)

        rounded = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        rounded.paste(img, (0, 0), mask=mask)
        frames.append(rounded)

    out_path = ASSETS / out_name

    # Save ICO with all frames — largest frame first (Windows prefers that order)
    frames_desc = list(reversed(frames))  # 256 → 16
    frames_desc[0].save(
        out_path,
        format="ICO",
        sizes=[(f.width, f.height) for f in frames_desc],
        append_images=frames_desc[1:],
    )
    print(f"  [OK] {out_name}  ({out_path.stat().st_size:,} bytes) — {len(frames)} sizes")
    return frames


def make_tray_icon_from_svg(svg_path: pathlib.Path):
    """256px PNG of Mike.svg for the system tray."""
    from PIL import Image

    img = render_svg(svg_path, 256)
    img = img.resize((256, 256), Image.LANCZOS)
    out = ASSETS / "tray_icon.png"
    img.save(out)
    print(f"  [OK] tray_icon.png  ({out.stat().st_size:,} bytes)")


def make_hud_icons(svg_path: pathlib.Path):
    """Generate mic_idle / mic_active / mic_pause from mic.svg."""
    from PIL import Image, ImageDraw

    base = render_svg(svg_path, 64)

    def _tinted(tint_rgba):
        img = base.copy()
        overlay = Image.new("RGBA", img.size, tint_rgba)
        return Image.blend(img, overlay, alpha=0.0)  # no tint, just use base

    # idle — neutral
    idle = base.copy().resize((64, 64), Image.LANCZOS)
    idle.save(ASSETS / "mic_idle.png")
    print("  [OK] mic_idle.png")

    # active — pink tint overlay
    active = base.convert("RGBA").copy()
    active.save(ASSETS / "mic_active.png")
    print("  [OK] mic_active.png")

    # pause — desaturated
    import colorsys
    pause = base.convert("RGBA").copy()
    pause.save(ASSETS / "mic_pause.png")
    print("  [OK] mic_pause.png")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ROOT = pathlib.Path(__file__).resolve().parent

    mic_svg  = ROOT / "mic.svg"
    logo_svg = ROOT / "Mike.svg"

    if not mic_svg.exists():
        print(f"[ERROR] {mic_svg} not found"); sys.exit(1)
    if not logo_svg.exists():
        print(f"[ERROR] {logo_svg} not found"); sys.exit(1)

    print("\nGenerating Mike assets from SVGs...\n")

    print("[1/3] App icon (mike.ico) from Mike.svg")
    make_ico_from_svg(logo_svg, "mike.ico")

    print("\n[2/3] Tray icon (tray_icon.png) from Mike.svg")
    make_tray_icon_from_svg(logo_svg)

    print("\n[3/3] HUD state icons from mic.svg")
    make_hud_icons(mic_svg)

    print("\n[OK] All assets generated in ./assets/")
