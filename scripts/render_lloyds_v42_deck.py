#!/usr/bin/env python3
"""
Build Lloyds v42 deck — assembles 30 slides:
- 16 reused PNGs from v29-extended/
- 14 new PNGs rendered via PIL + ReportLab (text-only, Lloyds aesthetic)

Output: slides-v42/2026-06-04-lloyds-banking-proposal-v42.pdf
"""

from __future__ import annotations
import math
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from reportlab.pdfgen.canvas import Canvas

# ---- Paths -----------------------------------------------------------------

V29_DIR = Path("/Users/gregor/Data/1-datafund/1-tracks/comms/proposals/lloyds-banking-offer/slides-v29-extended")
V42_DIR = Path("/Users/gregor/Data/1-datafund/1-tracks/comms/proposals/lloyds-banking-offer/slides-v42")
V42_DIR.mkdir(parents=True, exist_ok=True)

# ---- Canvas ----------------------------------------------------------------

W, H = 1920, 1080  # 16:9, half-4K. Will scale to match v29 4K when needed.

# ---- Typography (SYSTEM SETTING — applies to all slides) -------------------
# Canonical sizes per user spec 2026-06-04:
#   - Body text: 18pt
#   - Slide titles: 36pt
#   - Subtitles: 22pt (interpolated)
#   - Cover title: 60pt (impact moment)
#   - Dramatic pause ("One more thing"): 72pt
# Scaled to W=1920 canvas. PIL works in pixels; we scale these by FONT_SCALE
# below if needed for higher DPI output.

FONT_SCALE = 1.0  # set >1 for higher-resolution renders
TITLE_PT = int(36 * FONT_SCALE)
SUBTITLE_PT = int(22 * FONT_SCALE)
BODY_PT = int(18 * FONT_SCALE)
COVER_TITLE_PT = int(60 * FONT_SCALE)
PAUSE_TITLE_PT = int(72 * FONT_SCALE)
FOOTER_PT = int(11 * FONT_SCALE)
ACCENT_RULE_W = 4  # blue accent bar under title

# ---- Palette (Lloyds aesthetic) --------------------------------------------

WHITE = (255, 255, 255)
CHARCOAL_DARK = (26, 26, 26)
CHARCOAL_BODY = (51, 51, 51)
CHARCOAL_MID = (85, 85, 85)
MUTED_GREY = (136, 136, 136)
BLUE = (0, 102, 255)
BLUE_LIGHT = (122, 163, 240)
LAVENDER = (201, 184, 232)
PEACH = (255, 202, 168)
SKY = (168, 197, 232)
MINT = (181, 219, 194)
PALE_YELLOW = (245, 229, 168)


# ---- Font discovery --------------------------------------------------------

def font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ---- Visual primitives -----------------------------------------------------

def pastel_orb(layer, cx, cy, radius, rgb, layers=10, layer_alpha=8):
    """Stacked translucent ellipses → soft radial-gradient pastel orb."""
    d = ImageDraw.Draw(layer)
    for i in range(layers, 0, -1):
        r = int(radius * (i / layers))
        d.ellipse([(cx - r, cy - r), (cx + r, cy + r)],
                  fill=(*rgb, layer_alpha))


def flowing_curve(layer, y_start, color, alpha=24, amp=180, freq=2.8):
    """A single thin flowing sine curve."""
    d = ImageDraw.Draw(layer)
    pts = []
    n = 220
    for k in range(n + 1):
        x = -50 + (W + 100) * k / n
        y = y_start + amp * math.sin(k / n * math.pi * freq)
        pts.append((x, y))
    d.line(pts, fill=(*color, alpha), width=3)


def make_background():
    """Light cream background with pastel orbs and faint flowing lines.
    Mirrors v29 Gemini-aesthetic minimally."""
    bg = Image.new("RGB", (W, H), WHITE)
    orb_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pastel_orb(orb_layer, W - 130, 180, 460, PEACH, layers=10, layer_alpha=7)
    pastel_orb(orb_layer, 130, H - 220, 420, LAVENDER, layers=10, layer_alpha=7)
    pastel_orb(orb_layer, W - 350, H - 100, 280, SKY, layers=10, layer_alpha=6)
    pastel_orb(orb_layer, -30, 90, 320, PALE_YELLOW, layers=10, layer_alpha=6)
    bg = Image.alpha_composite(bg.convert("RGBA"), orb_layer)

    wave_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    flowing_curve(wave_layer, 280, BLUE_LIGHT, alpha=18, amp=160)
    flowing_curve(wave_layer, 720, LAVENDER, alpha=18, amp=200, freq=2.4)
    flowing_curve(wave_layer, 900, PEACH, alpha=16, amp=120)
    wave_layer = wave_layer.filter(ImageFilter.GaussianBlur(radius=1.5))
    bg = Image.alpha_composite(bg, wave_layer)
    return bg.convert("RGB")


def draw_text_wrap(d, text, x, y, max_w, fnt, color, line_h=None):
    """Word-wrap text to fit max_w. Returns y after final line."""
    line_h = line_h or int(fnt.size * 1.35)
    words = text.split()
    line = []
    for w in words:
        cand = " ".join(line + [w])
        bbox = d.textbbox((0, 0), cand, font=fnt)
        if (bbox[2] - bbox[0]) <= max_w:
            line.append(w)
        else:
            if line:
                d.text((x, y), " ".join(line), fill=color, font=fnt)
                y += line_h
            line = [w]
    if line:
        d.text((x, y), " ".join(line), fill=color, font=fnt)
        y += line_h
    return y


def blue_square(d, x, y, size=14):
    d.rectangle([(x, y), (x + size, y + size)], fill=BLUE)


def render_slide(title, subtitle=None, bullets=None, body=None, closing=None,
                 slide_num=None):
    """Render one Lloyds-aesthetic slide with title + subtitle + bullets/body.
    Typography per system setting: title 36pt, body 18pt."""
    img = make_background()
    d = ImageDraw.Draw(img)

    mx = 110
    y = 90

    # Title — 36pt system default
    title_fnt = font(TITLE_PT)
    y = draw_text_wrap(d, title, mx, y, W - 2 * mx, title_fnt, CHARCOAL_DARK,
                       line_h=int(TITLE_PT * 1.25))
    y += 12

    # Blue accent rule under title
    d.rectangle([(mx, y), (mx + 60, y + ACCENT_RULE_W)], fill=BLUE)
    y += 26

    # Subtitle — 22pt
    if subtitle:
        sub_fnt = font(SUBTITLE_PT)
        y = draw_text_wrap(d, subtitle, mx, y, W - 2 * mx, sub_fnt, CHARCOAL_MID,
                           line_h=int(SUBTITLE_PT * 1.35))
        y += 24

    # Bullets — 18pt system default
    if bullets:
        bullet_fnt = font(BODY_PT)
        for b in bullets:
            blue_square(d, mx, y + 6, size=10)
            y = draw_text_wrap(d, b, mx + 22, y, W - 2 * mx - 22, bullet_fnt,
                               CHARCOAL_BODY, line_h=int(BODY_PT * 1.5))
            y += 14

    # Body (paragraph) — 18pt
    if body:
        body_fnt = font(BODY_PT)
        for para in body:
            y = draw_text_wrap(d, para, mx, y, W - 2 * mx, body_fnt,
                               CHARCOAL_BODY, line_h=int(BODY_PT * 1.5))
            y += 12

    # Closing line — in blue, 20pt
    if closing:
        close_fnt = font(20)
        y += 18
        draw_text_wrap(d, closing, mx, y, W - 2 * mx, close_fnt, BLUE,
                       line_h=int(20 * 1.4))

    # Footer
    foot_fnt = font(FOOTER_PT)
    d.text((mx, H - 40), "DATAFUND  ·  2026", fill=MUTED_GREY, font=foot_fnt)
    if slide_num:
        sn = f"{slide_num} / 30"
        bbox = d.textbbox((0, 0), sn, font=foot_fnt)
        d.text((W - mx - (bbox[2] - bbox[0]), H - 40), sn, fill=MUTED_GREY,
               font=foot_fnt)

    return img


def render_dramatic_pause(num=29):
    """One more thing — minimalist slide."""
    img = make_background()
    d = ImageDraw.Draw(img)
    fnt = font(PAUSE_TITLE_PT)
    text = "One more thing."
    bbox = d.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text(((W - tw) // 2, (H - th) // 2 - 40), text,
           fill=CHARCOAL_DARK, font=fnt)
    foot_fnt = font(FOOTER_PT)
    d.text((110, H - 40), "DATAFUND  ·  2026", fill=MUTED_GREY, font=foot_fnt)
    sn = f"{num} / 30"
    bbox = d.textbbox((0, 0), sn, font=foot_fnt)
    d.text((W - 110 - (bbox[2] - bbox[0]), H - 40), sn, fill=MUTED_GREY,
           font=foot_fnt)
    return img


# ---- Slide content (the 14 new slides) ------------------------------------

NEW_SLIDES = {
    1: {
        "title": "Data is the new asset.",
        "subtitle": "A Strategic Proposal for Lloyds Banking Group.",
        "cover": True,
    },
    2: {
        "title": "What we propose: Lloyds' Agent Data Exchange.",
        "subtitle": "Built in three phases over 12 months. Each phase pays for itself before the next begins.",
        "bullets": [
            "Phase 0 — Foundation (8 weeks). Legal scaffolding. Two-way door — Lloyds walks with the framework if it walks. MFN pricing locked.",
            "Phase 1 — Memory (months 2–4). PLUR Enterprise deployed on one team. Pays for itself via 3.3× more tasks per dollar.",
            "Phase 2 — Products (months 4–9). Memory active across teams. First consented data products live under Consumer Duty.",
            "Phase 3 — The Exchange (months 9–12+). Selected partners on Lloyds' rails. Lloyds owns the platform.",
        ],
        "closing": "10-year horizon: data as a balance-sheet asset class. One team. Six layers no other team has built.",
    },
    3: {
        "title": "Three layers of value.",
        "subtitle": "How operational data becomes a business. Today, Lloyds operates at Layer 1 only.",
        "bullets": [
            "Layer 1 — Data assets. Raw transactional, behavioral, decisional data. Not valued, not productised, not on the balance sheet.",
            "Layer 2 — Data products. Productised, packaged, priced — aggregate signals, consented profiles, synthetic, individual datasets.",
            "Layer 3 — Data business. A platform where data flows transact, agents buy and sell, Lloyds earns commission on every exchange.",
        ],
        "closing": "Each layer requires the previous. The rest of this deck explains the journey from Layer 1 to Layer 3.",
    },
    4: {
        "title": "A data asset Lloyds hasn't activated yet.",
        "subtitle": "Lloyds holds one of the most valuable data positions in UK financial services.",
        "bullets": [
            "The asset. Decades of transactional, behavioral, decisional, risk data across ~30M customer relationships. Cross-product views no fintech has.",
            "The status quo. Operational silos. Not productised at scale. Not on the balance sheet — like an estimated ~$1.3T of user data sitting inside global platforms.",
            "The unlock. Lloyds can sell signals with consent at agent-economy velocity — into a tier today's broker model wasn't built to serve.",
        ],
        "closing": "This proposal is how to activate the asset.",
    },
    6: {
        "title": "Agents are what make it tradeable.",
        "subtitle": "Why act now? Data has always had value. Agents are what make it tradeable at agent-economy speed.",
        "bullets": [
            "Data broker industry today: ~$460B globally. Mostly opaque, mostly without consent. Banks participate but capture a fraction of the upside.",
            "Legitimate data marketplaces (AWS, Snowflake, Datarade): ~$8B combined. A 57× gap — no infrastructure for consented exchange at agent speed.",
            "The unlock. Whoever builds the memory + consent rails first owns the consented-data infrastructure of the agent economy.",
        ],
        "closing": "The agent economy doesn't disrupt the broker market. It creates a new tier nobody currently serves.",
    },
    7: {
        "title": "The agent economy is already running.",
        "subtitle": "Not a 2030 projection. Transactions are happening now, on rails that didn't exist 18 months ago.",
        "bullets": [
            "Infrastructure live. Coinbase x402 (AI Agents App Store, June 2026, 400+ builders). Stripe Machine Payments Protocol (April 2026, 11M+ businesses). Skyfire KYAPay. Meta Agentic Commerce Protocol.",
            "Volume is real. x402: ~165M transactions cleared. Alipay AI Pay: ~120M agent-initiated transactions in a single week (Feb 2026).",
            "The math has flipped. 76% of agent transactions fall below Visa's $0.30 fee floor. Traditional rails cannot process them economically.",
        ],
        "closing": "Agents are already the market makers. The question is who owns the rails they run on.",
    },
    10: {
        "title": "Memory is the precondition.",
        "subtitle": "For agents to function. For data to become product. For Lloyds to become a platform.",
        "bullets": [
            "For agents to function as agents. Not just autonomy — judgement, pricing, market intelligence. Without memory, you have stateless tools, not agents.",
            "For data to become product. Lloyds needs memory of what's valuable, what data owners consented to, what buyers pay for. Memory is the product-development engine.",
            "For Lloyds to become a platform. Memory is the substrate that makes every layer above it possible — services, customer agents, the Agent Data Exchange.",
        ],
        "closing": "PLUR is the first step. Everything else is built on it.",
    },
    18: {
        "title": "Data isn't a commodity — it's an information asset.",
        "subtitle": "Same data has different value to different buyers. Memory is what makes that pricing work at agent speed.",
        "bullets": [
            "Value asymmetry. ICDE study of 4,200+ commercial data products: pricing from $100/month (open data) to $150,000/month (premium financial) — a 1,500× spread by buyer context.",
            "Memory enables pricing. Flat-priced products capture one slice of the curve. Memory captures which buyers paid what for which signal under which conditions.",
            "Agents serve the long tail. Each query individual; each result bespoke. The service is a productized category. Agents transact what humans couldn't.",
            "Privacy at the exchange level. Counterparty discretion is the default.",
        ],
        "closing": "Agents price the asymmetry. Memory teaches them how. The two-sided market emerges.",
    },
    19: {
        "title": "What banking data becomes.",
        "subtitle": "Four categories. Four revenue lines. All under Consumer Duty.",
        "bullets": [
            "Aggregate signals. Anonymized spending patterns, regional trends, sector signals. B2B licensed. Today's brokers sell similar without consent — Lloyds sells with consent.",
            "Consented profiles. Data owners opt in. Their financial agent represents them. Data owner earns. Lloyds earns commission. The market today's brokers cannot enter.",
            "Synthetic derivatives. Privacy-preserving generated data. Provably non-reversible. For research labs, model vendors, regulatory sandboxes.",
            "Individual Datasets. Agent-assembled, query-specific, bespoke per buyer. Dynamic, buyer-context-aware pricing. The agent-economy native product.",
        ],
    },
    20: {
        "title": "Memory + Data — compounding.",
        "subtitle": "Each makes the other smarter.",
        "bullets": [
            "Memory learns from data flows. Patterns of consent, product discovery, what buyers pay for, what data owners value — captured as engrams.",
            "Data flows benefit from memory. Better consent UX, smarter product recommendations, faster regulatory adaptation. Data layer ships better because PLUR is underneath.",
            "Memory tells you what to sell. Discovery, consent intelligence, agent feedback loop — memory is the product-development engine for the data economy.",
        ],
        "closing": "The two layers don't sit side by side. They reinforce each other.",
    },
    21: {
        "title": "The Agent Data Exchange.",
        "subtitle": "Consent at the protocol level. Settlement at agent speed. Audit at the protocol layer.",
        "bullets": [
            "Granular consent. Data owners choose: which data, for which use, for how long, with whom. Every access logged. Revocable at any time.",
            "Settlement at the speed agents need. Permissioned, programmable, auditable. Bank-grade infrastructure — already deployed across tier-1 institutions internally.",
            "Revenue model. Data owner earns. Lloyds earns commission. Buyers get high-quality, regulated data — at scale, at agent-economy speed.",
        ],
        "closing": "Regulated under Consumer Duty, GDPR, ICO. Built for the regulator, not retrofitted.",
    },
    22: {
        "title": "Lloyds becomes the rails.",
        "subtitle": "Not just a data seller. The consented-data infrastructure of UK financial services.",
        "bullets": [
            "Phase 1–2. Lloyds runs both layers internally. Captures all the upside itself. No external dependency.",
            "Phase 3 (Lloyds' choice). Lloyds opens the rails to selected partners — insurance, fintech, retail, government. No competitor banks unless Lloyds chooses.",
            "The compounding moat. The more institutions use the rails, the better the rails get. The agent economy runs on Lloyds infrastructure — under Lloyds' rules.",
        ],
        "closing": "Memory pays for itself in months. The platform pays for decades.",
    },
    30: {
        "title": "Data as a new asset class.",
        "subtitle": "The Agent Data Exchange positions Lloyds to do something no UK bank has done before — turn data into a balance-sheet asset.",
        "bullets": [
            "Today. Banks recognize intangibles on balance sheet — goodwill, brand, software. Data is excluded. ~$1.3T of user data sits inside global platforms with no balance-sheet recognition.",
            "The shift. Agent-driven exchange creates the four conditions for asset recognition: market prices, identifiable ownership, marketability, audit trail. Lloyds' architecture has all four.",
            "What this unlocks (10-year horizon). New collateral classes. New credit products. Tier 2 capital recognition. Securitised consented data flows under FCA oversight.",
        ],
        "closing": "Lead the data economy. Then redefine what's on the balance sheet.",
    },
}


# ---- v42 → source mapping --------------------------------------------------

# Slides where we reuse v29 PNGs directly
V29_MAP = {
    5: "slide-09-why-lloyds.png",
    8: "slide-03-every-agent-forgets.png",
    9: "slide-10-monday-at-lloyds.png",
    11: "slide-04-gap.png",
    12: "slide-06-introducing-plur.png",
    13: "slide-08-how-plur-works.png",
    14: "slide-12-how-lloyds-learns.png",  # proxy for "Two chats. One memory."
    15: "slide-15-engrams.png",
    16: "slide-19-sovereign-by-design.png",
    17: "slide-14-brain.png",
    23: "slide-21-three-steps.png",
    24: "slide-24-how-it-starts.png",
    25: "slide-26-credibility.png",
    26: "slide-27-risk-posture.png",
    27: "slide-28-design-partner-terms.png",
    28: "slide-29-next-steps.png",
}


# ---- Build deck ------------------------------------------------------------

def build_deck():
    image_paths = []

    for slide_num in range(1, 31):
        out_path = V42_DIR / f"slide-{slide_num:02d}.png"

        if slide_num == 29:
            # One more thing — dramatic minimalist
            img = render_dramatic_pause(num=29)
            img.save(out_path, "PNG")
            print(f"  [new]  slide-{slide_num:02d} — One more thing")
            image_paths.append(out_path)
            continue

        if slide_num in NEW_SLIDES:
            spec = NEW_SLIDES[slide_num]
            if spec.get("cover"):
                # Cover: minimalist
                img = make_background()
                d = ImageDraw.Draw(img)
                title_fnt = font(COVER_TITLE_PT)
                bbox = d.textbbox((0, 0), spec["title"], font=title_fnt)
                tw = bbox[2] - bbox[0]
                d.text(((W - tw) // 2, H // 2 - 70), spec["title"],
                       fill=CHARCOAL_DARK, font=title_fnt)
                sub_fnt = font(SUBTITLE_PT)
                if spec.get("subtitle"):
                    bbox = d.textbbox((0, 0), spec["subtitle"], font=sub_fnt)
                    sw = bbox[2] - bbox[0]
                    d.text(((W - sw) // 2, H // 2 + 30), spec["subtitle"],
                           fill=CHARCOAL_MID, font=sub_fnt)
                img.save(out_path, "PNG")
            else:
                img = render_slide(
                    title=spec["title"],
                    subtitle=spec.get("subtitle"),
                    bullets=spec.get("bullets"),
                    body=spec.get("body"),
                    closing=spec.get("closing"),
                    slide_num=slide_num,
                )
                img.save(out_path, "PNG")
            print(f"  [new]  slide-{slide_num:02d} — {spec['title'][:50]}")
            image_paths.append(out_path)

        elif slide_num in V29_MAP:
            src = V29_DIR / V29_MAP[slide_num]
            # Copy and rename
            import shutil
            shutil.copy(src, out_path)
            print(f"  [v29]  slide-{slide_num:02d} ← {V29_MAP[slide_num]}")
            image_paths.append(out_path)
        else:
            print(f"  [??]   slide-{slide_num:02d} — UNMAPPED")

    return image_paths


def build_pdf(image_paths, output_path):
    """Create PDF — one slide per page, 16:9."""
    page_w = W * 0.5  # render at half-resolution PDF (still high quality)
    page_h = H * 0.5
    c = Canvas(str(output_path), pagesize=(page_w, page_h))
    for img_path in image_paths:
        # Open to verify
        with Image.open(img_path) as im:
            iw, ih = im.size
        c.drawImage(str(img_path), 0, 0, width=page_w, height=page_h,
                    preserveAspectRatio=True, anchor='c')
        c.showPage()
    c.save()
    print(f"\nPDF: {output_path}")


if __name__ == "__main__":
    print("Building v42 deck — 30 slides (14 new + 16 v29 reuse)\n")
    paths = build_deck()
    pdf_path = V42_DIR / "2026-06-04-lloyds-banking-proposal-v42.pdf"
    build_pdf(paths, pdf_path)
    print(f"\nDone. {len(paths)} slides assembled.")
