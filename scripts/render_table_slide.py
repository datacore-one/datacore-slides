#!/usr/bin/env python3
"""
render_table_slide.py — deterministic table-slide renderer.

WHY THIS EXISTS
---------------
nano-banana-slides.py sends slide copy to an image-generation model. For layout
and diagram slides that works well. For DENSE FACTUAL TABLES it does not: on the
2026-08-12 SRC deck a ten-row defect table came back with a duplicated row on one
render and SIX FABRICATED ROWS on the next — invented entries, an invented
category heading and a truncated cell, silently, with no error.

A generative renderer cannot be trusted to reproduce a factual table verbatim,
and the failure is silent. Any slide whose content is data a reader could check
should be typeset instead. That is what this does.

Shared canvas, palette and title treatment come from slide_chrome.py so this
cannot drift from the other typeset slides.

USAGE
-----
    python3 render_table_slide.py spec.json -o out.png

SPEC (JSON)
-----------
    {
      "title": "...", "subtitle": "...", "caption": "...",
      "columns": ["Field", "What it holds"],
      "rows": [
        {"group": "RETRIEVAL"},
        {"cells": ["statement", "what was learned"], "emphasis": true}
      ]
    }

`emphasis: true` renders a row as a summary line — accent type on a tinted band.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import ImageDraw

from slide_chrome import (W, H, INK, BODY, MUTE, ACCENT, ACCENT_SOFT, RULE,
                          MARGIN, CONTENT_BOTTOM, canvas, title_block,
                          caption as _cap, font, tracked, save)


def render(spec: dict, out: Path) -> None:
    img = canvas(int(spec.get("variant", 0)))
    d = ImageDraw.Draw(img)

    top = title_block(d, spec["title"], spec.get("subtitle", ""))

    f_head, f_cell, f_group = font(40), font(52), font(34)

    cols = [c for c in (spec.get("columns") or [])]
    n_cols = max(2, len(cols))
    col_x = [MARGIN, int(W * 0.50)] if n_cols == 2 else [MARGIN, int(W * 0.40), int(W * 0.70)]

    y = top
    if any(cols):
        for i, head in enumerate(cols[:len(col_x)]):
            if head:
                tracked(d, (col_x[i], y), head.upper(), f_head, ACCENT, spacing=7)
        y += 78
        d.line([(MARGIN, y), (W - MARGIN, y)], fill=ACCENT, width=3)
        y += 20

    rows = spec["rows"]
    avail = (CONTENT_BOTTOM - y)
    row_h = min(158, avail // max(len(rows), 1))
    # a short table would otherwise cling to the top and leave the lower half
    # empty — centre the block in whatever space is left
    slack = avail - row_h * len(rows)
    if slack > 0:
        y += min(slack // 3, 120)

    for row in rows:
        if "group" in row:
            tracked(d, (MARGIN, y + row_h // 2 - 26), row["group"].upper(),
                    f_group, ACCENT, spacing=6)
        else:
            if row.get("emphasis"):
                d.rounded_rectangle([MARGIN - 34, y + 8, W - MARGIN + 34, y + row_h - 8],
                                    radius=14, fill=ACCENT_SOFT)
            colour = ACCENT if row.get("emphasis") else BODY
            first = ACCENT if row.get("emphasis") else INK
            for i, cell in enumerate(row["cells"][:len(col_x)]):
                d.text((col_x[i], y + row_h // 2 - 34), cell, font=f_cell,
                       fill=first if i == 0 else colour)
        y += row_h
        if not row.get("emphasis"):
            d.line([(MARGIN, y), (W - MARGIN, y)], fill=RULE, width=2)

    _cap(d, spec.get("caption"))
    save(img, out)
    print(f"rendered {out}  ({len([r for r in rows if 'cells' in r])} data rows, "
          f"{len([r for r in rows if 'group' in r])} group headings)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args()
    render(json.loads(Path(args.spec).read_text()), Path(args.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
