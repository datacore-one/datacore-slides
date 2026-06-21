#!/usr/bin/env python3
"""
Readable edition of the Dubai entity PLUR two-pagers.

Design priority: ONE idea that lands in 30 seconds. Large type, generous
whitespace, few words. Distilled from the research/auditor output (which lives
in the dossiers) — NOT the dense prose itself.

A4 portrait, deterministic ReportLab.
Usage: python3 render_dubai_twopager_readable.py [entity ...]
"""
from __future__ import annotations
import sys
import math
from pathlib import Path
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT_DIR = Path("/Users/gregor/Data/1-datafund/1-tracks/comms/proposals/dubai-twopagers/entities")
DATE = "2026-06-21"

WHITE = HexColor("#FFFFFF")
DARK = HexColor("#1A1A1A")
BODY = HexColor("#333333")
MID = HexColor("#555555")
GREY = HexColor("#8A8A8A")
PALE = HexColor("#E6E6E6")
BLUE = HexColor("#0066FF")
BLUE_PALE = HexColor("#EAF1FE")
PEACH = HexColor("#FFCAA8")
LAV = HexColor("#C9B8E8")


def register_font():
    reg = "Helvetica"; bold = "Helvetica-Bold"
    try:
        for fam, path in [("HN", "/System/Library/Fonts/HelveticaNeue.ttc")]:
            if Path(path).exists():
                pdfmetrics.registerFont(TTFont("HN", path))
                reg = "HN"
        # Bold face
        for p in ["/System/Library/Fonts/Supplemental/Helvetica.ttc"]:
            pass
    except Exception:
        pass
    return reg


FONT = register_font()
# Helvetica-Bold is always available as a base-14 font
BOLD = "Helvetica-Bold"


def sw(t, f, s):
    return pdfmetrics.stringWidth(t, f, s)


def wrap(text, size, max_w, font=None):
    font = font or FONT
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


def para(c, text, x, y, size, colour, max_w, lh, font=None):
    font = font or FONT
    c.setFont(font, size); c.setFillColor(colour)
    for ln in wrap(text, size, max_w, font):
        c.drawString(x, y, ln); y -= lh
    return y


def rule(c, y, x0, x1, colour=PALE, w=0.6):
    c.setStrokeColor(colour); c.setLineWidth(w); c.line(x0, y, x1, y)


def left(c, t, x, y, s, col, font=None):
    c.setFont(font or FONT, s); c.setFillColor(col); c.drawString(x, y, t)


def right(c, t, xr, y, s, col, font=None):
    c.setFont(font or FONT, s); c.setFillColor(col); c.drawString(xr - sw(t, font or FONT, s), y, t)


def orbs(c, W, H):
    c.saveState(); c.setStrokeAlpha(0)
    for cx, cy, r, col in [(W - 6*mm, H - 12*mm, 26*mm, PEACH), (6*mm, 24*mm, 24*mm, LAV)]:
        c.setFillColor(col)
        for i in range(8, 0, -1):
            c.setFillAlpha(0.018)
            c.circle(cx, cy, r*i/8, fill=1, stroke=0)
    c.restoreState()


def marker(c, x, y, text_size, col=BLUE, d=5.0):
    """A square bullet vertically centred on the cap-height of text at baseline y."""
    c.setFillColor(col); c.setStrokeAlpha(0)
    c.rect(x, y + text_size * 0.36 - d / 2, d, d, fill=1, stroke=0)


def bullets(c, items, x, y, max_w, lead_size=12, body_size=11, gap=8.5*mm, lh=15):
    """Problem bullets: bold lead on its own line, grey body indented beneath."""
    tx = x + 14
    for lead, body in items:
        marker(c, x, y, lead_size)
        c.setFont(BOLD, lead_size); c.setFillColor(DARK); c.drawString(tx, y, lead)
        y -= lh
        c.setFont(FONT, body_size); c.setFillColor(MID)
        for ln in wrap(body, body_size, max_w - 14):
            c.drawString(tx, y, ln); y -= lh
        y -= (gap - lh)
    return y


def callout(c, text, x, y_top, w, size=13.5):
    pad = 6*mm
    lines = wrap(text, size, w - 2*pad - 4, BOLD)
    lh = size * 1.4
    h = len(lines)*lh + pad*1.6
    c.setFillColor(BLUE_PALE); c.setStrokeAlpha(0)
    c.rect(x, y_top - h, w, h, fill=1, stroke=0)
    c.setFillColor(BLUE); c.rect(x, y_top - h, 3, h, fill=1, stroke=0)
    c.setFont(BOLD, size); c.setFillColor(DARK)
    cy = y_top - pad - size*0.4
    for ln in lines:
        c.drawString(x + pad, cy, ln); cy -= lh
    return y_top - h


def section(c, label, x, y, size=12.5):
    c.setFont(BOLD, size); c.setFillColor(BLUE); c.drawString(x, y, label.upper())
    return y


# ===========================================================================
# Page renderers
# ===========================================================================

def page1(c, W, H, mx, cw, e):
    orbs(c, W, H)
    star(c, W - 16*mm, 46*mm, 50*mm)
    y = H - 16*mm
    left(c, e["tag"], mx, y, 9, GREY)
    right(c, "1 / 2", W - mx, y, 8.5, GREY)
    y -= 5*mm; rule(c, y, mx, W - mx)

    y -= 11*mm
    accent_bar(c, mx, y)
    y -= 11*mm
    c.setFillColor(DARK); c.setFont(BOLD, 29)
    c.drawString(mx, y, "Institutional Memory")
    y -= 32; c.drawString(mx, y, "for Sovereign AI.")

    y -= 12*mm
    y = para(c, e["thesis"], mx, y, 14.5, MID, cw, 20.5)

    y -= 6*mm; rule(c, y, mx, W - mx)

    y -= 9*mm; section(c, "The problem today", mx, y)
    y -= 9.5*mm; y = bullets(c, e["problem"], mx, y, cw)

    y -= 2*mm; section(c, "What PLUR is", mx, y)
    y -= 9.5*mm; y = para(c, e["what_is"], mx, y, 11.5, BODY, cw, 16.5)

    y -= 8*mm
    callout(c, e["callout"], mx, y, cw)

    credibility(c, mx, 24*mm, cw)
    right(c, "Continued  →", W - mx, 24*mm, 8.5, GREY)


def accent_bar(c, x, y, wd=46, h=4):
    c.setFillColor(BLUE); c.setStrokeAlpha(0); c.rect(x, y, wd, h, fill=1, stroke=0)


def star(c, cx, cy, R, col=BLUE, alpha=0.05, w=0.8):
    """Faint 8-pointed khatam motif — two squares at 45 degrees (Dubai design language)."""
    c.saveState(); c.setStrokeColor(col); c.setStrokeAlpha(alpha)
    c.setLineWidth(w); c.setFillAlpha(0)
    for off in (0.0, math.pi / 4):
        p = c.beginPath()
        for k in range(4):
            a = off + k * math.pi / 2
            xx = cx + R * math.cos(a); yy = cy + R * math.sin(a)
            (p.moveTo if k == 0 else p.lineTo)(xx, yy)
        p.close(); c.drawPath(p, stroke=1, fill=0)
    c.restoreState()


def credibility(c, x, y, w):
    label = "TRACK RECORD"
    txt = "Swarm Foundation co-founders   ·   Fair Data Society   ·   EU CWA 17525:2020 co-authors   ·   3× MyData Operator Award"
    c.setFont(BOLD, 8); c.setFillColor(BLUE); c.drawString(x, y, label)
    c.setFont(FONT, 8.5); c.setFillColor(MID); c.drawString(x, y - 12, txt)


def flow(c, items, x, y_top, w):
    """Horizontal Capture -> Recall -> Compound flow with numbered nodes + arrows."""
    n = len(items); col = w / n; r = 9.5
    cy = y_top - r
    c.setStrokeColor(BLUE); c.setLineWidth(1.2); c.setFillColor(BLUE)
    for i in range(n - 1):
        x0 = x + i * col + col / 2 + r + 5
        x1 = x + (i + 1) * col + col / 2 - r - 9
        c.line(x0, cy, x1, cy)
        p = c.beginPath(); p.moveTo(x1 + 6, cy); p.lineTo(x1, cy + 4); p.lineTo(x1, cy - 4)
        p.close(); c.setStrokeAlpha(0); c.drawPath(p, fill=1, stroke=0); c.setStrokeAlpha(1)
    for i, (label, body) in enumerate(items):
        cx = x + i * col + col / 2
        c.setFillColor(BLUE); c.circle(cx, cy, r, fill=1, stroke=0)
        c.setFont(BOLD, 10); c.setFillColor(WHITE)
        c.drawString(cx - sw(str(i + 1), BOLD, 10) / 2, cy - 3.5, str(i + 1))
        c.setFont(BOLD, 12); c.setFillColor(DARK)
        c.drawString(cx - sw(label, BOLD, 12) / 2, cy - r - 14, label)
        c.setFont(FONT, 9.5); c.setFillColor(MID)
        yy = cy - r - 27
        for ln in wrap(body, 9.5, col - 18):
            c.drawString(cx - sw(ln, FONT, 9.5) / 2, yy, ln); yy -= 12
    return y_top - 33 * mm


def rows(c, items, x, y, max_w, lh=15, gap=7.5*mm):
    """label + body inline, one entry each, marker aligned to the lead."""
    tx = x + 14
    for lead, body in items:
        marker(c, x, y, 11.5)
        c.setFont(BOLD, 11.5); c.setFillColor(DARK); c.drawString(tx, y, lead)
        lw = sw(lead, BOLD, 11.5)
        c.setFont(FONT, 11); c.setFillColor(MID)
        bw = wrap(body, 11, max_w - (lw + 8) - 14)
        if bw:
            c.drawString(tx + lw + 8, y, bw[0]); y -= lh
            for ln in wrap(" ".join(bw[1:]), 11, max_w - 14):
                c.drawString(tx, y, ln); y -= lh
        else:
            y -= lh
        y -= (gap - lh)
    return y


def page2(c, W, H, mx, cw, e):
    orbs(c, W, H)
    star(c, 18*mm, 74*mm, 46*mm)
    y = H - 16*mm
    left(c, e["tag"], mx, y, 9, GREY)
    right(c, "2 / 2", W - mx, y, 8.5, GREY)
    y -= 5*mm; rule(c, y, mx, W - mx)

    y -= 11*mm
    accent_bar(c, mx, y)
    y -= 10*mm
    c.setFillColor(DARK); c.setFont(BOLD, 21)
    for ln in e["headline"].split("\n"):
        c.drawString(mx, y, ln); y -= 25

    y -= 8*mm; section(c, "How it works", mx, y)
    y -= 13*mm
    y = flow(c, [
        ("Capture", "Record the ruling and the reasoning, in-workflow."),
        ("Recall", "Surface it to any agent facing a like case."),
        ("Compound", "Each decision makes the next one better."),
    ], mx, y, cw)

    y -= 6*mm; section(c, "The plan", mx, y)
    y -= 10*mm; y = rows(c, e["plan"], mx, y, cw)

    y -= 4*mm; section(c, "Why PLUR", mx, y)
    y -= 10*mm; y = rows(c, [
        ("Sovereign by design.", "On-premise, air-gapped, open-source. Nothing leaves your borders."),
        ("Proven team.", "Eight years on data sovereignty. Swarm co-founders. EU-standard co-authors."),
        ("No lock-in.", "Plain-text, exportable, yours to keep — fork it any time."),
    ], mx, y, cw)

    # Footer
    ft = 26*mm
    rule(c, ft, mx, W - mx)
    c.setFont(BOLD, 12); c.setFillColor(BLUE)
    cta = e.get("ask", "Three weeks to a scoped pilot. First result in 60 days.")
    c.drawString(mx, ft - 7*mm, cta)
    c.setFont(FONT, 9); c.setFillColor(MID)
    c.drawString(mx, ft - 12.5*mm, "Gregor Žavcer  ·  CEO, PLUR  ·  gregor@plur.ai  ·  plur.ai")
    c.setFont(FONT, 7.5); c.setFillColor(GREY)
    for i, ln in enumerate(wrap(e["disclaimer"], 7.5, cw)):
        c.drawString(mx, ft - 18*mm - i*9, ln)


def render(key, e):
    W, H = A4; mx = 22*mm; cw = W - 2*mx
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf = OUT_DIR / f"{DATE}-{key}-twopager.pdf"
    c = Canvas(str(pdf), pagesize=A4)
    page1(c, W, H, mx, cw, e); c.showPage()
    page2(c, W, H, mx, cw, e); c.save()
    print(f"  → {pdf.name}")


# ===========================================================================
# Distilled content
# ===========================================================================

CONTENT = {
 "dubai-government": {
  "tag": "PLUR  ·  Sovereign AI for the Dubai Government",
  "thesis": "Dubai's government is going agentic. But every AI agent it runs starts each task from zero — and the judgement its people make is lost the moment the session ends. PLUR is a sovereign memory layer that captures that judgement and serves it back to every agent, on the government's own infrastructure.",
  "problem": [
    ("AI starts blank every time.", "Models keep no memory between sessions. Hard-won decisions vanish."),
    ("Knowledge never compounds.", "One entity's lesson never reaches the next. The same problems get re-solved."),
    ("Vendor memory isn't sovereign.", "Frontier AI builds memory on its cloud — your data leaving the country."),
  ],
  "what_is": "PLUR captures the rulings, corrections and reasoning your people produce as they work, and serves them back to any AI agent — Claude, ChatGPT, Copilot, or your own. Private, on-premise, model-agnostic. Institutional judgement becomes an asset the government owns outright.",
  "callout": "Memory is what turns AI tools into autonomous agents. The government that owns it owns its agentic future.",
  "headline": "Start with one entity.\nScale across government.",
  "plan": [
    ("Foundation.", "Deploy on government infrastructure. The keys stay yours."),
    ("One entity.", "First result in 60 days — read-only, beside live systems."),
    ("Across government.", "Judgement compounds entity by entity, under governance."),
  ],
  "ask": "Three weeks to a scoped pilot. Be among the first.",
  "disclaimer": "Prepared from publicly available information on Digital Dubai's AI programme; to be refined following a meeting with stakeholders.",
 },
 "rta": {
  "tag": "PLUR  ·  Sovereign AI for RTA",
  "thesis": "RTA's AI Strategy 2030 puts 81 AI projects on the road. But each agent re-derives its context every session, and a ruling one makes is lost to the next. PLUR gives RTA a memory it owns — so its agents accumulate judgement, on RTA's own hardware.",
  "problem": [
    ("Every agent forgets.", "Across RTA's AI initiatives, judgement resets at the end of each session."),
    ("Tools scale, learning doesn't.", "The Big Data Platform holds data — not the reasoning behind decisions."),
    ("Recall must be safe.", "Operational memory can never touch live signal timing or autonomous control."),
  ],
  "what_is": "PLUR captures each ruling — the decision, the conditions it holds under, and when — and serves it back to any agent, recall-only, for decision review. On RTA hardware, open-source, exportable. A scope engine rejects a ruling whose conditions don't match before any agent sees it.",
  "callout": "Memory turns 81 parallel pilots into one system that compounds — judgement RTA owns and governs.",
  "headline": "Start with one team.\nMake RTA's autonomy governable.",
  "plan": [
    ("Sandbox.", "One Cognitive Licensing team, offline. First result in 60 days."),
    ("Scale.", "Extend to each pillar through a non-invasive memory API."),
    ("Govern.", "Signed audit trail, RTA-held keys, recall-only by design."),
  ],
  "ask": "Three weeks to a scoped pilot. Be among the first.",
  "disclaimer": "Prepared from publicly available information on RTA's AI Strategy 2030; to be refined following a meeting with stakeholders. No live pilot is claimed.",
 },
 "dewa": {
  "tag": "PLUR  ·  Sovereign AI for DEWA",
  "thesis": "DEWA is becoming the world's first AI-native utility. But every agent's reasoning is captive to a foreign vendor's model — swap the model, lose a decade of engineering judgement. PLUR makes that judgement DEWA's own, and the model a commodity it can change at will.",
  "problem": [
    ("Judgement is locked to the vendor.", "A decade of engineering reasoning stays inside someone else's model."),
    ("Expertise walks out the door.", "When a senior engineer retires, their reasoning leaves with them."),
    ("Reasoning resets each session.", "Agents re-derive context every time; nothing accumulates."),
  ],
  "what_is": "PLUR captures DEWA's own corrections and the reasoning behind them, on-premise, and serves them back to any agent — even after the underlying model is swapped. The judgement becomes a sovereign asset DEWA owns; the model becomes replaceable.",
  "callout": "Own the judgement. Rent the model. Memory is DEWA's sovereignty hedge.",
  "headline": "Prove portability.\nThen a national pattern.",
  "plan": [
    ("Prove.", "One agent, read-only and air-gapped. First result in 60 days."),
    ("Validate.", "Show a captured correction survives a full model swap."),
    ("Govern.", "Classify and redact before inference, under DEWA's own key."),
  ],
  "ask": "Three weeks to a scoped pilot. Be among the first.",
  "disclaimer": "Prepared from publicly available information on DEWA's published initiatives; to be refined following a meeting with stakeholders.",
 },
 "dld": {
  "tag": "PLUR  ·  Sovereign AI for the Dubai Land Department",
  "thesis": "DLD made Dubai the MENA-first tokenised real-estate registry. But the judgement behind it — valuations, precedent, deal structuring — lives in foreign clouds and in analysts' heads. PLUR keeps that reasoning inside the Emirate, compounding under DLD's own control.",
  "problem": [
    ("The judgement isn't yours.", "The AI layer interpreting deeds and values sits in someone else's cloud."),
    ("Agents repeat known-wrong answers.", "Tools quote prices and comps the registry has already superseded."),
    ("Expertise is trapped in heads.", "Staff re-disambiguate building names and valuations by hand."),
  ],
  "what_is": "PLUR captures a confirmed correction once — an alias, a valuation override, a precedent — and every agent inherits it, deterministic and auditable. On-premise and vendor-neutral, with supersession and expiry so a stale answer never resurfaces.",
  "callout": "Tokenised property is only as trustworthy as the valuation behind it. Own that judgement.",
  "headline": "Start with one desk.\nReuse it nationally.",
  "plan": [
    ("One desk.", "A side panel valuers consult. First result in 60 days."),
    ("Grounding.", "Agents query confirmed corrections; the raw store stays air-gapped."),
    ("Governed recall.", "Every agent answer traces to the correction behind it."),
  ],
  "ask": "Three weeks to a scoped pilot. Be among the first.",
  "disclaimer": "Prepared from publicly available information on DLD's stated initiatives; to be refined following a meeting with stakeholders.",
 },
 "dib": {
  "tag": "PLUR  ·  Sovereign AI for Dubai Islamic Bank",
  "thesis": "DIB is scaling AI built on Islamic principles — fairness, transparency, no riba. But the rulings its scholars and reviewers make live inside vendor models and reset each generation. PLUR makes them a bank-owned asset: every ruling recallable, each with a named-scholar trail.",
  "problem": [
    ("Rulings aren't portable.", "Hard-won Shariah and credit judgement is locked in vendor model weights."),
    ("Reasoning resets.", "Each new model generation relearns what the bank already decided."),
    ("The board needs provenance.", "A probabilistic model cannot show who ruled, and why."),
  ],
  "what_is": "PLUR captures each ruling as a short, human-readable record — the decision, the rationale, the scholar of record, the scope — stored on DIB's own infrastructure and cited back into the next agent's context. Portable, model-agnostic, auditable.",
  "callout": "Fair-data principles are Islamic-finance ethics, expressed technically. Own the reasoning.",
  "headline": "Observe one Shariah team.\nScale across the bank.",
  "plan": [
    ("Sandbox.", "One team, observation mode. First result in 60 days."),
    ("Scale.", "Extend across credit, fraud and advisory; scholar-attested."),
    ("Federate.", "Only the ruling abstraction crosses borders; data stays resident."),
  ],
  "ask": "Three weeks to a scoped pilot. Be among the first.",
  "disclaimer": "Prepared from publicly available information on DIB's stated initiatives; to be refined following a meeting with the bank.",
 },
}

if __name__ == "__main__":
    keys = sys.argv[1:] or list(CONTENT.keys())
    for k in keys:
        if k in CONTENT:
            print(f"[{k}]"); render(k, CONTENT[k])
    print("Done.")
