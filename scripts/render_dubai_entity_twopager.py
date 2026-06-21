#!/usr/bin/env python3
"""
Render entity-specific PLUR two-pagers for Dubai government entities.

Memory-first ("Institutional Memory for Sovereign AI") spine, identical to the
universal v2 two-pager, with per-entity customization of:
  - Page-1 subtitle + opportunity section (grounded in the entity's real AI programme)
  - The PLUR "concrete example" paragraph
  - Page-2 masthead + Phase-3 ("Beyond") line
  - Use-case / value-proposition appendix

Pure PLUR play: branding is PLUR, contact is gregor@plur.ai.

This is a PARAMETERIZED rebuild of render_uae_twopager_v2.py — layout helpers are
reused verbatim; only the content-bearing functions take per-entity data.

Single source of truth: the SPECS dict below drives BOTH the PDF and a companion
markdown file, so the two never drift.

Deterministic ReportLab. A4 portrait.

Usage:
    python3 render_dubai_entity_twopager.py            # render all entities (md + pdf)
    python3 render_dubai_entity_twopager.py rta dewa   # render a subset
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


OUT_DIR = Path(
    "/Users/gregor/Data/1-datafund/1-tracks/comms/proposals/dubai-twopagers/entities"
)
DATE = "2026-06-20"


# ===========================================================================
# Palette — Lloyds-aesthetic light (identical to v2)
# ===========================================================================

WHITE = HexColor("#FFFFFF")
CHARCOAL_DARK = HexColor("#1A1A1A")
CHARCOAL_BODY = HexColor("#333333")
CHARCOAL_MID = HexColor("#555555")
MUTED_GREY = HexColor("#888888")
LIGHT_GREY = HexColor("#C8C8C8")
PALE_GREY = HexColor("#E8E8E8")

BLUE = HexColor("#0066FF")
BLUE_PALE = HexColor("#DCE9F8")
BLUE_LIGHT = HexColor("#7AA3F0")

LAVENDER = HexColor("#C9B8E8")
PEACH = HexColor("#FFCAA8")
SKY = HexColor("#A8C5E8")
MINT = HexColor("#B5DBC2")

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
# Low-level helpers (verbatim from v2)
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
# Decorative background (verbatim from v2)
# ===========================================================================

def pastel_orb(c, cx, cy, radius, colour, layers=8, layer_alpha=0.025):
    c.saveState()
    c.setStrokeAlpha(0)
    c.setFillColor(colour)
    c.setFillAlpha(layer_alpha)
    for i in range(layers, 0, -1):
        r = radius * (i / layers)
        c.circle(cx, cy, r, fill=1, stroke=0)
    c.restoreState()


def minimal_orbs(c, page_w, page_h):
    pastel_orb(c, page_w - 10 * mm, page_h - 18 * mm,
               radius=22 * mm, colour=PEACH, layers=8, layer_alpha=0.022)
    pastel_orb(c, 8 * mm, 28 * mm,
               radius=20 * mm, colour=LAVENDER, layers=8, layer_alpha=0.022)


def flowing_curve(c, x0, y0, x1, y1, ctrl1_offset=(0, 0), ctrl2_offset=(0, 0),
                  colour=LIGHT_GREY, alpha=0.18, w=0.45):
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
    if page_index == 0:
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
    y = y_top
    inter_bullet_gap = 4.5 * mm
    line_h_body = 13
    body_x = x + 9
    body_max = width - 9
    size = 9.5

    highlights = [HIGHLIGHT_PEACH, HIGHLIGHT_BLUE, HIGHLIGHT_LAVENDER, HIGHLIGHT_PEACH]

    for i, (lead, punch) in enumerate(lines):
        blue_bullet(c, x, y + 1.5, size=4)

        lead_w = c.stringWidth(lead, FONT, size)
        c.setFillColor(highlights[i % len(highlights)])
        c.setStrokeAlpha(0)
        c.rect(body_x - 1, y - 2, lead_w + 2, size * 0.95, fill=1, stroke=0)

        c.setFillColor(CHARCOAL_DARK)
        c.setFont(FONT, size)
        c.drawString(body_x, y, lead)

        first_line_max = body_max - lead_w
        body_wrapped_first = wrap(punch, size, first_line_max)
        c.setFillColor(CHARCOAL_BODY)
        if body_wrapped_first:
            c.drawString(body_x + lead_w + 4, y, body_wrapped_first[0])
            y -= line_h_body
            remaining = " ".join(body_wrapped_first[1:])
            if remaining:
                rest = wrap(remaining, size, body_max)
                for line in rest:
                    c.drawString(body_x, y, line)
                    y -= line_h_body
        y -= inter_bullet_gap - line_h_body + 5 * mm
    return y


def autonomy_pullquote(c, x, y_top, width, body):
    pad = 3.6 * mm
    inner_w = width - pad * 2

    wrapped = wrap(body, 9.5, inner_w)
    line_h = 13
    body_h = len(wrapped) * line_h
    block_h = body_h + pad * 2.0

    c.setFillColor(HIGHLIGHT_BLUE)
    c.setStrokeAlpha(0)
    c.rect(x, y_top - block_h, width, block_h, fill=1, stroke=0)

    c.setFillColor(BLUE)
    c.rect(x, y_top - block_h, 2.5, block_h, fill=1, stroke=0)

    c.setFillColor(CHARCOAL_DARK)
    c.setFont(FONT, 9.5)
    cy = y_top - pad - 8
    for line in wrapped:
        c.drawString(x + pad + 4, cy, line)
        cy -= line_h

    return y_top - block_h


def theory_practice_diagram(c, cx, cy_top, width):
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
        c.setStrokeColor(LIGHT_GREY)
        c.setFillColor(WHITE)
        c.setLineWidth(0.6)
        c.roundRect(bx, y_bot, box_w, box_h, 4, stroke=1, fill=1)

        c.setFillColor(BLUE_PALE)
        c.setStrokeAlpha(0)
        c.rect(bx, y_top - 5 * mm, box_w, 5 * mm, fill=1, stroke=0)

        c.setFillColor(BLUE)
        c.setFont(FONT, 8.5)
        c.drawString(bx + 3 * mm, y_top - 3.5 * mm, tag.upper())

        c.setFillColor(CHARCOAL_DARK)
        c.setFont(FONT, 10.5)
        c.drawString(bx + 3 * mm, y_top - 9.5 * mm, lead)

        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, 7.5)
        wrapped = wrap(body, 7.5, box_w - 6 * mm)
        by = y_top - 13.5 * mm
        for line in wrapped:
            c.drawString(bx + 3 * mm, by, line)
            by -= 9

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

        c.setStrokeColor(PALE_GREY)
        c.setFillColor(WHITE)
        c.setLineWidth(0.4)
        c.roundRect(cell_x, cell_y_top - cell_h, cell_w, cell_h, 3,
                    stroke=1, fill=1)

        c.setFillColor(BLUE_PALE)
        c.setStrokeAlpha(0)
        c.rect(cell_x, cell_y_top - 2, cell_w, 2, fill=1, stroke=0)

        c.setFillColor(BLUE)
        c.setFont(FONT, 10)
        c.drawString(cell_x + 2.5 * mm, cell_y_top - 6 * mm, tag)

        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, 8)
        wrapped = wrap(body, 8, cell_w - 5 * mm)
        by = cell_y_top - 9.5 * mm
        for line in wrapped:
            c.drawString(cell_x + 2.5 * mm, by, line)
            by -= 9.5

    return cy_top - 2 * (cell_h + gap) + gap


def guarantees_clean(c, x, y_top, width):
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

        c.setFillColor(CHARCOAL_DARK)
        c.setFont(FONT, size)
        c.drawString(body_x, y, lead)
        lead_w = c.stringWidth(lead, FONT, size)

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


def phase_timeline(c, cx, cy_top, width, phases):
    x_left = cx - width / 2
    n = len(phases)
    col_w = width / n
    circle_r = 4 * mm
    circle_y = cy_top - circle_r - 1.5 * mm

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


# ===========================================================================
# Page renderers (driven by spec)
# ===========================================================================

def render_page_1(c, page_w, page_h, mx, cw, spec):
    flowing_lines(c, page_w, page_h, page_index=0)
    minimal_orbs(c, page_w, page_h)

    y = page_h - 13 * mm
    left_text(c, "PLUR  ·  2026", mx, y, 7.5, MUTED_GREY)
    right_text(c, "Page 1 / 2", page_w - mx, y, 7.5, MUTED_GREY)

    y -= 4 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    y -= 14 * mm
    y = title_block(c, page_w, y, spec["p1_title"],
                    mx=mx, title_size=28, line_gap=1.05)

    y -= 4 * mm
    c.setFillColor(CHARCOAL_MID)
    sub_lines = wrap(spec["p1_subtitle"], 12, cw)
    for i, sl in enumerate(sub_lines):
        c.setFont(FONT, 12)
        c.drawString(mx, y - i * 15, sl)
    y -= (len(sub_lines) - 1) * 15

    y -= 10 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # §1 — Opportunity (entity-specific)
    y -= 6 * mm
    y = section_title(c, spec["opportunity_title"], mx, y, size=14, max_w=cw)
    y -= 6 * mm
    for i, para in enumerate(spec["opportunity_paras"]):
        if i > 0:
            y -= 1.5 * mm
        y = paragraph(c, para, mx, y, 9, CHARCOAL_BODY, cw, line_h=12.3)

    y -= 4 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # §2 — Today's AI forgets (shared)
    y -= 6 * mm
    y = section_title(c, "Today's AI forgets — and sovereignty is unresolved.",
                      mx, y, size=14, max_w=cw)
    y -= 6 * mm
    y = problem_bullets(c, mx, y, cw, SHARED_PROBLEM_BULLETS)

    y -= 1 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    # §3 — PLUR captures (shared frame + entity concrete example)
    y -= 6 * mm
    y = section_title(c, "PLUR captures, stores, and serves institutional reasoning.",
                      mx, y, size=14, max_w=cw)
    y -= 6 * mm
    y = paragraph(c,
                  "Private, locally-hosted, model-agnostic. Works with any AI tool — "
                  "Claude, ChatGPT, Copilot, OpenClaw, or your own.",
                  mx, y, 9, CHARCOAL_BODY, cw, line_h=12.3)
    y -= 1.5 * mm
    y = paragraph(c, spec["plur_concrete"], mx, y, 9, CHARCOAL_BODY, cw, line_h=12.3)
    y -= 1.5 * mm
    y = paragraph(c,
                  "A force-multiplier across the institution. The compounding effect over "
                  "12 months is transformational, not incremental.",
                  mx, y, 9, CHARCOAL_BODY, cw, line_h=12.3)

    # §4 — autonomy pull-quote (shared)
    y -= 6 * mm
    y = section_title(c, "Memory is what makes agents autonomous.",
                      mx, y, size=14, max_w=cw)
    y -= 5 * mm
    y = autonomy_pullquote(c, mx, y, cw, SHARED_AUTONOMY_BODY)

    if y < 16 * mm:
        print(f"  WARNING: page-1 content ended at y={y/mm:.1f}mm — risk of footer overlap")

    centred_text(c,
                 "Continued on page 2  ·  Theory & Practice  ·  Sovereignty  ·  Guarantees  ·  Phases  ·  Close",
                 12 * mm, 7.5, MUTED_GREY, page_w)


def render_page_2(c, page_w, page_h, mx, cw, spec):
    flowing_lines(c, page_w, page_h, page_index=1)
    minimal_orbs(c, page_w, page_h)

    footer_top = 31 * mm

    thin_rule(c, footer_top - 1 * mm,
              mx + 20 * mm, page_w - mx - 20 * mm,
              colour=PALE_GREY)

    # Disclaimer — small grey, wrapped, centred
    disc = spec.get("disclaimer", "")
    dy = footer_top - 4.5 * mm
    for dl in wrap(disc, 6.5, cw - 10 * mm):
        centred_text(c, dl, dy, 6.5, MUTED_GREY, page_w)
        dy -= 8

    centred_text(c, "Three weeks to Phase 0.  Be among the first.",
                 footer_top - 17 * mm, 9.5, BLUE, page_w)

    centred_text(c, SHARED_FOOTER_TRACK, footer_top - 22 * mm, 6.5, MUTED_GREY, page_w)

    centred_text(c, SHARED_CONTACT, footer_top - 27 * mm, 7, CHARCOAL_MID, page_w)

    y = page_h - 13 * mm
    left_text(c, "PLUR  ·  2026", mx, y, 7.5, MUTED_GREY)
    right_text(c, "Page 2 / 2", page_w - mx, y, 7.5, MUTED_GREY)

    y -= 4 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    y -= 13 * mm
    y = title_block(c, page_w, y, spec["p2_title"],
                    mx=mx, title_size=20, line_gap=1.08)

    y -= 3 * mm
    c.setFillColor(CHARCOAL_MID)
    c.setFont(FONT, 11)
    c.drawString(mx, y, "Architecture, not policy.")

    y -= 7 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    y -= 5 * mm
    y = section_title(c, "The gap between theory and practice.",
                      mx, y, size=12.5, max_w=cw)
    y -= 4 * mm
    y = theory_practice_diagram(c, page_w / 2, y, cw)

    y -= 2 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    y -= 5 * mm
    y = section_title(c, "Sovereignty by architecture, not by policy.",
                      mx, y, size=12.5, max_w=cw)
    y -= 4 * mm
    y = sovereignty_grid_2x2(c, page_w / 2, y, cw)

    y -= 2 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    y -= 5 * mm
    y = section_title(c, "No risk, full control.",
                      mx, y, size=12.5, max_w=cw)
    y -= 4 * mm
    y = guarantees_clean(c, mx + 2 * mm, y, cw)

    y -= 1 * mm
    thin_rule(c, y, mx, page_w - mx, colour=PALE_GREY)

    y -= 5 * mm
    y = section_title(c, spec["phases_title"], mx, y, size=12.5, max_w=cw)
    y -= 3 * mm
    y = phase_timeline(c, page_w / 2, y, cw, spec["phases"])

    if y < footer_top + 2 * mm:
        print(f"  WARNING: page-2 content ended at y={y:.1f}pt — overlaps footer "
              f"(reserved at {footer_top:.1f}pt)")


# ===========================================================================
# Shared content
# ===========================================================================

SHARED_PROBLEM_BULLETS = [
    ("Sovereignty is unresolved.",
     "Frontier AI vendors build memory — on their cloud, under their terms, with your data leaving institutional borders."),
    ("Knowledge does not compound.",
     "Every team starts fresh. Lessons learned by one department never reach another."),
    ("AI is forgetful by design.",
     "LLMs do not retain context between sessions. Practical know-how lives in heads, not in systems."),
    ("Costs scale linearly, not learnings.",
     "Without memory, institutions pay repeatedly for AI to rediscover the same answers."),
]

SHARED_AUTONOMY_BODY = (
    "Institutional intelligence is what enables agent autonomy. Without memory, "
    "AI agents cannot accumulate judgement — only execute tasks. The institution "
    "that owns the memory layer owns the substrate on which every autonomous agent "
    "inside it will operate.")

SHARED_FOOTER_TRACK = ("CEN/CENELEC CWA 17525:2020  ·  Swarm Foundation  ·  "
                       "Fair Data Society  ·  3× MyData Operator Award")

SHARED_CONTACT = "Gregor Žavcer  ·  CEO, PLUR  ·  gregor@plur.ai  ·  plur.ai"


# ===========================================================================
# Entity specifications (single source of truth for PDF + markdown)
# ===========================================================================

SPECS = {
    "dubai-government": {
        "name": "Dubai Government",
        "p1_title": ["Institutional Memory", "for Sovereign AI."],
        "p1_subtitle": "The substrate Dubai's agentic-government commitment runs on.",
        "opportunity_title": "Memory is the missing layer for agentic government.",
        "opportunity_paras": [
            "Dubai has committed to delivering the majority of government services through AI "
            "agents. Every entity — transport, utilities, land, finance — is investing heavily "
            "in AI. Yet the same inefficiency repeats daily: every team starts fresh, knowledge "
            "never compounds, and sovereignty over institutional intelligence is unresolved.",
            "What is missing — across every entity — is the layer between the foundation model "
            "and the government's actual operating knowledge. PLUR fills this gap, on the "
            "government's own infrastructure.",
            "Deploying it now secures architectural first-mover advantage at the infrastructure "
            "level. Within 12 months it becomes the substrate the agentic-government commitment "
            "needs to deliver.",
        ],
        "plur_concrete": (
            "Concrete: a senior official solves a complex problem in one entity at 2 PM on "
            "Sunday. By Monday morning, a colleague in another entity facing a structurally "
            "similar problem already has the solution surfaced by their AI assistant. No manual "
            "sharing. No data leaving government borders."),
        "p2_title": ["Start with one Entity.", "Scale across Government.", "Then Beyond."],
        "phases_title": "From one entity to the agent economy in 12 months.",
        "phases": [
            ("0", "Foundation", "2 weeks", "Legal scaffolding. Walk-away gate."),
            ("1", "Entity", "Weeks 2–8", "One entity. First outcome ≤ 60 days."),
            ("2", "Government", "Months 3–9", "Cross-entity Knowledge Packs under consent."),
            ("3", "Beyond", "Months 9–12+", "Substrate for sovereign agents and a Dubai data economy."),
        ],
        "use_cases": [
            "Cross-entity knowledge transfer without data leaving government borders.",
            "Continuity through staff transitions — institutional judgement is retained, not lost.",
            "Agent autonomy across government services — agents that act, not tools that wait.",
            "Consistent, auditable reasoning across ministries and authorities.",
            "Horizon: a sovereign Dubai data economy, built on the same memory substrate.",
        ],
        "context_note": (
            "Umbrella two-pager — the master narrative. The entity-specific versions "
            "(RTA, DEWA, DLD, DIB) are verticals of this same memory-first spine."),
    },

    "rta": {
        "name": "Roads and Transport Authority (RTA)",
        "p1_title": ["Institutional Memory", "for Sovereign AI."],
        "p1_subtitle": "The memory layer for AI Strategy 2030 and autonomous mobility.",
        "opportunity_title": "Memory is the missing layer in AI Strategy 2030.",
        "opportunity_paras": [
            "RTA's AI Strategy 2030 spans 81 projects across six pillars — from intelligent "
            "traffic management to autonomous mobility, with a target of 25% of all trips "
            "self-driving by 2030. Each initiative invests heavily in AI. Yet judgement earned "
            "in one project rarely reaches the next, and sovereignty over that intelligence is "
            "unresolved.",
            "What is missing is the layer between the foundation model and RTA's actual operating "
            "knowledge — the traffic decisions, the incident learnings, the licensing edge cases. "
            "PLUR captures it, on RTA's own infrastructure.",
            "Deploying it now turns 81 parallel pilots into one compounding system — and secures "
            "first-mover advantage at the infrastructure level.",
        ],
        "plur_concrete": (
            "Concrete: a control-room engineer resolves a complex congestion pattern at a major "
            "interchange on Sunday. By Monday, the AI assistant supporting another district "
            "facing a structurally similar pattern already surfaces the resolution. No manual "
            "sharing. No data leaving RTA's borders."),
        "p2_title": ["Start with a Team.", "Scale across RTA.", "Then Beyond."],
        "phases_title": "From one team to autonomous mobility in 12 months.",
        "phases": [
            ("0", "Foundation", "2 weeks", "Legal scaffolding. Walk-away gate."),
            ("1", "Team", "Weeks 2–8", "One team. First outcome ≤ 60 days."),
            ("2", "RTA-wide", "Months 3–9", "Cross-pillar Knowledge Packs under consent."),
            ("3", "Beyond", "Months 9–12+", "Substrate for autonomous mobility — and mobility data as a sovereign asset."),
        ],
        "use_cases": [
            "Traffic-management decisions captured once, reused at every intersection — "
            "compounding the AI smart-signal rollout.",
            "Autonomous-vehicle incident and edge-case learnings retained across the fleet for "
            "safer commercial scale-up.",
            "Cognitive-licensing and customer-service reasoning kept consistent across channels.",
            "The 81 AI initiatives stop rediscovering the same answers — one compounding system.",
            "Horizon: anonymised Salik / Nol / metro / AV mobility data → tokenised mobility-data "
            "assets (urban planning, insurers, AV training).",
        ],
        "context_note": (
            "Grounded in RTA's AI Strategy 2030 (launched June 2025, 81 projects, six pillars) "
            "and the Pony.ai autonomous-taxi commercial rollout targeted for 2026."),
    },

    "dewa": {
        "name": "Dubai Electricity and Water Authority (DEWA)",
        "p1_title": ["Institutional Memory", "for Sovereign AI."],
        "p1_subtitle": "Memory for the world's first AI-native utility.",
        "opportunity_title": "Memory is the missing layer in an AI-native utility.",
        "opportunity_paras": [
            "DEWA has set out to become the world's first AI-native utility — Rammas has answered "
            "over 12 million enquiries, generative AI is rolling out across operations, and an AI "
            "Virtual Engineer joins the power network in 2026. Each system invests heavily in AI. "
            "Yet the judgement they accumulate does not persist or compound, and sovereignty over "
            "it is unresolved.",
            "What is missing is the layer between the foundation model and DEWA's actual operating "
            "knowledge — the root-cause analyses, the grid decisions, the consumption insights. "
            "PLUR captures it, on DEWA's own infrastructure.",
            "Deploying it now means the AI Virtual Engineer and Rammas accumulate expertise "
            "instead of resetting — and secures first-mover advantage at the infrastructure level.",
        ],
        "plur_concrete": (
            "Concrete: an engineer resolves a transformer-load anomaly on Sunday. By Monday, the "
            "AI Virtual Engineer supporting a structurally similar asset already surfaces the root "
            "cause and the fix. No manual sharing. No data leaving DEWA's borders."),
        "p2_title": ["Start with a Team.", "Scale across DEWA.", "Then Beyond."],
        "phases_title": "From one team to an AI-native utility in 12 months.",
        "phases": [
            ("0", "Foundation", "2 weeks", "Legal scaffolding. Walk-away gate."),
            ("1", "Team", "Weeks 2–8", "One team. First outcome ≤ 60 days."),
            ("2", "DEWA-wide", "Months 3–9", "Cross-division Knowledge Packs under consent."),
            ("3", "Beyond", "Months 9–12+", "Substrate for sovereign energy agents — and grid data as a sovereign asset."),
        ],
        "use_cases": [
            "Grid and asset root-cause analyses retained → the AI Virtual Engineer compounds "
            "expertise instead of resetting.",
            "Rammas's 12-million-enquiry knowledge captured and reused across 'Rammas for You' and "
            "'Rammas for Work'.",
            "Cross-team learnings across generation, transmission, water and solar "
            "(Mohammed bin Rashid Al Maktoum Solar Park).",
            "The Microsoft Copilot / generative-AI rollout grounded in DEWA's real operating "
            "knowledge — sovereign, not on a vendor cloud.",
            "Horizon: grid / water / solar consumption data → demand-forecasting and ESG / carbon "
            "data assets.",
        ],
        "context_note": (
            "Grounded in DEWA's 'world's first AI-native utility' roadmap (March 2025), the Rammas "
            "virtual employee, the AI Virtual Engineer (live 2026), and the $1.9B smart-grid "
            "investment."),
    },

    "dld": {
        "name": "Dubai Land Department (DLD)",
        "p1_title": ["Institutional Memory", "for Sovereign AI."],
        "p1_subtitle": "The reasoning layer behind tokenised real estate.",
        "opportunity_title": "Memory is the missing layer behind tokenised real estate.",
        "opportunity_paras": [
            "DLD launched MENA's first licensed tokenised real-estate platform and projects "
            "tokenised property could reach roughly 7% of transactions — about $16 billion — by "
            "2033. It is the most advanced real-asset tokenisation programme in the region. Yet "
            "the reasoning behind it — valuations, deal structuring, regulatory precedent — lives "
            "in heads, not systems, and sovereignty over it is unresolved.",
            "What is missing is the layer between the foundation model and DLD's actual operating "
            "knowledge. PLUR captures it, on DLD's own infrastructure — the institution that owns "
            "the asset also owns the reasoning behind it.",
            "Deploying it now secures first-mover advantage at the infrastructure level, and a "
            "memory backbone for the tokenisation programme as it scales.",
        ],
        "plur_concrete": (
            "Concrete: a valuer settles a complex methodology question on a landmark asset on "
            "Sunday. By Monday, the AI assistant supporting a structurally similar valuation "
            "already surfaces the precedent and the rationale. No manual sharing. No data leaving "
            "DLD's borders."),
        "p2_title": ["Start with a Team.", "Scale across DLD.", "Then Beyond."],
        "phases_title": "From one team to a sovereign property-intelligence layer in 12 months.",
        "phases": [
            ("0", "Foundation", "2 weeks", "Legal scaffolding. Walk-away gate."),
            ("1", "Team", "Weeks 2–8", "One team. First outcome ≤ 60 days."),
            ("2", "DLD-wide", "Months 3–9", "Cross-department Knowledge Packs under consent."),
            ("3", "Beyond", "Months 9–12+", "Substrate for sovereign property agents — and transaction data as a sovereign asset."),
        ],
        "use_cases": [
            "Valuation methodology and market-intelligence reasoning captured and kept consistent.",
            "Tokenisation deal-structuring and VARA / Central Bank regulatory precedent retained "
            "across the Prypco Mint programme.",
            "Registration and dispute edge-case judgement preserved through staff change.",
            "Cross-department knowledge across registration, Ejari and investment.",
            "Horizon: property transaction / valuation data → a tokenised data-asset class "
            "complementing the property RWA programme.",
        ],
        "context_note": (
            "Grounded in DLD's MENA-first tokenised real-estate launch (Prypco Mint, May 2025, on "
            "the XRP Ledger, under VARA and Central Bank oversight) and the $16B-by-2033 target."),
    },

    "dib": {
        "name": "Dubai Islamic Bank (DIB)",
        "p1_title": ["Institutional Memory", "for Sovereign AI."],
        "p1_subtitle": "Memory for AI built on Islamic principles.",
        "opportunity_title": "Memory is the missing layer in responsible AI.",
        "opportunity_paras": [
            "Dubai Islamic Bank — the world's first Islamic bank — is scaling AI through the DIB "
            "Academy and its HCLTech partnership, aligned with Islamic principles of fairness, "
            "transparency, and the prohibition of riba and exploitation. Yet the judgement its AI "
            "accumulates does not persist or compound, and sovereignty over it is unresolved.",
            "What is missing is the layer between the foundation model and DIB's actual operating "
            "knowledge — the Sharia-compliance rulings, the credit reasoning, the fraud patterns. "
            "PLUR captures it on DIB's own infrastructure, with fairness and consent built into "
            "the architecture, not bolted on.",
            "Fair-data principles are Islamic-finance ethics expressed technically: no "
            "exploitation, full provenance, consent at the core. PLUR makes that the foundation "
            "of every agent in the bank.",
        ],
        "plur_concrete": (
            "Concrete: a Sharia-compliance officer resolves a nuanced structuring question on "
            "Sunday. By Monday, the AI assistant supporting a similar case already surfaces the "
            "ruling and its rationale — auditable, consistent, explainable. No data leaves the "
            "bank's borders."),
        "p2_title": ["Start with a Team.", "Scale to the Bank.", "Then Beyond."],
        "phases_title": "From one team to a sovereign, Sharia-compliant AI bank in 12 months.",
        "phases": [
            ("0", "Foundation", "2 weeks", "Legal scaffolding. Walk-away gate."),
            ("1", "Team", "Weeks 2–8", "One team. First outcome ≤ 60 days."),
            ("2", "Bank-wide", "Months 3–9", "Cross-department Knowledge Packs under consent."),
            ("3", "Beyond", "Months 9–12+", "Substrate for sovereign, Sharia-compliant agents."),
        ],
        "use_cases": [
            "Sharia-compliance rulings and rationale captured → consistent, auditable, reused "
            "(reinforcing the HCLTech AI rollout).",
            "Credit and risk reasoning that avoids exploitative assessment — retained and "
            "explainable.",
            "Fraud-pattern and customer-protection learnings compounding across the bank.",
            "DIB Academy upskilling reinforced by an institutional memory every employee's AI "
            "draws on.",
            "Fairness, consent and provenance built into the architecture — fair data is Islamic-"
            "finance ethics, expressed technically.",
            "Horizon: consent-based, Sharia-compliant data monetisation.",
        ],
        "context_note": (
            "Recycled from the Lloyds Banking Group spine (PLUR-led memory + agent economy), "
            "re-skinned for Islamic finance. Grounded in the DIB Academy (Q1 2025) and the "
            "HCLTech AI partnership (October 2025)."),
    },
}


# ===========================================================================
# Finalized content override (auditor-loop output, fitted to layout)
# ===========================================================================

_FINAL = OUT_DIR / "_final_content.json"
if _FINAL.exists():
    _data = json.loads(_FINAL.read_text(encoding="utf-8"))
    for _k, _v in _data.items():
        SPECS[_k] = {**SPECS.get(_k, {}), **_v}


# ===========================================================================
# Markdown emission (mirrors the PDF, from the same spec)
# ===========================================================================

def write_markdown(key, spec, md_path):
    title = " ".join(spec["p1_title"]).rstrip(".")
    lines = []
    lines.append("---")
    lines.append("type: two-pager")
    lines.append(f'title: "Institutional Memory for Sovereign AI — {spec["name"]}"')
    lines.append(f'subtitle: "{spec["p1_subtitle"]}"')
    lines.append(f'entity: "{spec["name"]}"')
    lines.append("project: dubai-pilot")
    lines.append(f"created: {DATE}")
    lines.append("format: A4 portrait, 2 pages")
    lines.append("renderer: .datacore/modules/slides/scripts/render_dubai_entity_twopager.py")
    lines.append(f"output: {DATE}-{key}-twopager.pdf")
    lines.append("spine: memory-first (pure PLUR play)")
    lines.append("status: draft")
    lines.append("---")
    lines.append("")
    lines.append(f"# Institutional Memory for Sovereign AI — {spec['name']}")
    lines.append("")
    lines.append(f"**{spec['p1_subtitle']}**")
    lines.append("")
    lines.append(f"> Context: {spec['context_note']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Page 1 — The Opportunity")
    lines.append("")
    lines.append(f"### {spec['opportunity_title']}")
    lines.append("")
    for para in spec["opportunity_paras"]:
        lines.append(para)
        lines.append("")
    lines.append("### Today's AI forgets — and sovereignty is unresolved.")
    lines.append("")
    for lead, body in SHARED_PROBLEM_BULLETS:
        lines.append(f"- **{lead}** {body}")
    lines.append("")
    lines.append("### PLUR captures, stores, and serves institutional reasoning.")
    lines.append("")
    lines.append("Private, locally-hosted, model-agnostic. Works with any AI tool — "
                 "Claude, ChatGPT, Copilot, OpenClaw, or your own.")
    lines.append("")
    lines.append(spec["plur_concrete"])
    lines.append("")
    lines.append("A force-multiplier across the institution. The compounding effect over "
                 "12 months is transformational, not incremental.")
    lines.append("")
    lines.append("### Memory is what makes agents autonomous.")
    lines.append("")
    lines.append(f"> {SHARED_AUTONOMY_BODY}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Page 2 — The Plan")
    lines.append("")
    lines.append(f"**{' '.join(spec['p2_title'])}**")
    lines.append("*Architecture, not policy.*")
    lines.append("")
    lines.append("### The gap between theory and practice.")
    lines.append("")
    lines.append("| | Theory | Practice | Autonomy |")
    lines.append("|---|---|---|---|")
    lines.append("| **What it is** | What LLMs know | What PLUR remembers | What agents become |")
    lines.append("| **Source** | World knowledge from training | Your institution's actual rules, "
                 "norms, judgement | Capable of exercising judgement |")
    lines.append("| **Without it** | Generic answers | Forgetful AI | Tools that wait, not agents "
                 "that act |")
    lines.append("")
    lines.append("**Theory + Practice = Autonomy.**")
    lines.append("")
    lines.append("### Sovereignty by architecture, not by policy.")
    lines.append("")
    lines.append("- **Local** — Memory lives on institutional infrastructure. No external queries.")
    lines.append("- **Open** — Apache 2.0 open source. Audit the code. Fork it.")
    lines.append("- **Air-gapped** — Runs without internet. No external dependencies.")
    lines.append("- **Exportable** — Plain-text YAML source of truth. Move between deployments at "
                 "any time.")
    lines.append("")
    lines.append("### No risk, full control.")
    lines.append("")
    lines.append("- **Zero data exfiltration.** No API to a foreign cloud, no telemetry, no "
                 "training-data leakage.")
    lines.append("- **No operational disruption.** PLUR is additive. Workflows continue unaffected "
                 "if turned off.")
    lines.append("- **No vendor lock-in.** Plain-text YAML. Owned and exportable at any time.")
    lines.append("- **Proven team.** Eight years on Swarm and Fair Data Society.")
    lines.append("")
    lines.append(f"### {spec['phases_title']}")
    lines.append("")
    lines.append("| Phase | Scope | What happens |")
    lines.append("|---|---|---|")
    for num, label, dur, body in spec["phases"]:
        lines.append(f"| **{num} — {label}** | {dur} | {body} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Use cases / value proposition")
    lines.append("")
    for uc in spec["use_cases"]:
        lines.append(f"- {uc}")
    lines.append("")
    if spec.get("disclaimer"):
        lines.append(f"> _{spec['disclaimer']}_")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**Three weeks to Phase 0. Be among the first.**")
    lines.append("")
    lines.append(SHARED_FOOTER_TRACK.replace("  ·  ", " · "))
    lines.append("")
    lines.append(SHARED_CONTACT.replace("  ·  ", " · "))
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")


# ===========================================================================
# Render
# ===========================================================================

def render_pdf(spec, pdf_path):
    page_w, page_h = A4
    mx = 18 * mm
    cw = page_w - 2 * mx

    c = Canvas(str(pdf_path), pagesize=A4)
    render_page_1(c, page_w, page_h, mx, cw, spec)
    c.showPage()
    render_page_2(c, page_w, page_h, mx, cw, spec)
    c.save()


def render(key):
    spec = SPECS[key]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUT_DIR / f"{DATE}-{key}-twopager.pdf"
    md_path = OUT_DIR / f"{DATE}-{key}-twopager.md"
    print(f"[{key}] {spec['name']}")
    render_pdf(spec, pdf_path)
    write_markdown(key, spec, md_path)
    print(f"  → {pdf_path.name}")
    print(f"  → {md_path.name}")


if __name__ == "__main__":
    keys = sys.argv[1:] or list(SPECS.keys())
    for k in keys:
        if k not in SPECS:
            print(f"Unknown entity '{k}'. Known: {', '.join(SPECS)}")
            continue
        render(k)
    print("Done.")
