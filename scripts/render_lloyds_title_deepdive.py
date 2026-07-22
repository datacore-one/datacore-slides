#!/usr/bin/env python3
"""
Render the 4-slide title-insurance deep-dive for the "How Lloyd's Insurance Works" deck.

These 4 slides splice into the existing 13-slide deck, replacing its single slide 11
("The title-insurance analogy") with a 4-slide deep dive. They must match the existing
deck's visual style EXACTLY, so this script replicates the ORIGINAL generation recipe:

  - model: gemini-3-pro-image-preview  (same as the rest of the deck)
  - the SAME `design_system` block that produced slides 1-13 (institutional City house
    style, cream #F6F2EA, navy #14294B, ochre #B8862F accent, editorial serif headline)
  - the SAME landscape orientation instruction and the SAME "leave bottom-right empty for
    the logo, added in post" directive nano-banana-slides.py appends for design_system decks
  - the SAME 4k (3840x2160) save/resize logic
  - NO reference images and NO baked logo — exactly as generation-log.json records for the
    original deck (reference: null, logo: null). Consistency comes from the design system.

Output: ti-1.png .. ti-4.png in the title-deepdive/ folder. No PDF, no logo overlay —
those are handled downstream by the caller.
"""

import os
import time
from pathlib import Path
from io import BytesIO

from dotenv import load_dotenv
load_dotenv(Path.home() / "Data/.datacore/env/.env")

import google.generativeai as genai
from PIL import Image

MODEL = "gemini-3-pro-image-preview"
TARGET = (3840, 2160)  # 4k, matches the existing deck
OUT_DIR = Path(
    "/Users/gregor/Data/1-datafund/1-tracks/comms/presentations/"
    "lloyds-of-london/slides-v1/title-deepdive"
)

# ---------------------------------------------------------------------------
# EXACT design_system block from how-lloyds-insurance-works.slides.md frontmatter.
# This is what produced the visual style of every existing slide. Do not alter.
# ---------------------------------------------------------------------------
DESIGN_SYSTEM = """DESIGN SYSTEM — Institutional editorial financial house style. Think a top-tier
strategy consultancy deck crossed with a Lloyd's of London / City of London
house style. Restrained, precise, confident, calm. NOT a startup deck, NOT
playful, NO pastel orbs, NO gradients, NO glow, NO photographic imagery.

BACKGROUND: Flat warm off-white / soft cream #F6F2EA across the whole slide.
Absolutely no gradient orbs, no blurred blobs, no texture, no vignette.
Generous whitespace — at least 45% of the slide is empty cream.

COLOR PALETTE — use ONLY these, nothing else:
- Deep navy #14294B — headlines, primary structure, diagram lines, boxes, rules
- Charcoal #33383F — body text and labels
- Warm ochre / gold #B8862F — the ONE accent. Use sparingly: the single key node,
  row, step or word per slide, tick-marks, and thin emphasis rules.
- Cream #F6F2EA — background
- Muted slate grey #8A8F98 — eyebrows, captions, secondary labels, hairlines
NO saturated blue, NO green, NO red, NO purple. Everything sober and institutional.

TYPOGRAPHY — strong hierarchy, four clear levels:
1. EYEBROW / KICKER: small uppercase, generously letter-spaced, slate grey or ochre,
   top-left of the content area.
2. HEADLINE: a high-contrast editorial SERIF (Times / Georgia / Tiempos feel),
   deep navy, large but refined, left-aligned. This is the dominant element.
3. DECK / SUPPORTING LINE: neutral sans-serif (Helvetica / Inter feel), charcoal,
   medium size.
4. BODY / LABELS / DIAGRAM TEXT: same neutral sans, charcoal, small and precise.
A thin navy or ochre hairline rule sits under the headline on every content slide.

DIAGRAMS — real vector-style, precise and editorial, never decorative clip-art:
- Thin crisp navy hairlines. Boxes have 1px navy borders, square or lightly rounded
  corners (consistent across the whole deck), generous internal padding, cream fill.
- Flow arrows are thin navy lines with small clean arrowheads.
- Use the ochre accent to highlight exactly ONE key node / row / step / pillar.
- Any icons are minimal single-weight navy line icons only — sparse. NO 3D, NO drop
  shadows, NO gradients, NO emoji, NO stock illustration, NO photographs.

LAYOUT — one consistent template on every slide:
- Eyebrow top-left, headline below it, thin rule under the headline, then the content
  area (text left, supporting diagram right — or a full-width diagram band).
- Small slate slide number bottom-left. Leave the bottom-right corner empty for a logo.
- Everything aligned to a clean grid, left-aligned. Comfortable margins (~6% of width).

TEXT FIDELITY — CRITICAL: render every word EXACTLY as written in the content, with
perfect spelling. Do not paraphrase, summarise, translate, or invent text. Keep all
terms and figures verbatim: Lloyd's, ERC-3643, PLUR, Verity, GDPR, $500k. Curly apostrophes."""

ORIENTATION = (
    "Generate a WIDE presentation slide image. CRITICAL: Output must be 16:9 LANDSCAPE "
    "aspect ratio (width much greater than height, like 1920x1080 or 1456x816). NOT square. "
    "NOT portrait."
)

LOGO_RULE = (
    "LOGO: DO NOT draw any logo, brand mark, or icon. Do NOT draw the word 'Datafund' or any "
    "wordmark. Leave the bottom-right corner completely empty — the logo is added in post."
)

SYSTEM_STYLE = f"{ORIENTATION}\n\n{DESIGN_SYSTEM}\n\n{LOGO_RULE}\n"

# ---------------------------------------------------------------------------
# The four slides. Each carries verbatim content + precise design notes that encode
# the layout patterns observed on existing slides 6/10/11/12.
# ---------------------------------------------------------------------------
SLIDES = [
    {
        "file": "ti-1.png",
        "page": "11",
        "prompt": """CONTENT TO RENDER — render every word verbatim, perfect spelling.

EYEBROW (small uppercase, letter-spaced, slate): TITLE INSURANCE
HEADLINE (editorial serif, deep navy): Title insurance: insuring ownership, not the building

LEFT COLUMN — four lines as a clean charcoal list, each with a small ochre tick-mark:
- The scary risk in buying property isn't fire — that's hazard cover
- It's that someone has a better claim: a forged deed, an undisclosed lien, a missing heir, a break in the chain of title
- Title insurance protects the buyer — and crucially the lender — against pre-existing, undiscovered ownership defects
- A one-time premium at closing; it insures ownership validity, retrospectively

OCHRE EMPHASIS (colour these exact phrases ochre inside the lines above): "better claim", "the lender", "ownership validity, retrospectively".

RIGHT — a precise navy line-vector diagram that contrasts BUILDING vs TITLE:
- A simple thin-navy house outline. Small slate caption beneath it: "THE BUILDING — hazard cover".
- In FRONT of / beside the house, a document/deed icon labelled "DEED / TITLE". An ochre shield outline with a small ochre check sits ON the deed (NOT on the house). Small ochre caption beneath the deed: "OWNERSHIP — title insurance".
- A thin slate caption under the diagram: "the cover sits on the title, not the bricks."
The single ochre highlight of the slide is the shield-on-the-deed.

DESIGN NOTES: Institutional editorial layout — eyebrow top-left, serif headline, thin navy hairline rule under the headline, then text left / diagram right. Generous cream whitespace. Small slate page number bottom-left reading exactly "11". Bottom-right corner empty.""",
    },
    {
        "file": "ti-2.png",
        "page": "12",
        "prompt": """CONTENT TO RENDER — render every word verbatim, perfect spelling.

EYEBROW (small uppercase, letter-spaced, slate): WHY IT SCALED
HEADLINE (editorial serif, deep navy): Why this built a multi-trillion market

LEFT COLUMN — four lines as a tight charcoal list with small ochre tick-marks:
- A bank won't lend $500k against a house if the borrower might not own it
- Title insurance transfers that risk — so banks lend with confidence
- Mortgages scale, and real estate becomes liquid, financeable, securitizable
- The insight: it didn't insure returns — it made ownership defensible enough to lend against

OCHRE EMPHASIS (colour this exact phrase ochre inside the last line): "defensible enough to lend against".

RIGHT / MAIN BAND — the dominant element is a left-to-right vector CAUSATION CHAIN: four square navy-outlined nodes (lightly rounded corners, cream fill, thin navy borders) connected by thin navy arrows with small clean arrowheads, in this exact order:
"Title insurance"  →  "Confident lending"  →  "Mortgages at scale"  →  "Liquid, investable asset class"
Highlight ONLY the final node "Liquid, investable asset class" in ochre (ochre outline + ochre text). All other nodes navy.

DESIGN NOTES: Institutional editorial layout — eyebrow top-left, serif headline, thin navy hairline rule under the headline. The causation chain reads clearly left to right across the slide (same box-and-arrow flow style as the deck's other process slides). Generous cream whitespace. Small slate page number bottom-left reading exactly "12". Bottom-right corner empty.""",
    },
    {
        "file": "ti-3.png",
        "page": "13",
        "prompt": """CONTENT TO RENDER — render every word verbatim, perfect spelling.

Top-left KICKER LABEL (small uppercase, generously letter-spaced, slate grey) reading exactly, and only, these two words: THE ANALOGY
(Do NOT print the word "eyebrow" or "kicker" or "label" — render ONLY the text "THE ANALOGY".)
HEADLINE (editorial serif, deep navy): The same move, for data

MAIN ELEMENT — a clean two-column MAPPING TABLE with hairline navy borders, cream fill, generous cell padding, centred. Header row (navy, emphasised):
Real estate  |  Data asset
Then exactly these six rows, left cell | right cell:
Deed / title            | Ownership token (ERC-3643)
Land registry           | Provenance substrate (PLUR / Verity)
Title search            | Provenance verification
Title defect            | Forged / hidden-licence provenance
Title insurer           | Lloyd's
Mortgage                | Financing a data asset

Highlight EXACTLY TWO rows in ochre (ochre text in both cells + an ochre outline around the whole row): the "Land registry | Provenance substrate (PLUR / Verity)" row and the "Title insurer | Lloyd's" row. All other rows navy/charcoal.

BELOW THE TABLE — a slim full-width callout banner with a thin ochre accent, punchline text: "PLUR / Verity is the land registry. Lloyd's is the title insurer." Set the whole punchline in ochre.

DESIGN NOTES: Institutional editorial layout — eyebrow top-left, serif headline, thin navy hairline rule under the headline, then the table. Keep terms verbatim: ERC-3643, PLUR, Verity, Lloyd's. Generous cream whitespace. Small slate page number bottom-left reading exactly "13". Bottom-right corner empty.""",
    },
    {
        "file": "ti-4.png",
        "page": "14",
        "prompt": """CONTENT TO RENDER — render every word verbatim, perfect spelling.

EYEBROW (small uppercase, letter-spaced, slate): INSURABLE DEFECTS
HEADLINE (editorial serif, deep navy): What could be wrong with the title?

MAIN DIAGRAM — a navy line-vector "certificate of title" at the centre: a portrait document icon labelled "DATA ASSET — CERTIFICATE OF TITLE" with a small navy seal. Radiating from it, five small navy-outlined callout boxes (cream fill, thin navy borders) connected to the certificate by thin navy leader lines. Each callout is marked with a small OCHRE warning flag / exclamation mark (ochre, NOT red — there is no red anywhere on the slide). The five callouts carry these exact texts, verbatim, including the parenthetical real-estate equivalents:
- Forged or mis-attributed provenance (a forged deed)
- An undisclosed prior exclusive licence (a lien on the data)
- A consent / GDPR defect in how it was collected
- A copyright / database-right claim
- A contributor who resurfaces claiming rights (a missing heir)

BELOW — a full-width slim navy-outlined callout band with the closing line: "The provenance substrate is what makes these defects detectable — and therefore insurable." Emphasise the phrase "detectable — and therefore insurable" in ochre.

DESIGN NOTES: Institutional editorial layout — eyebrow top-left, serif headline, thin navy hairline rule under the headline. Ochre is the ONLY accent colour (the warning flags), everything else navy/charcoal on cream — absolutely no red. Balanced, airy, not crowded. Small slate page number bottom-left reading exactly "14". Bottom-right corner empty.""",
    },
]


def fit_to_target(image: Image.Image, target=TARGET) -> Image.Image:
    """Resize into target dims; if aspect already ~16:9 resize directly, else pad with cream."""
    img = image.convert("RGB")
    w, h = img.size
    aspect = w / h
    tw, th = target
    if abs(aspect - tw / th) < 0.1:
        return img.resize(target, Image.Resampling.LANCZOS)
    scale = min(tw / w, th / h)
    nw, nh = int(w * scale), int(h * scale)
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    # cream background matching the deck (#F6F2EA)
    canvas = Image.new("RGB", target, (246, 242, 234))
    canvas.paste(resized, ((tw - nw) // 2, (th - nh) // 2))
    return canvas


def generate(model, slide, attempts=3):
    prompt = f"{SYSTEM_STYLE}\n\n---\n\n{slide['prompt']}\n\nCRITICAL: Perfect spelling of ALL text."
    for a in range(1, attempts + 1):
        try:
            resp = model.generate_content(
                contents=[prompt],
                generation_config={"response_modalities": ["IMAGE"]},
            )
            for part in resp.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    return part.inline_data.data
            print(f"  [{slide['file']}] attempt {a}: no image in response")
        except Exception as e:
            print(f"  [{slide['file']}] attempt {a} error: {e}")
        if a < attempts:
            time.sleep(5)
    return None


def main():
    import sys
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not found")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Optional CLI filter: render only the named files (e.g. `ti-3.png`).
    only = set(a for a in sys.argv[1:] if a.endswith(".png"))
    slides = [s for s in SLIDES if not only or s["file"] in only]

    results = []
    for slide in slides:
        print(f"Generating {slide['file']} (page {slide['page']})...")
        data = generate(model, slide)
        if not data:
            print(f"  FAILED: {slide['file']}")
            results.append((slide["file"], "FAILED", None))
            continue
        img = Image.open(BytesIO(data))
        print(f"  Gemini output: {img.size[0]}x{img.size[1]} (aspect {img.size[0]/img.size[1]:.2f})")
        out = fit_to_target(img)
        out_path = OUT_DIR / slide["file"]
        out.save(out_path, "PNG", optimize=False)
        print(f"  Saved: {out_path} -> {out.size[0]}x{out.size[1]}")
        results.append((slide["file"], "ok", f"{out.size[0]}x{out.size[1]}"))

    print("\nSummary:")
    for f, status, size in results:
        print(f"  {f}: {status} {size or ''}")


if __name__ == "__main__":
    main()
