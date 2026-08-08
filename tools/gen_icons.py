#!/usr/bin/env python3
"""Generate HELLFORGE VS Code file icons as PNGs using PIL."""
import os
from PIL import (
    Image,
    ImageDraw,
)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "extensions", "vscode-hellforge", "icons")
os.makedirs(OUT, exist_ok=True)

SIZE = 64
BORDER = 6

DARK = (30, 30, 46)
GOLD = (255, 196, 0)
GOLD_D = (196, 150, 0)
WHITE = (240, 240, 250)
CYAN = (80, 200, 255)
PURPLE = (180, 120, 255)
RED = (255, 90, 90)
GREEN = (120, 220, 120)
BLUE = (90, 140, 255)
ORANGE = (255, 160, 80)


def new_canvas():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([BORDER, BORDER, SIZE - BORDER, SIZE - BORDER],
                        radius=10, fill=DARK, outline=GOLD_D, width=2)
    return img, d


def note(d, cx, cy, scale=1.0, color=GOLD):
    """Draw a music note (stem + head)."""
    hw = 3 * scale  # head half-width
    stem = 18 * scale
    x = cx
    y = cy
    d.ellipse([x - hw, y - hw, x + hw, y + hw], fill=color)
    d.rectangle([x, y - stem, x + 2 * scale, y], fill=color)
    d.ellipse([x + 2 * scale, y - stem - 2 * scale, x + 6 * scale, y - stem + 2 * scale], fill=color)


def wave(d, cx, cy, width=22, amp=6, color=CYAN, n=3):
    step = width / (n * 2)
    pts = []
    for i in range(n * 2 + 1):
        x = cx - width / 2 + i * step
        y = cy - amp * (1 if i % 2 == 0 else -1) if i % 2 == 0 else cy - amp * 0.4
        pts.append((x, y))
    d.line(pts, fill=color, width=3)


def lock(d, cx, cy, color=GOLD):
    d.rounded_rectangle([cx - 7, cy - 4, cx + 7, cy + 10], radius=3, fill=color)
    d.arc([cx - 5, cy - 14, cx + 5, cy - 2], 180, 360, fill=color, width=3)


def folder(d, cx, cy, color=GOLD):
    d.rounded_rectangle([cx - 14, cy - 8, cx + 14, cy + 10], radius=3, outline=color, width=2)
    d.line([cx - 14, cy - 2, cx - 6, cy - 2, cx - 2, cy + 2], fill=color, width=2)


def gear(d, cx, cy, r=10, color=CYAN):
    for i in range(8):
        import math
        ang = i * math.pi / 4
        x1 = cx + (r - 3) * math.cos(ang)
        y1 = cy + (r - 3) * math.sin(ang)
        x2 = cx + (r + 3) * math.cos(ang)
        y2 = cy + (r + 3) * math.sin(ang)
        d.line([x1, y1, x2, y2], fill=color, width=3)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=color)


def play_tri(d, cx, cy, color=GREEN):
    d.polygon([(cx - 5, cy - 8), (cx - 5, cy + 8), (cx + 9, cy)], fill=color)


def save(name, img):
    img.save(os.path.join(OUT, f"{name}.png"))
    print(f"  {name}.png")


# e — golden note
img, d = new_canvas()
note(d, 32, 34, 1.6)
save("e", img)

# ei — folder + note
img, d = new_canvas()
folder(d, 32, 30)
note(d, 32, 42, 1.0)
save("ei", img)

# eic — split note (half machine, half human)
img, d = new_canvas()
note(d, 26, 34, 1.3, GOLD)
d.line([32, 12, 32, 52], fill=WHITE, width=2)
note(d, 42, 34, 1.3, CYAN)
save("eic", img)

# enx — stacked sheets + play
img, d = new_canvas()
for i, dy in enumerate([-4, 0, 4]):
    d.rounded_rectangle([16 + i * 4, 14 + dy, 40 + i * 4, 42 + dy], radius=3,
                        outline=GOLD if i == 2 else WHITE, width=2)
play_tri(d, 46, 34)
save("enx", img)

# eci — note with arrows
img, d = new_canvas()
note(d, 32, 34, 1.3)
d.line([14, 18, 24, 18], fill=CYAN, width=2)
d.polygon([(24, 14), (28, 18), (24, 22)], fill=CYAN)
d.line([40, 46, 50, 46], fill=CYAN, width=2)
d.polygon([(50, 42), (54, 46), (50, 50)], fill=CYAN)
save("eci", img)

# ec — gear + note
img, d = new_canvas()
gear(d, 30, 32, 12)
note(d, 44, 42, 0.9, GOLD)
save("ec", img)

# ee — note behind lock
img, d = new_canvas()
note(d, 32, 36, 1.3)
lock(d, 38, 30)
save("ee", img)

# ecc — gear + lock + note
img, d = new_canvas()
gear(d, 24, 28, 9)
lock(d, 40, 26, GOLD)
note(d, 40, 44, 0.8, CYAN)
save("ecc", img)

# mid — MIDI plug icon
img, d = new_canvas()
d.rounded_rectangle([20, 22, 34, 42], radius=3, fill=ORANGE)
d.rectangle([27, 42, 27, 48], fill=ORANGE)
d.rounded_rectangle([36, 30, 46, 36], radius=2, outline=ORANGE, width=2)
d.line([20, 28, 14, 28], fill=ORANGE, width=2)
d.line([20, 36, 14, 36], fill=ORANGE, width=2)
save("mid", img)

# wav — sound wave
img, d = new_canvas()
wave(d, 32, 34, 30, 8, CYAN, 3)
save("wav", img)

# mp3 — wave + label
img, d = new_canvas()
wave(d, 32, 30, 24, 6, CYAN, 2)
d.text((20, 38), "mp3", fill=WHITE)
save("mp3", img)

# mp4 — film frame + note
img, d = new_canvas()
d.rounded_rectangle([14, 18, 50, 46], radius=3, outline=PURPLE, width=2)
d.line([24, 18, 24, 46], fill=PURPLE, width=1)
d.line([40, 18, 40, 46], fill=PURPLE, width=1)
note(d, 32, 34, 1.0)
save("mp4", img)

# machine — bracket glyph
img, d = new_canvas()
d.line([16, 16, 12, 32, 16, 48], fill=GREEN, width=3)
d.line([48, 16, 52, 32, 48, 48], fill=GREEN, width=3)
d.text((20, 26), "T0", fill=WHITE)
d.text((30, 26), "N60", fill=GOLD)
save("machine", img)

# human — speech bubble + note
img, d = new_canvas()
d.rounded_rectangle([14, 14, 46, 38], radius=6, outline=GOLD, width=2)
d.polygon([(22, 38), (22, 46), (30, 38)], fill=GOLD)
note(d, 30, 26, 0.8, GOLD)
save("human", img)

print("All icons generated.")
