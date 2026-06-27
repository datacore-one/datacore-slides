#!/usr/bin/env python3
"""
PLUR entity ONE-PAGER (Dubai) — elegant dark institutional brief.

Design language from the Dubai-blueprint cover: deep midnight navy, warm gold
corner glow, faint Islamic girih tessellation, gold khatam motifs, ivory + gold
+ slate, Baskerville display + Avenir Next body. Priority this revision:
LESS PACKED, MORE PUNCH — lean numeral strip (no boxes), inline sovereignty
line (no pills), no "Measures" lines, upright (readable) hero, an elevated
gold pull-quote, hairline-trailed section labels.

A4 portrait, deterministic ReportLab. Distilled from entities/research/.
Usage: python3 render_entity_onepager.py [entity ...]   (default: dewa)
"""
from __future__ import annotations
import sys
import math
from pathlib import Path
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT_DIR = Path("/Users/gregor/Data/1-datafund/1-tracks/comms/proposals/dubai-twopagers/entities")
DATE = "2026-06-27"

# --- palette --------------------------------------------------------------
NAVY      = HexColor("#090C18")
NAVY_TOP  = HexColor("#0C1124")
NAVY_BOT  = HexColor("#06080F")
IVORY     = HexColor("#EFE9DA")
IVORY_DIM = HexColor("#CFC9BB")
SLATE     = HexColor("#939CB2")
FAINT     = HexColor("#586079")
GOLD      = HexColor("#C9A24A")
GOLD_SOFT = HexColor("#A98F52")
GOLD_GLOW = HexColor("#E8C66A")


# --- fonts (Baskerville display + Avenir Next body) -----------------------
def _reg(name, paths, idx, fallback):
    for p in paths:
        try:
            if Path(p).exists():
                pdfmetrics.registerFont(TTFont(name, p, subfontIndex=idx))
                return name
        except Exception:
            continue
    return fallback


_BASK = ["/System/Library/Fonts/Supplemental/Baskerville.ttc",
         "/System/Library/Fonts/Baskerville.ttc"]
_AVN = ["/System/Library/Fonts/Avenir Next.ttc",
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc"]

SERIF    = _reg("BAS",  _BASK, 0, "Times-Roman")     # Baskerville Regular
SERIF_SB = _reg("BASB", _BASK, 4, "Times-Bold")      # Baskerville SemiBold
SANS     = _reg("AVN",  _AVN,  7, "Helvetica")       # Avenir Next Regular


def sw(t, f, s):
    return pdfmetrics.stringWidth(t, f, s)


def wrap(text, size, max_w, font):
    out, cur = [], []
    for w in text.split():
        cand = " ".join(cur + [w])
        if sw(cand, font, size) <= max_w:
            cur.append(w)
        else:
            if cur:
                out.append(" ".join(cur))
            cur = [w]
    if cur:
        out.append(" ".join(cur))
    return out


def para(c, text, x, y, size, colour, max_w, lh, font):
    c.setFont(font, size)
    c.setFillColor(colour)
    for ln in wrap(text, size, max_w, font):
        c.drawString(x, y, ln)
        y -= lh
    return y


def spaced(c, text, x, y, font, size, colour, cs):
    c.setFont(font, size)
    c.setFillColor(colour)
    cx = x
    for ch in text:
        c.drawString(cx, y, ch)
        cx += sw(ch, font, size) + cs
    return sw(text, font, size) + cs * max(0, len(text) - 1)


def spwidth(text, font, size, cs):
    return sw(text, font, size) + cs * max(0, len(text) - 1)


def right_spaced(c, t, xr, y, font, s, col, cs=0.0):
    spaced(c, t, xr - spwidth(t, font, s, cs), y, font, s, col, cs)


# --- ornament -------------------------------------------------------------
def khatam(c, cx, cy, R, col=GOLD, alpha=0.5, w=0.7, octagon=True):
    c.saveState()
    c.setStrokeColor(col)
    c.setStrokeAlpha(alpha)
    c.setLineWidth(w)
    c.setFillAlpha(0)
    for off in (0.0, math.pi / 4):
        p = c.beginPath()
        for k in range(4):
            a = off + k * math.pi / 2 + math.pi / 8
            (p.moveTo if k == 0 else p.lineTo)(cx + R * math.cos(a), cy + R * math.sin(a))
        p.close()
        c.drawPath(p, stroke=1, fill=0)
    if octagon:
        p = c.beginPath()
        r = R * 0.62
        for k in range(8):
            a = math.pi / 8 + k * math.pi / 4
            (p.moveTo if k == 0 else p.lineTo)(cx + r * math.cos(a), cy + r * math.sin(a))
        p.close()
        c.drawPath(p, stroke=1, fill=0)
    c.restoreState()


def lattice(c, W, H, cell=24 * mm, col=GOLD, alpha=0.024):
    c.saveState()
    r = cell * 0.5
    j = 0
    y = -cell
    while y < H + cell:
        x = -cell + (cell / 2 if j % 2 else 0)
        while x < W + cell:
            khatam(c, x, y, r, col, alpha, 0.3, octagon=False)
            x += cell
        y += cell * 0.86
        j += 1
    c.restoreState()


def glow(c, cx, cy, R, col=GOLD_GLOW):
    c.saveState()
    c.setStrokeAlpha(0)
    c.setFillColor(col)
    for i in range(14, 0, -1):
        c.setFillAlpha(0.013)
        c.circle(cx, cy, R * i / 14, fill=1, stroke=0)
    c.restoreState()


def vgrad(c, W, H, top, bot, steps=64):
    bh = H / steps
    for i in range(steps):
        t = i / (steps - 1)
        c.setFillColor(Color(top.red + (bot.red - top.red) * t,
                             top.green + (bot.green - top.green) * t,
                             top.blue + (bot.blue - top.blue) * t))
        c.rect(0, H - (i + 1) * bh, W, bh + 1, fill=1, stroke=0)


def background(c, W, H):
    vgrad(c, W, H, NAVY_TOP, NAVY_BOT)
    lattice(c, W, H)
    glow(c, W - 2 * mm, H + 6 * mm, 140 * mm)
    # corner-bleeding khatam ornaments — subtle, diagonal balance
    khatam(c, W - 4 * mm, H - 3 * mm, 13 * mm, GOLD, alpha=0.10, w=0.6, octagon=True)
    khatam(c, 3 * mm, 4 * mm, 12 * mm, GOLD, alpha=0.07, w=0.6, octagon=True)


def hrule(c, x0, x1, y, col=GOLD_SOFT, w=0.6, alpha=0.5):
    c.saveState()
    c.setStrokeColor(col)
    c.setStrokeAlpha(alpha)
    c.setLineWidth(w)
    c.line(x0, y, x1, y)
    c.restoreState()


def label(c, text, x, y, xr, size=8.4, cs=1.8, trail=True):
    """Gold caps label with a faint trailing hairline to the right margin."""
    w = spaced(c, text.upper(), x, y, SANS, size, GOLD, cs)
    if trail:
        hrule(c, x + w + 5 * mm, xr, y + 2.4, GOLD_SOFT, 0.5, 0.22)


def statstrip(c, x, y_top, cw, stats):
    n = len(stats)
    col = cw / n
    cap_top = y_top - 13.6 * mm
    lh = 10.5
    maxl = max(len(wrap(lab, 8.6, col - 8 * mm, SANS)) for _, lab in stats)
    for i, (big, lab) in enumerate(stats):
        cx = x + i * col + col / 2
        if i > 0:  # short divider spanning only the numeral row
            c.saveState()
            c.setStrokeColor(GOLD)
            c.setStrokeAlpha(0.26)
            c.setLineWidth(0.6)
            c.line(x + i * col, y_top - 2 * mm, x + i * col, y_top - 11 * mm)
            c.restoreState()
        c.setFont(SERIF, 26)
        c.setFillColor(GOLD)
        c.drawCentredString(cx, y_top - 9 * mm, big)
        c.setFont(SANS, 8.6)
        c.setFillColor(IVORY_DIM)
        ly = cap_top
        for ln in wrap(lab, 8.6, col - 8 * mm, SANS):
            c.drawCentredString(cx, ly, ln)
            ly -= lh
    return cap_top - maxl * lh - 4.5 * mm


def inline_terms(c, terms, x, y, size=9.4):
    cx = x
    for i, t in enumerate(terms):
        if i:
            c.setFont(SANS, size)
            c.setFillColor(GOLD)
            c.drawString(cx, y, "  ·  ")
            cx += sw("  ·  ", SANS, size)
        c.setFont(SANS, size)
        c.setFillColor(IVORY_DIM)
        c.drawString(cx, y, t)
        cx += sw(t, SANS, size)


def pilot(c, x, y_top, w, title, body):
    khatam(c, x + 1.8 * mm, y_top - 1.0 * mm, 1.9 * mm, GOLD, 0.95, 0.7, octagon=False)
    c.setFont(SERIF_SB, 11)
    c.setFillColor(IVORY)
    c.drawString(x + 6 * mm, y_top - 2 * mm, title)
    return para(c, body, x + 6 * mm, y_top - 8 * mm, 9.4, IVORY_DIM, w - 6 * mm, 13.4, SANS)


def callout(c, text, x, y_top, w, size=10.5):
    pad = 5 * mm
    lines = wrap(text, size, w - 2 * pad, SANS)
    lh = size * 1.5
    h = len(lines) * lh + pad * 1.7
    c.setStrokeColor(GOLD)
    c.setStrokeAlpha(0.6)
    c.setLineWidth(1.0)
    c.setFillAlpha(0)
    c.roundRect(x, y_top - h, w, h, 2.2 * mm, stroke=1, fill=0)
    c.setStrokeAlpha(1)
    c.setFillAlpha(1)
    c.setFont(SANS, size)
    c.setFillColor(IVORY)
    cy = y_top - pad - size * 0.5
    for ln in lines:
        c.drawString(x + pad, cy, ln)
        cy -= lh
    return y_top - h


def pullquote(c, text, cx, y_top, cw, size=13.5):
    khatam(c, cx, y_top, 3.0 * mm, GOLD, 0.85, 0.7, octagon=False)
    yy = y_top - 8 * mm
    c.setFont(SERIF, size)
    c.setFillColor(GOLD)
    for ln in wrap(text, size, cw - 26 * mm, SERIF):
        c.drawCentredString(cx, yy, ln)
        yy -= size * 1.42
    return yy


def render(key, e):
    W, H = A4
    mx = 18 * mm
    cw = W - 2 * mx
    xr = W - mx
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf = OUT_DIR / f"{DATE}-{key}-onepager.pdf"
    c = Canvas(str(pdf), pagesize=A4)
    background(c, W, H)

    # ---- masthead -----------------------------------------------------
    y = H - 17 * mm
    spaced(c, e["wordmark"], mx, y, SERIF_SB, 13, GOLD, 3.2)
    right_spaced(c, e["kicker_right"], xr, y, SANS, 8.4, SLATE, 1.7)
    y -= 5 * mm
    spaced(c, e["brief_for"].upper(), mx, y, SANS, 7.6, SLATE, 1.3)
    y -= 4 * mm
    hrule(c, mx, xr, y)

    # ---- title --------------------------------------------------------
    y -= 11.5 * mm
    c.setFillColor(IVORY)
    c.setFont(SERIF, 25)
    for ln in e["title"]:
        c.drawString(mx, y, ln)
        y -= 25
    # ---- thesis (upright Baskerville, ivory — readable) ---------------
    y -= 6.5 * mm
    y = para(c, e["hero"], mx, y, 11.5, IVORY, cw, 16, SERIF)

    # ---- stat strip ---------------------------------------------------
    y -= 8 * mm
    y = statstrip(c, mx, y, cw, e["stats"])

    # ---- memory layer -------------------------------------------------
    y -= 7 * mm
    label(c, e["gap_label"], mx, y, xr)
    y -= 6 * mm
    y = para(c, e["gap"], mx, y, 9.8, IVORY_DIM, cw, 14, SANS)

    # ---- sovereign by architecture (inline) — sits with the layer -----
    y -= 7.5 * mm
    label(c, e["arch_label"], mx, y, xr)
    y -= 6 * mm
    inline_terms(c, e["arch_terms"], mx, y)

    # ---- pilots -------------------------------------------------------
    y -= 9.5 * mm
    label(c, e["pilots_label"], mx, y, xr)
    y -= 7 * mm
    pgap = 8 * mm
    pw = (cw - pgap) / 2
    yb0 = pilot(c, mx, y, pw, e["pilots"][0][0], e["pilots"][0][1])
    yb1 = pilot(c, mx + pw + pgap, y, pw, e["pilots"][1][0], e["pilots"][1][1])
    y = min(yb0, yb1)

    # ---- horizon ------------------------------------------------------
    y -= 9.5 * mm
    label(c, e["horizon_label"], mx, y, xr)
    y -= 6 * mm
    y = para(c, e["horizon"], mx, y, 9.6, SLATE, cw, 13.6, SANS)

    # ---- pull-quote ("more intelligence per watt") --------------------
    y -= 10 * mm
    y = pullquote(c, e["kicker"], W / 2, y, cw)

    # ---- CTA ----------------------------------------------------------
    y -= 11 * mm
    c.setFont(SERIF, 19)
    c.setFillColor(IVORY)
    c.drawString(mx, y, e["cta"])

    # ---- footer -------------------------------------------------------
    fy = 21 * mm
    hrule(c, mx, xr, fy)
    c.setFont(SERIF_SB, 9)
    c.setFillColor(IVORY)
    c.drawString(mx, fy - 6 * mm, e["contact_name"])
    right_spaced(c, e["contact_reach"], xr, fy - 6 * mm, SANS, 8.6, GOLD, 0.2)
    c.setFont(SANS, 6.6)
    c.setFillColor(FAINT)
    c.drawString(mx, fy - 11.5 * mm, e["ribbon"])

    c.showPage()
    c.save()
    print(f"  -> {pdf.name}")


# ===========================================================================
CONTENT = {
 "dewa": {
  "wordmark": "PLUR",
  "kicker_right": "PILOT PROPOSAL",
  "brief_for": "Institutional Brief  ·  for Dubai Electricity & Water Authority",
  "title": ["Institutional Memory for the", "World's First AI-Native Utility"],
  "hero": ("DEWA already runs the world's first AI-native utility. The next sovereign "
           "frontier isn't more AI — it's owning the institutional memory that AI produces. "
           "Days after the UAE made government data a national asset under a new federal AI & "
           "Data Authority, DEWA can be the flagship: every grid decision and Virtual-Engineer "
           "judgement captured and compounding on its own sovereign infrastructure — not "
           "rented back from a foreign cloud."),
  "stats": [
    ("World #1", "AI-native utility"),
    ("50%", "of government to agentic AI, two years"),
    ("13M+", "AI answers already given by Rammas"),
  ],
  "gap_label": "The Memory Layer",
  "gap": ("PLUR is the sovereign memory layer beneath the models, not another model. It captures DEWA's own "
          "rules, decisions and judgement and feeds them back to any AI agent — Claude, "
          "ChatGPT, Copilot, or DEWA's own — on the infrastructure DEWA already runs: Moro "
          "Hub and Rafay."),
  "pilots_label": "Two Pilots to Start",
  "pilots": [
    ("AI Virtual Engineer — a memory spine",
     "A root-cause fix found on one asset on Sunday is surfaced on a similar asset on Monday — no manual sharing, nothing leaving DEWA."),
    ("Rammas — remember every answer",
     "Rammas has answered 13M+ enquiries. Capture that judgement once, and every division inherits it — instead of re-deriving the same answers."),
  ],
  "arch_label": "Sovereign by Architecture",
  "arch_terms": ["Local", "Air-gapped", "Open-source", "No exfiltration", "No lock-in"],
  "horizon_label": "Horizon",
  "horizon": ("DEWA's institutional memory stays DEWA's. Built into the energy and water "
              "verticals, it becomes something Dubai can take to utilities worldwide — first "
              "mover, on DEWA's terms. Data as an asset, owned where it is earned."),
  "kicker": "An agent that remembers doesn't recompute what DEWA already knows — more intelligence per watt.",
  "timeline": ("Start small: one read-only pilot beside live systems. A first result in weeks, "
               "not quarters — then judgement compounds across DEWA."),
  "cta": "Let's Dubai it.",
  "contact_name": "Hind Abdallah Belhab Alameri  ·  Board Member, PLUR",
  "contact_reach": "+971 50 888 6767   ·   H.belhabb@hotmail.com   ·   plur.ai",
  "ribbon": "8 YRS SOVEREIGN DATA   ·   3× MYDATA OPERATOR AWARD   ·   CEN/CENELEC CWA 17525:2020   ·   SWARM FOUNDATION   ·   FAIR DATA SOCIETY",
 },
}

if __name__ == "__main__":
    keys = sys.argv[1:] or ["dewa"]
    for k in keys:
        if k in CONTENT:
            print(f"[{k}]")
            render(k, CONTENT[k])
        else:
            print(f"  ! unknown entity: {k}")
    print("Done.")
