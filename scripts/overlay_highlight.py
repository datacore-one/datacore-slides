#!/usr/bin/env python3
"""
overlay_highlight.py — composite a precisely-placed highlight onto a slide image.

WHY THIS EXISTS
---------------
Image generators reliably draw a subject but routinely REFUSE to add a specific
labelled sub-structure to it. On the 2026-08-12 SRC deck, three separate renders
with three different prompting strategies (add-the-detail, ghost-the-cortex,
invert-the-composition) each produced a beautiful blue brain and silently
omitted the yellow hippocampus that was the entire point of the slide.

Prompt-tightening does not fix a structural refusal. So: let the generator draw
what it draws well (the organic subject), then composite the highlight, the
leader line and the label deterministically, exactly where they belong.

Same pixels every run. No API.

USAGE
-----
    python3 overlay_highlight.py spec.json

SPEC (JSON)
-----------
    {
      "input":  "slide.png",
      "output": "slide-annotated.png",
      "shapes": [
        {
          "path": [[x,y], ...],          # control points, smoothed
          "widths": [r0, r1, ...],       # radius at each control point (tapers)
          "fill": [245, 190, 30],
          "outline": [190, 140, 10]
        }
      ],
      "leader": {"from": [x,y], "to": [x,y], "color": [40,44,52]},
      "label":  {"text": "hippocampus", "at": [x,y], "size": 44,
                 "color": [40,44,52]}
    }

Coordinates are in the INPUT IMAGE's pixel space.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"


def catmull_rom(points, samples_per_seg: int = 24):
    """Smooth an open polyline through its control points."""
    if len(points) < 3:
        return points
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(len(pts) - 3):
        p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        for s in range(samples_per_seg):
            t = s / samples_per_seg
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(tuple(points[-1]))
    return out


def lerp_widths(widths, n: int):
    """Resample the per-control-point radii to n samples."""
    if len(widths) == 1:
        return [widths[0]] * n
    out = []
    span = len(widths) - 1
    for i in range(n):
        t = (i / max(n - 1, 1)) * span
        lo = min(int(t), span - 1)
        f = t - lo
        out.append(widths[lo] * (1 - f) + widths[lo + 1] * f)
    return out


def draw_tapered(draw, path, widths, fill, outline=None):
    """A smooth organic form: overlapping discs of varying radius along a path."""
    pts = catmull_rom(path)
    rs = lerp_widths(widths, len(pts))
    if outline:
        for (x, y), r in zip(pts, rs):
            ro = r + 3
            draw.ellipse([x - ro, y - ro, x + ro, y + ro], fill=tuple(outline))
    for (x, y), r in zip(pts, rs):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=tuple(fill))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text())
    img = Image.open(spec["input"]).convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    for shape in spec.get("shapes", []):
        draw_tapered(draw, shape["path"], shape["widths"],
                     shape["fill"], shape.get("outline"))

    lead = spec.get("leader")
    if lead:
        draw.line([tuple(lead["from"]), tuple(lead["to"])],
                  fill=tuple(lead.get("color", [40, 44, 52])), width=lead.get("width", 4))

    lab = spec.get("label")
    if lab:
        try:
            fnt = ImageFont.truetype(FONT_PATH, lab.get("size", 44))
        except OSError:
            fnt = ImageFont.load_default(lab.get("size", 44))
        draw.text(tuple(lab["at"]), lab["text"], font=fnt,
                  fill=tuple(lab.get("color", [40, 44, 52])))

    out = Path(spec["output"])
    Image.alpha_composite(img, layer).convert("RGB").save(out, "PNG")
    print(f"composited {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
