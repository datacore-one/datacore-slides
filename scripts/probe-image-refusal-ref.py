#!/usr/bin/env python3
"""Probe the FULL render path (reference images + long prompt) for the real
API diagnostic when nano-banana returns no image. Companion to
probe-image-refusal.py, which only tests bare prompts.

Usage: python3 probe-image-refusal-ref.py <reference.pdf> [model]
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from pdf2image import convert_from_path

load_dotenv(Path.home() / "Data/.datacore/env/.env")
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

REF = sys.argv[1]
MODEL = sys.argv[2] if len(sys.argv) > 2 else "gemini-3-pro-image-preview"
model = genai.GenerativeModel(MODEL)
refs = convert_from_path(REF, first_page=1, last_page=2, dpi=150)
print(f"loaded {len(refs)} reference pages; model={MODEL}")

LONG = ("Datafund Data Business visual language: light, editorial, FT-print-scale "
        "small tight text, 60-70% white space, Helvetica Neue regular, pure-blue "
        "(#0066FF) bullet squares, soft pastel orbs behind, strict two-column.\n\n---\n\n"
        "Generate a presentation slide.\nCONTENT TO RENDER:\n"
        "Title: Rented access can be revoked.\n"
        "Body:\nThe capability you don't own can be withdrawn — on terms you don't set.\n"
        "- 12 June 2026: a US export-control order forced Anthropic to suspend its most "
        "capable models for all foreign nationals — worldwide.\n"
        "- The first export control on an AI model, not just the chips.\n"
        "- It reignited the global push for sovereign AI.\n"
        "If your AI is someone else's, it can be taken away. What's yours cannot.\n"
        "Right column: a Nadella pull-quote card: 'There is no societal permission for an "
        "AI future that hollows out entire industries.' — Satya Nadella, June 2026.")

INNOCUOUS = LONG.replace(
    "Title: Rented access can be revoked.",
    "Title: How PLUR works.").replace(
    "The capability you don't own can be withdrawn — on terms you don't set.",
    "PLUR captures how your organisation works and serves it back to any AI.").replace(
    "- 12 June 2026: a US export-control order forced Anthropic to suspend its most "
    "capable models for all foreign nationals — worldwide.",
    "- Captures knowledge as typed memory records in plain text.").replace(
    "- The first export control on an AI model, not just the chips.",
    "- Serves it back to any model — Arabic-first, Claude, or your own.").replace(
    "- It reignited the global push for sovereign AI.",
    "- Runs on your own infrastructure.").replace(
    "If your AI is someone else's, it can be taken away. What's yours cannot.",
    "Not a chatbot, not a model — the layer that holds what your institution knows.").replace(
    "Right column: a Nadella pull-quote card: 'There is no societal permission for an "
    "AI future that hollows out entire industries.' — Satya Nadella, June 2026.",
    "Right column: a simple node diagram of inputs flowing into a central PLUR box.")


def probe(name, text):
    for attempt in (1, 2):
        contents = ["REFERENCE IMAGES - Match this exact visual style:", refs[0], refs[1],
                    "\nNow generate a new slide matching this style:\n", text]
        resp = model.generate_content(contents=contents,
                                       generation_config={"response_modalities": ["IMAGE"]})
        pf = getattr(resp, "prompt_feedback", None)
        block = getattr(pf, "block_reason", None) if pf else None
        cands = getattr(resp, "candidates", []) or []
        finishes, has_img = [], False
        for c in cands:
            finishes.append(str(getattr(c, "finish_reason", None)))
            for p in (getattr(getattr(c, "content", None), "parts", []) or []):
                if getattr(p, "inline_data", None) and p.inline_data.data:
                    has_img = True
        print(f"[{name}#{attempt}] image={has_img} block_reason={block} finish_reason={finishes}")


NO_COMPANY = LONG.replace("forced Anthropic to suspend", "forced a leading US lab to suspend")
NO_GOV = NO_COMPANY.replace(
    "12 June 2026: a US export-control order forced a leading US lab to suspend its most "
    "capable models for all foreign nationals — worldwide.",
    "12 June 2026: an export-control order forced a leading lab to suspend its most "
    "capable models for entire classes of users — overnight.").replace(
    "- The first export control on an AI model, not just the chips.",
    "- The first time frontier-model access was cut off by policy, not price.")

probe("EVENT_with_ref", LONG)
probe("NO_COMPANY_with_ref", NO_COMPANY)
probe("NO_GOV_with_ref", NO_GOV)
probe("INNOCUOUS_with_ref", INNOCUOUS)
