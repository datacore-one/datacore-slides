#!/usr/bin/env python3
"""
Render an A4 portrait one-pager from structured content (Python dict).

Deterministic PDF generation — exact text fidelity, guaranteed layout.
Used when Gemini image generation paraphrases or hallucinates content,
which is unacceptable for outbound prospect documents.

Design: editorial single-page document.
  - White background
  - Dark charcoal titles, body text
  - Muted grey metadata
  - Soft warm gold (#C9A961) accents (section headers, eight-pointed star,
    closing line) — matches the Dubai blueprint deck visual palette
  - Hairline horizontal rules separating sections
  - Helvetica throughout

Usage:
    from render_onepager import render
    render(content_dict, output_pdf_path)

Or as CLI:
    python render_onepager.py <content.json> <output.pdf>
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# Brand palette — matches dubai-blueprint deck hero/variant slides
CHARCOAL_DARK = HexColor("#1A1A1A")
CHARCOAL_BODY = HexColor("#2A2A2A")
MUTED_GREY = HexColor("#888888")
HAIRLINE_GREY = HexColor("#D0D0D0")
GOLD = HexColor("#C9A961")
WHITE = HexColor("#FFFFFF")


def _register_helvetica() -> tuple[str, str, str]:
    """Try to register system Helvetica Neue; fall back to ReportLab default Helvetica."""
    candidates = [
        ("Helvetica-Neue", "/System/Library/Fonts/HelveticaNeue.ttc"),
        ("Helvetica", "/System/Library/Fonts/Helvetica.ttc"),
    ]
    for name, path in candidates:
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                return name, name, name
            except Exception:
                continue
    # ReportLab built-in default — always available
    return "Helvetica", "Helvetica", "Helvetica-Oblique"


def _draw_eight_pointed_star(c: Canvas, cx: float, cy: float, outer: float,
                              colour=GOLD, stroke_width: float = 1.0) -> None:
    """Draw a hairline eight-pointed star (Khatim Sulayman) centred at (cx, cy)."""
    c.saveState()
    c.setStrokeColor(colour)
    c.setLineWidth(stroke_width)
    inner = outer * 0.42
    # Eight outer points + eight inner valley points alternating
    points = []
    for i in range(16):
        angle = math.pi / 2 - (i * math.pi / 8)  # start at top, clockwise
        r = outer if i % 2 == 0 else inner
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    path = c.beginPath()
    path.moveTo(*points[0])
    for p in points[1:]:
        path.lineTo(*p)
    path.close()
    c.drawPath(path, stroke=1, fill=0)
    c.restoreState()


def _draw_hairline_rule(c: Canvas, y: float, left: float, right: float,
                        colour=HAIRLINE_GREY, width: float = 0.5) -> None:
    c.saveState()
    c.setStrokeColor(colour)
    c.setLineWidth(width)
    c.line(left, y, right, y)
    c.restoreState()


def _draw_centred_string(c: Canvas, text: str, y: float, font_name: str,
                          font_size: float, colour, page_w: float) -> None:
    c.setFont(font_name, font_size)
    c.setFillColor(colour)
    w = c.stringWidth(text, font_name, font_size)
    c.drawString((page_w - w) / 2, y, text)


def _wrap(text: str, font_name: str, font_size: float, max_w: float) -> list[str]:
    """Greedy word-wrap into lines that fit max_w. Uses pdfmetrics for accurate width."""
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_w:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _draw_paragraph(c: Canvas, paragraphs: list[str], x: float, y_top: float,
                    font_name: str, font_size: float, colour, max_w: float,
                    line_height: float, paragraph_gap: float) -> float:
    """Draw stacked paragraphs starting at y_top, return final y after last line."""
    c.setFont(font_name, font_size)
    c.setFillColor(colour)
    y = y_top
    for i, para in enumerate(paragraphs):
        for line in _wrap(para, font_name, font_size, max_w):
            c.drawString(x, y, line)
            y -= line_height
        if i < len(paragraphs) - 1:
            y -= paragraph_gap
    return y


def render(content: dict[str, Any], output_path: str | Path) -> None:
    """Render a one-pager PDF.

    Expected content dict keys:
        - header_label (str): e.g. "DATAFUND · 2026"
        - title_lines (list[str]): title broken into display lines (1-2 lines)
        - subtitle (str)
        - sections (list[dict]): each {header, body (list[str] of paragraphs)}
        - closing (str): single line pulled-quote in gold
        - contact (str): "email · website"
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    regular, bold, italic = _register_helvetica()
    font_body = regular

    page_w, page_h = A4
    margin_x = 22 * mm
    content_w = page_w - 2 * margin_x

    c = Canvas(str(output_path), pagesize=A4)
    c.setTitle(content.get("title_lines", ["One-pager"])[0])

    # ---- Top header strip (DATAFUND · 2026) ----
    header_y = page_h - 15 * mm
    _draw_centred_string(c, content["header_label"], header_y,
                          font_body, 7.5, MUTED_GREY, page_w)

    # ---- Title (one or two lines, centred) ----
    title_top = header_y - 14 * mm
    title_size = 30
    title_line_height = title_size * 1.15
    title_lines = content["title_lines"]
    for i, line in enumerate(title_lines):
        _draw_centred_string(c, line, title_top - i * title_line_height,
                              font_body, title_size, CHARCOAL_DARK, page_w)
    title_bottom = title_top - len(title_lines) * title_line_height

    # ---- Subtitle ----
    subtitle_y = title_bottom - 4 * mm
    _draw_centred_string(c, content["subtitle"], subtitle_y,
                          font_body, 11.5, MUTED_GREY, page_w)

    # ---- Eight-pointed gold star anchor ----
    star_y = subtitle_y - 12 * mm
    _draw_eight_pointed_star(c, page_w / 2, star_y, outer=5.5 * mm,
                              colour=GOLD, stroke_width=0.9)

    # ---- Body sections ----
    y_cursor = star_y - 10 * mm
    _draw_hairline_rule(c, y_cursor, margin_x, page_w - margin_x)

    section_header_size = 9.5
    section_header_gap = 4 * mm
    body_size = 10.5
    body_line_height = body_size * 1.4
    paragraph_gap = 3 * mm
    section_gap = 5 * mm

    for sect in content["sections"]:
        y_cursor -= section_gap

        # Section header in gold small-caps
        c.setFont(font_body, section_header_size)
        c.setFillColor(GOLD)
        c.drawString(margin_x, y_cursor, sect["header"].upper())
        y_cursor -= section_header_gap

        # Body paragraphs in charcoal
        y_cursor = _draw_paragraph(
            c,
            paragraphs=sect["body"],
            x=margin_x,
            y_top=y_cursor,
            font_name=font_body,
            font_size=body_size,
            colour=CHARCOAL_BODY,
            max_w=content_w,
            line_height=body_line_height,
            paragraph_gap=paragraph_gap,
        )

        y_cursor -= section_gap / 2
        _draw_hairline_rule(c, y_cursor, margin_x, page_w - margin_x)

    # ---- Closing pulled-quote ----
    closing_top = 32 * mm  # fixed offset from bottom of page
    closing_size = 13
    _draw_centred_string(c, content["closing"], closing_top, font_body,
                          closing_size, GOLD, page_w)

    # ---- Contact line ----
    contact_y = 14 * mm
    _draw_centred_string(c, content["contact"], contact_y, font_body, 8.5,
                          MUTED_GREY, page_w)

    c.showPage()
    c.save()
    print(f"Rendered: {output_path}")


if __name__ == "__main__":
    import json
    if len(sys.argv) != 3:
        print("Usage: render_onepager.py <content.json> <output.pdf>", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1]) as f:
        content = json.load(f)
    render(content, sys.argv[2])
