#!/usr/bin/env python3
"""
render_cover_slide.py — deterministic cover with a Conway's Game of Life field.

WHY A LIFE FIELD
----------------
The product is memory. The field renders SEVERAL GENERATIONS AT ONCE — the newest
in full accent blue, each older one fainter behind it — so the image is a trace of
what came before rather than a snapshot. That is the thesis of the deck as a
picture, and it is the reason this is not just decoration.

Deterministic: fixed seed, fixed rules (B3/S23), same pixels every run. The image
generator would produce a plausible-looking grid that is not actually Life, which
on a slide about verifiability would be a poor joke.

USAGE
-----
    python3 render_cover_slide.py spec.json

SPEC (JSON)
-----------
    {
      "output": "cover.png",
      "title": "Verifiable Memory",
      "subtitle": "...",
      "meta": ["PLUR Enterprise · Datafund", "Pripravljeno za SRC · 12. avgust 2026"],
      "generations": 6,      # how many layered generations
      "settle": 28           # generations to run before we start drawing
    }
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from slide_chrome import W, H, INK, MUTE, ACCENT, MARGIN, font, save

# --- field geometry -------------------------------------------------------
COLS, ROWS = 34, 30
PITCH = 42
CELL = 30
FIELD_X = W - MARGIN - COLS * PITCH
FIELD_Y = 430


def step(live: set) -> set:
    """One generation of B3/S23."""
    counts = {}
    for (x, y) in live:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    counts[(x + dx, y + dy)] = counts.get((x + dx, y + dy), 0) + 1
    return {c for c, n in counts.items()
            if n == 3 or (n == 2 and c in live)}


def seed() -> set:
    """R-pentomino plus two gliders — chaotic enough to look alive, small enough
    to stay inside the field for the generations we draw."""
    cells = set()
    cx, cy = COLS // 2 - 1, ROWS // 2 + 4
    for dx, dy in [(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)]:          # R-pentomino
        cells.add((cx + dx, cy + dy))
    for ox, oy in [(6, 5), (COLS - 10, ROWS - 9)]:                    # gliders
        for dx, dy in [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)]:
            cells.add((ox + dx, oy + dy))
    return cells


def render(spec: dict, out: Path) -> None:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))

    gens = int(spec.get("generations", 6))
    settle = int(spec.get("settle", 28))

    live = seed()
    for _ in range(settle):
        live = step(live)

    history = []
    for _ in range(gens):
        history.append(live)
        live = step(live)

    # --- faint guide lines: the grid the field lives on --------------------
    guides = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(guides)
    for c in range(COLS + 1):
        x = FIELD_X + c * PITCH - 6
        g.line([(x, FIELD_Y - 6), (x, FIELD_Y + ROWS * PITCH - 6)],
               fill=(26, 86, 219, 16), width=2)
    for r in range(ROWS + 1):
        y = FIELD_Y + r * PITCH - 6
        g.line([(FIELD_X - 6, y), (FIELD_X + COLS * PITCH - 6, y)],
               fill=(26, 86, 219, 16), width=2)
    img.alpha_composite(guides)

    # --- generations, oldest first so the newest sits on top --------------
    for i, gen in enumerate(reversed(history)):
        age = len(history) - 1 - i          # 0 = newest
        alpha = int(210 * (0.16 ** (age / max(len(history) - 1, 1)))) if age else 235
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for (cx, cy) in gen:
            if 0 <= cx < COLS and 0 <= cy < ROWS:
                x = FIELD_X + cx * PITCH
                y = FIELD_Y + cy * PITCH
                d.rounded_rectangle([x, y, x + CELL, y + CELL], radius=5,
                                    fill=ACCENT + (alpha,))
        img.alpha_composite(layer)

    d = ImageDraw.Draw(img)

    # --- type -------------------------------------------------------------
    f_title, f_sub, f_meta = font(190), font(62), font(40)
    ty = 700
    d.text((MARGIN, ty), spec["title"], font=f_title, fill=INK)
    d.line([(MARGIN, ty + 268), (MARGIN + 190, ty + 268)], fill=ACCENT, width=8)
    if spec.get("subtitle"):
        d.text((MARGIN, ty + 330), spec["subtitle"], font=f_sub, fill=(70, 78, 94))

    my = H - 430
    for line in spec.get("meta", []):
        d.text((MARGIN, my), line, font=f_meta, fill=MUTE)
        my += 66

    save(img, out)
    print(f"rendered {out}  (Life: {settle} settle + {gens} generations layered)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    a = ap.parse_args()
    s = json.loads(Path(a.spec).read_text())
    render(s, Path(s["output"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
