#!/usr/bin/env python3
"""
Hybrid Gemini + ReportLab slide renderer for Lloyds v30.

Architecture:
- Layer 1 (Gemini): background ornaments + diagrams + in-diagram labels.
  Slide title, subtitle, and bullet body text are NOT rendered by Gemini.
- Layer 2 (ReportLab): vector text overlay — title, subtitle, bullets, footer.
  Pixel-perfect Helvetica-Neue typography, deterministic across all slides.

Usage:
    python render_lloyds_hybrid.py <source.md> [--regen]
    python render_lloyds_hybrid.py --deck <sources/dir> [--regen-all]
    python render_lloyds_hybrid.py --build-pdf <deck-name>

Each source markdown has YAML frontmatter (title, subtitle, bullets, layout)
plus a Gemini prompt body separated by `# Gemini Background Prompt`.

Backgrounds are cached in slides-v30-hybrid/backgrounds/ — only regenerate
when source changes or --regen is passed.
"""

from __future__ import annotations

import argparse
import re
import sys
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.home() / "Data/.datacore/env/.env")

import google.generativeai as genai
import yaml
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DECK_ROOT = Path("/Users/gregor/Data/1-datafund/1-tracks/comms/proposals/lloyds-banking-offer/slides-v30-hybrid")
SOURCES_DIR = DECK_ROOT / "sources"
BACKGROUNDS_DIR = DECK_ROOT / "backgrounds"
FINALS_DIR = DECK_ROOT / "finals"

# Slide canvas — 16:9 at PowerPoint widescreen sizing (1280×720pt)
PAGE_W = 1280
PAGE_H = 720

# Margins
MX = 60  # left/right margin pt

# Brand palette (matches v28/v29 Lloyds aesthetic)
WHITE = HexColor("#FFFFFF")
CHARCOAL_DARK = HexColor("#1A1A1A")
CHARCOAL_BODY = HexColor("#333333")
CHARCOAL_MID = HexColor("#555555")
MUTED_GREY = HexColor("#888888")
BLUE = HexColor("#0066FF")

# Gemini model + resolution
GEMINI_MODEL = "gemini-3.1-flash-image-preview"
TARGET_SIZE = (3840, 2160)  # 4K background


# ---------------------------------------------------------------------------
# Font registration
# ---------------------------------------------------------------------------

def register_font():
    for path in (
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont("Helvetica-Neue", path))
                return "Helvetica-Neue"
            except Exception:
                continue
    return "Helvetica"


FONT = register_font()


# ---------------------------------------------------------------------------
# Source parsing
# ---------------------------------------------------------------------------

def parse_slide_source(path: Path) -> dict:
    """Parse YAML frontmatter + Gemini prompt from a slide source markdown."""
    text = path.read_text()
    if not text.startswith("---"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path}: malformed frontmatter")
    fm = yaml.safe_load(parts[1])
    body = parts[2]
    m = re.search(r"# Gemini Background Prompt\s*\n", body)
    prompt = body[m.end():].strip() if m else ""
    fm["_gemini_prompt"] = prompt
    fm["_source_path"] = str(path)
    return fm


# ---------------------------------------------------------------------------
# Gemini background generation
# ---------------------------------------------------------------------------

def configure_gemini():
    import os
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not in environment")
    genai.configure(api_key=api_key)


def generate_placeholder_background(slide: dict, bg_path: Path):
    """Polished placeholder: pastel orbs + flowing curves + faint diagram-region
    marker. Mimics the v28 visual ornaments so the prototype shows what the
    final composite will look like once Gemini reconnects."""
    from PIL import ImageDraw, ImageFilter, ImageFont
    W, H = TARGET_SIZE
    img = Image.new("RGB", (W, H), (255, 255, 255))

    # ---- Pastel orbs (stacked translucent ellipses → soft gradient feel) ----
    orb_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(orb_layer)

    def orb(cx, cy, r, rgb):
        for i in range(14, 0, -1):
            ri = int(r * (i / 14))
            alpha = 8  # low — stacking builds the gradient
            od.ellipse([(cx - ri, cy - ri), (cx + ri, cy + ri)],
                       fill=(*rgb, alpha))

    # Top-right peach
    orb(W - 200, 250, 750, (255, 202, 168))
    # Bottom-left lavender
    orb(150, H - 300, 700, (201, 184, 232))
    # Mid-right sky-blue (subtle)
    orb(W - 600, H // 2 + 150, 450, (168, 197, 232))
    # Top-left pale yellow
    orb(-50, 100, 500, (245, 229, 168))

    img = Image.alpha_composite(img.convert("RGBA"), orb_layer)

    # ---- Flowing wave lines (bezier-feel via repeated stroked arcs) ----
    wave_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wave_layer)
    # 6 thin curving lines layered with low alpha
    waves = [
        {"y0": 400, "y1": 600, "amp": 220, "color": (170, 170, 200, 28)},
        {"y0": 550, "y1": 500, "amp": 280, "color": (255, 200, 170, 24)},
        {"y0": 800, "y1": 700, "amp": 200, "color": (200, 180, 220, 22)},
        {"y0": 1200, "y1": 1100, "amp": 260, "color": (170, 200, 230, 26)},
        {"y0": 1500, "y1": 1700, "amp": 240, "color": (200, 180, 220, 22)},
        {"y0": 1800, "y1": 1600, "amp": 280, "color": (170, 200, 230, 22)},
    ]
    for w_ in waves:
        # Draw as a polyline approximating a sine wave
        pts = []
        n = 240
        import math
        for k in range(n + 1):
            x = -100 + (W + 200) * k / n
            t = k / n
            y = w_["y0"] + (w_["y1"] - w_["y0"]) * t + \
                w_["amp"] * math.sin(t * math.pi * 3.2)
            pts.append((x, y))
        wd.line(pts, fill=w_["color"], width=4)

    # Soften the waves slightly
    wave_layer = wave_layer.filter(ImageFilter.GaussianBlur(radius=2))
    img = Image.alpha_composite(img, wave_layer)

    # ---- Faint diagram-region marker (right 45%) — barely visible cue ----
    diag_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(diag_layer)
    diag_x = int(W * 0.55)
    # Very subtle dashed border to indicate where Gemini diagram will go
    label = "[ Gemini diagram region — billing blocked ]"
    try:
        font = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 56)
    except Exception:
        font = ImageFont.load_default()
    bbox = dd.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    dd.text(
        ((diag_x + W) // 2 - tw // 2, H // 2 - th // 2),
        label, fill=(180, 180, 180, 140), font=font,
    )
    img = Image.alpha_composite(img, diag_layer)

    img.convert("RGB").save(bg_path, "PNG", optimize=False)
    print(f"  [placeholder] {bg_path.name} (Gemini billing currently blocked)")


def generate_background(slide: dict, force: bool = False,
                        allow_placeholder: bool = True) -> Path:
    """Generate or load cached Gemini background for one slide.
    Falls back to placeholder if Gemini fails and allow_placeholder=True."""
    slide_num = slide["slide_num"]
    slide_id = slide["slide_id"]
    bg_path = BACKGROUNDS_DIR / f"slide-{slide_num:02d}-{slide_id}-bg.png"

    if bg_path.exists() and not force:
        print(f"  [cache hit] {bg_path.name}")
        return bg_path

    try:
        configure_gemini()
        model = genai.GenerativeModel(GEMINI_MODEL)

        prompt = slide["_gemini_prompt"]
        print(f"  [gemini] generating background for slide {slide_num} ({slide_id})...")

        response = model.generate_content(
            contents=[prompt],
            generation_config={"response_modalities": ["IMAGE"]},
        )

        image_data = None
        for part in response.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                image_data = part.inline_data.data
                break

        if image_data is None:
            raise RuntimeError(f"Gemini returned no image for slide {slide_num}")

        image = Image.open(BytesIO(image_data))
        if image.size != TARGET_SIZE:
            image = image.resize(TARGET_SIZE, Image.LANCZOS)
        image.save(bg_path, "PNG", optimize=False)
        print(f"  [saved] {bg_path.name} ({image.size[0]}x{image.size[1]})")
        return bg_path

    except Exception as e:
        if allow_placeholder:
            print(f"  [gemini failed: {str(e)[:80]}] falling back to placeholder")
            generate_placeholder_background(slide, bg_path)
            return bg_path
        raise


# ---------------------------------------------------------------------------
# ReportLab text overlay
# ---------------------------------------------------------------------------

def wrap_text(text: str, size: float, max_w: float) -> list[str]:
    words = text.split()
    lines, current = [], []
    for word in words:
        cand = " ".join(current + [word])
        if pdfmetrics.stringWidth(cand, FONT, size) <= max_w:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def render_standard_body(c: Canvas, slide: dict, bg_path: Path):
    """Standard body slide: title + optional subtitle + bullets in LEFT 55%,
    diagram (already in background) on RIGHT 45%."""

    # Draw the Gemini background full-bleed
    c.drawImage(str(bg_path), 0, 0, width=PAGE_W, height=PAGE_H, mask="auto")

    # Text-column width (left 55% minus margin) — give breathing room from diagram
    text_w = PAGE_W * 0.50 - MX - 20
    text_x = MX

    # ----- Title -----
    title = slide.get("title", "")
    title_size = 38  # was 32 — bigger for impact
    title_lh = title_size * 1.12
    title_lines = wrap_text(title, title_size, text_w)

    y = PAGE_H - 100
    c.setFillColor(CHARCOAL_DARK)
    c.setFont(FONT, title_size)
    for line in title_lines:
        c.drawString(text_x, y, line)
        y -= title_lh

    # Short blue accent rule under title
    y_after_title = y + title_lh - 8
    c.setFillColor(BLUE)
    c.rect(text_x, y - 14, 36, 2.5, fill=1, stroke=0)

    # ----- Subtitle (optional) -----
    y -= 22
    subtitle = slide.get("subtitle", "") or ""
    if subtitle.strip():
        sub_size = 17
        c.setFillColor(MUTED_GREY)
        c.setFont(FONT, sub_size)
        for line in wrap_text(subtitle, sub_size, text_w):
            c.drawString(text_x, y, line)
            y -= sub_size * 1.35
        y -= 12

    # ----- Bullets -----
    y -= 24
    bullet_size = 17
    bullet_lh = bullet_size * 1.45  # line height within a bullet
    inter_bullet_gap = 14  # extra space between bullets
    bullet_indent = 22
    bullet_max_w = text_w - bullet_indent
    square_size = 7  # smaller, more elegant

    bullets = slide.get("bullets", []) or []
    for bullet in bullets:
        lines = wrap_text(bullet, bullet_size, bullet_max_w)
        # Square marker aligned with the FIRST line's x-height (cap-height/2)
        # drawString baseline is at y; x-height is ~0.5*size above baseline
        square_y = y + (bullet_size * 0.45) - (square_size / 2)
        c.setFillColor(BLUE)
        c.rect(text_x, square_y, square_size, square_size, fill=1, stroke=0)

        # Bullet text
        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, bullet_size)
        for line in lines:
            c.drawString(text_x + bullet_indent, y, line)
            y -= bullet_lh
        # Remove the last-line decrement, add a clean inter-bullet gap
        y += bullet_lh
        y -= bullet_lh + inter_bullet_gap

    # ----- Footer page indicator -----
    page_num = slide.get("slide_num")
    if page_num is not None:
        c.setFillColor(MUTED_GREY)
        c.setFont(FONT, 9)
        c.drawRightString(PAGE_W - MX, 22, str(page_num))


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def render_slide(source_md: Path, regen: bool = False) -> Path:
    """Render one slide: parse, generate/load background, overlay text, output PDF."""
    slide = parse_slide_source(source_md)
    print(f"\n=== slide {slide['slide_num']:02d}: {slide['slide_id']} ===")

    bg_path = generate_background(slide, force=regen)

    pdf_path = FINALS_DIR / f"slide-{slide['slide_num']:02d}-{slide['slide_id']}.pdf"
    c = Canvas(str(pdf_path), pagesize=(PAGE_W, PAGE_H))

    layout = slide.get("layout", "standard-body")
    if layout == "standard-body":
        render_standard_body(c, slide, bg_path)
    else:
        raise NotImplementedError(f"layout {layout} not implemented yet")

    c.save()
    print(f"  [pdf] {pdf_path.name}")
    return pdf_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("source", nargs="?", help="Source markdown path")
    p.add_argument("--regen", action="store_true",
                   help="Force Gemini regen even if background cached")
    args = p.parse_args()

    if not args.source:
        p.error("source markdown path required")

    source_path = Path(args.source)
    if not source_path.exists():
        p.error(f"source not found: {source_path}")

    BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)
    FINALS_DIR.mkdir(parents=True, exist_ok=True)

    pdf_path = render_slide(source_path, regen=args.regen)
    print(f"\nDone: {pdf_path}")


if __name__ == "__main__":
    main()
