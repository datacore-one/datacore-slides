#!/usr/bin/env python3
"""
Render the universal two-pager v5 — Institutional Memory for Sovereign AI.

v5 (2026-06-01 evening, second iteration) — Lloyds-aesthetic rebuild:
- Pure white background
- Minimal pastel orbs (very small, two corners only, low alpha)
- No gold, no dark callout blocks, no dark footer band
- Pure blue (#0066FF) square bullets — Lloyds style
- Light pastel highlight rectangles behind key phrases
- Large dark Helvetica titles, generous breathing
- Clean centred tagline + contact at natural end of flow
- Section reorder preserved: Theory/Practice → Sovereignty → Guarantees → Phases → Close
- "Five hard guarantees." (renamed)
- §IX inspirational close with horizontal CTA pathway

Deterministic ReportLab. A4 portrait.
"""

from __future__ import annotations

import math
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ===========================================================================
# Palette — Lloyds-aesthetic light
# ===========================================================================

WHITE = HexColor("#FFFFFF")
CHARCOAL_DARK = HexColor("#1A1A1A")
CHARCOAL_BODY = HexColor("#333333")
CHARCOAL_MID = HexColor("#555555")
MUTED_GREY = HexColor("#888888")
LIGHT_GREY = HexColor("#C8C8C8")
PALE_GREY = HexColor("#E8E8E8")

# Primary accent
BLUE = HexColor("#0066FF")
BLUE_PALE = HexColor("#DCE9F8")
BLUE_LIGHT = HexColor("#7AA3F0")

# Pastel orb colours (used at very low alpha)
LAVENDER = HexColor("#C9B8E8")
PEACH = HexColor("#FFCAA8")
SKY = HexColor("#A8C5E8")
MINT = HexColor("#B5DBC2")

# Pastel highlight (behind text)
HIGHLIGHT_PEACH = HexColor("#FFE6D5")
HIGHLIGHT_BLUE = HexColor("#DCE9F8")
HIGHLIGHT_LAVENDER = HexColor("#E8DDF5")


def register_font() -> str:
    for path in ("/System/Library/Fonts/HelveticaNeue.ttc",
                 "/System/Library/Fonts/Helvetica.ttc"):
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont("Helvetica-Neue", path))
                return "Helvetica-Neue"
            except Exception:
                continue
    return "Helvetica"


FONT = register_font()


# ===========================================================================
# Low-level helpers
# ===========================================================================

def centred_text(c, text, y, size, colour, page_w):
    c.setFont(FONT, size)
    c.setFillColor(colour)
    w = c.stringWidth(text, FONT, size)
    c.drawString((page_w - w) / 2, y, text)


def left_text(c, text, x, y, size, colour):
    c.setFont(FONT, size)
    c.setFillColor(colour)
    c.drawString(x, y, text)


def right_text(c, text, x_right, y, size, colour):
    c.setFont(FONT, size)
    c.setFillColor(colour)
    w = c.stringWidth(text, FONT, size)
    c.drawString(x_right - w, y, text)


def wrap(text, size, max_w):
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


def paragraph(c, text, x, y_top, size, colour, max_w, line_h=None):
    line_h = line_h or size * 1.5
    c.setFont(FONT, size)
    c.setFillColor(colour)
    y = y_top
    for line in wrap(text, size, max_w):
        c.drawString(x, y, line)
        y -= line_h
    return y


def thin_rule(c, y, x0, x1, colour=PALE_GREY, w=0.4):
    c.setStrokeColor(colour)
    c.setLineWidth(w)
    c.line(x0, y, x1, y)


# ===========================================================================
# Pastel orbs — MINIMAL presence (small, faint, two corners only)
# ===========================================================================

def pastel_orb(c, cx, cy, radius, colour, layers=8, layer_alpha=0.025):
    """Stacked translucent circles → soft radial-gradient feel.
    Kept VERY subtle — small radius, low layer alpha."""
    c.saveState()
    c.setStrokeAlpha(0)
    c.setFillColor(colour)
    c.setFillAlpha(layer_alpha)
    for i in range(layers, 0, -1):
        r = radius * (i / layers)
        c.circle(cx, cy, r, fill=1, stroke=0)
    c.restoreState()


def minimal_orbs(c, page_w, page_h):
    """Just TWO small pastel orbs — one in top-right corner area, one in
    bottom-left. Tiny, faint. Barely present."""
    # Top-right: pale peach, partly off-page
    pastel_orb(c, page_w - 10 * mm, page_h - 18 * mm,
               radius=22 * mm, colour=PEACH, layers=8, layer_alpha=0.022)
    # Bottom-left: pale lavender, partly off-page
    pastel_orb(c, 8 * mm, 28 * mm,
               radius=20 * mm, colour=LAVENDER, layers=8, layer_alpha=0.022)


def flowing_curve(c, x0, y0, x1, y1, ctrl1_offset=(0, 0), ctrl2_offset=(0, 0),
                  colour=LIGHT_GREY, alpha=0.18, w=0.45):
    """Single subtle flowing bezier curve."""
    c.saveState()
    c.setStrokeColor(colour)
    c.setStrokeAlpha(alpha)
    c.setLineWidth(w)
    c.setFillAlpha(0)
    cx1 = x0 + (x1 - x0) * 0.3 + ctrl1_offset[0]
    cy1 = y0 + ctrl1_offset[1]
    cx2 = x0 + (x1 - x0) * 0.7 + ctrl2_offset[0]
    cy2 = y1 + ctrl2_offset[1]
    path = c.beginPath()
    path.moveTo(x0, y0)
    path.curveTo(cx1, cy1, cx2, cy2, x1, y1)
    c.drawPath(path, stroke=1, fill=0)
    c.restoreState()


def flowing_lines(c, page_w, page_h, page_index=0):
    """Subtle flowing curves across the page — varied per page for organic feel."""
    if page_index == 0:
        # Page 1: arc descending from upper-left, plus a counter-arc lower
        flowing_curve(c, -10 * mm, page_h - 50 * mm, page_w + 10 * mm, page_h - 110 * mm,
                      ctrl1_offset=(0, 50 * mm), ctrl2_offset=(0, -30 * mm),
                      colour=BLUE_LIGHT, alpha=0.12, w=0.5)
        flowing_curve(c, -5 * mm, page_h / 2 - 20 * mm, page_w + 5 * mm, page_h / 2 - 50 * mm,
                      ctrl1_offset=(0, 35 * mm), ctrl2_offset=(0, -25 * mm),
                      colour=LAVENDER, alpha=0.10, w=0.5)
        flowing_curve(c, -10 * mm, 90 * mm, page_w + 10 * mm, 60 * mm,
                      ctrl1_offset=(0, 25 * mm), ctrl2_offset=(0, -15 * mm),
                      colour=PEACH, alpha=0.10, w=0.5)
    else:
        # Page 2: different curve set so pages feel related, not identical
        flowing_curve(c, -10 * mm, page_h - 70 * mm, page_w + 10 * mm, page_h - 130 * mm,
                      ctrl1_offset=(0, -40 * mm), ctrl2_offset=(0, 30 * mm),
                      colour=PEACH, alpha=0.10, w=0.5)
        flowing_curve(c, -5 * mm, page_h / 2, page_w + 5 * mm, page_h / 2 - 30 * mm,
                      ctrl1_offset=(0, 30 * mm), ctrl2_offset=(0, -20 * mm),
                      colour=BLUE_LIGHT, alpha=0.10, w=0.5)
        flowing_curve(c, -10 * mm, 70 * mm, page_w + 10 * mm, 100 * mm,
                      ctrl1_offset=(0, -30 * mm), ctrl2_offset=(0, 20 * mm),
                      colour=LAVENDER, alpha=0.10, w=0.5)


# ===========================================================================
# Inline highlight
# ===========================================================================

def text_with_highlight(c, x, y, lead_text, body_text, size, max_w,
                       highlight=HIGHLIGHT_PEACH, lead_colour=CHARCOAL_DARK,
                       body_colour=CHARCOAL_BODY, line_h=None):
    """Draw a phrase with a pastel underline highlight under the lead text,
    followed by body text. Wraps. Returns y after the block."""
    line_h = line_h or size * 1.45
    c.saveState()

    # Wrap full text to know layout
    full = f"{lead_text} {body_text}"
    wrapped = wrap(full, size, max_w)

    if wrapped:
        first_line = wrapped[0]
        # Highlight under lead text
        lead_w = c.stringWidth(lead_text, FONT, size)
        # Highlight rectangle
        c.setFillColor(highlight)
        c.setStrokeAlpha(0)
        c.rect(x - 1, y - 2, lead_w + 2, size * 0.95, fill=1, stroke=0)
        # Lead text on top
        c.setFillColor(lead_colour)
        c.setFont(FONT, size)
        c.drawString(x, y, lead_text)
        # Remainder of first line
        if first_line.startswith(lead_text):
            remainder = first_line[len(lead_text):]
            c.setFillColor(body_colour)
            c.drawString(x + lead_w, y, remainder)
        y -= line_h
        # Continuation lines
        c.setFillColor(body_colour)
        for line in wrapped[1:]:
            c.drawString(x, y, line)
            y -= line_h
    c.restoreState()
    return y


# ===========================================================================
# Composed elements
# ===========================================================================

def section_title(c, text, x, y, size=14, max_w=None):
    c.saveState()
    c.setFillColor(CHARCOAL_DARK)
    c.setFont(FONT, size)
    if max_w:
        wrapped = wrap(text, size, max_w)
        for i, line in enumerate(wrapped):
            c.drawString(x, y - i * size * 1.2, line)
        c.restoreState()
        return y - (len(wrapped) - 1) * size * 1.2
    else:
        c.drawString(x, y, text)
        c.restoreState()
        return y


def title_block(c, page_w, y_top, lines, mx, title_size, line_gap=1.05):
    """Large left-aligned title — no star anchor, no logo. Just type."""
    c.setFillColor(CHARCOAL_DARK)
    c.setFont(FONT, title_size)
    line_h = title_size * line_gap
    cy = y_top
    for line in lines:
        c.drawString(mx, cy, line)
        cy -= line_h
    return cy


def blue_bullet(c, x, y, size=4.5):
    c.setFillColor(BLUE)
    c.setStrokeColor(BLUE)
    c.rect(x, y - size + 1, size, size, fill=1, stroke=0)


def problem_bullets(c, x, y_top, width, lines):
    """Lloyds-style: blue square bullet, lead phrase with pastel highlight,
    body in muted charcoal. Generous breathing room."""
    y = y_top
    inter_bullet_gap = 4.5 * mm
    line_h_body = 13
    body_x = x + 9
    body_max = width - 9
    size = 9.5

    highlights = [HIGHLIGHT_PEACH, HIGHLIGHT_BLUE, HIGHLIGHT_LAVENDER, HIGHLIGHT_PEACH]

    for i, (lead, punch) in enumerate(lines):
        blue_bullet(c, x, y + 1.5, size=4)

        # Highlight rectangle behind the lead phrase
        lead_w = c.stringWidth(lead, FONT, size)
        c.setFillColor(highlights[i % len(highlights)])
        c.setStrokeAlpha(0)
        c.rect(body_x - 1, y - 2, lead_w + 2, size * 0.95, fill=1, stroke=0)

        # Lead text on top
        c.setFillColor(CHARCOAL_DARK)
        c.setFont(FONT, size)
        c.drawString(body_x, y, lead)

        # Wrap and draw the body
        body_full = " " + punch
        # Render the first body fragment on the same line if it fits
        first_line_max = body_max - lead_w
        body_wrapped_first = wrap(punch, size, first_line_max)
        c.setFillColor(CHARCOAL_BODY)
        if body_wrapped_first:
            c.drawString(body_x + lead_w + 4, y, body_wrapped_first[0])
            y -= line_h_body
            # Remaining body wraps to full width
            remaining = " ".join(body_wrapped_first[1:])
            if remaining:
                rest = wrap(remaining, size, body_max)
                for line in rest:
                    c.drawString(body_x, y, line)
                    y -= line_h_body
        y -= inter_bullet_gap - line_h_body + 5 * mm
    return y


def autonomy_pullquote(c, x, y_top, width):
    """Soft pastel-blue highlighted block for the autonomy claim.
    No dark box — light Lloyds-style."""
    pad = 5 * mm
    inner_w = width - pad * 2

    body = ("Institutional intelligence is what enables agent autonomy. Without memory, "
            "AI agents cannot accumulate judgement — only execute tasks. The institution "
            "that owns the memory layer owns the substrate on which every autonomous agent "
            "inside it will operate.")

    # Measure
    wrapped = wrap(body, 10.5, inner_w)
    line_h = 14.5
    body_h = len(wrapped) * line_h
    block_h = body_h + pad * 2.0

    # Soft pastel block
    c.setFillColor(HIGHLIGHT_BLUE)
    c.setStrokeAlpha(0)
    c.rect(x, y_top - block_h, width, block_h, fill=1, stroke=0)

    # Blue accent bar on left
    c.setFillColor(BLUE)
    c.rect(x, y_top - block_h, 2.5, block_h, fill=1, stroke=0)

    # Body
    c.setFillColor(CHARCOAL_DARK)
    c.setFont(FONT, 10.5)
    cy = y_top - pad - 9
    for line in wrapped:
        c.drawString(x + pad + 4, cy, line)
        cy -= line_h

    return y_top - block_h


def theory_practice_diagram(c, cx, cy_top, width):
    """3 clean boxes — light Lloyds style. Pale blue tag bars, charcoal type."""
    box_h = 23 * mm
    op_w = 11 * mm
    box_w = (width - 2 * op_w) / 3

    x_left = cx - width / 2
    y_top = cy_top
    y_bot = y_top - box_h

    boxes = [
        ("Theory", "What LLMs know.",
         "Vast world knowledge from training. General reasoning. Out-of-the-box capability."),
        ("Practice", "What PLUR remembers.",
         "Your institution's actual rules, norms, judgement, decisions, and history."),
        ("Autonomy", "What agents become.",
         "Capable of exercising judgement — not just executing tasks. Agents that operate, not assistants that wait."),
    ]

    for i, (tag, lead, body) in enumerate(boxes):
        bx = x_left + i * (box_w + op_w)
        # Outer light frame
        c.setStrokeColor(LIGHT_GREY)
        c.setFillColor(WHITE)
        c.setLineWidth(0.6)
        c.roundRect(bx, y_bot, box_w, box_h, 4, stroke=1, fill=1)

        # Top pale blue accent bar
        c.setFillColor(BLUE_PALE)
        c.setStrokeAlpha(0)
        c.rect(bx, y_top - 5 * mm, box_w, 5 * mm, fill=1, stroke=0)

        # Tag inside blue bar
        c.setFillColor(BLUE)
        c.setFont(FONT, 8.5)
        c.drawString(bx + 3 * mm, y_top - 3.5 * mm, tag.upper())

        # Lead
        c.setFillColor(CHARCOAL_DARK)
        c.setFont(FONT, 10.5)
        c.drawString(bx + 3 * mm, y_top - 9.5 * mm, lead)

        # Body
        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, 7.5)
        wrapped = wrap(body, 7.5, box_w - 6 * mm)
        by = y_top - 13.5 * mm
        for line in wrapped:
            c.drawString(bx + 3 * mm, by, line)
            by -= 9

    # Operators — clean charcoal, no gold
    operators = [
        (x_left + box_w + op_w / 2, "+"),
        (x_left + 2 * box_w + op_w + op_w / 2, "="),
    ]
    for ox, sym in operators:
        c.setFillColor(CHARCOAL_MID)
        c.setFont(FONT, 22)
        sym_w = c.stringWidth(sym, FONT, 22)
        c.drawString(ox - sym_w / 2, y_top - box_h / 2 - 6, sym)

    return y_bot


def sovereignty_grid_2x2(c, cx, cy_top, width):
    """2x2 — light blue top accents."""
    gap = 3 * mm
    cell_w = (width - gap) / 2
    cell_h = 13 * mm
    x_left = cx - width / 2

    cells = [
        ("Local", "Memory lives on institutional infrastructure. No external queries."),
        ("Open", "Apache 2.0 open source. Audit the code. Fork it."),
        ("Air-gapped", "Runs without internet. No external dependencies."),
        ("Exportable", "Plain-text YAML source of truth. Move between deployments at any time."),
    ]

    for i, (tag, body) in enumerate(cells):
        row = i // 2
        col = i % 2
        cell_x = x_left + col * (cell_w + gap)
        cell_y_top = cy_top - row * (cell_h + gap)

        # Frame
        c.setStrokeColor(PALE_GREY)
        c.setFillColor(WHITE)
        c.setLineWidth(0.4)
        c.roundRect(cell_x, cell_y_top - cell_h, cell_w, cell_h, 3,
                    stroke=1, fill=1)

        # Top accent bar (pale blue)
        c.setFillColor(BLUE_PALE)
        c.setStrokeAlpha(0)
        c.rect(cell_x, cell_y_top - 2, cell_w, 2, fill=1, stroke=0)

        # Tag
        c.setFillColor(BLUE)
        c.setFont(FONT, 10)
        c.drawString(cell_x + 2.5 * mm, cell_y_top - 6 * mm, tag)

        # Body
        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, 8)
        wrapped = wrap(body, 8, cell_w - 5 * mm)
        by = cell_y_top - 9.5 * mm
        for line in wrapped:
            c.drawString(cell_x + 2.5 * mm, by, line)
            by -= 9.5

    return cy_top - 2 * (cell_h + gap) + gap


def guarantees_clean(c, x, y_top, width):
    """4 guarantees, no numbering — blue square bullets, lead + body inline."""
    items = [
        ("Zero data exfiltration.", "No API to a foreign cloud, no telemetry, no training-data leakage."),
        ("No operational disruption.", "PLUR is additive. Workflows continue unaffected if turned off."),
        ("No vendor lock-in.", "Plain-text YAML. Owned and exportable at any time."),
        ("Proven team.", "Eight years on Swarm and Fair Data Society."),
    ]

    y = y_top
    inter_gap = 2 * mm
    line_h = 11.5
    size = 9
    body_x = x + 9
    body_max = width - 9

    for lead, body in items:
        blue_bullet(c, x, y + 1.5, size=4)

        # Lead in dark
        c.setFillColor(CHARCOAL_DARK)
        c.setFont(FONT, size)
        c.drawString(body_x, y, lead)
        lead_w = c.stringWidth(lead, FONT, size)

        # Body inline, wrapping to full width if needed
        body_str = " " + body
        first_max = body_max - lead_w
        first_wrapped = wrap(body, size, first_max)
        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, size)
        if first_wrapped:
            c.drawString(body_x + lead_w + 4, y, first_wrapped[0])
            y -= line_h
            remainder = " ".join(first_wrapped[1:])
            if remainder:
                rest = wrap(remainder, size, body_max)
                for line in rest:
                    c.drawString(body_x, y, line)
                    y -= line_h
        else:
            y -= line_h
        y -= inter_gap

    return y


def phase_timeline(c, cx, cy_top, width):
    """Horizontal phase timeline — blue circles, clean."""
    phases = [
        ("0", "Foundation", "2 weeks",
         "Legal scaffolding. Walk-away gate."),
        ("1", "Team", "Weeks 2–8",
         "One team. First outcome ≤ 60 days."),
        ("2", "Institution", "Months 3–9",
         "Cross-department. Knowledge Packs."),
        ("3", "Beyond", "Months 9–12+",
         "Substrate for sovereign agents."),
    ]

    x_left = cx - width / 2
    n = len(phases)
    col_w = width / n
    circle_r = 4 * mm
    circle_y = cy_top - circle_r - 1.5 * mm

    # Connecting line
    c.setStrokeColor(BLUE_LIGHT)
    c.setLineWidth(1.1)
    c.line(x_left + col_w / 2, circle_y,
           x_left + width - col_w / 2, circle_y)

    for i, (num, label, dur, body) in enumerate(phases):
        cx_node = x_left + i * col_w + col_w / 2

        c.setFillColor(BLUE)
        c.setStrokeColor(BLUE)
        c.circle(cx_node, circle_y, circle_r, fill=1, stroke=0)

        c.setFillColor(WHITE)
        c.setFont(FONT, 10.5)
        nw = c.stringWidth(num, FONT, 10.5)
        c.drawString(cx_node - nw / 2, circle_y - 3, num)

        label_y = circle_y - circle_r - 5
        c.setFillColor(CHARCOAL_DARK)
        c.setFont(FONT, 9.5)
        lw = c.stringWidth(label, FONT, 9.5)
        c.drawString(cx_node - lw / 2, label_y, label)

        c.setFillColor(MUTED_GREY)
        c.setFont(FONT, 7)
        dw = c.stringWidth(dur, FONT, 7)
        c.drawString(cx_node - dw / 2, label_y - 8, dur)

        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, 7)
        wrapped = wrap(body, 7, col_w - 4)
        by = label_y - 16
        for line in wrapped:
            line_w = c.stringWidth(line, FONT, 7)
            c.drawString(cx_node - line_w / 2, by, line)
            by -= 8.5

    return cy_top - 30 * mm


def horizontal_pathway(c, cx, cy_top, width, stops):
    """3-stop CTA pathway — filled blue circles connected by line.
    Lloyds-aesthetic, no gold."""
    n = len(stops)
    col_w = width / n
    x_left = cx - width / 2

    circle_r = 3.5 * mm
    circle_y = cy_top - circle_r

    c.setStrokeColor(BLUE)
    c.setLineWidth(1.2)
    c.line(x_left + col_w / 2, circle_y,
           x_left + width - col_w / 2, circle_y)

    for i, (num, label, body) in enumerate(stops):
        cx_node = x_left + i * col_w + col_w / 2

        c.setFillColor(BLUE)
        c.setStrokeColor(BLUE)
        c.circle(cx_node, circle_y, circle_r, fill=1, stroke=0)

        c.setFillColor(WHITE)
        c.setFont(FONT, 9.5)
        nw = c.stringWidth(num, FONT, 9.5)
        c.drawString(cx_node - nw / 2, circle_y - 3, num)

        c.setFillColor(CHARCOAL_DARK)
        c.setFont(FONT, 9.5)
        lw = c.stringWidth(label, FONT, 9.5)
        c.drawString(cx_node - lw / 2, circle_y - circle_r - 5, label)

        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, 7)
        wrapped = wrap(body, 7, col_w - 4 * mm)
        by = circle_y - circle_r - 12
        for line in wrapped:
            line_w = c.stringWidth(line, FONT, 7)
            c.drawString(cx_node - line_w / 2, by, line)
            by -= 8.5

    return cy_top - 22 * mm


def inspirational_lines(c, cx, y_top, lines, size=11, line_h=15,
                        colour=CHARCOAL_DARK):
    """Centered stack of short statement lines."""
    y = y_top
    for line in lines:
        c.setFillColor(colour)
        c.setFont(FONT, size)
        lw = c.stringWidth(line, FONT, size)
        c.drawString(cx - lw / 2, y, line)
        y -= line_h
    return y


# ===========================================================================
# Page renderers
# ===========================================================================

def render_page_1(c, page_w, page_h, mx, cw):
    # Subtle background first — flowing lines, then orbs, then content
    flowing_lines(c, page_w, page_h, page_index=0)
    minimal_orbs(c, page_w, page_h)

    # Top metadata strip
    y = page_h - 13 * mm
    left_text(c, "DATAFUND  ·  2026", mx, y, 7.5, MUTED_GREY)
    right_text(c, "Page 1 / 2", page_w - mx, y, 7.5, MUTED_GREY)

    # Top thin rule
    y -= 4 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # Title block — no star, no logo
    y -= 14 * mm
    y = title_block(c, page_w, y,
                    ["Institutional Memory", "for Sovereign AI."],
                    mx=mx, title_size=28, line_gap=1.05)

    # Subtitle
    y -= 4 * mm
    c.setFillColor(CHARCOAL_MID)
    c.setFont(FONT, 12.5)
    c.drawString(mx, y, "Make your agents autonomous. Unlock the agent economy.")

    # Divider
    y -= 10 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # §1 — Memory is missing layer
    y -= 8 * mm
    y = section_title(c, "Memory is the missing AI infrastructure layer.",
                      mx, y, size=14, max_w=cw)
    y -= 7 * mm
    y = paragraph(c,
                  "Every major government, enterprise, and ministry is investing heavily in AI — "
                  "yet the same fundamental inefficiency repeats itself daily. Every team starts fresh. "
                  "Knowledge never compounds. Sovereignty over institutional intelligence is unresolved.",
                  mx, y, 9.5, CHARCOAL_BODY, cw, line_h=14)
    y -= 2 * mm
    y = paragraph(c,
                  "What is missing — globally — is the layer between the foundation model and the "
                  "institution's actual operating knowledge. PLUR fills this gap.",
                  mx, y, 9.5, CHARCOAL_BODY, cw, line_h=14)
    y -= 2 * mm
    y = paragraph(c,
                  "Deploying it now, before peers do, secures architectural first-mover advantage at "
                  "the infrastructure level. Within 12 months, this becomes the substrate on which "
                  "the agent economy is built.",
                  mx, y, 9.5, CHARCOAL_BODY, cw, line_h=14)

    # Divider
    y -= 5 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # §2 — Today's AI forgets
    y -= 8 * mm
    y = section_title(c, "Today's AI forgets — and sovereignty is unresolved.",
                      mx, y, size=14, max_w=cw)
    y -= 7 * mm
    problem_lines = [
        ("Sovereignty is unresolved.",
         "Frontier AI vendors build memory — on their cloud, under their terms, with your data leaving institutional borders."),
        ("Knowledge does not compound.",
         "Every team starts fresh. Lessons learned by one department never reach another."),
        ("AI is forgetful by design.",
         "LLMs do not retain context between sessions. Practical know-how lives in heads, not in systems."),
        ("Costs scale linearly, not learnings.",
         "Without memory, institutions pay repeatedly for AI to rediscover the same answers."),
    ]
    y = problem_bullets(c, mx, y, cw, problem_lines)

    # Divider
    y -= 1 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # §3 — PLUR captures
    y -= 8 * mm
    y = section_title(c, "PLUR captures, stores, and serves institutional reasoning.",
                      mx, y, size=14, max_w=cw)
    y -= 7 * mm
    y = paragraph(c,
                  "Private, locally-hosted, model-agnostic. Works with any AI tool — "
                  "Claude, ChatGPT, Copilot, OpenClaw, or your own.",
                  mx, y, 9.5, CHARCOAL_BODY, cw, line_h=14)
    y -= 2 * mm
    y = paragraph(c,
                  "Concrete: a senior staff member solves a complex problem at 2 PM on Sunday. "
                  "By Monday morning, a colleague in another department tackling a structurally similar "
                  "problem already has the solution surfaced by their AI assistant. No manual sharing. "
                  "No data leaving institutional borders.",
                  mx, y, 9.5, CHARCOAL_BODY, cw, line_h=14)
    y -= 2 * mm
    y = paragraph(c,
                  "A force-multiplier across the institution. The compounding effect over "
                  "12 months is transformational, not incremental.",
                  mx, y, 9.5, CHARCOAL_BODY, cw, line_h=14)

    # §4 — pastel-blue autonomy pull-quote (replaces dark callout)
    y -= 8 * mm
    y = section_title(c, "Memory is what makes agents autonomous.",
                      mx, y, size=14, max_w=cw)
    y -= 6 * mm
    y = autonomy_pullquote(c, mx, y, cw)

    # Continued marker — bottom-aligned
    centred_text(c,
                 "Continued on page 2  ·  Theory & Practice  ·  Sovereignty  ·  Guarantees  ·  Phases  ·  Close",
                 12 * mm, 7.5, MUTED_GREY, page_w)


def render_page_2(c, page_w, page_h, mx, cw):
    flowing_lines(c, page_w, page_h, page_index=1)
    minimal_orbs(c, page_w, page_h)

    # ---- FOOTER: drawn FIRST so it acts as a fixed reserved area ----
    # All content above must end at y > footer_top.
    footer_top = 24 * mm

    # Thin rule above closing
    thin_rule(c, footer_top - 1 * mm,
              mx + 20 * mm, page_w - mx - 20 * mm,
              colour=PALE_GREY)

    centred_text(c, "Three weeks to Phase 0.  Be among the first.",
                 footer_top - 7 * mm, 9.5, BLUE, page_w)

    track = ("CEN/CENELEC CWA 17525:2020  ·  Swarm Foundation  ·  "
             "Fair Data Society  ·  3× MyData Operator Award")
    centred_text(c, track, footer_top - 13 * mm, 6.5, MUTED_GREY, page_w)

    centred_text(c, "Gregor Žavcer  ·  CEO, PLUR  ·  gregor@plur.ai  ·  plur.ai",
                 footer_top - 19 * mm, 7, CHARCOAL_MID, page_w)

    # ---- Top metadata ----
    y = page_h - 13 * mm
    left_text(c, "DATAFUND  ·  2026", mx, y, 7.5, MUTED_GREY)
    right_text(c, "Page 2 / 2", page_w - mx, y, 7.5, MUTED_GREY)

    # Top rule
    y -= 4 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # Masthead
    y -= 13 * mm
    y = title_block(c, page_w, y,
                    ["Start with a Team.",
                     "Scale to the Institution.",
                     "Then Beyond."],
                    mx=mx, title_size=20, line_gap=1.08)

    # Subtitle
    y -= 3 * mm
    c.setFillColor(CHARCOAL_MID)
    c.setFont(FONT, 11)
    c.drawString(mx, y, "Architecture, not policy.")

    # Divider
    y -= 7 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # §5 — Theory + Practice = Autonomy (no intro paragraph — diagram speaks)
    y -= 5 * mm
    y = section_title(c, "The gap between theory and practice.",
                      mx, y, size=12.5, max_w=cw)
    y -= 4 * mm
    y = theory_practice_diagram(c, page_w / 2, y, cw)

    # Divider
    y -= 2 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # §6 — Sovereignty pillars
    y -= 5 * mm
    y = section_title(c, "Sovereignty by architecture, not by policy.",
                      mx, y, size=12.5, max_w=cw)
    y -= 4 * mm
    y = sovereignty_grid_2x2(c, page_w / 2, y, cw)

    # Divider
    y -= 2 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # §7 — No risk, full control
    y -= 5 * mm
    y = section_title(c, "No risk, full control.",
                      mx, y, size=12.5, max_w=cw)
    y -= 4 * mm
    y = guarantees_clean(c, mx + 2 * mm, y, cw)

    # Divider
    y -= 1 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # §8 — Phase timeline (closes the document content; footer follows)
    y -= 5 * mm
    y = section_title(c, "From one team to the agent economy in 12 months.",
                      mx, y, size=12.5, max_w=cw)
    y -= 3 * mm
    y = phase_timeline(c, page_w / 2, y, cw)

    # Diagnostic: warn if content overlaps reserved footer area
    if y < footer_top + 2 * mm:
        print(f"WARNING: page-2 content ended at y={y:.1f}pt — overlaps footer "
              f"(reserved at {footer_top:.1f}pt)")


def render(output_path):
    page_w, page_h = A4
    mx = 18 * mm
    cw = page_w - 2 * mx

    c = Canvas(str(output_path), pagesize=A4)
    render_page_1(c, page_w, page_h, mx, cw)
    c.showPage()
    render_page_2(c, page_w, page_h, mx, cw)
    c.save()


if __name__ == "__main__":
    out = Path("/Users/gregor/Data/1-datafund/1-tracks/comms/proposals/dubai-twopagers/2026-06-01-uae-twopager-v2.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    render(out)
    print(f"Rendered: {out}")
