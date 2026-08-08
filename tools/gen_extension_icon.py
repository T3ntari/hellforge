#!/usr/bin/env python3
"""Render a polished 512x512 HELLFORGE extension icon (PNG for Marketplace)."""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "extensions", "vscode-hellforge", "icons", "e.png")

S = 512
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Rounded background with vertical gradient
def lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

TOP = (38, 38, 64)
BOT = (20, 20, 38)
BORDER = (255, 196, 0)

margin = 24
r = 90
# Draw gradient by horizontal bands inside a rounded-rect mask
mask = Image.new("L", (S, S), 0)
md = ImageDraw.Draw(mask)
md.rounded_rectangle([margin, margin, S - margin, S - margin], radius=r, fill=255)
for y in range(S):
    t = y / S
    color = lerp(TOP, BOT, t)
    band = Image.new("RGBA", (S, S), color + (255,))
    img = Image.composite(band, img, mask)

d = ImageDraw.Draw(img)
# Border
d.rounded_rectangle([margin, margin, S - margin, S - margin], radius=r,
                    outline=BORDER, width=10)

# The note: big elegant eighth note
gold = (255, 196, 0)
gold_hi = (255, 220, 90)
stem_x = 300
stem_top = 150
stem_bot = 400
d.line([(stem_x, stem_top), (stem_x, stem_bot)], fill=gold, width=34)
# Flag
d.arc([stem_x - 10, stem_top - 30, stem_x + 200, stem_top + 110], 40, 120,
      fill=gold_hi, width=30)
# Head (rotated ellipse via polygon approximation)
import math
cx, cy = 226, 430
rx, ry = 62, 46
rot = math.radians(-20)
pts = []
for a in range(0, 360, 6):
    x = cx + rx * math.cos(math.radians(a))
    y = cy + ry * math.sin(math.radians(a))
    xr = cx + (x - cx) * math.cos(rot) - (y - cy) * math.sin(rot)
    yr = cy + (x - cx) * math.sin(rot) + (y - cy) * math.cos(rot)
    pts.append((xr, yr))
d.polygon(pts, fill=gold)
# Soft highlight on head
d.ellipse([cx - 38, cy - 26, cx - 8, cy - 4], fill=gold_hi)

# Subtle glow behind note
glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([80, 120, 440, 460], fill=(255, 196, 0, 26))
img = Image.alpha_composite(img, glow)
d = ImageDraw.Draw(img)
# Redraw note over glow
d.line([(stem_x, stem_top), (stem_x, stem_bot)], fill=gold, width=34)
d.arc([stem_x - 10, stem_top - 30, stem_x + 200, stem_top + 110], 40, 120,
      fill=gold_hi, width=30)
d.polygon(pts, fill=gold)
d.ellipse([cx - 38, cy - 26, cx - 8, cy - 4], fill=gold_hi)

img.save(OUT, "PNG")
print(f"Saved {OUT} ({os.path.getsize(OUT)//1024}KB, 512x512)")
