# Ralph Loop: [Presentation Title]

Iteratively generate and evaluate [brief description] until all evaluators pass.

## Configuration

Fill in before running:

```
WORKING_DIR:   /path/to/presentation/
SOURCE_MD:     [name].md
OUTPUT_DIR:    [name]/
PDF_NAME:      [name]
AUDIENCE:      [who this is for — defines Evaluator A persona]
```

## Working Directory

`[WORKING_DIR]`

## State

Read `[OUTPUT_DIR]/ralph-state.json`. If missing, start fresh: iteration=1, no feedback.

---

## PHASE 1 — CREATION

1. Read `[SOURCE_MD]` (current content + design notes).
2. If `applied_fixes` exist in state from a previous iteration, apply them now:
   - Content fixes → update the text sections in `[SOURCE_MD]`
   - Design fixes → update the Design notes section in `[SOURCE_MD]`
   - Duplication issues → explicitly add to design notes: "DO NOT repeat [phrase] — it already appears in [section]"
3. Generate the image:
   ```
   DATA_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)" && \
   source "$DATA_DIR/.datacore/env/.env" && \
   python "$DATA_DIR/.datacore/modules/slides/scripts/nano-banana-slides.py" \
     [WORKING_DIR][SOURCE_MD] \
     --output-dir [WORKING_DIR][OUTPUT_DIR] \
     --model gemini-3.1-flash-image-preview \
     --portrait \
     --add-logo "$DATA_DIR/1-datafund/1-tracks/comms/brand/Datafund Logo on transparent (1).png" \
     --logo-height 80 \
     --pdf-name [PDF_NAME]
   ```
   *(Remove `--portrait` and adjust flags for landscape/multi-slide decks)*
4. If generation fails (timeout/error): retry once, then log failure and proceed to evaluation with previous image.
5. Proceed immediately to Phase 2.

---

## PHASE 2 — EVALUATION

Read the generated PNG from `[OUTPUT_DIR]/` using the Read tool (image view).

Run three evaluators in sequence. Each gives a PASS or FAIL with specific, actionable fixes.

---

### EVALUATOR A — THE [AUDIENCE PERSONA]

*[Describe the persona: role, mindset, time pressure, what they care about.]*

*Example: Senior DMCC executive. Sophisticated, time-pressed. Sees 50 decks a year. Has 10 seconds.*

Evaluate:
- Is the core proposition legible at a glance?
- Is the ask completely unambiguous?
- Does it feel worthy of their desk — premium, not generic?
- Is there anything that would make you set it aside?

Verdict: **PASS** or **FAIL**
If FAIL: up to 3 specific, actionable fixes (what to change, not just what's wrong).

---

### EVALUATOR B — THE DESIGN DIRECTOR

*Design director at a premium financial publisher. FT Weekend, Bloomberg Businessweek. Judges print quality.*

Evaluate:
- Is visual hierarchy immediately clear — title → sections → footer?
- Does any illustration add elegance or create noise?
- Is any text duplicated, misplaced, or cut off?
- Does it read as premium and intentional, or as generic AI output?
- Are headings distinct and beautiful, or flat?

Verdict: **PASS** or **FAIL**
If FAIL: up to 3 specific, actionable fixes.

---

### EVALUATOR C — THE COPY EDITOR

*Ruthless copy editor. Hemingway standard. Every word earns its place or gets cut.*

Evaluate:
- Is any phrase repeated or duplicated on the page?
- Is any section heading mismatched to its content?
- Any jargon that obscures rather than clarifies?
- Any sentence that could be cut without loss?
- Is any text visibly different from the source markdown (Gemini rewriting)?

Verdict: **PASS** or **FAIL**
If FAIL: up to 3 specific, actionable fixes.

---

## COMPLETION LOGIC

**If ALL THREE evaluators PASS:**
- Update `[OUTPUT_DIR]/ralph-state.json` with final state.
- Open the PDF: `open [OUTPUT_DIR]/[PDF_NAME].pdf`
- Output: `<promise>[PRESENTATION TITLE] COMPLETE</promise>`

**If ANY evaluator FAILS:**
- Collect all feedback into a unified list of fixes.
- Update `[OUTPUT_DIR]/ralph-state.json`:
  ```json
  {
    "iteration": N,
    "evaluations": [
      {"evaluator": "[AUDIENCE PERSONA]", "verdict": "PASS/FAIL", "feedback": ["..."]},
      {"evaluator": "Design Director",    "verdict": "PASS/FAIL", "feedback": ["..."]},
      {"evaluator": "Copy Editor",        "verdict": "PASS/FAIL", "feedback": ["..."]}
    ],
    "applied_fixes": ["concrete description of each change to make"]
  }
  ```
- Loop continues (Phase 1 picks up the fixes).

---

## CONSTRAINTS

- Max 6 iterations. If not passing by iteration 6, output best version and `<promise>[PRESENTATION TITLE] COMPLETE</promise>`.
- Do not ask the user for input during the loop.
- Each evaluator must be genuinely critical — a PASS is earned, not given.
- Gemini may timeout (504). On timeout: retry once. If second attempt fails, use the last successfully generated image.

---

## KNOWN GEMINI ISSUES (apply fixes proactively in design notes)

- **Text rewriting**: Add "TEXT FIDELITY — CRITICAL: Render body text EXACTLY as written. Do NOT rephrase." to design notes.
- **Date hallucination**: If doc contains a year, add "YEAR IS XXXX — DO NOT CHANGE" near footer spec.
- **Orientation label bleeding**: Never start portrait instruction with text that reads like a visible label (e.g. "TALL A4 PORTRAIT"). Use "ASPECT RATIO CRITICAL: must be taller than wide."
- **System prompt overrides slide notes**: Colour and no-orbs rules must be in `PORTRAIT DOCUMENT COLOR RULES` in the orientation instruction, not just in slide design notes.
- **Landscape output in portrait mode**: Script auto-retries once. If persistent, add "CRITICAL: output must be in PORTRAIT orientation (height > width)" explicitly in design notes.
