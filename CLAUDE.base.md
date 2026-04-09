---
summary: "Visual content generation — Gamma.app presentations, Nano Banana (Gemini) slide images, and iterative quality refinement."
triggers: ["create presentation", "create slides", "index presentation", "sync gamma", "nano banana", "generate slide images"]
context: on_match
---

# Slides Module

## Purpose

Visual content generation with two complementary tools: Gamma.app for structured presentations (API-driven creation, slide reuse, export) and Nano Banana for Gemini-powered slide image generation with brand templates. Includes a reusable slide library and iterative quality workflow.

## Quick Start

> Say "create presentation" for the smart creation wizard, or "generate slide images" for Nano Banana image-based decks.

## How It Works

### Gamma.app Presentations

1. **Purpose & Context** — audience, project, meeting type
2. **Template Selection** — investor-pitch, partner-intro, product-demo, or blank
3. **Slide Suggestions** — search index for reusable existing slides
4. **Generate** — call Gamma API, auto-export PDF, index new slides

MCP Server provides: `gamma_create_presentation`, `gamma_list_themes`, `gamma_list_folders`, `gamma_get_file_urls`.

### Nano Banana (Gemini Image Slides)

Full-image slide decks generated from markdown with `---` separators.

**Workflow:**
1. Write deck markdown with design notes per slide
2. Generate: `nano-banana-slides.py deck.md --output-dir slides/ --resolution 4k --reference style.pdf`
3. Add logos and compile: `nano-banana-slides.py --rebuild-pdf slides/ --add-logo logo.svg`
4. Iterate single slides as needed, rebuild PDF

**Critical patterns:**
- Never edit text in generated images — always regenerate
- Use `--add-logo` for post-processing (not `--logo` flag)
- Add "TEXT FIDELITY — CRITICAL" to design notes (Gemini paraphrases)
- Add "YEAR IS XXXX — DO NOT CHANGE" to prevent date hallucination
- Portrait mode: `--portrait` flag (3508x4961, 300 DPI A4)

### Ralph Loop (High-Stakes Documents)

For external-facing documents, use three evaluator personas over 3-5 iterations:

| Evaluator | Catches |
|-----------|---------|
| A — Audience Persona | Narrative clarity, proposition strength |
| B — Design Director | Visual hierarchy, generic AI aesthetic |
| C — Copy Editor | Text bugs, Gemini rewrites, jargon |

Template: `templates/ralph-nano-banana.md`

## Agents & Commands

| Name | Type | When to use |
|------|------|-------------|
| `gamma-presentation-generator` | agent | Create presentations via Gamma API |
| `gamma-slide-indexer` | agent | Index slides for reuse |
| `presentation-generator` | agent | Gemini image-based presentations |
| `/create-presentation` | skill | Smart creation wizard |
| `/index-presentation` | skill | Index existing deck |
| `/sync-gamma` | skill | Pull presentations from Gamma |

## Key Paths

| Path | Purpose |
|------|---------|
| `[space]/presentations/` | Presentation metadata + source |
| `[space]/presentations/_slides/index.json` | Searchable slide library |
| `[space]/exports/` | Downloaded PDF/PPTX files |
| `templates/` | investor-pitch, partner-intro, product-demo, ralph-nano-banana |

## Setup

Env vars in `.datacore/env/.env`:
- `GAMMA_API_KEY` — required for Gamma.app
- `GEMINI_API_KEY` — required for Nano Banana

## Boundaries

- Gamma API has no edit endpoint — store inputText and recreate with modifications.
- Export URLs expire — download immediately after generation.
- Cannot pull slides from web-created Gamma decks (API-created only).

---

*This file covers structure, capability, and stable configuration. Learned behavior, user corrections, and operational preferences live as engrams — call `plur_recall_hybrid` for those.*
