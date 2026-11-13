"""
generate_icons.py — Generates 24x24 Lucide-style monochrome PNG icons
using Pillow's ImageDraw. Run once; icons saved to assets/icons/.

Why PIL instead of SVG download:
  cairosvg requires libcairo which isn't trivially available on Windows.
  Drawing with Pillow keeps the dependency list minimal while producing
  crisp, correctly-sized icons that scale cleanly at 2x for HiDPI.
"""

import os
from PIL import Image, ImageDraw

ICON_DIR = os.path.join(os.path.dirname(__file__), "assets", "icons")
os.makedirs(ICON_DIR, exist_ok=True)

SIZE = 24
FG  = (200, 210, 230)   # #C8D2E6 — cool near-white, matches the sidebar muted text
BG  = (0, 0, 0, 0)      # Transparent background


def _new():
    img = Image.new("RGBA", (SIZE, SIZE), BG)
    return img, ImageDraw.Draw(img)


def save(img, name):
    path = os.path.join(ICON_DIR, f"{name}.png")
    img.save(path)
    print(f"  ✓ {path}")


# --- chat: speech bubble with two horizontal lines ---
def icon_chat():
    img, d = _new()
    # Bubble outline (rounded rect approximation)
    d.rounded_rectangle([2, 2, 21, 17], radius=4, outline=FG, width=2)
    # Tail triangle at bottom-left
    d.polygon([(4, 17), (3, 22), (9, 17)], fill=FG)
    # Two text lines inside bubble
    d.line([(5, 7), (18, 7)], fill=FG, width=2)
    d.line([(5, 11), (14, 11)], fill=FG, width=2)
    save(img, "chat")


# --- upload: folder with upward arrow ---
def icon_upload():
    img, d = _new()
    # Folder body
    d.rounded_rectangle([2, 7, 22, 20], radius=3, outline=FG, width=2)
    # Folder tab
    d.rounded_rectangle([2, 5, 10, 8], radius=2, outline=FG, width=2)
    # Upward arrow
    d.line([(12, 17), (12, 10)], fill=FG, width=2)
    d.polygon([(8, 13), (12, 8), (16, 13)], fill=FG)
    save(img, "upload")


# --- charts: bar chart ascending ---
def icon_charts():
    img, d = _new()
    # Three ascending bars
    d.rectangle([3, 14, 7, 21],  fill=FG)
    d.rectangle([9, 9,  13, 21], fill=FG)
    d.rectangle([15, 4, 19, 21], fill=FG)
    # Baseline
    d.line([(2, 21), (21, 21)], fill=FG, width=2)
    save(img, "charts")


# --- interactive: globe with meridians ---
def icon_interactive():
    img, d = _new()
    # Globe circle
    d.ellipse([2, 2, 21, 21], outline=FG, width=2)
    # Vertical meridian
    d.arc([7, 2, 16, 21], start=0, end=180, fill=FG, width=2)
    d.arc([7, 2, 16, 21], start=180, end=360, fill=FG, width=2)
    # Horizontal equator
    d.line([(2, 11), (21, 11)], fill=FG, width=2)
    save(img, "interactive")


# --- ml: brain / neural nodes ---
def icon_ml():
    img, d = _new()
    r = 3
    # Input nodes (left)
    for cy in [5, 11, 17]:
        d.ellipse([2, cy-r, 2+2*r, cy+r], outline=FG, width=2)
    # Output node (right)
    d.ellipse([16, 8, 22, 14], outline=FG, width=2)
    # Connections
    for cy in [5, 11, 17]:
        d.line([(2+2*r, cy), (16, 11)], fill=FG, width=1)
    save(img, "ml")


# --- settings: gear / cog ---
def icon_settings():
    img, d = _new()
    # Center circle
    d.ellipse([8, 8, 15, 15], outline=FG, width=2)
    # 8 teeth via short rectangles radiating outward
    teeth = [
        (10, 1, 13, 4),   # top
        (10, 19, 13, 22), # bottom
        (1, 10, 4, 13),   # left
        (19, 10, 22, 13), # right
        (4, 4, 7, 7),     # top-left
        (16, 4, 19, 7),   # top-right
        (4, 16, 7, 19),   # bottom-left
        (16, 16, 19, 19), # bottom-right
    ]
    for t in teeth:
        d.rectangle(t, fill=FG)
    save(img, "settings")


if __name__ == "__main__":
    print("Generating icons...")
    icon_chat()
    icon_upload()
    icon_charts()
    icon_interactive()
    icon_ml()
    icon_settings()
    print("Done — 6 icons written to assets/icons/")
