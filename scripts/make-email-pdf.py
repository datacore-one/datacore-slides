#!/usr/bin/env python3
"""
Email-sized PDF builder for nano-banana slide decks.

nano-banana-slides.py --rebuild-pdf embeds PNGs losslessly, which produces
100MB+ decks at 4k. This builds a JPEG-backed companion PDF for sending,
typically 20-40x smaller, from the same slide PNGs.

Usage:
    python3 make-email-pdf.py <slides_dir> --out <file.pdf> [--width 1600] [--quality 80]

Example:
    python3 make-email-pdf.py 5-plur/.../slides-v11 \
        --out 5-plur/.../plur-seed-2026-05-v11-email.pdf
"""

import argparse
import sys
from pathlib import Path

from PIL import Image


def build(slides_dir: str, out_path: str, width: int, quality: int) -> int:
    slides_path = Path(slides_dir)
    if not slides_path.is_dir():
        print(f"Error: {slides_dir} is not a directory")
        return 1

    pngs = sorted(slides_path.glob("*.png"))
    if not pngs:
        print(f"Error: no PNGs in {slides_dir}")
        return 1

    pages = []
    for png in pngs:
        img = Image.open(png).convert("RGB")
        if img.width > width:
            height = round(img.height * width / img.width)
            img = img.resize((width, height), Image.LANCZOS)
        pages.append(img)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(
        out,
        "PDF",
        save_all=True,
        append_images=pages[1:],
        quality=quality,
        optimize=True,
    )

    mb = out.stat().st_size / (1024 * 1024)
    print(f"Built {out} — {len(pages)} slides, {mb:.1f} MB "
          f"(width {width}px, JPEG q{quality})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slides_dir", help="Directory of slide PNGs")
    ap.add_argument("--out", "-o", required=True, help="Output PDF path")
    ap.add_argument("--width", "-w", type=int, default=1600,
                    help="Max width in px (default 1600)")
    ap.add_argument("--quality", "-q", type=int, default=80,
                    help="JPEG quality 1-95 (default 80)")
    args = ap.parse_args()
    return build(args.slides_dir, args.out, args.width, args.quality)


if __name__ == "__main__":
    sys.exit(main())
