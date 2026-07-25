#!/usr/bin/env python3
"""Patch a rectangular region of a rendered slide/one-pager by cloning clean background.

Why this exists
---------------
The nano-banana (Gemini) image pipeline intermittently leaks fragments of the
design_system prompt into the rendered page — most often a colour hex code
("#555", "#0066FF") or a spec label, usually dropped into empty margin space.
This is a documented, recurring failure mode (ICE one-pager v11-v13; Irish Tech
News v2).

Re-rolling the render to clear a leak is expensive and risky: each roll is a
fresh generation, so it can fix the leak while introducing new *text* defects in
dense copy. When the rendered TEXT has already been verified verbatim, the
cheaper and safer fix is a same-roll splice — clone a clean patch of background
over the artifact and keep every verified glyph untouched.

This is the generalised form of the manual splice used on ICE v19.

Usage
-----
    # Clone from directly below the artifact (default, best for margin leaks)
    python3 patch_render_region.py page.png --box 200,4715,420,4800

    # Clone from an explicit source offset instead
    python3 patch_render_region.py page.png --box 200,4715,420,4800 --from 200,4820

    # Solid fill sampled from a point (fallback for flat backgrounds)
    python3 patch_render_region.py page.png --box 200,4715,420,4800 --sample 300,4850

    # Write elsewhere instead of in-place (in-place keeps a .orig backup)
    python3 patch_render_region.py page.png --box ... -o patched.png

Boxes are LEFT,TOP,RIGHT,BOTTOM in pixels of the source image.
Always re-verify the page visually after patching.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required: pip install Pillow")


def parse_box(raw: str) -> tuple[int, int, int, int]:
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--box needs LEFT,TOP,RIGHT,BOTTOM")
    left, top, right, bottom = (int(p) for p in parts)
    if right <= left or bottom <= top:
        raise argparse.ArgumentTypeError(
            f"--box must have RIGHT>LEFT and BOTTOM>TOP (got {left},{top},{right},{bottom})"
        )
    return left, top, right, bottom


def parse_point(raw: str) -> tuple[int, int]:
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("expected X,Y")
    return int(parts[0]), int(parts[1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", type=Path, help="Rendered PNG to patch")
    ap.add_argument("--box", required=True, type=parse_box, help="Region to cover: LEFT,TOP,RIGHT,BOTTOM")
    ap.add_argument("--from", dest="src", type=parse_point, default=None,
                    help="Top-left of the clean region to clone from (default: directly below the box)")
    ap.add_argument("--sample", type=parse_point, default=None,
                    help="Solid-fill using the colour at this point instead of cloning")
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="Output path (default: patch in place, keeping a .orig backup)")
    args = ap.parse_args()

    if not args.image.is_file():
        return print(f"error: no such file: {args.image}", file=sys.stderr) or 1

    im = Image.open(args.image).convert("RGB")
    W, H = im.size
    left, top, right, bottom = args.box
    bw, bh = right - left, bottom - top

    if right > W or bottom > H:
        print(f"error: box {args.box} exceeds image bounds {W}x{H}", file=sys.stderr)
        return 1

    if args.sample:
        sx, sy = args.sample
        if not (0 <= sx < W and 0 <= sy < H):
            print(f"error: --sample {sx},{sy} outside image {W}x{H}", file=sys.stderr)
            return 1
        colour = im.getpixel((sx, sy))
        im.paste(Image.new("RGB", (bw, bh), colour), (left, top))
        how = f"solid fill {colour} sampled at {sx},{sy}"
    else:
        if args.src:
            sx, sy = args.src
        else:
            # default: clone the band immediately below the artifact
            sx, sy = left, bottom + 8
        if sx + bw > W or sy + bh > H:
            print(
                f"error: clone source ({sx},{sy}) + {bw}x{bh} exceeds image {W}x{H}; "
                "pass --from or --sample explicitly",
                file=sys.stderr,
            )
            return 1
        patch = im.crop((sx, sy, sx + bw, sy + bh))
        im.paste(patch, (left, top))
        how = f"cloned {bw}x{bh} from {sx},{sy}"

    out = args.output
    if out is None:
        backup = args.image.with_suffix(args.image.suffix + ".orig")
        if not backup.exists():
            shutil.copy2(args.image, backup)
            print(f"backup: {backup}")
        out = args.image

    im.save(out)
    print(f"patched {args.image.name}: covered {left},{top},{right},{bottom} via {how}")
    print(f"wrote:  {out}")
    print("Re-verify the page visually before promoting it to final.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
