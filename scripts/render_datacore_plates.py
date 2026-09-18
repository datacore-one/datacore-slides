#!/usr/bin/env python3
"""Generate Datacore-brand background plates with Nano Banana Pro (Gemini 3 Pro Image).

Why a model at all, when the deck is HTML: a plate carries NO TEXT. That is the one
job an image model does better than CSS and cannot get wrong — garbled letters and
drifting typography are impossible when there are no letters. Type, tables and code
stay in HTML; the model only makes the ground they sit on. (Approach lifted from
5-plur/.../plur-seed-2026-05/render_bg_plates.py, which proved it on the seed deck.)

Every prompt is built from Datacore's own vocabulary, taken from the website
(2-datacore/2-projects/website/index.html): sacred geometry — flower of life, nested
tesseract, morphing polygon-to-circle, neuron-like blinks — in #3b82f6 on the light
palette #f0f7ff / #e6f0fa / #dbe8f5. Nothing painterly: no orbs, no glow washes, no
gradient skies. A plate must survive text laid over its left two thirds.

The key comes from the broker, never from a .env hunt:
    python3 .datacore/lib/creds.py get gemini-api-key --consumer render_datacore_plates

Usage:
    python3 render_datacore_plates.py --out <dir>            # all variants
    python3 render_datacore_plates.py --only lattice --out <dir>
    python3 render_datacore_plates.py --list                 # generate nothing
    python3 render_datacore_plates.py --theme dark --out <dir>

Output: <dir>/<variant>-<theme>.jpg (1920x1080, JPEG q72) + contact-sheet.png
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

from PIL import Image

DATA = Path.home() / "Data"
MODEL = "gemini-3-pro-image-preview"

# Light is the deck default; dark mirrors the website's dark mode.
PALETTES = {
    "light": {"field": "#f0f7ff", "deep": "#dbe8f5", "ink": "#2563eb",
              "desc": "a very pale cool blue-white field (#f0f7ff), marks in a "
                      "soft blue (#2563eb) at low opacity"},
    "dark":  {"field": "#0a0a0a", "deep": "#111111", "ink": "#3b82f6",
              "desc": "a near-black field (#0a0a0a), marks in a clear blue "
                      "(#3b82f6) at low opacity"},
}

# The geometry is Datacore's, not decoration borrowed from elsewhere: the website
# canvas draws exactly these four things.
VARIANTS = {
    "flower": "A single flower-of-life pattern — one centre circle, a ring of six, "
              "a partial outer ring — drawn as thin open outlines, no fill, placed "
              "small in the far RIGHT THIRD of the frame. The left two thirds are "
              "empty field. Line weight one pixel, opacity about eight percent.",
    "tesseract": "One nested tesseract: a square inside a rotated square inside a "
                 "third, connected at the corners, thin open outlines only, sitting "
                 "in the lower RIGHT corner at a slight rotation. Rest of the frame "
                 "empty. Line weight one pixel, opacity about ten percent.",
    "lattice": "A regular lattice of very small circular dots across the whole frame, "
               "spacing about 40 pixels, each dot under two pixels, opacity about "
               "five percent, perfectly even, no clustering and no variation.",
    "blink": "A sparse scatter of small circular dots across the RIGHT HALF only, "
             "irregular and neuron-like, a handful slightly brighter than the rest "
             "as though momentarily firing, thin straight hairlines connecting a few "
             "neighbouring pairs. Left half empty. Overall opacity about seven percent.",
}

GUARD = ("Absolutely no text, no letters, no numbers, no logos, no watermark, no UI. "
         "Flat vector geometry only — no photography, no 3D, no bevels, no drop "
         "shadows, no glow, no gradient wash, no vignette. The image must read as a "
         "quiet background that dark text can sit on top of without losing contrast. "
         "Composition strictly 16:9.")


def prompt_for(variant: str, theme: str) -> str:
    p = PALETTES[theme]
    return (f"A minimal abstract presentation background on {p['desc']}. "
            f"{VARIANTS[variant]} {GUARD}")


def api_key() -> str:
    """Ask the broker. It resolves the one declared location and verifies."""
    r = subprocess.run(
        [sys.executable, str(DATA / ".datacore/lib/creds.py"), "get", "gemini-api-key",
         "--consumer", "render_datacore_plates"],
        capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit(f"broker refused the credential: {r.stderr.strip()[:300]}")
    return r.stdout.strip()


def generate(prompt: str, model: str, key: str) -> bytes | None:
    payload = {"contents": [{"parts": [{"text": prompt}]}],
               "generationConfig": {"responseModalities": ["IMAGE"],
                                    "imageConfig": {"imageSize": "2K"}}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        body = json.load(resp)
    for cand in body.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
    print("   no image in response:", json.dumps(body)[:300])
    return None


def save_plate(data: bytes, path: Path) -> tuple[int, int]:
    im = Image.open(io.BytesIO(data)).convert("RGB")
    tw, th = 1920, 1080
    scale = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left, top = (im.width - tw) // 2, (im.height - th) // 2
    im = im.crop((left, top, left + tw, top + th))
    im.save(path, "JPEG", quality=72, optimize=True)
    return im.size


def contact_sheet(paths: list[Path], out_dir: Path) -> Path:
    cols, w, h = 2, 720, 405
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), (230, 240, 250))
    for i, p in enumerate(paths):
        sheet.paste(Image.open(p).resize((w - 8, h - 8)), ((i % cols) * w + 4, (i // cols) * h + 4))
    out = out_dir / "contact-sheet.png"
    sheet.save(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--only", default="", help="one variant name")
    ap.add_argument("--theme", default="light", choices=sorted(PALETTES))
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        for k, v in VARIANTS.items():
            print(f"  {k:10} {v[:88]}...")
        return 0
    if not a.out:
        return ap.error("--out is required unless --list")

    out_dir = Path(a.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    names = [a.only] if a.only else list(VARIANTS)
    bad = [n for n in names if n not in VARIANTS]
    if bad:
        return ap.error(f"unknown variant(s): {bad}")

    key, made = api_key(), []
    for n in names:
        print(f"  {n:10} generating ({a.theme})...")
        try:
            data = generate(prompt_for(n, a.theme), a.model, key)
        except Exception as e:                      # noqa: BLE001 — report, keep going
            print(f"  {n:10} FAILED: {str(e)[:200]}")
            continue
        if not data:
            continue
        path = out_dir / f"{n}-{a.theme}.jpg"
        size = save_plate(data, path)
        print(f"  {n:10} wrote {path.name} {size} {path.stat().st_size // 1024} KB")
        made.append(path)

    if made:
        print(f"  sheet      {contact_sheet(made, out_dir)}")
    print(f"\n  {len(made)}/{len(names)} plate(s)")
    return 0 if made else 1


if __name__ == "__main__":
    raise SystemExit(main())
