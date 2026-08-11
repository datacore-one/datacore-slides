#!/usr/bin/env python3
"""
render_table_slide.py — deterministic table-slide renderer.

WHY THIS EXISTS
---------------
nano-banana-slides.py sends slide copy to an image-generation model. For layout
and diagram slides that works well. For DENSE FACTUAL TABLES it does not: on the
2026-08-12 SRC deck, a ten-row defect table came back with a duplicated row on
one render and SIX FABRICATED ROWS on the next — invented defects, an invented
category heading, and a truncated cell, silently, with no error.

A generative renderer cannot be trusted to reproduce a factual table verbatim,
and the failure is silent, so it must be proofread every time. Any slide whose
content is data — real numbers, real log entries, anything a reader could check
— should be typeset deterministically instead. That is what this does.

Draws directly with PIL. No API, no network, no model. Same pixels every run.

USAGE
-----
    python3 render_table_slide.py spec.json -o out.png

SPEC (JSON)
-----------
    {
      "title": "Ten defects, one codebase, several weeks.",
      "subtitle": "Our own log. Offered as evidence, not a claim about anyone else.",
      "columns": ["WHAT BROKE", "HOW IT FAILED"],
      "rows": [
        {"group": "RETRIEVAL"},
        {"cells": ["Feedback was stored and shown", "ranking never read it"]}
      ],
      "caption": "none of these crashed."
    }
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 3840, 2160

INK = (26, 29, 36)
BODY = (42, 47, 58)
MUTE = (118, 125, 141)
ACCENT = (26, 86, 219)
RULE = (226, 228, 234)
BG = (255, 255, 255)

MARGIN = 200
FONT_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"


def font(size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    """Helvetica Neue. index 0 = regular (the deck forbids bold anywhere)."""
    try:
        return ImageFont.truetype(FONT_PATH, size, index=index)
    except OSError:
        return ImageFont.load_default(size)


def tracked(draw, xy, text, fnt, fill, spacing=0):
    """Draw text with manual letter-spacing (PIL has no tracking)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + spacing
    return x


def orbs(img):
    """Two soft pastel orbs, corner-anchored, cut off by the edge, barely there."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([-260, -300, 620, 560], fill=(196, 208, 244, 30))
    d.ellipse([W - 560, H - 460, W + 320, H + 400], fill=(226, 206, 238, 26))
    layer = layer.filter(__import__("PIL.ImageFilter", fromlist=["ImageFilter"]).GaussianBlur(120))
    img.alpha_composite(layer)


def render(spec: dict, out: Path) -> None:
    img = Image.new("RGBA", (W, H), BG + (255,))
    orbs(img)
    draw = ImageDraw.Draw(img)

    f_title = font(104)
    f_sub = font(50)
    f_head = font(36)
    f_cell = font(52)
    f_group = font(36)
    f_cap = font(40)

    y = 150
    draw.text((MARGIN, y), spec["title"], font=f_title, fill=INK)
    y += 150

    if spec.get("subtitle"):
        draw.text((MARGIN, y), spec["subtitle"], font=f_sub, fill=MUTE)
        y += 130

    col_x = [MARGIN, int(W * 0.53)]

    cols = spec.get("columns") or []
    if cols:
        for i, head in enumerate(cols):
            tracked(draw, (col_x[i], y), head.upper(), f_head, MUTE, spacing=4)
        y += 70
        draw.line([(MARGIN, y), (W - MARGIN, y)], fill=RULE, width=3)
        y += 18

    rows = spec["rows"]
    # Fit every row on the canvas, leaving room for the caption.
    avail = H - y - (190 if spec.get("caption") else 110)
    row_h = min(128, avail // max(len(rows), 1))

    for row in rows:
        if "group" in row:
            tracked(draw, (MARGIN, y + row_h // 2 - 26), row["group"].upper(),
                    f_group, ACCENT, spacing=5)
        else:
            for i, cell in enumerate(row["cells"][:2]):
                draw.text((col_x[i], y + row_h // 2 - 34), cell, font=f_cell, fill=BODY)
        y += row_h
        draw.line([(MARGIN, y), (W - MARGIN, y)], fill=RULE, width=2)

    if spec.get("caption"):
        draw.text((MARGIN, y + 46), spec["caption"], font=f_cap, fill=MUTE)

    img.convert("RGB").save(out, "PNG")
    print(f"rendered {out}  ({len([r for r in rows if 'cells' in r])} data rows, "
          f"{len([r for r in rows if 'group' in r])} group headings)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="JSON spec file")
    ap.add_argument("-o", "--output", required=True, help="output PNG path")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text())
    render(spec, Path(args.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
