#!/usr/bin/env python3
"""
render_stats_slide.py — deterministic "headline figures + capability list" slide.

WHY THIS EXISTS
---------------
Same reason as the other deterministic renderers in this directory: the
generative slide pipeline paraphrases and fabricates factual content. Benchmark
figures are the last thing that should be generated.

Design: the numbers are the slide. Three large stat callouts across the top,
each with its protocol underneath in small type, then a two-column capability
list below a rule, then a caption carrying the source link.

USAGE
-----
    python3 render_stats_slide.py spec.json

SPEC (JSON)
-----------
    {
      "output": "slide.png",
      "title": "...", "subtitle": "...",
      "stats": [{"value":"97.6%","metric":"R@5, local rerank",
                 "detail":"LongMemEval-S, N = 500"}],
      "list_heading": "LOCAL FIRST",
      "items": [["Where it runs","your infrastructure"]],
      "caption": "..."
    }
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import ImageDraw

from slide_chrome import (W, H, INK, BODY, MUTE, ACCENT, ACCENT_SOFT, RULE,
                          MARGIN, canvas, title_block, caption as _cap,
                          font, tracked, save)


def render(spec, out: Path):
    img = canvas()
    d = ImageDraw.Draw(img)

    f_stat, f_metric, f_detail = font(176), font(42), font(34)
    f_head, f_item, f_val = font(32), font(48), font(48)

    y0 = title_block(d, spec["title"], spec.get("subtitle", ""))

    # --- stat callouts -----------------------------------------------------
    stats = spec.get("stats", [])
    if stats:
        usable = W - 2 * MARGIN
        col = usable / len(stats)
        for i, s in enumerate(stats):
            x = MARGIN + i * col
            # tinted plate behind each figure so the row reads as one object
            d.rounded_rectangle([x - 34, y0 - 26, x + col - 90, y0 + 316],
                                radius=18, fill=ACCENT_SOFT)
            d.text((x, y0), s["value"], font=f_stat, fill=ACCENT)
            d.text((x, y0 + 216), s["metric"], font=f_metric, fill=BODY)
            if s.get("detail"):
                d.text((x, y0 + 274), s["detail"], font=f_detail, fill=MUTE)
        y0 += 420

    d.line([(MARGIN, y0), (W - MARGIN, y0)], fill=RULE, width=3)
    y0 += 60

    # --- capability list, two columns --------------------------------------
    if spec.get("list_heading"):
        tracked(d, (MARGIN, y0), spec["list_heading"].upper(), f_head, ACCENT, 5)
        y0 += 76

    items = spec.get("items", [])
    half = (len(items) + 1) // 2
    cols = [items[:half], items[half:]]
    col_x = [MARGIN, MARGIN + (W - 2 * MARGIN) / 2 + 60]
    row_h = 108

    for ci, colitems in enumerate(cols):
        x = col_x[ci]
        y = y0
        for label, value in colitems:
            d.text((x, y), label, font=f_item, fill=MUTE)
            d.text((x + 430, y), value, font=f_val, fill=BODY)
            y += row_h
            d.line([(x, y - 22), (x + (W - 2 * MARGIN) / 2 - 90, y - 22)],
                   fill=RULE, width=2)

    _cap(d, spec.get("caption"))
    save(img, out)
    print(f"rendered {out}  ({len(stats)} stats, {len(items)} items)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    a = ap.parse_args()
    s = json.loads(Path(a.spec).read_text())
    render(s, Path(s["output"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
