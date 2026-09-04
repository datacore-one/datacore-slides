#!/usr/bin/env python3
"""Re-render a SUBSET of slides from a nano-banana deck, keeping their real slide numbers.

nano-banana-slides.py renders every slide of a markdown deck, and its prompt tells the
model "slide N of TOTAL". When only one or two slides changed, re-rendering the whole
deck wastes money and, worse, replaces approved renders with new ones that may regress.
Feeding a trimmed markdown file does not work either: the slide numbers and total would
be wrong in the prompt ("slide 1 of 2"), and the model uses those for layout cues.

This driver parses the FULL deck, selects the slides you name, and calls the generator
with the true number/total. Output filenames match what nano-banana-slides.py would have
produced, so the PNGs drop straight into an existing slides-vNN/ directory.

Usage:
    python3 render_slides_subset.py deck.md --only 7,8 -o slides-v14.1 [-r reference.pdf]
        [-m gemini-3-pro-image-preview] [--resolution 4k] [--retries 1]

Then rebuild the PDFs:
    python3 nano-banana-slides.py --rebuild-pdf slides-v14.1 --pdf-name deck-v14.1
    python3 make-email-pdf.py slides-v14.1 --out deck-v14.1-email.pdf
"""

import argparse
import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = Path.home() / "Data"
for p in (DATA / ".datacore" / "lib", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _load_generator():
    spec = importlib.util.spec_from_file_location("nano_banana_slides", HERE / "nano-banana-slides.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description="Re-render selected slides of a nano-banana deck")
    ap.add_argument("markdown_file")
    ap.add_argument("--only", required=True, help="comma-separated 1-based slide numbers, e.g. 7,8")
    ap.add_argument("--output-dir", "-o", required=True)
    ap.add_argument("--reference", "-r", default=None, help="reference PDF for style matching")
    ap.add_argument("--model", "-m", default="gemini-3-pro-image-preview")
    ap.add_argument("--resolution", default="4k")
    ap.add_argument("--retries", type=int, default=1, help="extra attempts when the model returns no image")
    args = ap.parse_args()

    nbs = _load_generator()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment (nano-banana-slides.py loads .datacore/env/.env)")
        return 1
    nbs.genai.configure(api_key=api_key)
    model = nbs.genai.GenerativeModel(args.model)

    slides, frontmatter = nbs.parse_markdown_slides(args.markdown_file)
    total = len(slides)
    wanted = {int(x) for x in args.only.split(",") if x.strip()}
    selected = [s for s in slides if s["number"] in wanted]
    missing = wanted - {s["number"] for s in selected}
    if missing:
        print(f"Error: deck has {total} slides; no slide numbered {sorted(missing)}")
        return 1
    print(f"Deck: {total} slides. Rendering {[s['number'] for s in selected]} with true numbering.")

    design_system = frontmatter.get("design_system")
    if design_system:
        print(f"design_system from frontmatter: {len(design_system)} chars")

    refs = nbs.load_reference_images(args.reference) if args.reference else []
    target = nbs.get_resolution(args.resolution)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "generation-log-subset.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {"runs": []}
    run = {
        "source": args.markdown_file,
        "model": args.model,
        "reference": args.reference,
        "resolution": args.resolution,
        "generated_at": datetime.now().isoformat(),
        "slides": [],
    }

    rc = 0
    for s in selected:
        print(f"Generating slide {s['number']} of {total}: {s['title'][:50]}...")
        data = None
        for attempt in range(args.retries + 1):
            data = nbs.generate_slide_image(s, model, total, refs, None, portrait=False,
                                            design_system_override=design_system)
            if data:
                break
            print(f"  no image (attempt {attempt + 1})")
        entry = {"number": s["number"], "title": s["title"]}
        if not data:
            entry["status"] = "generation_failed"
            rc = 2
        else:
            safe = re.sub(r"[^\w\s-]", "", s["title"])[:30].strip().replace(" ", "-").lower()
            fn = f"slide-{s['number']:02d}-{safe}.png"
            ok, orig = nbs.save_image(data, str(out / fn), target)
            entry.update({"file": fn, "original_size": f"{orig[0]}x{orig[1]}" if orig else None,
                          "status": "success" if ok else "save_failed"})
            print(f"  Saved: {fn}" if ok else f"  save failed: {fn}")
            if not ok:
                rc = 2
        run["slides"].append(entry)

    log["runs"].append(run)
    log_path.write_text(json.dumps(log, indent=2))
    print(f"Log: {log_path}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
