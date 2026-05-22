#!/usr/bin/env python3
"""
Render the Dubai-blueprint TWO-PAGER for combined readership (executives who
want more detail than the one-pager but still scannable in 5 minutes).

Page 1: Positioning (Opportunity → Proposition → Why Now / First-in-the-world)
Page 2: Plan (Pilot phases → Economics → Track record → First step)

Deterministic ReportLab. Same design system as the Dubai one-pagers.
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


# Brand palette
CHARCOAL_DARK = HexColor("#1A1A1A")
CHARCOAL_BODY = HexColor("#2A2A2A")
MUTED_GREY = HexColor("#888888")
HAIRLINE_GREY = HexColor("#D0D0D0")
GOLD = HexColor("#C9A961")
GOLD_PALE = HexColor("#F2E6C7")
WHITE = HexColor("#FFFFFF")


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


# ---------- low-level drawing helpers ----------

def centred_text(c: Canvas, text: str, y: float, size: float, colour, page_w: float):
    c.setFont(FONT, size)
    c.setFillColor(colour)
    w = c.stringWidth(text, FONT, size)
    c.drawString((page_w - w) / 2, y, text)


def left_text(c: Canvas, text: str, x: float, y: float, size: float, colour):
    c.setFont(FONT, size)
    c.setFillColor(colour)
    c.drawString(x, y, text)


def hairline(c: Canvas, y: float, x0: float, x1: float, colour=HAIRLINE_GREY, w=0.5):
    c.setStrokeColor(colour)
    c.setLineWidth(w)
    c.line(x0, y, x1, y)


def wrap(text: str, size: float, max_w: float) -> list[str]:
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


def paragraph(c: Canvas, text: str, x: float, y_top: float, size: float,
              colour, max_w: float, line_h: float | None = None) -> float:
    line_h = line_h or size * 1.42
    c.setFont(FONT, size)
    c.setFillColor(colour)
    y = y_top
    for line in wrap(text, size, max_w):
        c.drawString(x, y, line)
        y -= line_h
    return y


def eight_pointed_star(c: Canvas, cx: float, cy: float, outer: float,
                       colour=GOLD, fill=False, stroke_w=0.9):
    c.saveState()
    c.setStrokeColor(colour)
    c.setFillColor(colour)
    c.setLineWidth(stroke_w)
    inner = outer * 0.42
    pts = []
    for i in range(16):
        angle = math.pi / 2 - (i * math.pi / 8)
        r = outer if i % 2 == 0 else inner
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    path = c.beginPath()
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    path.close()
    c.drawPath(path, stroke=1, fill=1 if fill else 0)
    c.restoreState()


def small_caps_header(c: Canvas, text: str, x: float, y: float, size: float = 9.5):
    c.saveState()
    c.setFillColor(GOLD)
    c.setFont(FONT, size)
    spacing = size * 0.25
    cx = x
    for ch in text.upper():
        c.drawString(cx, y, ch)
        cx += c.stringWidth(ch, FONT, size) + spacing
    c.restoreState()


# ---------- visual elements ----------

def sovereign_callout(c: Canvas, cx: float, cy: float, width: float, height: float = 14):
    """Pale-gold rounded band with sovereignty assurances."""
    x = cx - width / 2
    y = cy - height / 2
    c.setFillColor(GOLD_PALE)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.6)
    c.roundRect(x, y, width, height, 4, fill=1, stroke=1)
    # Small flanking stars
    eight_pointed_star(c, x + 6, cy, outer=2.2, colour=GOLD)
    eight_pointed_star(c, x + width - 6, cy, outer=2.2, colour=GOLD)
    # Centred message
    msg = "Self-sovereign architecture  ·  Local-first & Private  ·  Regulatory compliant"
    c.setFont(FONT, 8)
    c.setFillColor(CHARCOAL_BODY)
    w = c.stringWidth(msg, FONT, 8)
    c.drawString(cx - w / 2, cy - 2.5, msg)


def two_propositions(c: Canvas, cx: float, cy: float, width: float, height: float,
                     left_label: str, left_lines: list[str],
                     right_label: str, right_lines: list[str]):
    """Two side-by-side proposition cards with bulleted lines."""
    gap = 14
    card_w = (width - gap) / 2
    card_h = height

    for i, (label, lines, left_x) in enumerate([
        (left_label, left_lines, cx - width / 2),
        (right_label, right_lines, cx - width / 2 + card_w + gap),
    ]):
        # Card outline
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        c.setFillColor(WHITE)
        c.roundRect(left_x, cy - card_h / 2, card_w, card_h, 4, fill=0, stroke=1)
        # Label (gold small-caps)
        small_caps_header(c, label, left_x + 8, cy + card_h / 2 - 12, 8)
        # Body lines (bullets)
        y = cy + card_h / 2 - 28
        for line in lines:
            # bullet
            c.setFillColor(GOLD)
            c.circle(left_x + 11, y + 2, 1.0, fill=1, stroke=0)
            # text
            c.setFillColor(CHARCOAL_BODY)
            c.setFont(FONT, 8.5)
            for wline in wrap(line, 8.5, card_w - 22):
                c.drawString(left_x + 16, y, wline)
                y -= 10.5
            y -= 3


def four_pillars(c: Canvas, cx: float, cy: float, width: float,
                 pillars: list[tuple[str, str]]):
    """Four horizontal pillar boxes — DATA / AI / CRYPTO / REGULATORY."""
    n = len(pillars)
    gap = 8
    box_w = (width - (n - 1) * gap) / n
    box_h = 56
    box_y = cy - box_h / 2

    for i, (label, body) in enumerate(pillars):
        x = cx - width / 2 + i * (box_w + gap)
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        c.setFillColor(WHITE)
        c.roundRect(x, box_y, box_w, box_h, 3, fill=0, stroke=1)
        # Label
        small_caps_header(c, label, x + (box_w - small_caps_w(label, 8)) / 2,
                          box_y + box_h - 13, 8)
        # Body
        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, 7.5)
        lines = wrap(body, 7.5, box_w - 12)
        ty = box_y + box_h - 26
        for line in lines:
            lw = c.stringWidth(line, FONT, 7.5)
            c.drawString(x + (box_w - lw) / 2, ty, line)
            ty -= 9


def small_caps_w(text: str, size: float) -> float:
    """Visual width of small-caps rendered text (with letter-spacing)."""
    spacing = size * 0.25
    return sum(pdfmetrics.stringWidth(ch, FONT, size) + spacing
               for ch in text.upper()) - spacing


def pilot_phases_detailed(c: Canvas, cx: float, cy: float, width: float):
    """Three phase boxes with internal/external sub-bullets."""
    phases = [
        ("PHASE 0", "Weeks 0–2", "Alignment", [
            "Internal: ownership policy signed",
            "External: tokenisation framework agreed",
        ]),
        ("PHASE 1", "Weeks 2–14", "Capture & tokenise", [
            "Internal: PLUR knowledge capture deployed",
            "External: first asset listed on DDE sandbox",
        ]),
        ("PHASE 2", "Months 4–12", "Scale & production", [
            "Internal: rollout across ministries",
            "External: full DDE launch, asset categories expand",
        ]),
    ]
    n = len(phases)
    gap = 8
    box_w = (width - (n - 1) * gap) / n
    box_h = 78
    box_y = cy - box_h / 2

    for i, (label, duration, theme, bullets) in enumerate(phases):
        x = cx - width / 2 + i * (box_w + gap)
        # Box (phase 0 highlighted)
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.9)
        c.setFillColor(GOLD_PALE if i == 0 else WHITE)
        c.roundRect(x, box_y, box_w, box_h, 3, fill=1 if i == 0 else 0, stroke=1)
        # Phase label
        small_caps_header(c, label, x + (box_w - small_caps_w(label, 8)) / 2,
                          box_y + box_h - 12, 8)
        # Duration
        c.setFont(FONT, 7.5)
        c.setFillColor(MUTED_GREY)
        dw = c.stringWidth(duration, FONT, 7.5)
        c.drawString(x + (box_w - dw) / 2, box_y + box_h - 22, duration)
        # Theme
        c.setFont(FONT, 9)
        c.setFillColor(CHARCOAL_DARK)
        tw = c.stringWidth(theme, FONT, 9)
        c.drawString(x + (box_w - tw) / 2, box_y + box_h - 35, theme)
        # Hairline separator
        hairline(c, box_y + box_h - 41, x + 8, x + box_w - 8)
        # Bullets
        c.setFont(FONT, 7.5)
        c.setFillColor(CHARCOAL_BODY)
        by = box_y + box_h - 50
        for bullet in bullets:
            for line in wrap(bullet, 7.5, box_w - 16):
                c.drawString(x + 10, by, line)
                by -= 9
            by -= 1

        # Arrow between
        if i < n - 1:
            ax = x + box_w
            c.setStrokeColor(GOLD)
            c.setLineWidth(0.9)
            c.line(ax, cy, ax + gap - 2, cy)
            c.line(ax + gap - 2, cy, ax + gap - 5, cy + 2.5)
            c.line(ax + gap - 2, cy, ax + gap - 5, cy - 2.5)


def three_sided_market(c: Canvas, cx: float, cy: float, width: float, height: float = 44):
    """Three-column flat layout: Data Owners | AI Buyers | Investors.
    Cleaner than triangle — fits in fixed vertical band."""
    n = 3
    gap = 10
    col_w = (width - (n - 1) * gap) / n
    col_h = height
    col_y = cy - col_h / 2

    cols = [
        ("DATA OWNERS",  "Host entity, government,\nindividuals.",
         "Earn royalties on access."),
        ("AI BUYERS",    "Model developers,\nagent operators.",
         "License fees per access."),
        ("INVESTORS",    "Institutional capital,\ntoken-holders.",
         "ERC-3643 security tokens\non data cashflows."),
    ]

    for i, (label, who, earns) in enumerate(cols):
        x = cx - width / 2 + i * (col_w + gap)
        # Subtle gold-pale fill, gold outline
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        c.setFillColor(GOLD_PALE)
        c.roundRect(x, col_y, col_w, col_h, 3, fill=1, stroke=1)
        # Label
        lw = small_caps_w(label, 8)
        small_caps_header(c, label, x + (col_w - lw) / 2, col_y + col_h - 11, 8)
        # Who (charcoal)
        c.setFont(FONT, 7.5)
        c.setFillColor(CHARCOAL_BODY)
        wy = col_y + col_h - 23
        for line in who.split("\n"):
            tw = c.stringWidth(line, FONT, 7.5)
            c.drawString(x + (col_w - tw) / 2, wy, line)
            wy -= 9
        # Earns (gold accent)
        c.setFillColor(GOLD)
        c.setFont(FONT, 7.5)
        for line in earns.split("\n"):
            tw = c.stringWidth(line, FONT, 7.5)
            c.drawString(x + (col_w - tw) / 2, wy - 1, line)
            wy -= 9


def label_text(c: Canvas, header: str, body: str, x: float, y: float,
               anchor: str = "left", up: bool = False):
    """Two-line label (gold header + grey body lines) anchored at x,y.
    anchor: left | right | centre-below-above"""
    c.setFont(FONT, 8)
    body_lines = body.split("\n")
    if anchor == "centre-below-above":
        # Header above the point, body lines above that
        hw = small_caps_w(header, 8)
        small_caps_header(c, header, x - hw / 2, y, 8)
        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, 7.5)
        by = y + 12 if up else y - 12
        for line in body_lines:
            lw = c.stringWidth(line, FONT, 7.5)
            c.drawString(x - lw / 2, by, line)
            by += 9 if up else -9
    elif anchor == "right":
        hw = small_caps_w(header, 8)
        small_caps_header(c, header, x - hw, y, 8)
        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, 7.5)
        by = y - 10
        for line in body_lines:
            lw = c.stringWidth(line, FONT, 7.5)
            c.drawString(x - lw, by, line)
            by -= 9
    else:  # left
        small_caps_header(c, header, x, y, 8)
        c.setFillColor(CHARCOAL_BODY)
        c.setFont(FONT, 7.5)
        by = y - 10
        for line in body_lines:
            c.drawString(x, by, line)
            by -= 9


def track_record_grid(c: Canvas, cx: float, cy: float, width: float):
    """Five-row credibility grid: each row a hairline-separated factoid."""
    rows = [
        ("8 years",     "Building data-sovereignty infrastructure"),
        ("Swarm",       "Foundation co-founders (Ethereum-incubated storage)"),
        ("EU standard", "Co-authors, CWA 17525:2020 (data sovereignty)"),
        ("PLUR live",   "Knowledge-capture layer in production — demo.plur.ai"),
        ("3×",          "MyData Operator Award"),
    ]
    row_h = 11
    total_h = len(rows) * row_h
    y = cy + total_h / 2
    left_w = width * 0.22

    for i, (key, val) in enumerate(rows):
        # Top hairline
        if i > 0:
            hairline(c, y, cx - width / 2, cx + width / 2)
        # Key (gold)
        c.setFont(FONT, 9)
        c.setFillColor(GOLD)
        c.drawString(cx - width / 2 + 4, y - 8, key)
        # Value (charcoal)
        c.setFont(FONT, 8.5)
        c.setFillColor(CHARCOAL_BODY)
        c.drawString(cx - width / 2 + left_w, y - 8, val)
        y -= row_h


def two_track_first_step(c: Canvas, cx: float, cy: float, width: float):
    """Two parallel tracks: Internal | External. Each with timeline + deliverable."""
    gap = 14
    card_w = (width - gap) / 2
    card_h = 50

    tracks = [
        ("INTERNAL TRACK", [
            "2-hour scoping call with chosen entity",
            "Within 2 weeks: ownership policy signed",
            "Pilot starts immediately on signing",
        ]),
        ("EXTERNAL TRACK", [
            "Alignment session with DMCC + DGCX",
            "Plus VARA / ADGM / DIFC review",
            "Within 4 weeks: tokenisation framework agreed",
        ]),
    ]

    for i, (label, lines) in enumerate(tracks):
        x = cx - width / 2 + i * (card_w + gap)
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        c.setFillColor(WHITE)
        c.roundRect(x, cy - card_h / 2, card_w, card_h, 3, fill=0, stroke=1)
        # Label
        small_caps_header(c, label, x + 8, cy + card_h / 2 - 11, 8)
        # Lines
        c.setFont(FONT, 8.5)
        c.setFillColor(CHARCOAL_BODY)
        ty = cy + card_h / 2 - 23
        for line in lines:
            c.setFillColor(GOLD)
            c.circle(x + 11, ty + 2, 1.0, fill=1, stroke=0)
            c.setFillColor(CHARCOAL_BODY)
            c.drawString(x + 16, ty, line)
            ty -= 10.5


# ---------- pages ----------

def render_page_1(c: Canvas, page_w: float, page_h: float, mx: float, cw: float):
    # Header strip
    y = page_h - 14 * mm
    centred_text(c, "DATAFUND  ·  2026", y, 7, MUTED_GREY, page_w)
    centred_text(c, "page 1 of 2", page_h - 19 * mm, 6.5, MUTED_GREY, page_w)

    # Title
    y -= 18 * mm
    centred_text(c, "A Sovereign Data Economy", y, 26, CHARCOAL_DARK, page_w)
    y -= 8.5 * mm
    centred_text(c, "for the UAE", y, 26, CHARCOAL_DARK, page_w)

    # Subtitle — the world-first thesis
    y -= 8 * mm
    centred_text(c,
                 "First-in-the-world. The building blocks are here.",
                 y, 11, MUTED_GREY, page_w)

    # Gold star
    y -= 9 * mm
    eight_pointed_star(c, page_w / 2, y, outer=4.5 * mm, colour=GOLD)

    # Rule
    y -= 6 * mm
    hairline(c, y, mx, page_w - mx)

    # §1 The Opportunity
    y -= 6 * mm
    small_caps_header(c, "The Opportunity", mx, y, 9)
    y -= 7 * mm
    y = paragraph(c,
                  "AI is a multi-trillion-dollar industry running on an unregulated commodity. "
                  "In the UAE — DMCC trade flows, Dubai Municipality datasets, regulated entity records — "
                  "substantial value is generated daily. None of it appears on any balance sheet. "
                  "None is under sovereign control.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=13.5)
    y -= 3 * mm
    y = paragraph(c,
                  "The country that defines the data layer sets the rules of the next century — "
                  "the way the United States defined the dollar, the way London defined insurance. "
                  "The UAE has committed to fifty percent agentic government by 2028; the data layer is the missing piece.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=13.5)

    # Sovereign callout
    y -= 5 * mm
    sovereign_callout(c, page_w / 2, y - 7, cw)
    y -= 14 * mm

    hairline(c, y, mx, page_w - mx)

    # §2 The Proposition
    y -= 6 * mm
    small_caps_header(c, "The Proposition", mx, y, 9)
    y -= 7 * mm
    y = paragraph(c,
                  "Two products on one stack. The same captured knowledge that powers internal government services "
                  "becomes the asset listed on a sovereign marketplace.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=13.5)

    # Two cards
    y -= 4 * mm
    prop_h = 38 * mm
    two_propositions(c, page_w / 2, y - prop_h / 2, cw, prop_h,
                     left_label="Internal · PLUR",
                     left_lines=[
                         "Captures the practice knowledge frontier AI doesn't have",
                         "Every captured engram makes government agents more capable",
                         "Institutional memory survives staff transitions",
                         "The substrate the fifty-percent commitment needs to deliver",
                     ],
                     right_label="External · Dubai Data Exchange",
                     right_lines=[
                         "Sovereign, tokenised, agent-first marketplace",
                         "ERC-3643 compliant security tokens for data assets",
                         "Three-sided market: owners, AI buyers, investors",
                         "Dubai becomes the global data hub — like the gold hub",
                     ])
    y -= prop_h + 3 * mm

    hairline(c, y, mx, page_w - mx)

    # §3 Why Now / Why First
    y -= 6 * mm
    small_caps_header(c, "Why Now  ·  Why First in the World", mx, y, 9)
    y -= 7 * mm
    y = paragraph(c,
                  "The data, AI, crypto, and regulatory building blocks all exist. "
                  "No one has connected them in a way that works. The UAE is the only jurisdiction that can.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=13.5)

    # Four pillars
    y -= 4 * mm
    pillar_h = 56
    four_pillars(c, page_w / 2, y - pillar_h / 2, cw, [
        ("Data", "Personal data stores. Swarm decentralised storage. EU CWA 17525:2020 standard."),
        ("AI", "Production agent runtime. Knowledge layer — PLUR live at demo.plur.ai."),
        ("Crypto", "ERC-3643 security tokens. Regulated tokenisation rails. Base / EVM execution."),
        ("Regulatory", "VARA, ADGM, DIFC — the only trio with the frameworks to host this."),
    ])
    y -= pillar_h + 8

    # Continued marker
    centred_text(c, "Continued on page 2  ·  Pilot · Economics · Track record · First step",
                 18 * mm, 8, MUTED_GREY, page_w)


def render_page_2(c: Canvas, page_w: float, page_h: float, mx: float, cw: float):
    # Header strip
    y = page_h - 14 * mm
    centred_text(c, "DATAFUND  ·  2026", y, 7, MUTED_GREY, page_w)
    centred_text(c, "page 2 of 2", page_h - 19 * mm, 6.5, MUTED_GREY, page_w)

    # Page title
    y -= 14 * mm
    centred_text(c, "From Proposition to Pilot", y, 22, CHARCOAL_DARK, page_w)

    y -= 6 * mm
    centred_text(c,
                 "What the first thirty days, twelve weeks, and twelve months look like.",
                 y, 10.5, MUTED_GREY, page_w)

    # Star
    y -= 8 * mm
    eight_pointed_star(c, page_w / 2, y, outer=4 * mm, colour=GOLD)

    # Rule
    y -= 5 * mm
    hairline(c, y, mx, page_w - mx)

    # §4 The Pilot Plan
    y -= 5 * mm
    small_caps_header(c, "The Pilot Plan", mx, y, 9)
    y -= 6 * mm
    y = paragraph(c,
                  "Two pilots in parallel. Internal (government capture) and external (commodity-trade tokenisation). "
                  "From thirty-day alignment to year-one production.",
                  mx, y, 9.5, CHARCOAL_BODY, cw, line_h=13)

    # Three phase boxes — drawn so top sits below current y, bottom advances cursor
    y -= 4 * mm
    phase_h = 70
    pilot_phases_detailed(c, page_w / 2, y - phase_h / 2, cw)
    y -= phase_h + 10  # clear the box plus padding for next text

    # KPI line
    kpi = "KPIs: capture coverage  ·  agent quality benchmark  ·  first listing  ·  transaction volume  ·  royalty flow"
    centred_text(c, kpi, y, 7.5, MUTED_GREY, page_w)
    y -= 6 * mm

    hairline(c, y, mx, page_w - mx)

    # §5 The Economics — flat 3-column
    y -= 5 * mm
    small_caps_header(c, "The Economics", mx, y, 9)
    y -= 6 * mm
    y = paragraph(c,
                  "A three-sided market. Data becomes a real-world asset class — like gold-backed securities, captured knowledge becomes tradeable equity.",
                  mx, y, 9.5, CHARCOAL_BODY, cw, line_h=13)

    # 3-column row
    y -= 4 * mm
    econ_h = 52
    three_sided_market(c, page_w / 2, y - econ_h / 2, cw, econ_h)
    y -= econ_h + 10

    # Platform-operator line
    op_line = "Datafund operates the platform (5% commission)  ·  SPV is the issuer (management fee)  ·  Host entity holds the asset (royalties)"
    centred_text(c, op_line, y, 8, MUTED_GREY, page_w)
    y -= 6 * mm

    hairline(c, y, mx, page_w - mx)

    # §6 The First Step
    y -= 5 * mm
    small_caps_header(c, "The First Step", mx, y, 9)
    y -= 7 * mm

    track_h = 52
    two_track_first_step(c, page_w / 2, y - track_h / 2, cw)
    y -= track_h + 10

    # Outcome line
    outcome = "Output of the first thirty days: a Sovereign Data Economy Blueprint, decision-ready for the next budget cycle."
    centred_text(c, outcome, y, 9, CHARCOAL_BODY, page_w)
    y -= 8 * mm

    # Small star anchor before footer (visual rhythm with page 1)
    eight_pointed_star(c, page_w / 2, 46 * mm, outer=3 * mm, colour=GOLD)

    # Track-record single-line footer (folded from former §6)
    track = "Datafund — Swarm Foundation co-founders  ·  EU CWA 17525:2020 co-authors  ·  PLUR live at demo.plur.ai  ·  3× MyData Operator Award"
    centred_text(c, track, 36 * mm, 8, MUTED_GREY, page_w)

    # Closing line
    centred_text(c, "Whoever controls the data controls the future of AI.",
                 24 * mm, 13, GOLD, page_w)

    # Contact
    centred_text(c, "gregor@datafund.io  ·  datafund.io",
                 13 * mm, 8.5, MUTED_GREY, page_w)


def render(output_path: str):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_w, page_h = A4
    mx = 18 * mm
    cw = page_w - 2 * mx

    c = Canvas(str(output_path), pagesize=A4)
    c.setTitle("A Sovereign Data Economy for the UAE — Two-Pager — Datafund")

    render_page_1(c, page_w, page_h, mx, cw)
    c.showPage()
    render_page_2(c, page_w, page_h, mx, cw)

    c.save()
    print(f"Rendered: {output_path}")


OUT_DIR = "/Users/gregor/Data/1-datafund/1-tracks/comms/proposals/dubai-twopagers"

if __name__ == "__main__":
    render(f"{OUT_DIR}/2026-05-22-dubai-twopager.pdf")
