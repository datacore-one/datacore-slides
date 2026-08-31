#!/usr/bin/env python3
"""
render_flow_slide.py — deterministic node-and-arrow diagram slide.

WHY THIS EXISTS
---------------
Same reason as render_table_slide.py and overlay_highlight.py: the generative
slide renderer draws organic subjects well but will not reliably place precise,
labelled structure. On the 2026-08-12 SRC deck it fabricated six rows of a
factual table and, across three separate attempts, refused to draw a labelled
hippocampus at all.

A circuit diagram with exact node labels is the same class of content. Typeset
it; do not generate it.

USAGE
-----
    python3 render_flow_slide.py spec.json

SPEC (JSON)
-----------
    {
      "output": "slide.png",
      "title": "...", "subtitle": "...", "caption": "...",
      "nodes": [
        {"id":"n1","x":200,"y":950,"w":560,"h":230,
         "tag":"ASSOCIATION CORTEX","label":"The work itself",
         "sub":"your systems, your data","accent":false}
      ],
      "edges": [
        {"from":"n1","to":"n2"},
        {"from":"n5","to":"n1","route":"below","label":"and it compounds"}
      ]
    }

Edge routing: "direct" (default, straight with arrowhead) or "below"
(down, across, and back up — for return loops).
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from slide_chrome import (W, H, INK, BODY, MUTE, ACCENT, ACCENT_SOFT, ACCENT_EDGE,
                          RULE, PANEL, MARGIN, canvas, title_block, caption as _cap,
                          font, tracked, save)


def tracked(draw, xy, text, fnt, fill, spacing=4):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + spacing
    return x


def centred(draw, cx, y, text, fnt, fill):
    w = draw.textlength(text, font=fnt)
    draw.text((cx - w / 2, y), text, font=fnt, fill=fill)


def centred_tracked(draw, cx, y, text, fnt, fill, spacing=4):
    w = sum(draw.textlength(c, font=fnt) + spacing for c in text) - spacing
    tracked(draw, (cx - w / 2, y), text, fnt, fill, spacing)


def arrow(draw, p0, p1, color=ACCENT, width=8, head=36):
    import math
    draw.line([p0, p1], fill=color, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for s in (-0.42, 0.42):
        draw.line([p1, (p1[0] - head * math.cos(ang + s),
                        p1[1] - head * math.sin(ang + s))], fill=color, width=width)


def render(spec, out: Path):
    img = canvas()
    d = ImageDraw.Draw(img)

    f_tag, f_label, f_nsub = font(28), font(52), font(34)
    f_edge = font(32)

    title_block(d, spec["title"], spec.get("subtitle", ""))

    nodes = {n["id"]: n for n in spec["nodes"]}

    def anchor(n, side):
        if side == "r":  return (n["x"] + n["w"], n["y"] + n["h"] / 2)
        if side == "l":  return (n["x"], n["y"] + n["h"] / 2)
        if side == "b":  return (n["x"] + n["w"] / 2, n["y"] + n["h"])
        return (n["x"] + n["w"] / 2, n["y"])

    # edges first, so boxes sit on top
    for e in spec.get("edges", []):
        a, b = nodes[e["from"]], nodes[e["to"]]
        if e.get("route") == "below":
            y = max(a["y"] + a["h"], b["y"] + b["h"]) + 150
            p0 = anchor(a, "b")
            p1 = anchor(b, "b")
            d.line([p0, (p0[0], y)], fill=ACCENT_EDGE, width=6)
            d.line([(p0[0], y), (p1[0], y)], fill=ACCENT_EDGE, width=6)
            arrow(d, (p1[0], y), (p1[0], p1[1] + 12), color=ACCENT_EDGE, width=6)
            if e.get("label"):
                centred(d, (p0[0] + p1[0]) / 2, y + 22, e["label"], f_edge, MUTE)
        else:
            # pick sides by relative position
            if abs(a["y"] - b["y"]) > 160 and b["x"] > a["x"]:
                p0, p1 = anchor(a, "r"), anchor(b, "l")
            else:
                p0, p1 = anchor(a, "r"), anchor(b, "l")
            arrow(d, (p0[0] + 14, p0[1]), (p1[0] - 20, p1[1]))
            if e.get("label"):
                centred(d, (p0[0] + p1[0]) / 2, min(p0[1], p1[1]) - 62,
                        e["label"], f_edge, MUTE)

    for n in spec["nodes"]:
        x, y, w, h = n["x"], n["y"], n["w"], n["h"]
        hero = n.get("accent")
        if hero:
            d.rounded_rectangle([x, y, x + w, y + h], radius=20,
                                fill=ACCENT_SOFT, outline=ACCENT, width=4)
            tag_c, lab_c, sub_c = ACCENT, INK, (74, 96, 140)
        else:
            d.rounded_rectangle([x, y, x + w, y + h], radius=20,
                                fill=PANEL, outline=RULE, width=3)
            tag_c, lab_c, sub_c = ACCENT, INK, MUTE
        cx = x + w / 2
        # an empty tag collapses its row rather than leaving a gap
        if n.get("tag"):
            centred_tracked(d, cx, y + 30, n["tag"], f_tag, tag_c)
            ly, sy = y + 84, y + 152
        else:
            ly, sy = y + 52, y + 128
        centred(d, cx, ly, n["label"], f_label, lab_c)
        if n.get("sub"):
            centred(d, cx, sy, n["sub"], f_nsub, sub_c)

    _cap(d, spec.get("caption"))

    save(img, out)
    print(f"rendered {out}  ({len(spec['nodes'])} nodes, {len(spec.get('edges', []))} edges)")


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
