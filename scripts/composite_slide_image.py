#!/usr/bin/env python3
"""
Composite a pre-existing image onto a rendered slide.

Use case: a slide is rendered by nano-banana-slides.py with a deliberately
empty region (e.g. blank right half), and a separately-prepared image
(comic, photo, diagram) is overlaid into that region. This avoids letting
Gemini regenerate an image that already exists and is approved.

Usage:
    python composite_slide_image.py <slide_png> <overlay_image> [options]

Options:
    --region {left,right,top,bottom,center}  Where to place the overlay
                                              (default: right)
    --margin-pct N    Margin from the region edges as percent of slide
                      dimensions (default: 8)
    --max-width-pct N Max overlay width as percent of slide width
                      (default: 40)
    --caption "text"  Caption to render below the overlay (optional)
    --output PATH     Output path (default: overwrites slide_png in place)
    --backup          Save the original slide as <slide>.bak.png before
                      overwriting

Author: Datafund slide module
"""

from __future__ import annotations
import argparse
import shutil
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def find_font(size: int) -> ImageFont.FreeTypeFont:
    """Locate a usable system sans-serif at the requested size."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Avenir Next.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def compute_overlay_box(
    slide_size: tuple[int, int],
    overlay_size: tuple[int, int],
    region: str,
    margin_pct: float,
    max_width_pct: float,
) -> tuple[int, int, int, int]:
    """Return (x, y, w, h) for the placed overlay, scaled to fit the region."""
    slide_w, slide_h = slide_size
    overlay_w, overlay_h = overlay_size
    margin = int(min(slide_w, slide_h) * margin_pct / 100)

    if region == "right":
        max_w = int(slide_w * max_width_pct / 100)
        region_x0 = slide_w // 2 + margin
        region_y0 = margin
        region_w = slide_w - region_x0 - margin
        region_h = slide_h - 2 * margin
    elif region == "left":
        max_w = int(slide_w * max_width_pct / 100)
        region_x0 = margin
        region_y0 = margin
        region_w = slide_w // 2 - 2 * margin
        region_h = slide_h - 2 * margin
    elif region == "center":
        max_w = int(slide_w * max_width_pct / 100)
        region_x0 = margin
        region_y0 = margin
        region_w = slide_w - 2 * margin
        region_h = slide_h - 2 * margin
    elif region == "top":
        max_w = int(slide_w * max_width_pct / 100)
        region_x0 = margin
        region_y0 = margin
        region_w = slide_w - 2 * margin
        region_h = slide_h // 2 - 2 * margin
    elif region == "bottom":
        max_w = int(slide_w * max_width_pct / 100)
        region_x0 = margin
        region_y0 = slide_h // 2 + margin
        region_w = slide_w - 2 * margin
        region_h = slide_h - region_y0 - margin
    else:
        raise ValueError(f"unknown region: {region}")

    # Scale overlay to fit region, preserving aspect ratio
    target_w = min(max_w, region_w)
    scale = target_w / overlay_w
    target_h = int(overlay_h * scale)
    if target_h > region_h:
        target_h = region_h
        scale = target_h / overlay_h
        target_w = int(overlay_w * scale)

    # Centre within region
    x = region_x0 + (region_w - target_w) // 2
    y = region_y0 + (region_h - target_h) // 2
    return x, y, target_w, target_h


def composite(
    slide_path: Path,
    overlay_path: Path,
    region: str,
    margin_pct: float,
    max_width_pct: float,
    caption: str | None,
    output_path: Path,
    backup: bool,
) -> None:
    if backup and slide_path == output_path:
        backup_path = slide_path.with_suffix(".bak.png")
        shutil.copyfile(slide_path, backup_path)
        print(f"Backup saved: {backup_path}")

    slide = Image.open(slide_path).convert("RGB")
    overlay = Image.open(overlay_path).convert("RGBA")

    x, y, w, h = compute_overlay_box(
        slide.size, overlay.size, region, margin_pct, max_width_pct
    )
    scaled_overlay = overlay.resize((w, h), Image.LANCZOS)
    slide.paste(scaled_overlay, (x, y), scaled_overlay)

    if caption:
        font_size = max(24, slide.size[1] // 80)
        font = find_font(font_size)
        draw = ImageDraw.Draw(slide)
        caption_y = y + h + max(20, slide.size[1] // 100)
        bbox = draw.textbbox((0, 0), caption, font=font)
        caption_w = bbox[2] - bbox[0]
        caption_x = x + (w - caption_w) // 2
        draw.text((caption_x, caption_y), caption, font=font, fill=(136, 136, 136))

    slide.save(output_path, format="PNG", optimize=True)
    print(
        f"Composited: {overlay_path.name} → {output_path.name} "
        f"(placed at {x},{y} size {w}x{h} in region '{region}')"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Composite a pre-existing image onto a rendered slide."
    )
    parser.add_argument("slide_png", type=Path, help="Path to the slide PNG to modify")
    parser.add_argument("overlay_image", type=Path, help="Path to the image to overlay")
    parser.add_argument(
        "--region",
        choices=["left", "right", "top", "bottom", "center"],
        default="right",
        help="Where to place the overlay (default: right)",
    )
    parser.add_argument(
        "--margin-pct", type=float, default=8.0, help="Margin from edges as percent"
    )
    parser.add_argument(
        "--max-width-pct",
        type=float,
        default=40.0,
        help="Maximum overlay width as percent of slide width",
    )
    parser.add_argument("--caption", type=str, default=None, help="Optional caption")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (defaults to overwriting input)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Save backup before overwriting",
    )
    args = parser.parse_args(argv)

    if not args.slide_png.exists():
        print(f"error: slide not found: {args.slide_png}", file=sys.stderr)
        return 1
    if not args.overlay_image.exists():
        print(f"error: overlay not found: {args.overlay_image}", file=sys.stderr)
        return 1

    output = args.output or args.slide_png
    composite(
        slide_path=args.slide_png,
        overlay_path=args.overlay_image,
        region=args.region,
        margin_pct=args.margin_pct,
        max_width_pct=args.max_width_pct,
        caption=args.caption,
        output_path=output,
        backup=args.backup,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
