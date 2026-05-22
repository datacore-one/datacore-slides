#!/usr/bin/env python3
"""
Render Dubai-blueprint infographic one-pagers (MBZ + General Director variants).

Visual one-pager with diagrams, comparison charts, and Arabic-inspired
geometric motifs. Deterministic — exact text fidelity, guaranteed layout.

Outputs two A4 portrait PDFs.
"""

from __future__ import annotations

import math
from pathlib import Path

from reportlab.lib.colors import HexColor, Color
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
GOLD_PALE = HexColor("#F2E6C7")  # soft gold tint for fills
INDIGO = HexColor("#0D0A1F")
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
    """Section header in gold small-caps with letter-spacing."""
    c.saveState()
    c.setFillColor(GOLD)
    c.setFont(FONT, size)
    # ReportLab doesn't have native letter-spacing; approximate by drawing chars
    spacing = size * 0.25
    cx = x
    for ch in text.upper():
        c.drawString(cx, y, ch)
        cx += c.stringWidth(ch, FONT, size) + spacing
    c.restoreState()


# ---------- visual elements ----------

def asset_comparison_bars(c: Canvas, cx: float, cy: float, width: float, height: float):
    """Three vertical bars comparing Gold / Oil / Data with values."""
    bar_w = width / 5
    gap = (width - 3 * bar_w) / 4
    max_value = 13.0  # $13T gold is the tallest
    values = [
        ("GOLD",   "$13T",   13.0, MUTED_GREY,    "on balance sheet"),
        ("OIL",    "$2T",     2.0, MUTED_GREY,    "on balance sheet"),
        ("DATA",   "$1.3T",   1.3, GOLD,          "off balance sheet"),
    ]
    x = cx - width / 2 + gap
    bar_zone_h = height * 0.65
    label_zone_h = height * 0.35

    for i, (name, value_label, value, colour, footnote) in enumerate(values):
        bar_h = bar_zone_h * (value / max_value)
        bar_x = x + i * (bar_w + gap)
        bar_y = cy - height / 2 + label_zone_h

        if colour == GOLD:
            # Highlighted bar (DATA) — filled gold
            c.setFillColor(GOLD)
            c.setStrokeColor(GOLD)
            c.rect(bar_x, bar_y, bar_w, bar_h, fill=1, stroke=0)
        else:
            # Muted hairline bars
            c.setFillColor(WHITE)
            c.setStrokeColor(MUTED_GREY)
            c.setLineWidth(0.7)
            c.rect(bar_x, bar_y, bar_w, bar_h, fill=0, stroke=1)

        # Value label above bar
        c.setFont(FONT, 11)
        c.setFillColor(colour)
        val_w = c.stringWidth(value_label, FONT, 11)
        c.drawString(bar_x + (bar_w - val_w) / 2, bar_y + bar_h + 4, value_label)

        # Name below bar
        c.setFont(FONT, 9.5)
        c.setFillColor(CHARCOAL_DARK)
        name_w = c.stringWidth(name, FONT, 9.5)
        c.drawString(bar_x + (bar_w - name_w) / 2, bar_y - 12, name)

        # Footnote below name
        c.setFont(FONT, 7.5)
        c.setFillColor(MUTED_GREY if colour != GOLD else GOLD)
        foot_w = c.stringWidth(footnote, FONT, 7.5)
        c.drawString(bar_x + (bar_w - foot_w) / 2, bar_y - 24, footnote)


def three_sided_triangle(c: Canvas, cx: float, cy: float, size: float):
    """Equilateral triangle with DATA OWNER / AI BUYER / INVESTOR at corners + central label."""
    # Vertices: top, bottom-left, bottom-right
    top = (cx, cy + size * 0.55)
    bl = (cx - size * 0.55, cy - size * 0.35)
    br = (cx + size * 0.55, cy - size * 0.35)

    c.saveState()
    c.setStrokeColor(CHARCOAL_BODY)
    c.setLineWidth(0.8)
    # Triangle outline
    c.line(top[0], top[1], bl[0], bl[1])
    c.line(bl[0], bl[1], br[0], br[1])
    c.line(br[0], br[1], top[0], top[1])

    # Centre label
    c.setFont(FONT, 7.5)
    c.setFillColor(MUTED_GREY)
    centre_label = "TOKENISED DATA BUSINESS"
    cw = c.stringWidth(centre_label, FONT, 7.5)
    c.drawString(cx - cw / 2, cy - 3, centre_label)

    # Corner labels in gold small-caps
    corner_size = 9
    c.setFillColor(GOLD)
    c.setFont(FONT, corner_size)
    for label, pos, offset in [
        ("DATA OWNER", top, (0, 6)),
        ("AI BUYER",   bl,  (-6, -10)),
        ("INVESTOR",   br,  (6, -10)),
    ]:
        w = c.stringWidth(label, FONT, corner_size)
        if "OWNER" in label:
            c.drawString(pos[0] - w / 2, pos[1] + offset[1], label)
        elif "BUYER" in label:
            c.drawString(pos[0] - w - 2, pos[1] + offset[1], label)
        else:
            c.drawString(pos[0] + 2, pos[1] + offset[1], label)
    c.restoreState()


def three_step_flow(c: Canvas, cx: float, cy: float, width: float,
                    steps: list[tuple[str, str]]):
    """Horizontal flow of N labeled boxes connected by gold arrows.
    steps: list of (top_label, bottom_label) tuples."""
    n = len(steps)
    box_w = (width - (n - 1) * 14) / n
    box_h = 36
    box_y = cy - box_h / 2

    for i, (top_label, bottom_label) in enumerate(steps):
        box_x = cx - width / 2 + i * (box_w + 14)
        # Box
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.9)
        c.setFillColor(WHITE)
        c.roundRect(box_x, box_y, box_w, box_h, 3, fill=0, stroke=1)
        # Top label (gold small-caps)
        c.setFont(FONT, 7.5)
        c.setFillColor(GOLD)
        tw = c.stringWidth(top_label.upper(), FONT, 7.5)
        c.drawString(box_x + (box_w - tw) / 2, box_y + box_h - 13, top_label.upper())
        # Bottom label (charcoal)
        c.setFont(FONT, 9)
        c.setFillColor(CHARCOAL_DARK)
        bw = c.stringWidth(bottom_label, FONT, 9)
        c.drawString(box_x + (box_w - bw) / 2, box_y + 10, bottom_label)

        # Arrow between boxes
        if i < n - 1:
            arrow_x = box_x + box_w + 2
            arrow_end = box_x + box_w + 12
            c.setStrokeColor(GOLD)
            c.setLineWidth(0.9)
            c.line(arrow_x, cy, arrow_end - 3, cy)
            # arrowhead
            c.line(arrow_end - 3, cy, arrow_end - 6, cy + 3)
            c.line(arrow_end - 3, cy, arrow_end - 6, cy - 3)


def pilot_phases_timeline(c: Canvas, cx: float, cy: float, width: float):
    """Three-phase timeline: Phase 0 (2w) / Phase 1 (12w) / Phase 2 (12mo)."""
    phases = [
        ("PHASE 0", "Property right workshop", "2 weeks"),
        ("PHASE 1", "PLUR knowledge capture",   "12 weeks"),
        ("PHASE 2", "Data products generating revenues", "12 months"),
    ]
    n = len(phases)
    box_w = (width - (n - 1) * 14) / n
    box_h = 56
    box_y = cy - box_h / 2

    for i, (label, body, duration) in enumerate(phases):
        box_x = cx - width / 2 + i * (box_w + 14)
        c.setStrokeColor(GOLD if i == 0 else CHARCOAL_BODY)
        c.setLineWidth(0.9)
        c.setFillColor(GOLD_PALE if i == 0 else WHITE)
        c.roundRect(box_x, box_y, box_w, box_h, 3, fill=1 if i == 0 else 0, stroke=1)

        # Phase label (gold small-caps)
        c.setFont(FONT, 7.5)
        c.setFillColor(GOLD)
        lw = c.stringWidth(label, FONT, 7.5)
        c.drawString(box_x + (box_w - lw) / 2, box_y + box_h - 13, label)

        # Body text wrapped
        c.setFont(FONT, 8.5)
        c.setFillColor(CHARCOAL_DARK)
        body_lines = wrap(body, 8.5, box_w - 12)
        ty = box_y + box_h - 26
        for line in body_lines:
            tw = c.stringWidth(line, FONT, 8.5)
            c.drawString(box_x + (box_w - tw) / 2, ty, line)
            ty -= 11

        # Duration in muted-grey at bottom
        c.setFont(FONT, 7.5)
        c.setFillColor(MUTED_GREY)
        dw = c.stringWidth(duration, FONT, 7.5)
        c.drawString(box_x + (box_w - dw) / 2, box_y + 7, duration)

        # Arrow to next phase
        if i < n - 1:
            arrow_x = box_x + box_w + 2
            arrow_end = box_x + box_w + 12
            c.setStrokeColor(GOLD)
            c.setLineWidth(0.9)
            c.line(arrow_x, cy, arrow_end - 3, cy)
            c.line(arrow_end - 3, cy, arrow_end - 6, cy + 3)
            c.line(arrow_end - 3, cy, arrow_end - 6, cy - 3)


def sovereign_callout(c: Canvas, cx: float, cy: float, width: float, height: float = 14):
    """Horizontal callout strip: self-sovereign architecture promise.

    Subtle gold hairline outline + pale gold fill + centred message + flanking stars.
    """
    box_x = cx - width / 2
    box_y = cy - height / 2

    c.saveState()
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.7)
    c.setFillColor(GOLD_PALE)
    c.roundRect(box_x, box_y, width, height, 2, fill=1, stroke=1)

    # Flanking stars
    star_inset = 12
    eight_pointed_star(c, box_x + star_inset, cy, outer=4, colour=GOLD, stroke_w=0.6)
    eight_pointed_star(c, box_x + width - star_inset, cy, outer=4, colour=GOLD, stroke_w=0.6)

    # Centred message
    msg = "Self-sovereign architecture  ·  Local-first & Private  ·  Regulatory compliant"
    c.setFont(FONT, 8.5)
    c.setFillColor(CHARCOAL_DARK)
    mw = c.stringWidth(msg, FONT, 8.5)
    c.drawString(cx - mw / 2, cy - 2.5, msg)
    c.restoreState()


def two_propositions(c: Canvas, cx: float, cy: float, width: float, height: float,
                     left_label: str, left_body: str,
                     right_label: str, right_body: str):
    """Two side-by-side cards for the dual proposition (internal/external)."""
    gap = 10
    box_w = (width - gap) / 2
    box_h = height
    box_y = cy - box_h / 2
    left_x = cx - width / 2
    right_x = cx + gap / 2

    for x, label, body, accent in [
        (left_x, left_label, left_body, GOLD),
        (right_x, right_label, right_body, GOLD),
    ]:
        c.setStrokeColor(accent)
        c.setLineWidth(0.9)
        c.setFillColor(WHITE)
        c.roundRect(x, box_y, box_w, box_h, 3, fill=0, stroke=1)

        # Label band — small-caps gold at top of card
        c.setFont(FONT, 8)
        c.setFillColor(GOLD)
        spacing = 8 * 0.25
        lx = x + 12
        ly = box_y + box_h - 14
        for ch in label.upper():
            c.drawString(lx, ly, ch)
            lx += c.stringWidth(ch, FONT, 8) + spacing

        # Body text
        body_size = 9
        body_lh = body_size * 1.4
        c.setFont(FONT, body_size)
        c.setFillColor(CHARCOAL_BODY)
        body_y = ly - 16
        for line in wrap(body, body_size, box_w - 24):
            c.drawString(x + 12, body_y, line)
            body_y -= body_lh


def two_pilots_to_rollout(c: Canvas, cx: float, cy: float, width: float,
                          pilot1_top: str, pilot1_name: str, pilot1_outcome: str,
                          pilot2_top: str, pilot2_name: str, pilot2_outcome: str,
                          rollout_label: str):
    """Two pilot cards side-by-side, both with arrows down to a national-rollout band.
    Total diagram height ~36mm (tightened from original 42mm by closing pilots-to-rollout gap)."""
    gap = 14
    pilot_w = (width - gap) / 2
    pilot_h = 56  # unchanged — inside-box text needs this height
    pilot_y = cy + 12  # was cy + 22 — pulled closer to cy to close gap to rollout

    for x_offset, top, name, outcome in [
        (-pilot_w / 2 - gap / 2, pilot1_top, pilot1_name, pilot1_outcome),
        (pilot_w / 2 + gap / 2, pilot2_top, pilot2_name, pilot2_outcome),
    ]:
        x = cx + x_offset - pilot_w / 2
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.9)
        c.setFillColor(GOLD_PALE)
        c.roundRect(x, pilot_y, pilot_w, pilot_h, 3, fill=1, stroke=1)
        # Top label gold small-caps
        c.setFont(FONT, 7.5)
        c.setFillColor(GOLD)
        tw = c.stringWidth(top.upper(), FONT, 7.5)
        c.drawString(x + (pilot_w - tw) / 2, pilot_y + pilot_h - 12, top.upper())
        # Pilot name
        c.setFont(FONT, 10.5)
        c.setFillColor(CHARCOAL_DARK)
        nw = c.stringWidth(name, FONT, 10.5)
        c.drawString(x + (pilot_w - nw) / 2, pilot_y + pilot_h - 28, name)
        # Outcome — wrapped
        c.setFont(FONT, 8)
        c.setFillColor(CHARCOAL_BODY)
        outcome_lines = wrap(outcome, 8, pilot_w - 14)
        oy = pilot_y + pilot_h - 42
        for line in outcome_lines:
            lw = c.stringWidth(line, FONT, 8)
            c.drawString(x + (pilot_w - lw) / 2, oy, line)
            oy -= 10

    # Arrows down from each pilot to rollout band
    rollout_y_top = cy - 8  # was cy - 14 — pulled closer to cy
    rollout_h = 22  # was 26 — slightly reduced
    rollout_y = rollout_y_top - rollout_h
    for x_offset in [-pilot_w / 2 - gap / 2, pilot_w / 2 + gap / 2]:
        arrow_x = cx + x_offset
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.9)
        c.line(arrow_x, pilot_y - 2, arrow_x, rollout_y_top + 4)
        c.line(arrow_x, rollout_y_top + 4, arrow_x - 3, rollout_y_top + 7)
        c.line(arrow_x, rollout_y_top + 4, arrow_x + 3, rollout_y_top + 7)

    # National rollout band
    rollout_w = width
    rollout_x = cx - rollout_w / 2
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.0)
    c.setFillColor(WHITE)
    c.roundRect(rollout_x, rollout_y, rollout_w, rollout_h, 3, fill=0, stroke=1)
    c.setFont(FONT, 9.5)
    c.setFillColor(CHARCOAL_DARK)
    lw = c.stringWidth(rollout_label, FONT, 9.5)
    c.drawString(rollout_x + (rollout_w - lw) / 2, rollout_y + rollout_h / 2 - 3, rollout_label)


def pipeline_diagram(c: Canvas, cx: float, cy: float, width: float):
    """Horizontal pipeline: KNOWLEDGE → DATA PRODUCT → TOKENISED ASSET → EXCHANGE."""
    nodes = ["KNOWLEDGE", "DATA PRODUCT", "TOKENISED ASSET", "EXCHANGE"]
    n = len(nodes)
    node_size = 22
    gap = (width - n * node_size) / (n - 1)
    y = cy

    for i, label in enumerate(nodes):
        node_x = cx - width / 2 + i * (node_size + gap) + node_size / 2

        # Node — different shape per position to suggest refinement
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.0)
        if i == n - 1:
            # Final node = filled gold orb (EXCHANGE)
            c.setFillColor(GOLD)
            c.circle(node_x, y, node_size / 2, fill=1, stroke=0)
        else:
            c.setFillColor(WHITE)
            if i == 0:
                c.circle(node_x, y, node_size / 2, fill=1, stroke=1)
            elif i == 1:
                c.rect(node_x - node_size / 2, y - node_size / 2, node_size, node_size,
                       fill=1, stroke=1)
            else:
                # Hexagon
                pts = []
                for k in range(6):
                    a = math.pi / 6 + k * math.pi / 3
                    pts.append((node_x + (node_size / 2) * math.cos(a),
                                y + (node_size / 2) * math.sin(a)))
                path = c.beginPath()
                path.moveTo(*pts[0])
                for p in pts[1:]:
                    path.lineTo(*p)
                path.close()
                c.drawPath(path, fill=1, stroke=1)

        # Label below node
        c.setFont(FONT, 7)
        c.setFillColor(GOLD if i == n - 1 else CHARCOAL_DARK)
        lw = c.stringWidth(label, FONT, 7)
        c.drawString(node_x - lw / 2, y - node_size / 2 - 11, label)

        # Arrow to next
        if i < n - 1:
            arrow_start = node_x + node_size / 2 + 2
            arrow_end = node_x + node_size + gap - node_size / 2 - 2
            c.setStrokeColor(GOLD)
            c.setLineWidth(0.9)
            c.line(arrow_start, y, arrow_end - 3, y)
            c.line(arrow_end - 3, y, arrow_end - 6, y + 3)
            c.line(arrow_end - 3, y, arrow_end - 6, y - 3)


# ---------- page templates ----------

def render_mbz(output_path: str):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_w, page_h = A4
    mx = 18 * mm
    cw = page_w - 2 * mx

    c = Canvas(str(output_path), pagesize=A4)
    c.setTitle("A Sovereign Data Economy for the UAE — Datafund")

    # Header strip
    y = page_h - 14 * mm
    centred_text(c, "DATAFUND  ·  2026", y, 7, MUTED_GREY, page_w)

    # Title
    y -= 16 * mm
    centred_text(c, "A Sovereign Data Economy", y, 28, CHARCOAL_DARK, page_w)
    y -= 9 * mm
    centred_text(c, "for the UAE", y, 28, CHARCOAL_DARK, page_w)

    # Subtitle
    y -= 9 * mm
    centred_text(c, "Building on the commitment to fifty percent agentic government by 2028.",
                 y, 10.5, MUTED_GREY, page_w)

    # Gold star anchor
    y -= 10 * mm
    eight_pointed_star(c, page_w / 2, y, outer=4.5 * mm, colour=GOLD)

    # Rule
    y -= 6 * mm
    hairline(c, y, mx, page_w - mx)

    # Section 1: The Opportunity (text-only — bar chart removed)
    y -= 6 * mm
    small_caps_header(c, "The Opportunity", mx, y, 9)
    y -= 7 * mm
    y = paragraph(c,
                  "AI is a multi-trillion-dollar industry running on an unregulated commodity. "
                  "In the UAE — DMCC trade flows, Dubai Municipality datasets, regulated entity records — substantial value is generated daily. "
                  "None of it appears on any balance sheet. None is under sovereign control.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=14)
    y -= 3 * mm
    y = paragraph(c,
                  "The country that defines the data layer sets the rules of the next century — "
                  "the way the United States defined the dollar, the way London defined insurance.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=14)

    # Self-sovereign callout
    y -= 5 * mm
    sovereign_callout(c, page_w / 2, y - 7, cw)
    y -= 14 * mm

    hairline(c, y, mx, page_w - mx)

    # Section 2: The Proposition (two-fold)
    y -= 6 * mm
    small_caps_header(c, "The Proposition", mx, y, 9)
    y -= 7 * mm
    y = paragraph(c,
                  "Two-fold: a substrate for the federal AI commitment, and a new financial vertical that makes Dubai the global data hub.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=14)

    # Two side-by-side proposition cards
    y -= 3 * mm
    prop_h = 38 * mm
    two_propositions(c, page_w / 2, y - prop_h / 2, cw, prop_h,
                     left_label="Internal · Government",
                     left_body="PLUR captures the practice knowledge frontier AI does not have. Every captured engram makes government agents more capable. Institutional memory survives transitions. The substrate the fifty-percent commitment needs to actually deliver.",
                     right_label="External · Market",
                     right_body="The Dubai Data Exchange — a sovereign, tokenised, agent-first marketplace — turns those captured assets into a new financial vertical. Dubai becomes the global data hub the way it became the global gold hub. DDE is the linchpin.")
    y -= prop_h + 3 * mm

    hairline(c, y, mx, page_w - mx)

    # Section 3: The First Step (two pilots → national rollout)
    y -= 6 * mm
    small_caps_header(c, "The First Step", mx, y, 9)
    y -= 7 * mm
    y = paragraph(c,
                  "Two pilot projects, one of each kind. From their results, a national rollout plan.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=14)

    # Two pilots + arrow to rollout
    # Diagram extends 68pt above cy to 30pt below cy → total ~98pt = ~35mm tall.
    # Place diagram top ~2pt below current y cursor: cy ≈ y - 25mm.
    y -= 4 * mm
    two_pilots_to_rollout(c, page_w / 2, y - 25 * mm, cw,
                          pilot1_top="Internal",
                          pilot1_name="Dubai Municipality",
                          pilot1_outcome="Captured municipal practice powers agentic services to citizens.",
                          pilot2_top="External",
                          pilot2_name="DMCC  ·  DGCX",
                          pilot2_outcome="Tokenised commodity trade data feeds the first DDE listings.",
                          rollout_label="National Rollout Plan")
    y -= 48 * mm

    # One-line credibility footer — kept short so it never collides with the closing line
    y = paragraph(c,
                  "Datafund — Swarm Foundation co-founders  ·  EU CWA 17525:2020 co-authors  ·  PLUR live at demo.plur.ai",
                  mx, y, 8.5, MUTED_GREY, cw, line_h=12)

    # Closing line — spaced clearly from credibility footer
    y = 28 * mm
    centred_text(c, "Whoever controls the data controls the future of AI.",
                 y, 13, GOLD, page_w)

    # Contact
    centred_text(c, "gregor@datafund.io  ·  datafund.io",
                 13 * mm, 8.5, MUTED_GREY, page_w)

    c.showPage()
    c.save()
    print(f"Rendered: {output_path}")


def render_gd(output_path: str):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_w, page_h = A4
    mx = 18 * mm
    cw = page_w - 2 * mx

    c = Canvas(str(output_path), pagesize=A4)
    c.setTitle("From Knowledge to Tokenised Data Asset — Datafund")

    # Header strip
    y = page_h - 14 * mm
    centred_text(c, "DATAFUND  ·  2026", y, 7, MUTED_GREY, page_w)

    # Title
    y -= 16 * mm
    centred_text(c, "From Knowledge to", y, 26, CHARCOAL_DARK, page_w)
    y -= 9 * mm
    centred_text(c, "Tokenised Data Asset", y, 26, CHARCOAL_DARK, page_w)

    # Subtitle
    y -= 9 * mm
    centred_text(c, "In twelve weeks. Pilot deployment for your organisation.",
                 y, 11, MUTED_GREY, page_w)

    # Gold star anchor
    y -= 10 * mm
    eight_pointed_star(c, page_w / 2, y, outer=4.5 * mm, colour=GOLD)

    # Rule
    y -= 6 * mm
    hairline(c, y, mx, page_w - mx)

    # Section 1: The Opportunity (with lead-in context)
    y -= 7 * mm
    small_caps_header(c, "The Opportunity", mx, y, 9)
    y -= 9 * mm

    y = paragraph(c,
                  "The UAE has committed to fifty percent agentic government by 2028 — "
                  "and to building the global hub for the data economy that powers it. "
                  "Every public organisation has a role: capture the data and knowledge that make agentic AI actually useful.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=14)
    y -= 4 * mm

    y = paragraph(c,
                  "Your organisation holds two assets that today appear nowhere on the balance sheet: "
                  "the data that flows through your operations, and the knowledge in your senior people's heads. "
                  "Both are leaking — into foreign AI tools, into staff transitions, into every quarter that passes without capture.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=14)

    # Self-sovereign callout
    y -= 5 * mm
    sovereign_callout(c, page_w / 2, y - 7, cw)
    y -= 15 * mm

    # Pipeline diagram — what the captured knowledge BECOMES
    y -= 2 * mm
    pipeline_diagram(c, page_w / 2, y - 10, cw * 0.85)
    y -= 22 * mm

    # Section 2: The Proposition (with timeline)
    hairline(c, y, mx, page_w - mx)
    y -= 8 * mm
    small_caps_header(c, "The Proposition", mx, y, 9)
    y -= 10 * mm
    y = paragraph(c,
                  "A twelve-week pilot to capture your organisation's first data product — "
                  "the knowledge no frontier AI has, attributed and owned by you.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=14)

    # Three-phase timeline
    y -= 6 * mm
    pilot_phases_timeline(c, page_w / 2, y - 12 * mm, cw * 0.95)
    y -= 30 * mm

    # Section 3: The First Step
    hairline(c, y, mx, page_w - mx)
    y -= 8 * mm
    small_caps_header(c, "The First Step", mx, y, 9)
    y -= 10 * mm

    y = paragraph(c,
                  "A scoping call to identify the highest-value workflow. "
                  "From the ownership policy, the pilot rhythm begins.",
                  mx, y, 10, CHARCOAL_BODY, cw, line_h=14)

    y -= 4 * mm
    y = paragraph(c,
                  "Datafund: PLUR Enterprise — knowledge capture layer in production today. "
                  "Live demos at demo.plur.ai. Swarm Foundation co-founders. Co-authors of the EU data-sovereignty standard. Three-time MyData Operator Award.",
                  mx, y, 9, MUTED_GREY, cw, line_h=12.5)

    # Closing line — matched to MBZ footer rhythm
    y = 28 * mm
    centred_text(c, "Models are commodities. Knowledge isn't.",
                 y, 13, GOLD, page_w)

    # Contact
    centred_text(c, "gregor@datafund.io  ·  datafund.io",
                 13 * mm, 8.5, MUTED_GREY, page_w)

    c.showPage()
    c.save()
    print(f"Rendered: {output_path}")


if __name__ == "__main__":
    OUT_DIR = "/Users/gregor/Data/1-datafund/1-tracks/comms/proposals/dubai-onepagers"
    render_mbz(f"{OUT_DIR}/2026-05-22-mbz-onepager.pdf")
    render_gd(f"{OUT_DIR}/2026-05-22-general-director-onepager.pdf")
    print("DONE")
