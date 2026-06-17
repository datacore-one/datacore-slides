#!/usr/bin/env python3
"""Diagnose WHY a Gemini image-gen call returns no image.

nano-banana-slides.py only prints "No image in response" and discards the
API's diagnostic fields. This probe surfaces prompt_feedback.block_reason,
candidate finish_reason, and safety_ratings so you can tell a content
refusal (SAFETY / PROHIBITED_CONTENT / IMAGE_SAFETY) apart from a
RECITATION block or a plain timeout.

Usage:  python3 probe-image-refusal.py [model]
        model defaults to gemini-3-pro-image-preview (the deck render model)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv(Path.home() / "Data/.datacore/env/.env")
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

MODEL = sys.argv[1] if len(sys.argv) > 1 else "gemini-3-pro-image-preview"
model = genai.GenerativeModel(MODEL)

STYLE = ("A clean minimalist presentation slide on a white background with soft "
         "pastel gradient orbs and fine line-work. Left-aligned. Headline in dark "
         "ink, body text below. ")

VARIANTS = {
    "A_named_event": STYLE + (
        "Headline: 'Rented access can be revoked.' "
        "Body: 'On June 12, 2026, a US export-control order forced Anthropic to cut "
        "off access to its most capable models for all foreign nationals.'"),
    "B_generic_gov": STYLE + (
        "Headline: 'Rented access can be revoked.' "
        "Body: 'A government export-control order forced a leading AI lab to cut off "
        "access to its most capable models for entire classes of users, overnight.'"),
    "C_no_gov_principle": STYLE + (
        "Headline: 'Rented access can be revoked.' "
        "Body: 'A model you rely on can be deprecated or cut off by forces outside "
        "your control. Owned memory cannot.'"),
    "D_control_innocuous": STYLE + (
        "Headline: 'How PLUR works.' "
        "Body: 'PLUR captures how your organisation works as typed memory records and "
        "serves it back to any AI.'"),
}


def probe(name, prompt):
    try:
        resp = model.generate_content(
            contents=[prompt],
            generation_config={"response_modalities": ["IMAGE"]},
        )
    except Exception as e:
        print(f"[{name}] EXCEPTION {type(e).__name__}: {e}")
        return

    pf = getattr(resp, "prompt_feedback", None)
    block = getattr(pf, "block_reason", None) if pf else None
    cands = getattr(resp, "candidates", []) or []
    finishes, has_img, safety = [], False, []
    for c in cands:
        finishes.append(str(getattr(c, "finish_reason", None)))
        content = getattr(c, "content", None)
        for p in (getattr(content, "parts", []) or []):
            if getattr(p, "inline_data", None) and p.inline_data.data:
                has_img = True
        for s in (getattr(c, "safety_ratings", []) or []):
            if str(getattr(s, "probability", "")) not in ("NEGLIGIBLE", "Probability.NEGLIGIBLE", ""):
                safety.append(f"{getattr(s, 'category', '?')}={getattr(s, 'probability', '?')}")
    print(f"[{name}] image={has_img} block_reason={block} finish_reason={finishes}")
    if safety:
        print(f"        safety_flags={safety}")


EVENT = ("12 June 2026: a US export-control order forced Anthropic to suspend its most "
         "capable models for all foreign nationals — worldwide.")
QUOTE = ("There is no societal permission for an AI future that hollows out entire "
         "industries. — Satya Nadella, Microsoft CEO, June 2026")

QTEXT = "There is no societal permission for an AI future that hollows out entire industries."
VARIANTS["H_quote_no_attrib"] = STYLE + f"A centred pull-quote in charcoal italic: '{QTEXT}'"
VARIANTS["I_quote_title_only"] = STYLE + (
    f"A centred pull-quote in charcoal italic: '{QTEXT}' attribution beneath: "
    "'— a Big Tech CEO, June 2026'")
VARIANTS["J_quote_named"] = STYLE + (
    f"A centred pull-quote in charcoal italic: '{QTEXT}' attribution beneath: "
    "'— Satya Nadella, Microsoft, June 2026'")
VARIANTS["K_event_plus_quote_noattrib"] = STYLE + (
    f"Headline: 'Rented access can be revoked.' Body: '{EVENT}' "
    f"Right-column quote card, charcoal italic: '{QTEXT}' — attribution: 'Microsoft CEO, 2026'")

print(f"== probing model: {MODEL} ==")
for n, p in VARIANTS.items():
    probe(n, p)
